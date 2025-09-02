"""
SimpleChaseAgent Implementation

This module contains the SimpleChaseAgent class, which is a concrete implementation
of the BaseAgent that exhibits simple pursuit behavior. This agent continuously
moves toward the nearest visible enemy and attacks when in range.

The SimpleChaseAgent:
- Identifies and pursues the nearest enemy
- Moves directly toward the target using simple pathfinding
- Attacks when enemies are within range
- Provides basic aggressive AI behavior
- Serves as a foundation for more sophisticated pursuit strategies
"""

import logging
import math
from typing import Dict, Any, Sequence, Optional

from src.agents.base_agent import BaseAgent, CombatAction, AgentRole, AgentStats
from src.utils.vector2d import Vector2D


class SimpleChaseAgent(BaseAgent):
    """
    A simple aggressive agent that chases and attacks the nearest enemy.
    
    This agent serves as:
    - A basic AI opponent with predictable behavior
    - A foundation for more complex pursuit algorithms
    - A testing agent for combat scenarios
    - An example of simple decision-making logic
    
    Behavior:
    - Movement: Always moves toward the nearest visible enemy
    - Target Selection: Prioritizes closest enemies
    - Combat Actions: Attacks when in range, otherwise moves to close distance
    - Decision Making: Simple distance-based logic with basic combat prioritization
    """
    
    def __init__(self, position: Vector2D, team_id: Optional[str] = None, 
                 role: AgentRole = AgentRole.DPS, stats: Optional[AgentStats] = None):
        """
        Initialize SimpleChaseAgent with default or provided parameters.
        
        Args:
            position: Starting position on the battlefield
            team_id: Team identifier (None for no team)
            role: Agent role (defaults to DPS for aggressive pursuit)
            stats: Agent stats (uses defaults if None)
        """
        super().__init__(
            agent_id=None,  # Let BaseAgent generate a unique ID
            position=position,
            stats=stats,
            genome=None,  # Let BaseAgent create default genome
            role=role,
            team_id=team_id
        )
        
        # Chase-specific properties
        self.current_target: Optional[BaseAgent] = None
        self.chase_distance_threshold = 200.0  # Max distance to consider for chasing
        self.attack_preference_melee = True  # Prefer melee over ranged attacks
        self.retreat_health_threshold = 0.2  # Retreat when health below 20%
        self.last_target_position: Optional[Vector2D] = None
        self.target_lost_time = 0.0
        self.max_target_lost_time = 2.0  # Continue to last known position for 2 seconds
        
        # Log agent creation
        self.log_startup_info()
        self.logger.info(f"⚔️ SimpleChaseAgent {self.agent_id[:8]} initialized - aggressive pursuit mode!")
    
    def update(self, dt: float, battlefield_info: Dict[str, Any]) -> None:
        """
        Update the SimpleChaseAgent for one simulation step.
        
        Args:
            dt: Time step in seconds
            battlefield_info: Current battlefield state information
        """
        # Update status effects and base agent systems
        self.update_status_effects(dt)
        
        # Update target tracking
        self._update_target_tracking(dt)
        
        # Log detailed state if debug level is enabled (every 30 updates to avoid spam)
        if self.logger.isEnabledFor(logging.DEBUG) and hasattr(self, '_update_count'):
            if self._update_count % 30 == 0:
                self.log_state_summary(log_level='DEBUG')
        
        # Track update count for debugging
        if not hasattr(self, '_update_count'):
            self._update_count = 0
        self._update_count += 1
        
        # Log decision context periodically
        if self._update_count % 50 == 0:
            self.log_decision_making(
                {
                    "agent_type": "SimpleChaseAgent", 
                    "current_target": self.current_target.agent_id[:8] if self.current_target else None,
                    "health_pct": self.health_percentage,
                    "alive": self.is_alive
                },
                f"Chase agent status - target: {'Yes' if self.current_target else 'None'}"
            )
    
    def decide_action(self, visible_agents: Sequence['BaseAgent'], 
                     battlefield_info: Dict[str, Any]) -> CombatAction:
        """
        Make a tactical decision based on current situation.
        
        Args:
            visible_agents: List of agents visible to this agent
            battlefield_info: Current battlefield state information
            
        Returns:
            Combat action to take this turn
        """
        # Get visible enemies
        visible_enemies = self.get_enemies(visible_agents)
        
        # Update current target based on visible enemies
        self.current_target = self.select_target(visible_enemies)
        
        # Decide action based on current situation
        action = self._determine_best_action(visible_enemies, visible_agents)
        
        # Log decision if detailed logging enabled
        if self.logger.isEnabledFor(logging.DEBUG):
            self.log_decision_making(
                {
                    "visible_enemies": len(visible_enemies),
                    "current_target": self.current_target.agent_id[:8] if self.current_target else None,
                    "health_pct": self.health_percentage,
                    "can_attack": self.can_attack,
                    "selected_action": action.value
                },
                f"Chase agent decision: {action.value}"
            )
        
        return action
    
    def select_target(self, visible_enemies: Sequence['BaseAgent']) -> Optional['BaseAgent']:
        """
        Select the best target from visible enemies (prioritizes closest).
        
        Args:
            visible_enemies: List of enemy agents within vision range
            
        Returns:
            Best target to pursue, or None if no enemies visible
        """
        if not visible_enemies:
            return None
        
        # Filter enemies that are alive and within chase distance
        valid_targets = [
            enemy for enemy in visible_enemies 
            if enemy.is_alive and self.position.distance_to(enemy.position) <= self.chase_distance_threshold
        ]
        
        if not valid_targets:
            return None
        
        # Prioritize targets based on multiple factors
        best_target = None
        best_score = float('inf')
        
        for enemy in valid_targets:
            distance = self.position.distance_to(enemy.position)
            
            # Calculate target priority score (lower is better)
            score = distance
            
            # Prefer low-health enemies (easier kills)
            health_factor = enemy.health_percentage
            score += health_factor * 50  # Bonus for low health enemies
            
            # Prefer current target if still valid (target persistence)
            if enemy == self.current_target:
                score -= 25  # Slight preference for current target
            
            # Prefer enemies that are closer to our attack range
            if distance <= self.stats.attack_range:
                score -= 30  # Strong preference for in-range targets
            
            if score < best_score:
                best_score = score
                best_target = enemy
        
        # Log target selection
        if best_target and self.logger.isEnabledFor(logging.DEBUG):
            self.log_decision_making(
                {
                    "available_targets": len(valid_targets),
                    "target_id": best_target.agent_id[:8],
                    "target_health": best_target.health_percentage,
                    "distance": self.position.distance_to(best_target.position),
                    "target_score": best_score
                },
                f"Chase agent selected target: {best_target.agent_id[:8]}"
            )
        
        return best_target
    
    def calculate_movement(self, visible_agents: Sequence['BaseAgent'], 
                         battlefield_info: Dict[str, Any]) -> Vector2D:
        """
        Calculate movement toward the current target or last known position.
        
        Args:
            visible_agents: List of agents visible to this agent
            battlefield_info: Current battlefield state information
            
        Returns:
            Velocity vector for movement
        """
        # Check if we should retreat due to low health
        if self.health_percentage < self.retreat_health_threshold:
            return self._calculate_retreat_movement(visible_agents)
        
        # Determine target position
        target_position = None
        movement_reason = "no_target"
        
        if self.current_target and self.current_target.is_alive:
            target_position = self.current_target.position
            movement_reason = "pursuing_target"
        elif self.last_target_position and self.target_lost_time < self.max_target_lost_time:
            target_position = self.last_target_position
            movement_reason = "last_known_position"
        
        if not target_position:
            # No target - minimal random movement to avoid being completely static
            return self._calculate_search_movement()
        
        # Calculate direction to target
        direction = target_position - self.position
        distance = direction.magnitude()
        
        if distance < 0.1:  # Very close to target
            return Vector2D(0, 0)
        
        # Normalize direction and apply speed
        direction_normalized = direction.normalize()
        
        # Determine movement speed based on situation
        speed_factor = self._calculate_speed_factor(distance)
        target_speed = self._get_effective_speed() * speed_factor
        
        velocity = direction_normalized * target_speed
        
        # Log movement decision
        self.log_decision_making(
            {
                "movement_reason": movement_reason,
                "target_distance": distance,
                "speed_factor": speed_factor,
                "target_speed": target_speed,
                "velocity": [velocity.x, velocity.y]
            },
            f"Chase movement: {movement_reason}, distance={distance:.1f}, speed={target_speed:.1f}"
        )
        
        return velocity
    
    def _determine_best_action(self, visible_enemies: Sequence['BaseAgent'], 
                              visible_agents: Sequence['BaseAgent']) -> CombatAction:
        """Determine the best action based on current tactical situation."""
        
        # If low health, prioritize retreat/defense
        if self.health_percentage < self.retreat_health_threshold:
            return CombatAction.RETREAT
        
        # If no target, just move (will be handled by movement calculation)
        if not self.current_target or not self.current_target.is_alive:
            return CombatAction.MOVE
        
        distance_to_target = self.position.distance_to(self.current_target.position)
        
        # If target is in attack range and we can attack
        if distance_to_target <= self.stats.attack_range and self.can_attack:
            # Choose between melee and ranged attack
            if self.attack_preference_melee and distance_to_target <= self.stats.attack_range * 0.5:
                return CombatAction.ATTACK_MELEE
            else:
                return CombatAction.ATTACK_RANGED
        
        # If target is very close but we can't attack (cooldown), consider defending
        if distance_to_target <= self.stats.attack_range * 1.2 and not self.can_attack:
            # Check if we're outnumbered
            nearby_enemies = [e for e in visible_enemies 
                             if self.position.distance_to(e.position) <= self.stats.vision_range * 0.5]
            if len(nearby_enemies) > 1:
                return CombatAction.DEFEND
        
        # Default action is to move toward target
        return CombatAction.MOVE
    
    def _calculate_retreat_movement(self, visible_agents: Sequence['BaseAgent']) -> Vector2D:
        """Calculate movement for retreating from enemies."""
        visible_enemies = self.get_enemies(visible_agents)
        
        if not visible_enemies:
            return Vector2D(0, 0)
        
        # Calculate average enemy position
        enemy_center = Vector2D(0, 0)
        for enemy in visible_enemies:
            enemy_center += enemy.position
        enemy_center = enemy_center / len(visible_enemies)
        
        # Move away from enemy center
        retreat_direction = self.position - enemy_center
        if retreat_direction.magnitude() < 0.1:
            # If at same position, pick random retreat direction
            retreat_direction = Vector2D(1, 0)
        
        retreat_direction = retreat_direction.normalize()
        retreat_speed = self._get_effective_speed() * 0.8  # Slightly slower when retreating
        
        return retreat_direction * retreat_speed
    
    def _calculate_search_movement(self) -> Vector2D:
        """Calculate movement when no target is available (search pattern)."""
        # Simple wandering movement
        if not hasattr(self, '_search_direction'):
            # Initialize random search direction
            import random
            angle = random.uniform(0, 2 * math.pi)
            self._search_direction = Vector2D(math.cos(angle), math.sin(angle))
            self._search_direction_timer = 0.0
        
        # Update search direction timer
        self._search_direction_timer = getattr(self, '_search_direction_timer', 0.0) + 0.1
        
        # Change direction every 3 seconds
        if self._search_direction_timer > 3.0:
            import random
            angle = random.uniform(0, 2 * math.pi)
            self._search_direction = Vector2D(math.cos(angle), math.sin(angle))
            self._search_direction_timer = 0.0
        
        search_speed = self._get_effective_speed() * 0.3  # Slow search movement
        return self._search_direction * search_speed
    
    def _calculate_speed_factor(self, distance_to_target: float) -> float:
        """Calculate speed factor based on distance to target."""
        if distance_to_target <= self.stats.attack_range:
            return 0.5  # Slow down when close to attack
        elif distance_to_target <= self.stats.attack_range * 2:
            return 0.8  # Medium speed in near range
        else:
            return 1.0  # Full speed when far
    
    def _update_target_tracking(self, dt: float) -> None:
        """Update target tracking and last known position."""
        if self.current_target and self.current_target.is_alive:
            self.last_target_position = Vector2D(self.current_target.position.x, self.current_target.position.y)
            self.target_lost_time = 0.0
        else:
            self.target_lost_time += dt
    
    def get_agent_type(self) -> str:
        """Return the agent type identifier."""
        return "SimpleChaseAgent"
    
    def get_strategy_description(self) -> str:
        """Return a description of this agent's strategy."""
        return ("Simple Chase Agent: Aggressively pursues the nearest enemy using basic "
                "pathfinding and distance-based decision making. Attacks when in range, "
                "retreats when low on health, and provides foundational pursuit AI behavior.")
    
    def get_chase_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about this chase agent's behavior.
        
        Returns:
            Dictionary containing chase-specific statistics
        """
        return {
            "current_target": self.current_target.agent_id[:8] if self.current_target else None,
            "target_distance": (self.position.distance_to(self.current_target.position) 
                              if self.current_target else None),
            "last_target_position": ([self.last_target_position.x, self.last_target_position.y] 
                                   if self.last_target_position else None),
            "target_lost_time": self.target_lost_time,
            "health_percentage": self.health_percentage,
            "in_retreat_mode": self.health_percentage < self.retreat_health_threshold,
            "can_attack": self.can_attack,
            "chase_distance_threshold": self.chase_distance_threshold,
            "update_count": getattr(self, '_update_count', 0)
        }
    
    def __str__(self) -> str:
        """String representation of the SimpleChaseAgent."""
        target_info = f", chasing:{self.current_target.agent_id[:8]}" if self.current_target else ""
        return f"SimpleChaseAgent({self.agent_id[:8]}, {self.role.value}, HP:{self.stats.current_health:.0f}{target_info})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the SimpleChaseAgent."""
        return (f"SimpleChaseAgent(id={self.agent_id[:8]}, pos={self.position}, "
                f"team={self.team_id}, role={self.role.value}, "
                f"hp={self.stats.current_health:.1f}/{self.stats.max_health}, "
                f"target={self.current_target.agent_id[:8] if self.current_target else 'None'})")

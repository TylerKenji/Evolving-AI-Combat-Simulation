"""
RandomAgent Implementation

This module contains the RandomAgent class, which is a concrete implementation
of the BaseAgent that makes completely random decisions for movement and combat.
This agent is useful for testing, baseline comparisons, and chaos scenarios.

The RandomAgent:
- Moves in random directions
- Attacks random targets when possible
- Makes random combat decisions
- Provides unpredictable behavior for simulation variety
"""

import random
import math
import logging
from typing import Dict, Any, Sequence, Optional

from src.agents.base_agent import BaseAgent, CombatAction, AgentRole, AgentStats
from src.utils.vector2d import Vector2D


class RandomAgent(BaseAgent):
    """
    A completely random agent that makes random decisions for all actions.
    
    This agent serves as:
    - A baseline for comparing other AI strategies
    - A source of unpredictability in simulations
    - A testing agent for system validation
    - A chaotic element in battles
    
    Behavior:
    - Movement: Random direction and speed
    - Target Selection: Random enemy from visible targets
    - Combat Actions: Random action selection with basic validity checks
    - Decision Making: No strategy, pure randomness
    """
    
    def __init__(self, position: Vector2D, team_id: Optional[str] = None, 
                 role: AgentRole = AgentRole.DPS, stats: Optional[AgentStats] = None):
        """
        Initialize RandomAgent with default or provided parameters.
        
        Args:
            position: Starting position on the battlefield
            team_id: Team identifier (None for no team)
            role: Agent role (defaults to DPS for random chaos)
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
        
        # Random-specific properties
        self.movement_change_frequency = 0.5  # Change direction every 0.5 seconds
        self.last_movement_change = 0.0
        self.current_random_direction = Vector2D(0, 0)
        
        # Log agent creation
        self.log_startup_info()
        self.logger.info(f"🎲 RandomAgent {self.agent_id[:8]} initialized - pure chaos mode!")
    
    def update(self, dt: float, battlefield_info: Dict[str, Any]) -> None:
        """
        Update the RandomAgent for one simulation step.
        
        Args:
            dt: Time step in seconds
            battlefield_info: Current battlefield state information
        """
        # Log detailed state if debug level is enabled
        if self.logger.isEnabledFor(logging.DEBUG):
            self.log_state_summary(log_level='DEBUG')
        
        # Update status effects and base agent systems
        self.update_status_effects(dt)
        
        # Track time for movement changes
        self.last_movement_change += dt
        
        # Randomly change behavior patterns
        if random.random() < 0.1:  # 10% chance per update
            self._randomize_behavior_parameters()
        
        # Log decision context
        self.log_decision_making(
            {"agent_type": "RandomAgent", "dt": dt, "alive": self.is_alive},
            "Random agent update cycle"
        )
    
    def decide_action(self, visible_agents: Sequence['BaseAgent'], 
                     battlefield_info: Dict[str, Any]) -> CombatAction:
        """
        Make a completely random combat decision.
        
        Args:
            visible_agents: List of agents visible to this agent
            battlefield_info: Current battlefield state information
            
        Returns:
            Random combat action
        """
        # Get visible enemies for action context
        visible_enemies = self.get_enemies(visible_agents)
        
        # Define possible actions with weights (some actions more likely)
        action_weights = {
            CombatAction.MOVE: 3.0,          # Most common - always move randomly
            CombatAction.ATTACK_MELEE: 2.0,   # Common if enemies nearby
            CombatAction.ATTACK_RANGED: 1.5,  # Less common
            CombatAction.DODGE: 1.0,          # Defensive action
            CombatAction.DEFEND: 0.8,         # Less likely
            CombatAction.RETREAT: 0.5,        # Rare
            CombatAction.USE_SPECIAL: 0.2,    # Very rare
            CombatAction.COOPERATE: 0.1       # Extremely rare
        }
        
        # Adjust weights based on context
        if not visible_enemies:
            # No enemies visible - prefer movement
            action_weights[CombatAction.ATTACK_MELEE] = 0.0
            action_weights[CombatAction.ATTACK_RANGED] = 0.0
            action_weights[CombatAction.MOVE] = 5.0
        
        if not self.can_attack:
            # Can't attack - reduce attack weights
            action_weights[CombatAction.ATTACK_MELEE] *= 0.1
            action_weights[CombatAction.ATTACK_RANGED] *= 0.1
        
        if self.health_percentage < 0.3:
            # Low health - prefer defensive actions
            action_weights[CombatAction.RETREAT] = 2.0
            action_weights[CombatAction.DODGE] = 2.0
            action_weights[CombatAction.DEFEND] = 1.5
        
        # Weighted random selection
        actions = list(action_weights.keys())
        weights = list(action_weights.values())
        selected_action = random.choices(actions, weights=weights)[0]
        
        # Log the decision
        self.log_decision_making(
            {
                "visible_enemies": len(visible_enemies), 
                "can_attack": self.can_attack,
                "health_pct": self.health_percentage,
                "action_weights": action_weights
            },
            f"Random action selected: {selected_action.value}"
        )
        
        return selected_action
    
    def select_target(self, visible_enemies: Sequence['BaseAgent']) -> Optional['BaseAgent']:
        """
        Select a completely random target from visible enemies.
        
        Args:
            visible_enemies: List of enemy agents within vision range
            
        Returns:
            Randomly selected target, or None if no enemies visible
        """
        if not visible_enemies:
            return None
        
        # Completely random selection
        target = random.choice(visible_enemies)
        
        # Log target selection
        self.log_decision_making(
            {
                "available_targets": len(visible_enemies),
                "target_id": target.agent_id[:8],
                "target_health": target.health_percentage,
                "distance": self.position.distance_to(target.position)
            },
            f"Random target selected: {target.agent_id[:8]}"
        )
        
        return target
    
    def calculate_movement(self, visible_agents: Sequence['BaseAgent'], 
                         battlefield_info: Dict[str, Any]) -> Vector2D:
        """
        Calculate random movement direction and speed.
        
        Args:
            visible_agents: List of agents visible to this agent
            battlefield_info: Current battlefield state information
            
        Returns:
            Random velocity vector
        """
        # Change direction periodically or randomly
        if (self.last_movement_change >= self.movement_change_frequency or 
            random.random() < 0.05):  # 5% chance to change direction anytime
            
            self._generate_random_direction()
            self.last_movement_change = 0.0
        
        # Random speed variation (50% to 100% of max speed)
        speed_factor = random.uniform(0.5, 1.0)
        max_speed = self._get_effective_speed()
        target_speed = max_speed * speed_factor
        
        # Apply speed to direction
        if self.current_random_direction.magnitude() > 0:
            velocity = self.current_random_direction.normalize() * target_speed
        else:
            velocity = Vector2D(0, 0)
        
        # Add some random noise to movement
        noise_x = random.uniform(-10, 10)
        noise_y = random.uniform(-10, 10)
        velocity += Vector2D(noise_x, noise_y)
        
        # Log movement decision
        self.log_decision_making(
            {
                "direction": [self.current_random_direction.x, self.current_random_direction.y],
                "speed_factor": speed_factor,
                "target_speed": target_speed,
                "final_velocity": [velocity.x, velocity.y]
            },
            f"Random movement: speed={target_speed:.1f}, direction=({velocity.x:.1f}, {velocity.y:.1f})"
        )
        
        return velocity
    
    def _generate_random_direction(self) -> None:
        """Generate a new random movement direction."""
        # Random angle in radians
        angle = random.uniform(0, 2 * math.pi)
        
        # Convert to unit vector
        self.current_random_direction = Vector2D(
            math.cos(angle),
            math.sin(angle)
        )
        
        self.logger.debug(f"🎲 Agent {self.agent_id[:8]} new random direction: {self.current_random_direction}")
    
    def _randomize_behavior_parameters(self) -> None:
        """Randomly adjust behavior parameters for more chaos."""
        # Randomize movement change frequency
        self.movement_change_frequency = random.uniform(0.2, 1.5)
        
        # Sometimes force immediate direction change
        if random.random() < 0.3:
            self._generate_random_direction()
            self.last_movement_change = 0.0
        
        self.logger.debug(f"🎲 Agent {self.agent_id[:8]} randomized behavior parameters")
    
    def get_agent_type(self) -> str:
        """Return the agent type identifier."""
        return "RandomAgent"
    
    def get_strategy_description(self) -> str:
        """Return a description of this agent's strategy."""
        return ("Random Agent: Makes completely random decisions for movement, "
                "combat, and target selection. Provides unpredictable behavior "
                "and serves as a baseline for AI comparison.")
    
    def __str__(self) -> str:
        """String representation of the RandomAgent."""
        return f"RandomAgent({self.agent_id[:8]}, {self.role.value}, HP:{self.stats.current_health:.0f})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the RandomAgent."""
        return (f"RandomAgent(id={self.agent_id[:8]}, pos={self.position}, "
                f"team={self.team_id}, role={self.role.value}, "
                f"hp={self.stats.current_health:.1f}/{self.stats.max_health})")

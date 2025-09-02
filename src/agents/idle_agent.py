"""
IdleAgent Implementation

This module contains the IdleAgent class, which is a concrete implementation
of the BaseAgent that does absolutely nothing. This agent is designed purely
for testing purposes and serves as a passive participant in simulations.

The IdleAgent:
- Never moves (zero velocity)
- Never attacks or takes actions
- Never selects targets
- Provides predictable passive behavior
- Serves as a testing baseline and simulation dummy
"""

import logging
from typing import Dict, Any, Sequence, Optional

from src.agents.base_agent import BaseAgent, CombatAction, AgentRole, AgentStats
from src.utils.vector2d import Vector2D


class IdleAgent(BaseAgent):
    """
    A completely passive agent that takes no actions whatsoever.
    
    This agent serves as:
    - A testing dummy for system validation
    - A passive target for other agents to interact with
    - A baseline for measuring agent activity and performance
    - A placeholder agent for incomplete implementations
    
    Behavior:
    - Movement: Always returns zero velocity (no movement)
    - Target Selection: Never selects targets (always returns None)
    - Combat Actions: Always returns MOVE action (but with zero velocity)
    - Decision Making: No decision logic, completely passive
    """
    
    def __init__(self, position: Vector2D, team_id: Optional[str] = None, 
                 role: AgentRole = AgentRole.SUPPORT, stats: Optional[AgentStats] = None):
        """
        Initialize IdleAgent with default or provided parameters.
        
        Args:
            position: Starting position on the battlefield
            team_id: Team identifier (None for no team)
            role: Agent role (defaults to SUPPORT for passive role)
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
        
        # Idle-specific properties
        self.total_idle_time = 0.0
        self.update_count = 0
        
        # Log agent creation
        self.log_startup_info()
        self.logger.info(f"😴 IdleAgent {self.agent_id[:8]} initialized - complete inactivity mode!")
    
    def update(self, dt: float, battlefield_info: Dict[str, Any]) -> None:
        """
        Update the IdleAgent for one simulation step (does nothing).
        
        Args:
            dt: Time step in seconds
            battlefield_info: Current battlefield state information
        """
        # Track idle time and update count for statistics
        self.total_idle_time += dt
        self.update_count += 1
        
        # Update status effects (this is required for proper agent functioning)
        self.update_status_effects(dt)
        
        # Log detailed state if debug level is enabled (every 50 updates to avoid spam)
        if self.logger.isEnabledFor(logging.DEBUG) and self.update_count % 50 == 0:
            self.log_state_summary(log_level='DEBUG')
        
        # Log occasional idle status (every 100 updates)
        if self.update_count % 100 == 0:
            self.log_decision_making(
                {
                    "agent_type": "IdleAgent", 
                    "total_idle_time": self.total_idle_time,
                    "update_count": self.update_count,
                    "alive": self.is_alive
                },
                f"Idle agent status check - been idle for {self.total_idle_time:.1f}s"
            )
    
    def decide_action(self, visible_agents: Sequence['BaseAgent'], 
                     battlefield_info: Dict[str, Any]) -> CombatAction:
        """
        Make a decision (always MOVE with zero velocity).
        
        Args:
            visible_agents: List of agents visible to this agent
            battlefield_info: Current battlefield state information
            
        Returns:
            Always returns CombatAction.MOVE (but movement will be zero)
        """
        # Log decision context if detailed logging enabled
        if self.logger.isEnabledFor(logging.DEBUG):
            self.log_decision_making(
                {
                    "visible_agents": len(visible_agents),
                    "action": "MOVE",
                    "movement": "zero_velocity"
                },
                "Idle agent decides to remain stationary"
            )
        
        # Always return MOVE action (but calculate_movement will return zero velocity)
        return CombatAction.MOVE
    
    def select_target(self, visible_enemies: Sequence['BaseAgent']) -> Optional['BaseAgent']:
        """
        Select a target (always returns None - idle agents don't target).
        
        Args:
            visible_enemies: List of enemy agents within vision range
            
        Returns:
            Always returns None (no target selection)
        """
        # Log target selection context if detailed logging enabled
        if self.logger.isEnabledFor(logging.DEBUG) and visible_enemies:
            self.log_decision_making(
                {
                    "available_targets": len(visible_enemies),
                    "selection": "none",
                    "reason": "idle_agent_policy"
                },
                f"Idle agent ignores {len(visible_enemies)} available targets"
            )
        
        # Never select targets
        return None
    
    def calculate_movement(self, visible_agents: Sequence['BaseAgent'], 
                         battlefield_info: Dict[str, Any]) -> Vector2D:
        """
        Calculate movement (always returns zero velocity).
        
        Args:
            visible_agents: List of agents visible to this agent
            battlefield_info: Current battlefield state information
            
        Returns:
            Always returns Vector2D(0, 0) for no movement
        """
        # Log movement decision if detailed logging enabled
        if self.logger.isEnabledFor(logging.DEBUG):
            self.log_decision_making(
                {
                    "movement_type": "stationary",
                    "velocity": [0.0, 0.0],
                    "reason": "idle_agent_behavior"
                },
                "Idle agent remains completely stationary"
            )
        
        # Never move
        return Vector2D(0, 0)
    
    def get_idle_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about this idle agent's inactivity.
        
        Returns:
            Dictionary containing idle statistics
        """
        return {
            "total_idle_time": self.total_idle_time,
            "update_count": self.update_count,
            "average_update_interval": self.total_idle_time / max(1, self.update_count),
            "position": [self.position.x, self.position.y],
            "health_percentage": self.health_percentage,
            "is_alive": self.is_alive,
            "team_id": self.team_id,
            "role": self.role.value
        }
    
    def get_agent_type(self) -> str:
        """Return the agent type identifier."""
        return "IdleAgent"
    
    def get_strategy_description(self) -> str:
        """Return a description of this agent's strategy."""
        return ("Idle Agent: Takes no actions whatsoever. Remains completely passive "
                "and stationary. Serves as a testing dummy, baseline for performance "
                "measurement, and placeholder for incomplete implementations.")
    
    def __str__(self) -> str:
        """String representation of the IdleAgent."""
        return f"IdleAgent({self.agent_id[:8]}, {self.role.value}, HP:{self.stats.current_health:.0f}, idle:{self.total_idle_time:.1f}s)"
    
    def __repr__(self) -> str:
        """Detailed string representation of the IdleAgent."""
        return (f"IdleAgent(id={self.agent_id[:8]}, pos={self.position}, "
                f"team={self.team_id}, role={self.role.value}, "
                f"hp={self.stats.current_health:.1f}/{self.stats.max_health}, "
                f"idle_time={self.total_idle_time:.1f}s, updates={self.update_count})")

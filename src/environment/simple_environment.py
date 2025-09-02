"""
Simple Environment Implementation

This module provides a basic concrete implementation of the BaseEnvironment
class for initial testing and development. It includes essential features
like agent management, basic collision detection, and boundary enforcement.

Features:
- Agent spawning and lifecycle management
- Simple circular collision detection
- Boundary clamping for agent movement
- Basic battlefield information for agents
- Performance monitoring
- Event system for agent interactions

This implementation serves as a foundation for more complex environments
and provides a working example of the environment interface.
"""

from typing import List, Dict, Any, Optional
import time
import math

from .base_environment import (
    BaseEnvironment, EnvironmentState, CollisionType, CollisionEvent
)
from src.utils.vector2d import Vector2D
from src.utils.logging_config import get_logger


class SimpleEnvironment(BaseEnvironment):
    """
    Simple concrete implementation of BaseEnvironment.
    
    This environment provides basic functionality including:
    - Agent management and spawning
    - Circular collision detection
    - Boundary enforcement
    - Simple battlefield information
    """
    
    def __init__(
        self,
        width: float = 800.0,
        height: float = 600.0,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the simple environment.
        
        Args:
            width: Battlefield width in pixels
            height: Battlefield height in pixels
            config: Optional configuration dictionary
        """
        super().__init__(width, height, config)
        
        # Simple environment specific settings
        self.collision_radius = self.config.get('collision_radius', 10.0)
        self.enable_collisions = self.config.get('collision_detection', True)
        
        self.logger.info(f"🏟️ SimpleEnvironment initialized with collision radius {self.collision_radius}")
    
    def update(self, dt: float) -> None:
        """
        Update the environment for one simulation step.
        
        Args:
            dt: Time step in seconds
        """
        if self.state != EnvironmentState.RUNNING:
            return
        
        update_start = time.time()
        
        # Clear previous collision events
        self.collision_events.clear()
        
        # Update all living agents
        living_agents = self.get_living_agents()
        for agent in living_agents:
            try:
                # Get battlefield info for this agent
                battlefield_info = self.get_battlefield_info(agent.agent_id)
                
                # Let agent update its state
                agent.update(dt, battlefield_info)
                
                # Update agent position in our tracking
                self.agent_positions[agent.agent_id] = agent.position
                
            except Exception as e:
                self.logger.error(f"❌ Error updating agent {agent.agent_id[:8]}: {e}")
        
        # Check for collisions if enabled
        if self.enable_collisions:
            collision_start = time.time()
            collisions = self.check_collisions()
            collision_time = time.time() - collision_start
            self.metrics.collision_check_times.append(collision_time)
            
            # Process collision events
            for collision in collisions:
                self.emit_event('collision', collision)
        
        # Update metrics
        update_time = time.time() - update_start
        self.metrics.update_times.append(update_time)
        self.update_metrics(dt)
        
        # Check for simulation end conditions
        living_count = len(living_agents)
        if living_count == 0:
            self.logger.info("🏁 Simulation ended - no agents remaining")
            self.stop()
        elif living_count == 1:
            winner = living_agents[0]
            self.logger.info(f"🏆 Simulation ended - winner: Agent {winner.agent_id[:8]}")
            self.stop()
    
    def add_agent(self, agent: Any, position: Optional[Vector2D] = None) -> bool:
        """
        Add an agent to the environment.
        
        Args:
            agent: Agent instance to add
            position: Optional spawn position
            
        Returns:
            True if agent was successfully added
        """
        # Check if we're at capacity
        if len(self.agents) >= self.max_agents:
            self.logger.warning(f"⚠️ Cannot add agent - at maximum capacity ({self.max_agents})")
            return False
        
        # Check if agent ID already exists
        if agent.agent_id in self.agents:
            self.logger.warning(f"⚠️ Agent {agent.agent_id[:8]} already exists in environment")
            return False
        
        # Determine spawn position
        if position is None:
            if self.agent_spawn_points:
                # Use next available spawn point
                spawn_index = len(self.agents) % len(self.agent_spawn_points)
                position = self.agent_spawn_points[spawn_index]
            else:
                # Generate random position
                position = self.get_random_position()
        
        # Validate position
        if not self.is_position_valid(position):
            position = self.clamp_position(position)
        
        # Set agent position
        agent.position = position
        
        # Add to tracking dictionaries
        self.agents[agent.agent_id] = agent
        self.agent_positions[agent.agent_id] = position
        
        # Update metrics
        self.metrics.agents_spawned += 1
        
        self.logger.info(f"➕ Agent {agent.agent_id[:8]} added at {position}")
        
        # Emit spawn event
        self.emit_event('agent_spawned', {
            'agent': agent,
            'position': position,
            'timestamp': time.time()
        })
        
        return True
    
    def remove_agent(self, agent_id: str) -> bool:
        """
        Remove an agent from the environment.
        
        Args:
            agent_id: ID of agent to remove
            
        Returns:
            True if agent was successfully removed
        """
        if agent_id not in self.agents:
            self.logger.warning(f"⚠️ Agent {agent_id[:8]} not found in environment")
            return False
        
        agent = self.agents[agent_id]
        
        # Remove from tracking dictionaries
        del self.agents[agent_id]
        if agent_id in self.agent_positions:
            del self.agent_positions[agent_id]
        
        self.logger.info(f"➖ Agent {agent_id[:8]} removed from environment")
        
        # Emit removal event
        self.emit_event('agent_removed', {
            'agent': agent,
            'agent_id': agent_id,
            'timestamp': time.time()
        })
        
        return True
    
    def check_collisions(self) -> List[CollisionEvent]:
        """
        Check for collisions between agents using simple circular collision detection.
        
        Returns:
            List of collision events detected
        """
        collisions = []
        living_agents = self.get_living_agents()
        
        # Check agent-agent collisions
        for i, agent1 in enumerate(living_agents):
            for agent2 in living_agents[i + 1:]:
                distance = agent1.position.distance_to(agent2.position)
                collision_distance = self.collision_radius * 2  # Both agents have radius
                
                if distance < collision_distance:
                    # Calculate collision point and normal
                    collision_point = agent1.position + (agent2.position - agent1.position) * 0.5
                    collision_normal = (agent2.position - agent1.position).normalize()
                    
                    collision = CollisionEvent(
                        collision_type=CollisionType.AGENT_AGENT,
                        primary_object=agent1,
                        secondary_object=agent2,
                        collision_point=collision_point,
                        collision_normal=collision_normal
                    )
                    
                    collisions.append(collision)
                    self.metrics.collisions_detected += 1
        
        # Check agent-boundary collisions
        for agent in living_agents:
            boundary_collision = None
            
            if agent.position.x <= self.collision_radius:
                boundary_collision = CollisionEvent(
                    collision_type=CollisionType.AGENT_BOUNDARY,
                    primary_object=agent,
                    collision_point=Vector2D(0, agent.position.y),
                    collision_normal=Vector2D(1, 0)
                )
            elif agent.position.x >= self.width - self.collision_radius:
                boundary_collision = CollisionEvent(
                    collision_type=CollisionType.AGENT_BOUNDARY,
                    primary_object=agent,
                    collision_point=Vector2D(self.width, agent.position.y),
                    collision_normal=Vector2D(-1, 0)
                )
            elif agent.position.y <= self.collision_radius:
                boundary_collision = CollisionEvent(
                    collision_type=CollisionType.AGENT_BOUNDARY,
                    primary_object=agent,
                    collision_point=Vector2D(agent.position.x, 0),
                    collision_normal=Vector2D(0, 1)
                )
            elif agent.position.y >= self.height - self.collision_radius:
                boundary_collision = CollisionEvent(
                    collision_type=CollisionType.AGENT_BOUNDARY,
                    primary_object=agent,
                    collision_point=Vector2D(agent.position.x, self.height),
                    collision_normal=Vector2D(0, -1)
                )
            
            if boundary_collision:
                collisions.append(boundary_collision)
                self.metrics.collisions_detected += 1
        
        # Store collision events
        self.collision_events.extend(collisions)
        
        return collisions
    
    def get_battlefield_info(self, agent_id: str) -> Dict[str, Any]:
        """
        Get battlefield information visible to a specific agent.
        
        Args:
            agent_id: ID of the agent requesting information
            
        Returns:
            Dictionary containing battlefield state information
        """
        requesting_agent = self.agents.get(agent_id)
        if not requesting_agent:
            return {}
        
        # Get all visible agents for this agent
        all_agents = self.get_living_agents()
        visible_agents = requesting_agent.get_visible_agents(all_agents)
        
        # Create battlefield info
        battlefield_info = {
            'environment_bounds': self.bounds,
            'current_time': self.simulation_time,
            'time_step': self.time_step,
            'agent_count': len(all_agents),
            'visible_agents': visible_agents,
            'collision_events': [
                event for event in self.collision_events 
                if (event.primary_object == requesting_agent or 
                    event.secondary_object == requesting_agent)
            ],
            'terrain_at_position': None,  # Simple environment has no terrain
            'environment_state': self.state.value
        }
        
        # Add terrain information if available
        if self.terrain_grid:
            terrain_tile = self.get_terrain_at(requesting_agent.position)
            battlefield_info['terrain_at_position'] = terrain_tile
        
        return battlefield_info
    
    def spawn_agents_in_formation(self, agents: List[Any], formation: str = 'circle', 
                                center: Optional[Vector2D] = None, spacing: float = 50.0) -> bool:
        """
        Spawn multiple agents in a specific formation.
        
        Args:
            agents: List of agents to spawn
            formation: Formation type ('circle', 'line', 'grid', 'random')
            center: Center point for formation (defaults to environment center)
            spacing: Spacing between agents
            
        Returns:
            True if all agents were successfully spawned
        """
        if len(agents) > self.max_agents:
            self.logger.warning(f"⚠️ Cannot spawn {len(agents)} agents - exceeds maximum ({self.max_agents})")
            return False
        
        # Use coordinate system for position generation
        if center is None:
            center = self.center
        
        positions = self.coordinate_system.get_spawn_positions(
            len(agents), formation, center, spacing
        )
        
        # Spawn all agents
        success_count = 0
        for agent, position in zip(agents, positions):
            if self.add_agent(agent, position):
                success_count += 1
        
        self.logger.info(f"🎯 Spawned {success_count}/{len(agents)} agents in {formation} formation")
        return success_count == len(agents)
    
    def clear_dead_agents(self) -> int:
        """
        Remove all dead agents from the environment.
        
        Returns:
            Number of agents removed
        """
        dead_agent_ids = [
            agent_id for agent_id, agent in self.agents.items() 
            if not agent.is_alive
        ]
        
        for agent_id in dead_agent_ids:
            self.remove_agent(agent_id)
        
        if dead_agent_ids:
            self.logger.info(f"🧹 Cleared {len(dead_agent_ids)} dead agents")
        
        return len(dead_agent_ids)
    
    def get_environment_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current environment state.
        
        Returns:
            Dictionary containing environment summary
        """
        living_agents = self.get_living_agents()
        teams = {}
        
        # Count agents by team
        for agent in living_agents:
            team_id = agent.team_id or 'no_team'
            teams[team_id] = teams.get(team_id, 0) + 1
        
        return {
            'environment_id': self.environment_id,
            'state': self.state.value,
            'dimensions': f"{self.width}x{self.height}",
            'total_agents': len(self.agents),
            'living_agents': len(living_agents),
            'dead_agents': len(self.agents) - len(living_agents),
            'teams': teams,
            'simulation_time': round(self.simulation_time, 2),
            'real_time_elapsed': round(time.time() - self.start_time, 2),
            'performance': self.get_performance_stats()
        }

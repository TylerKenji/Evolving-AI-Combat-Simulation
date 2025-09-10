"""
Battle Environment Implementation

This module provides a comprehensive battle environment implementation
designed specifically for AI combat simulation. It extends the BaseEnvironment
with advanced features tailored for combat scenarios.

Key Features:
- Multi-team agent management
- Advanced collision detection with spatial partitioning
- Weapon and projectile systems integration
- Tactical battlefield information (cover, line of sight)
- Team-based spawning and objectives
- Combat-specific metrics and statistics
- Advanced event system for combat interactions
- Performance optimizations for large-scale battles

This is the primary environment class for the Battle AI simulation system.
"""

from typing import List, Dict, Any, Optional, Set, Tuple
import time
import math
import random
from collections import defaultdict
from enum import Enum

from .base_environment import (
    BaseEnvironment, EnvironmentState, CollisionType, CollisionEvent,
    TerrainType, TerrainTile
)
from src.utils.vector2d import Vector2D
from src.utils.logging_config import get_logger


class SpawnStrategy(Enum):
    """Different strategies for spawning agents."""
    RANDOM = "random"              # Random positions
    TEAMS_OPPOSITE = "teams_opposite"  # Teams spawn on opposite sides
    CORNERS = "corners"            # Agents spawn in corners
    CIRCLE = "circle"              # Agents spawn in a circle
    PREDEFINED = "predefined"      # Use predefined spawn points


class BattlePhase(Enum):
    """Different phases of a battle."""
    PREPARATION = "preparation"    # Setup phase before battle
    ACTIVE_COMBAT = "active_combat"  # Main battle phase
    CLEANUP = "cleanup"            # Final resolution phase
    COMPLETED = "completed"        # Battle finished


class TeamInfo:
    """Information about a team in the battle."""
    
    def __init__(self, team_id: str, name: str = "", color: str = "#FFFFFF"):
        self.team_id = team_id
        self.name = name or team_id
        self.color = color
        self.spawn_area: Optional[Tuple[Vector2D, Vector2D]] = None  # (min, max) corners
        self.agent_ids: Set[str] = set()
        self.score: int = 0
        self.kills: int = 0
        self.deaths: int = 0
        
    def add_agent(self, agent_id: str) -> None:
        """Add an agent to this team."""
        self.agent_ids.add(agent_id)
    
    def remove_agent(self, agent_id: str) -> None:
        """Remove an agent from this team."""
        self.agent_ids.discard(agent_id)
    
    @property
    def agent_count(self) -> int:
        """Get number of agents in this team."""
        return len(self.agent_ids)


class BattleEnvironment(BaseEnvironment):
    """
    Advanced battle environment for AI combat simulation.
    
    This environment is specifically designed for combat scenarios with
    support for teams, weapons, projectiles, and tactical elements.
    """
    
    def __init__(
        self,
        width: float = 1000.0,
        height: float = 800.0,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the battle environment.
        
        Args:
            width: Battlefield width in pixels
            height: Battlefield height in pixels
            config: Optional configuration dictionary
        """
        # Set up default configuration for battle environment
        default_battle_config = {
            'battlefield_width': width,  # Use the expected key name
            'battlefield_height': height,  # Use the expected key name
            'time_step': 0.016,  # Default to ~60 FPS
            'max_agents': 100,  # Default max agents
            'collision_radius': 12.0,
            'spatial_partitioning': True,
            'grid_cell_size': 64.0,
            'max_teams': 8,
            'spawn_strategy': 'teams_opposite',
            'spawn_margin': 50.0,  # Distance from edges for spawning
            'friendly_fire': False,
            'vision_range': 200.0,
            'projectile_system': True,
            'terrain_enabled': False,
            'collision_detection': True,
            'physics_enabled': True
        }
        
        if config:
            default_battle_config.update(config)
        
        super().__init__(width, height, default_battle_config)
        
        # Battle-specific properties
        self.battle_phase = BattlePhase.PREPARATION
        self.teams: Dict[str, TeamInfo] = {}
        self.team_agent_map: Dict[str, str] = {}  # agent_id -> team_id
        
        # Spatial partitioning for performance
        self.spatial_grid_enabled = self.config.get('spatial_partitioning', True)
        self.grid_cell_size = self.config.get('grid_cell_size', 64.0)
        self.spatial_grid: Dict[Tuple[int, int], Set[str]] = defaultdict(set)
        
        # Combat properties
        self.collision_radius = self.config.get('collision_radius', 12.0)
        self.spawn_strategy = SpawnStrategy(self.config.get('spawn_strategy', 'teams_opposite'))
        self.spawn_margin = self.config.get('spawn_margin', 50.0)
        self.friendly_fire = self.config.get('friendly_fire', False)
        self.vision_range = self.config.get('vision_range', 200.0)
        
        # Projectile system (placeholder for future implementation)
        self.projectiles: List[Any] = []
        self.projectile_system_enabled = self.config.get('projectile_system', True)
        
        # Battle statistics
        self.battle_start_time: Optional[float] = None
        self.battle_duration: float = 0.0
        self.total_kills: int = 0
        self.total_shots_fired: int = 0
        
        # Initialize spawn points based on strategy
        self._initialize_spawn_points()
        
        self.logger.info(f"⚔️ BattleEnvironment initialized "
                        f"({self.width}x{self.height}) with {self.spawn_strategy.value} spawning")
    
    # === Battle Management ===
    
    def start_battle(self) -> None:
        """Start the battle phase."""
        if self.battle_phase == BattlePhase.PREPARATION:
            self.battle_phase = BattlePhase.ACTIVE_COMBAT
            self.battle_start_time = time.time()
            self.start()  # Start the environment
            self.logger.info(f"⚔️ Battle started with {len(self.teams)} teams, "
                           f"{self.agent_count} total agents")
    
    def end_battle(self) -> None:
        """End the battle and calculate results."""
        if self.battle_phase == BattlePhase.ACTIVE_COMBAT:
            self.battle_phase = BattlePhase.CLEANUP
            if self.battle_start_time:
                self.battle_duration = time.time() - self.battle_start_time
            
            self._calculate_battle_results()
            self.battle_phase = BattlePhase.COMPLETED
            self.stop()  # Stop the environment
            
            self.logger.info(f"🏁 Battle ended after {self.battle_duration:.1f}s")
    
    def _calculate_battle_results(self) -> None:
        """Calculate final battle statistics."""
        for team in self.teams.values():
            living_agents = [aid for aid in team.agent_ids 
                           if aid in self.agents and self.agents[aid].is_alive]
            team.score = len(living_agents) * 100 + team.kills * 10
        
        winner = max(self.teams.values(), key=lambda t: t.score) if self.teams else None
        if winner:
            self.logger.info(f"🏆 Team '{winner.name}' wins with score {winner.score}!")
    
    # === Team Management ===
    
    def create_team(
        self, 
        team_id: str, 
        name: str = "", 
        color: str = "#FFFFFF"
    ) -> bool:
        """
        Create a new team.
        
        Args:
            team_id: Unique identifier for the team
            name: Display name for the team
            color: Team color in hex format
            
        Returns:
            True if team was created successfully
        """
        if team_id in self.teams:
            self.logger.warning(f"⚠️ Team {team_id} already exists")
            return False
        
        if len(self.teams) >= self.config.get('max_teams', 8):
            self.logger.warning(f"⚠️ Maximum number of teams reached")
            return False
        
        self.teams[team_id] = TeamInfo(team_id, name, color)
        self._assign_team_spawn_area(team_id)
        
        self.logger.info(f"👥 Team '{name or team_id}' created")
        return True
    
    def _assign_team_spawn_area(self, team_id: str) -> None:
        """Assign a spawn area to a team based on current spawn strategy."""
        team_count = len(self.teams)
        team = self.teams[team_id]
        
        if self.spawn_strategy == SpawnStrategy.TEAMS_OPPOSITE and team_count <= 2:
            if team_count == 1:  # First team - left side
                team.spawn_area = (
                    Vector2D(self.spawn_margin, self.spawn_margin),
                    Vector2D(self.width * 0.3, self.height - self.spawn_margin)
                )
            else:  # Second team - right side
                team.spawn_area = (
                    Vector2D(self.width * 0.7, self.spawn_margin),
                    Vector2D(self.width - self.spawn_margin, self.height - self.spawn_margin)
                )
        elif self.spawn_strategy == SpawnStrategy.TEAMS_OPPOSITE and team_count > 2:
            # Fallback for additional teams beyond 2 - use random areas
            team.spawn_area = (
                Vector2D(self.spawn_margin, self.spawn_margin),
                Vector2D(self.width - self.spawn_margin, self.height - self.spawn_margin)
            )
        
        elif self.spawn_strategy == SpawnStrategy.CORNERS:
            # Assign corners in order
            corners = [
                (Vector2D(self.spawn_margin, self.spawn_margin), 
                 Vector2D(self.width * 0.4, self.height * 0.4)),  # Top-left
                (Vector2D(self.width * 0.6, self.spawn_margin), 
                 Vector2D(self.width - self.spawn_margin, self.height * 0.4)),  # Top-right
                (Vector2D(self.spawn_margin, self.height * 0.6), 
                 Vector2D(self.width * 0.4, self.height - self.spawn_margin)),  # Bottom-left
                (Vector2D(self.width * 0.6, self.height * 0.6), 
                 Vector2D(self.width - self.spawn_margin, self.height - self.spawn_margin))  # Bottom-right
            ]
            if team_count <= len(corners):
                team.spawn_area = corners[team_count - 1]
            else:
                # Fallback to random area if too many teams for corners
                team.spawn_area = (
                    Vector2D(self.spawn_margin, self.spawn_margin),
                    Vector2D(self.width - self.spawn_margin, self.height - self.spawn_margin)
                )
        
        elif self.spawn_strategy == SpawnStrategy.CIRCLE:
            # Assign sectors around a circle for team areas
            center = Vector2D(self.width / 2, self.height / 2)
            radius = min(self.width, self.height) * 0.35
            angle_per_team = (2 * math.pi) / max(team_count, 1)
            team_angle = (team_count - 1) * angle_per_team
            
            # Create sector area for this team
            sector_size = min(self.width, self.height) * 0.15
            team_center_x = center.x + radius * math.cos(team_angle)
            team_center_y = center.y + radius * math.sin(team_angle)
            
            team.spawn_area = (
                Vector2D(
                    max(self.spawn_margin, team_center_x - sector_size),
                    max(self.spawn_margin, team_center_y - sector_size)
                ),
                Vector2D(
                    min(self.width - self.spawn_margin, team_center_x + sector_size),
                    min(self.height - self.spawn_margin, team_center_y + sector_size)
                )
            )
            
        elif self.spawn_strategy == SpawnStrategy.RANDOM:
            # For random spawning, each team gets the entire battlefield
            team.spawn_area = (
                Vector2D(self.spawn_margin, self.spawn_margin),
                Vector2D(self.width - self.spawn_margin, self.height - self.spawn_margin)
            )
            
        elif self.spawn_strategy == SpawnStrategy.PREDEFINED:
            # For predefined spawning, assign area around predefined points if available
            if self.agent_spawn_points and team_count <= len(self.agent_spawn_points):
                spawn_point = self.agent_spawn_points[team_count - 1]
                area_size = 100  # Default area size around spawn point
                team.spawn_area = (
                    Vector2D(
                        max(self.spawn_margin, spawn_point.x - area_size),
                        max(self.spawn_margin, spawn_point.y - area_size)
                    ),
                    Vector2D(
                        min(self.width - self.spawn_margin, spawn_point.x + area_size),
                        min(self.height - self.spawn_margin, spawn_point.y + area_size)
                    )
                )
            else:
                # Fallback to random area if no predefined points
                team.spawn_area = (
                    Vector2D(self.spawn_margin, self.spawn_margin),
                    Vector2D(self.width - self.spawn_margin, self.height - self.spawn_margin)
                )
        
        # Final safety check - ensure spawn area is always assigned
        if team.spawn_area is None:
            team.spawn_area = (
                Vector2D(self.spawn_margin, self.spawn_margin),
                Vector2D(self.width - self.spawn_margin, self.height - self.spawn_margin)
            )
    
    def get_team(self, team_id: str) -> Optional[TeamInfo]:
        """Get team information by ID."""
        return self.teams.get(team_id)
    
    def get_agent_team(self, agent_id: str) -> Optional[str]:
        """Get the team ID for an agent."""
        return self.team_agent_map.get(agent_id)
    
    # === Agent Management ===
    
    def add_agent(
        self, 
        agent: Any, 
        position: Optional[Vector2D] = None,
        team_id: Optional[str] = None
    ) -> bool:
        """
        Add an agent to the environment.
        
        Args:
            agent: Agent instance to add
            position: Optional spawn position (if None, uses team spawn area)
            team_id: Team to assign agent to
            
        Returns:
            True if agent was successfully added
        """
        if len(self.agents) >= self.max_agents:
            self.logger.warning(f"⚠️ Maximum agent limit ({self.max_agents}) reached")
            return False
        
        if agent.agent_id in self.agents:
            self.logger.warning(f"⚠️ Agent {agent.agent_id[:8]} already exists")
            return False
        
        # Determine spawn position
        spawn_position = position
        if spawn_position is None:
            spawn_position = self._get_spawn_position(team_id)
        
        # Ensure position is within bounds
        spawn_position = self.coordinate_system.world_bounds.clamp_position(spawn_position)
        
        # Set agent position
        agent.position = spawn_position
        
        # Add to agent tracking
        self.agents[agent.agent_id] = agent
        self.agent_positions[agent.agent_id] = spawn_position
        
        # Add to team if specified
        if team_id and team_id in self.teams:
            self.teams[team_id].add_agent(agent.agent_id)
            self.team_agent_map[agent.agent_id] = team_id
            agent.team = team_id  # Set agent's team property if it exists
        
        # Update spatial grid
        if self.spatial_grid_enabled:
            self._add_agent_to_spatial_grid(agent.agent_id, spawn_position)
        
        # Update metrics
        self.metrics.agents_spawned += 1
        self.metrics.agents_alive += 1
        
        team_info = f" (Team: {team_id})" if team_id else ""
        self.logger.info(f"🚀 Agent {agent.agent_id[:8]} spawned at {spawn_position}{team_info}")
        
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
            return False
        
        agent = self.agents[agent_id]
        
        # Remove from team
        team_id = self.team_agent_map.get(agent_id)
        if team_id and team_id in self.teams:
            self.teams[team_id].remove_agent(agent_id)
            self.teams[team_id].deaths += 1
            del self.team_agent_map[agent_id]
        
        # Remove from spatial grid
        if self.spatial_grid_enabled:
            self._remove_agent_from_spatial_grid(agent_id)
        
        # Remove from tracking
        del self.agents[agent_id]
        self.agent_positions.pop(agent_id, None)
        
        # Update metrics
        if agent.is_alive:
            self.metrics.agents_alive -= 1
        self.metrics.agents_dead += 1
        
        self.logger.info(f"💀 Agent {agent_id[:8]} removed from battle")
        return True
    
    def _get_spawn_position(self, team_id: Optional[str] = None) -> Vector2D:
        """
        Get a spawn position based on the current spawn strategy.
        
        Args:
            team_id: Team ID for team-based spawning
            
        Returns:
            Spawn position
        """
        if team_id and team_id in self.teams and self.teams[team_id].spawn_area is not None:
            # Spawn within team area
            spawn_area = self.teams[team_id].spawn_area
            if spawn_area is not None and len(spawn_area) == 2:
                min_pos, max_pos = spawn_area
                return Vector2D(
                    random.uniform(min_pos.x, max_pos.x),
                    random.uniform(min_pos.y, max_pos.y)
                )
            else:
                # Fallback if spawn area is malformed
                self.logger.warning(f"⚠️ Invalid spawn area for team {team_id}, using fallback")
                return Vector2D(
                    random.uniform(self.spawn_margin, self.width - self.spawn_margin),
                    random.uniform(self.spawn_margin, self.height - self.spawn_margin)
                )
        
        elif self.spawn_strategy == SpawnStrategy.CIRCLE:
            # Spawn in a circle around the center
            center = self.center
            angle = random.uniform(0, 2 * math.pi)
            radius = random.uniform(50, min(self.width, self.height) * 0.3)
            return Vector2D(
                center.x + radius * math.cos(angle),
                center.y + radius * math.sin(angle)
            )
        
        elif self.spawn_strategy == SpawnStrategy.PREDEFINED and self.agent_spawn_points:
            # Use predefined spawn points
            return random.choice(self.agent_spawn_points)
        
        else:
            # Random spawn with margin
            return Vector2D(
                random.uniform(self.spawn_margin, self.width - self.spawn_margin),
                random.uniform(self.spawn_margin, self.height - self.spawn_margin)
            )
    
    def _initialize_spawn_points(self) -> None:
        """Initialize spawn points based on the environment size."""
        # Create a grid of spawn points for predefined spawning
        grid_size = 8
        x_step = (self.width - 2 * self.spawn_margin) / grid_size
        y_step = (self.height - 2 * self.spawn_margin) / grid_size
        
        for i in range(grid_size):
            for j in range(grid_size):
                x = self.spawn_margin + i * x_step + x_step / 2
                y = self.spawn_margin + j * y_step + y_step / 2
                self.agent_spawn_points.append(Vector2D(x, y))
    
    # === Spatial Partitioning ===
    
    def _get_grid_cell(self, position: Vector2D) -> Tuple[int, int]:
        """Get spatial grid cell coordinates for a position."""
        return (
            int(position.x // self.grid_cell_size),
            int(position.y // self.grid_cell_size)
        )
    
    def _add_agent_to_spatial_grid(self, agent_id: str, position: Vector2D) -> None:
        """Add an agent to the spatial grid."""
        cell = self._get_grid_cell(position)
        self.spatial_grid[cell].add(agent_id)
    
    def _remove_agent_from_spatial_grid(self, agent_id: str) -> None:
        """Remove an agent from the spatial grid."""
        # Remove from all cells (inefficient but safe)
        for cell_agents in self.spatial_grid.values():
            cell_agents.discard(agent_id)
    
    def _update_agent_spatial_grid(self, agent_id: str, old_pos: Vector2D, new_pos: Vector2D) -> None:
        """Update an agent's position in the spatial grid."""
        old_cell = self._get_grid_cell(old_pos)
        new_cell = self._get_grid_cell(new_pos)
        
        if old_cell != new_cell:
            self.spatial_grid[old_cell].discard(agent_id)
            self.spatial_grid[new_cell].add(agent_id)
    
    def get_nearby_agents(self, position: Vector2D, radius: float) -> List[Any]:
        """
        Get agents near a position using spatial partitioning for efficiency.
        
        Args:
            position: Center position
            radius: Search radius
            
        Returns:
            List of nearby agents
        """
        if not self.spatial_grid_enabled:
            # Fallback to checking all agents
            return super().get_agents_near(position, radius)
        
        # Calculate which grid cells to check
        cells_to_check = set()
        cell_radius = int(math.ceil(radius / self.grid_cell_size))
        center_cell = self._get_grid_cell(position)
        
        for dx in range(-cell_radius, cell_radius + 1):
            for dy in range(-cell_radius, cell_radius + 1):
                cell = (center_cell[0] + dx, center_cell[1] + dy)
                cells_to_check.add(cell)
        
        # Check agents in relevant cells
        nearby_agents = []
        for cell in cells_to_check:
            if cell in self.spatial_grid:
                for agent_id in self.spatial_grid[cell]:
                    if agent_id in self.agents:
                        agent = self.agents[agent_id]
                        if position.distance_to(agent.position) <= radius:
                            nearby_agents.append(agent)
        
        return nearby_agents
    
    # === Core Environment Methods Implementation ===
    
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
        old_positions = {}
        
        for agent in living_agents:
            try:
                # Store old position for spatial grid updates
                old_positions[agent.agent_id] = agent.position.copy()
                
                # Get battlefield info for this agent
                battlefield_info = self.get_battlefield_info(agent.agent_id)
                
                # Let agent update its state
                agent.update(dt, battlefield_info)
                
                # Ensure agent stays within bounds
                agent.position = self.coordinate_system.world_bounds.clamp_position(agent.position)
                
                # Update agent position in our tracking
                self.agent_positions[agent.agent_id] = agent.position
                
                # Update spatial grid if position changed
                if self.spatial_grid_enabled:
                    old_pos = old_positions[agent.agent_id]
                    if agent.position != old_pos:
                        self._update_agent_spatial_grid(agent.agent_id, old_pos, agent.position)
                
            except Exception as e:
                self.logger.error(f"❌ Error updating agent {agent.agent_id[:8]}: {e}")
        
        # Check for collisions
        collision_start = time.time()
        collisions = self.check_collisions()
        collision_time = time.time() - collision_start
        self.metrics.collision_check_times.append(collision_time)
        
        # Process collisions
        for collision in collisions:
            self._handle_collision(collision)
        
        # Update projectiles (placeholder for future implementation)
        self._update_projectiles(dt)
        
        # Update metrics
        total_update_time = time.time() - update_start
        self.metrics.update_times.append(total_update_time)
        self.metrics.frame_count += 1
        self.metrics.simulation_time += dt
        self.metrics.real_time_elapsed = time.time() - self.start_time
        self.metrics.update_fps()
        
        # Check battle end conditions
        self._check_battle_end_conditions()
    
    def check_collisions(self) -> List[CollisionEvent]:
        """
        Check for collisions between agents using spatial partitioning.
        
        Returns:
            List of collision events detected
        """
        collisions = []
        
        if not self.config.get('collision_detection', True):
            return collisions
        
        living_agents = self.get_living_agents()
        checked_pairs = set()
        
        for agent1 in living_agents:
            # Get nearby agents for efficient collision checking
            nearby_agents = self.get_nearby_agents(agent1.position, self.collision_radius * 2)
            
            for agent2 in nearby_agents:
                if agent1.agent_id == agent2.agent_id:
                    continue
                
                # Avoid checking the same pair twice
                pair = tuple(sorted([agent1.agent_id, agent2.agent_id]))
                if pair in checked_pairs:
                    continue
                checked_pairs.add(pair)
                
                # Check if agents are colliding
                distance = agent1.position.distance_to(agent2.position)
                if distance < self.collision_radius:
                    collision = CollisionEvent(
                        collision_type=CollisionType.AGENT_AGENT,
                        primary_object=agent1,
                        secondary_object=agent2,
                        collision_point=agent1.position.midpoint(agent2.position),
                        collision_normal=(agent2.position - agent1.position).normalized()
                    )
                    collisions.append(collision)
        
        self.metrics.collisions_detected += len(collisions)
        return collisions
    
    def _handle_collision(self, collision: CollisionEvent) -> None:
        """Handle a collision event."""
        if collision.collision_type == CollisionType.AGENT_AGENT:
            # Simple collision response - push agents apart
            agent1 = collision.primary_object
            agent2 = collision.secondary_object
            
            if (collision.collision_normal and agent1 and agent2 and 
                hasattr(agent1, 'position') and hasattr(agent2, 'position') and
                agent1.position and agent2.position):
                # Push agents apart
                push_distance = self.collision_radius - agent1.position.distance_to(agent2.position)
                push_vector = collision.collision_normal * (push_distance / 2)
                
                agent1.position = agent1.position - push_vector
                agent2.position = agent2.position + push_vector
                
                # Clamp to bounds
                agent1.position = self.coordinate_system.world_bounds.clamp_position(agent1.position)
                agent2.position = self.coordinate_system.world_bounds.clamp_position(agent2.position)
    
    def get_battlefield_info(self, agent_id: str) -> Dict[str, Any]:
        """
        Get battlefield information visible to a specific agent.
        
        Args:
            agent_id: ID of the agent requesting information
            
        Returns:
            Dictionary containing battlefield state information
        """
        if agent_id not in self.agents:
            return {}
        
        agent = self.agents[agent_id]
        agent_team = self.get_agent_team(agent_id)
        
        # Get visible agents within vision range
        visible_agents = []
        nearby_agents = self.get_nearby_agents(agent.position, self.vision_range)
        
        for other_agent in nearby_agents:
            if other_agent.agent_id != agent_id and other_agent.is_alive:
                other_team = self.get_agent_team(other_agent.agent_id)
                
                agent_info = {
                    'agent_id': other_agent.agent_id,
                    'position': other_agent.position,
                    'health': other_agent.health,
                    'team': other_team,
                    'is_enemy': (other_team != agent_team) if agent_team and other_team else True,
                    'distance': agent.position.distance_to(other_agent.position)
                }
                visible_agents.append(agent_info)
        
        # Sort by distance
        visible_agents.sort(key=lambda a: a['distance'])
        
        return {
            'environment_bounds': (self.width, self.height),
            'agent_position': agent.position,
            'agent_team': agent_team,
            'visible_agents': visible_agents,
            'battle_phase': self.battle_phase.value,
            'simulation_time': self.simulation_time,
            'team_scores': {tid: team.score for tid, team in self.teams.items()},
            'collision_radius': self.collision_radius,
            'vision_range': self.vision_range
        }
    
    def _update_projectiles(self, dt: float) -> None:
        """Update projectile positions and check for hits (placeholder)."""
        # Placeholder for future projectile system implementation
        pass
    
    def _check_battle_end_conditions(self) -> None:
        """Check if the battle should end."""
        if self.battle_phase != BattlePhase.ACTIVE_COMBAT:
            return
        
        # Check if only one team has living agents
        teams_with_agents = set()
        for agent in self.get_living_agents():
            team = self.get_agent_team(agent.agent_id)
            if team:
                teams_with_agents.add(team)
        
        if len(teams_with_agents) <= 1:
            self.logger.info(f"🏁 Battle ending - only {len(teams_with_agents)} team(s) remaining")
            self.end_battle()
    
    # === Utility Methods ===
    
    def get_battle_statistics(self) -> Dict[str, Any]:
        """Get comprehensive battle statistics."""
        stats = {
            'battle_phase': self.battle_phase.value,
            'battle_duration': self.battle_duration,
            'total_agents': len(self.agents),
            'living_agents': len(self.get_living_agents()),
            'teams': {},
            'environment_metrics': {
                'frame_count': self.metrics.frame_count,
                'simulation_time': self.metrics.simulation_time,
                'average_fps': self.metrics.average_fps,
                'total_collisions': self.metrics.collisions_detected
            }
        }
        
        for team_id, team in self.teams.items():
            stats['teams'][team_id] = {
                'name': team.name,
                'agent_count': team.agent_count,
                'score': team.score,
                'kills': team.kills,
                'deaths': team.deaths
            }
        
        return stats
    
    def reset_battle(self) -> None:
        """Reset the battle environment for a new battle."""
        # Reset base environment
        self.reset()
        
        # Reset battle-specific state
        self.battle_phase = BattlePhase.PREPARATION
        self.battle_start_time = None
        self.battle_duration = 0.0
        self.total_kills = 0
        self.total_shots_fired = 0
        
        # Reset teams but keep team definitions
        for team in self.teams.values():
            team.agent_ids.clear()
            team.score = 0
            team.kills = 0
            team.deaths = 0
        
        self.team_agent_map.clear()
        self.spatial_grid.clear()
        self.projectiles.clear()
        
        self.logger.info(f"🔄 Battle environment reset - ready for new battle")

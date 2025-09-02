"""
Environment Base Class Interface

This module defines the core environment framework for the Battle AI system.
The environment manages the battlefield, agent interactions, physics simulation,
and overall game state.

Key Features:
- Agent lifecycle management (spawning, updating, removal)
- Collision detection and physics simulation
- Battlefield boundaries and terrain support
- Time step management and simulation loop
- Event system for agent interactions
- Performance monitoring and optimization
- Extensible architecture for future enhancements
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple, Set, Callable
from dataclasses import dataclass, field
import time
import uuid
from collections import defaultdict

from src.utils.vector2d import Vector2D
from src.utils.config import ConfigManager
from src.utils.logging_config import get_logger
from src.utils.coordinate_system import CoordinateSystem, BoundaryBehavior


class EnvironmentState(Enum):
    """Possible states for the environment/simulation."""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    FINISHED = "finished"
    ERROR = "error"


class CollisionType(Enum):
    """Types of collisions that can occur."""
    AGENT_AGENT = "agent_agent"
    AGENT_BOUNDARY = "agent_boundary"
    AGENT_OBSTACLE = "agent_obstacle"
    PROJECTILE_AGENT = "projectile_agent"
    PROJECTILE_OBSTACLE = "projectile_obstacle"


class TerrainType(Enum):
    """Types of terrain tiles."""
    FLAT = "flat"          # Normal movement speed
    ROUGH = "rough"        # Reduced movement speed
    WATER = "water"        # Very slow movement
    WALL = "wall"          # Impassable
    COVER = "cover"        # Provides protection
    HIGH_GROUND = "high"   # Tactical advantage


@dataclass
class CollisionEvent:
    """Represents a collision between objects in the environment."""
    collision_type: CollisionType
    primary_object: Any  # Agent, projectile, etc.
    secondary_object: Optional[Any] = None  # What was hit (if applicable)
    collision_point: Optional[Vector2D] = None
    collision_normal: Optional[Vector2D] = None  # Direction of collision
    timestamp: float = field(default_factory=time.time)


@dataclass
class EnvironmentMetrics:
    """Performance and state metrics for the environment."""
    frame_count: int = 0
    simulation_time: float = 0.0
    real_time_elapsed: float = 0.0
    agents_spawned: int = 0
    agents_alive: int = 0
    agents_dead: int = 0
    collisions_detected: int = 0
    average_fps: float = 0.0
    
    # Performance tracking
    update_times: List[float] = field(default_factory=list)
    collision_check_times: List[float] = field(default_factory=list)
    
    def update_fps(self) -> None:
        """Update the average FPS calculation."""
        if self.real_time_elapsed > 0:
            self.average_fps = self.frame_count / self.real_time_elapsed


@dataclass
class TerrainTile:
    """Represents a single terrain tile in the environment."""
    terrain_type: TerrainType
    movement_modifier: float = 1.0  # Speed multiplier (1.0 = normal)
    cover_value: float = 0.0        # Damage reduction (0.0-1.0)
    passable: bool = True
    elevation: float = 0.0
    
    def affects_movement(self) -> bool:
        """Check if this terrain affects agent movement."""
        return self.movement_modifier != 1.0 or not self.passable


class BaseEnvironment(ABC):
    """
    Abstract base class for all Battle AI environments.
    
    This class defines the core interface that all environment implementations
    must follow, providing standard methods for agent management, physics
    simulation, collision detection, and state management.
    """
    
    def __init__(
        self,
        width: float = 800.0,
        height: float = 600.0,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new environment.
        
        Args:
            width: Battlefield width in pixels
            height: Battlefield height in pixels  
            config: Optional configuration dictionary
        """
        # Load configuration
        config_manager = ConfigManager()
        if config:
            self.config = config
        else:
            default_config = config_manager.get_config()
            self.config = {
                'battlefield_width': width,
                'battlefield_height': height,
                'time_step': default_config.simulation.time_step,
                'max_agents': default_config.simulation.max_agents,
                'collision_detection': True,
                'physics_enabled': True
            }
        
        # Environment properties
        self.width = self.config['battlefield_width']
        self.height = self.config['battlefield_height']
        self.time_step = self.config['time_step']
        
        # Initialize coordinate system for this environment
        coord_config = {
            'battlefield_width': self.width,
            'battlefield_height': self.height,
            'grid_cell_size': self.config.get('grid_cell_size', 32.0),
            'boundary_behavior': self.config.get('boundary_behavior', 'clamp')
        }
        self.coordinate_system = CoordinateSystem(coord_config)
        self.max_agents = self.config['max_agents']
        
        # State management
        self.state = EnvironmentState.INITIALIZING
        self.environment_id = str(uuid.uuid4())
        
        # Agent management
        self.agents: Dict[str, Any] = {}  # agent_id -> BaseAgent
        self.agent_positions: Dict[str, Vector2D] = {}
        self.agent_spawn_points: List[Vector2D] = []
        
        # Event system
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self.collision_events: List[CollisionEvent] = []
        
        # Metrics and monitoring
        self.metrics = EnvironmentMetrics()
        self.start_time = time.time()
        
        # Terrain system (optional, can be None for simple environments)
        self.terrain_grid: Optional[List[List[TerrainTile]]] = None
        self.terrain_tile_size: float = 32.0  # pixels per tile
        
        # Logger
        self.logger = get_logger(f"Environment_{self.environment_id[:8]}")
        
        self.logger.info(f"🌍 Environment {self.environment_id[:8]} initialized "
                        f"({self.width}x{self.height})")
    
    # === Core Properties ===
    
    @property
    def bounds(self) -> Tuple[float, float]:
        """Get environment boundaries as (width, height)."""
        return (self.width, self.height)
    
    @property
    def center(self) -> Vector2D:
        """Get the center point of the environment."""
        return Vector2D(self.width / 2, self.height / 2)
    
    @property
    def agent_count(self) -> int:
        """Get current number of agents in the environment."""
        return len([agent for agent in self.agents.values() if agent.is_alive])
    
    @property
    def is_running(self) -> bool:
        """Check if the environment is currently running."""
        return self.state == EnvironmentState.RUNNING
    
    @property
    def simulation_time(self) -> float:
        """Get total simulation time elapsed."""
        return self.metrics.simulation_time
    
    # === Abstract Methods (Must be implemented by subclasses) ===
    
    @abstractmethod
    def update(self, dt: float) -> None:
        """
        Update the environment for one simulation step.
        
        Args:
            dt: Time step in seconds
        """
        pass
    
    @abstractmethod
    def add_agent(self, agent: Any, position: Optional[Vector2D] = None) -> bool:
        """
        Add an agent to the environment.
        
        Args:
            agent: Agent instance to add
            position: Optional spawn position
            
        Returns:
            True if agent was successfully added
        """
        pass
    
    @abstractmethod
    def remove_agent(self, agent_id: str) -> bool:
        """
        Remove an agent from the environment.
        
        Args:
            agent_id: ID of agent to remove
            
        Returns:
            True if agent was successfully removed
        """
        pass
    
    @abstractmethod
    def check_collisions(self) -> List[CollisionEvent]:
        """
        Check for collisions between objects in the environment.
        
        Returns:
            List of collision events detected
        """
        pass
    
    @abstractmethod
    def get_battlefield_info(self, agent_id: str) -> Dict[str, Any]:
        """
        Get battlefield information visible to a specific agent.
        
        Args:
            agent_id: ID of the agent requesting information
            
        Returns:
            Dictionary containing battlefield state information
        """
        pass
    
    # === Core Environment Methods ===
    
    def start(self) -> None:
        """Start the environment simulation."""
        if self.state == EnvironmentState.INITIALIZING:
            self.state = EnvironmentState.RUNNING
            self.start_time = time.time()
            self.logger.info(f"🚀 Environment {self.environment_id[:8]} started")
        else:
            self.logger.warning(f"⚠️ Cannot start environment in state {self.state}")
    
    def pause(self) -> None:
        """Pause the environment simulation."""
        if self.state == EnvironmentState.RUNNING:
            self.state = EnvironmentState.PAUSED
            self.logger.info(f"⏸️ Environment {self.environment_id[:8]} paused")
    
    def resume(self) -> None:
        """Resume the environment simulation."""
        if self.state == EnvironmentState.PAUSED:
            self.state = EnvironmentState.RUNNING
            self.logger.info(f"▶️ Environment {self.environment_id[:8]} resumed")
    
    def stop(self) -> None:
        """Stop the environment simulation."""
        if self.state in [EnvironmentState.RUNNING, EnvironmentState.PAUSED]:
            self.state = EnvironmentState.FINISHED
            self.logger.info(f"🛑 Environment {self.environment_id[:8]} stopped")
    
    def reset(self) -> None:
        """Reset the environment to initial state."""
        # Clear all agents
        self.agents.clear()
        self.agent_positions.clear()
        
        # Reset metrics
        self.metrics = EnvironmentMetrics()
        self.collision_events.clear()
        
        # Reset state
        self.state = EnvironmentState.INITIALIZING
        self.start_time = time.time()
        
        self.logger.info(f"🔄 Environment {self.environment_id[:8]} reset")
    
    # === Agent Management ===
    
    def get_agent(self, agent_id: str) -> Optional[Any]:
        """
        Get an agent by ID.
        
        Args:
            agent_id: ID of the agent to retrieve
            
        Returns:
            Agent instance or None if not found
        """
        return self.agents.get(agent_id)
    
    def get_all_agents(self) -> List[Any]:
        """Get list of all agents in the environment."""
        return list(self.agents.values())
    
    def get_living_agents(self) -> List[Any]:
        """Get list of all living agents in the environment."""
        return [agent for agent in self.agents.values() if agent.is_alive]
    
    def get_agents_near(self, position: Vector2D, radius: float) -> List[Any]:
        """
        Get all agents within a certain radius of a position.
        
        Args:
            position: Center position to search from
            radius: Search radius
            
        Returns:
            List of agents within the radius
        """
        nearby_agents = []
        for agent in self.get_living_agents():
            if position.distance_to(agent.position) <= radius:
                nearby_agents.append(agent)
        return nearby_agents
    
    def get_agents_by_team(self, team_id: str) -> List[Any]:
        """
        Get all agents belonging to a specific team.
        
        Args:
            team_id: Team identifier
            
        Returns:
            List of agents on the specified team
        """
        return [agent for agent in self.agents.values() 
                if agent.team_id == team_id and agent.is_alive]
    
    # === Positioning and Boundaries ===
    
    def is_position_valid(self, position: Vector2D, radius: float = 0.0) -> bool:
        """
        Check if a position is valid (within bounds and not blocked).
        
        Args:
            position: Position to check
            radius: Object radius for collision checking
            
        Returns:
            True if position is valid
        """
        # Use coordinate system for validation
        return self.coordinate_system.is_valid_position(position, radius)
    
    def clamp_position(self, position: Vector2D) -> Vector2D:
        """
        Clamp a position to environment boundaries.
        
        Args:
            position: Position to clamp
            
        Returns:
            Clamped position within boundaries
        """
        # Use coordinate system for boundary handling
        result = self.coordinate_system.apply_boundary_behavior(position)
        if isinstance(result, Vector2D):
            return result
        elif isinstance(result, tuple):
            return result[0]  # Return position from (position, velocity) tuple
        else:
            return position  # Fallback
    
    def get_random_position(self) -> Vector2D:
        """Get a random valid position in the environment."""
        import random
        
        max_attempts = 50
        for _ in range(max_attempts):
            position = Vector2D(
                random.uniform(0, self.width),
                random.uniform(0, self.height)
            )
            if self.is_position_valid(position):
                return position
        
        # Fallback to center if no valid position found
        return self.center
    
    def generate_spawn_points(self, count: int, min_distance: float = 50.0) -> List[Vector2D]:
        """
        Generate spawn points with minimum distance between them.
        
        Args:
            count: Number of spawn points to generate
            min_distance: Minimum distance between spawn points
            
        Returns:
            List of spawn point positions
        """
        import random
        
        spawn_points = []
        max_attempts = 100
        
        for i in range(count):
            attempts = 0
            while attempts < max_attempts:
                position = self.get_random_position()
                
                # Check distance from existing spawn points
                valid = True
                for existing in spawn_points:
                    if position.distance_to(existing) < min_distance:
                        valid = False
                        break
                
                if valid:
                    spawn_points.append(position)
                    break
                
                attempts += 1
            
            # If we couldn't find a valid position, use a fallback
            if len(spawn_points) <= i:
                fallback_x = (i % 4) * (self.width / 4) + self.width / 8
                fallback_y = (i // 4) * (self.height / 4) + self.height / 8
                spawn_points.append(Vector2D(fallback_x, fallback_y))
        
        self.agent_spawn_points = spawn_points
        return spawn_points
    
    # === Terrain System ===
    
    def initialize_terrain(self, tile_size: float = 32.0) -> None:
        """
        Initialize the terrain grid system.
        
        Args:
            tile_size: Size of each terrain tile in pixels
        """
        self.terrain_tile_size = tile_size
        
        cols = int(self.width // tile_size) + 1
        rows = int(self.height // tile_size) + 1
        
        # Initialize with flat terrain
        self.terrain_grid = []
        for row in range(rows):
            terrain_row = []
            for col in range(cols):
                terrain_row.append(TerrainTile(TerrainType.FLAT))
            self.terrain_grid.append(terrain_row)
        
        self.logger.info(f"🗺️ Terrain grid initialized ({cols}x{rows} tiles)")
    
    def get_terrain_at(self, position: Vector2D) -> Optional[TerrainTile]:
        """
        Get the terrain tile at a specific position.
        
        Args:
            position: World position
            
        Returns:
            Terrain tile or None if outside grid
        """
        if not self.terrain_grid:
            return None
        
        col = int(position.x // self.terrain_tile_size)
        row = int(position.y // self.terrain_tile_size)
        
        if (0 <= row < len(self.terrain_grid) and 
            0 <= col < len(self.terrain_grid[0])):
            return self.terrain_grid[row][col]
        
        return None
    
    def set_terrain_at(self, position: Vector2D, terrain_tile: TerrainTile) -> bool:
        """
        Set the terrain tile at a specific position.
        
        Args:
            position: World position
            terrain_tile: Terrain tile to place
            
        Returns:
            True if terrain was successfully set
        """
        if not self.terrain_grid:
            return False
        
        col = int(position.x // self.terrain_tile_size)
        row = int(position.y // self.terrain_tile_size)
        
        if (0 <= row < len(self.terrain_grid) and 
            0 <= col < len(self.terrain_grid[0])):
            self.terrain_grid[row][col] = terrain_tile
            return True
        
        return False
    
    # === Event System ===
    
    def register_event_handler(self, event_type: str, handler: Callable) -> None:
        """
        Register an event handler for a specific event type.
        
        Args:
            event_type: Type of event to handle
            handler: Callback function to handle the event
        """
        self.event_handlers[event_type].append(handler)
    
    def unregister_event_handler(self, event_type: str, handler: Callable) -> None:
        """
        Unregister an event handler.
        
        Args:
            event_type: Type of event
            handler: Handler function to remove
        """
        if handler in self.event_handlers[event_type]:
            self.event_handlers[event_type].remove(handler)
    
    def emit_event(self, event_type: str, event_data: Any) -> None:
        """
        Emit an event to all registered handlers.
        
        Args:
            event_type: Type of event to emit
            event_data: Data associated with the event
        """
        for handler in self.event_handlers[event_type]:
            try:
                handler(event_data)
            except Exception as e:
                self.logger.error(f"❌ Error in event handler for {event_type}: {e}")
    
    # === Utility Methods ===
    
    def update_metrics(self, dt: float) -> None:
        """
        Update environment performance metrics.
        
        Args:
            dt: Time step for this update
        """
        self.metrics.frame_count += 1
        self.metrics.simulation_time += dt
        self.metrics.real_time_elapsed = time.time() - self.start_time
        
        # Update agent counts
        living_agents = self.get_living_agents()
        self.metrics.agents_alive = len(living_agents)
        self.metrics.agents_dead = len(self.agents) - self.metrics.agents_alive
        
        # Update FPS
        self.metrics.update_fps()
        
        # Keep performance history manageable
        if len(self.metrics.update_times) > 100:
            self.metrics.update_times.pop(0)
        if len(self.metrics.collision_check_times) > 100:
            self.metrics.collision_check_times.pop(0)
    
    def get_performance_stats(self) -> Dict[str, float]:
        """
        Get current performance statistics.
        
        Returns:
            Dictionary of performance metrics
        """
        stats = {
            'fps': self.metrics.average_fps,
            'frame_count': self.metrics.frame_count,
            'simulation_time': self.metrics.simulation_time,
            'real_time_elapsed': self.metrics.real_time_elapsed,
            'agents_alive': self.metrics.agents_alive,
            'agents_dead': self.metrics.agents_dead,
            'collisions_detected': self.metrics.collisions_detected
        }
        
        # Add average timings if available
        if self.metrics.update_times:
            stats['avg_update_time'] = sum(self.metrics.update_times) / len(self.metrics.update_times)
        if self.metrics.collision_check_times:
            stats['avg_collision_time'] = sum(self.metrics.collision_check_times) / len(self.metrics.collision_check_times)
        
        return stats
    
    # === String Representation ===
    
    def __str__(self) -> str:
        """String representation of the environment."""
        return (f"Environment({self.environment_id[:8]}, {self.width}x{self.height}, "
                f"agents:{self.agent_count}, state:{self.state.value})")
    
    def __repr__(self) -> str:
        """Detailed string representation of the environment."""
        return str(self)

"""
Coordinate System and World Bounds

This module defines the standard coordinate system and world bounds used throughout
the Battle AI simulation. It provides utilities for coordinate transformations,
boundary checking, and spatial calculations.

Standard Coordinate System:
- Origin (0, 0) is at the top-left corner
- X-axis increases to the right
- Y-axis increases downward
- Units are in pixels for consistency with graphics rendering
- All positions use floating-point coordinates for precision

World Bounds:
- Rectangular battlefield with configurable dimensions
- Default size: 800x600 pixels
- Boundary enforcement with clamping and collision detection
- Support for different boundary behaviors (wrap, clamp, bounce)
"""

from typing import Tuple, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import math

from src.utils.vector2d import Vector2D
from src.utils.config import ConfigManager
from src.utils.logging_config import get_logger


class BoundaryBehavior(Enum):
    """Defines how objects behave when they reach world boundaries."""
    CLAMP = "clamp"           # Stop at boundary
    WRAP = "wrap"             # Teleport to opposite side
    BOUNCE = "bounce"         # Reflect off boundary
    DESTROY = "destroy"       # Remove object at boundary


class CoordinateSpace(Enum):
    """Different coordinate spaces used in the simulation."""
    WORLD = "world"           # World space coordinates (pixels)
    SCREEN = "screen"         # Screen space coordinates for rendering
    GRID = "grid"             # Grid space for terrain tiles
    NORMALIZED = "normalized"  # Normalized 0-1 coordinates


@dataclass
class WorldBounds:
    """
    Defines the boundaries of the simulation world.
    
    Attributes:
        width: World width in pixels
        height: World height in pixels
        min_x: Minimum X coordinate (usually 0)
        min_y: Minimum Y coordinate (usually 0)
        max_x: Maximum X coordinate (width)
        max_y: Maximum Y coordinate (height)
        boundary_behavior: How objects behave at boundaries
    """
    width: float
    height: float
    min_x: float = 0.0
    min_y: float = 0.0
    boundary_behavior: BoundaryBehavior = BoundaryBehavior.CLAMP
    
    def __post_init__(self):
        """Calculate derived properties after initialization."""
        self.max_x = self.min_x + self.width
        self.max_y = self.min_y + self.height
        self.center = Vector2D(self.width / 2, self.height / 2)
        self.area = self.width * self.height
    
    @property
    def bounds_rect(self) -> Tuple[float, float, float, float]:
        """Get bounds as (min_x, min_y, max_x, max_y) tuple."""
        return (self.min_x, self.min_y, self.max_x, self.max_y)
    
    @property
    def size(self) -> Vector2D:
        """Get world size as Vector2D."""
        return Vector2D(self.width, self.height)
    
    def contains_point(self, position: Vector2D) -> bool:
        """Check if a point is within the world bounds."""
        return (self.min_x <= position.x <= self.max_x and 
                self.min_y <= position.y <= self.max_y)
    
    def contains_circle(self, center: Vector2D, radius: float) -> bool:
        """Check if a circle is entirely within the world bounds."""
        return (self.min_x + radius <= center.x <= self.max_x - radius and
                self.min_y + radius <= center.y <= self.max_y - radius)
    
    def distance_to_boundary(self, position: Vector2D) -> float:
        """Calculate the minimum distance from a point to any boundary."""
        # Distance to each boundary (negative if outside)
        left_dist = position.x - self.min_x
        right_dist = self.max_x - position.x
        top_dist = position.y - self.min_y
        bottom_dist = self.max_y - position.y
        
        # If point is outside bounds, return 0 (already at boundary)
        if left_dist < 0 or right_dist < 0 or top_dist < 0 or bottom_dist < 0:
            return 0.0
        
        # Return minimum positive distance
        return min(left_dist, right_dist, top_dist, bottom_dist)
    
    def clamp_position(self, position: Vector2D) -> Vector2D:
        """Clamp a position to stay within world bounds."""
        x = max(self.min_x, min(self.max_x, position.x))
        y = max(self.min_y, min(self.max_y, position.y))
        return Vector2D(x, y)
    
    def wrap_position(self, position: Vector2D) -> Vector2D:
        """Wrap a position around world boundaries (toroidal topology)."""
        x = position.x
        y = position.y
        
        if x < self.min_x:
            x = self.max_x - (self.min_x - x) % self.width
        elif x > self.max_x:
            x = self.min_x + (x - self.max_x) % self.width
            
        if y < self.min_y:
            y = self.max_y - (self.min_y - y) % self.height
        elif y > self.max_y:
            y = self.min_y + (y - self.max_y) % self.height
            
        return Vector2D(x, y)
    
    def reflect_position(self, position: Vector2D, velocity: Vector2D) -> Tuple[Vector2D, Vector2D]:
        """
        Reflect position and velocity off boundaries.
        
        Returns:
            Tuple of (new_position, new_velocity)
        """
        new_pos = Vector2D(position.x, position.y)
        new_vel = Vector2D(velocity.x, velocity.y)
        
        # Reflect off left/right boundaries
        if new_pos.x < self.min_x:
            new_pos.x = self.min_x + (self.min_x - new_pos.x)
            new_vel.x = -new_vel.x
        elif new_pos.x > self.max_x:
            new_pos.x = self.max_x - (new_pos.x - self.max_x)
            new_vel.x = -new_vel.x
            
        # Reflect off top/bottom boundaries
        if new_pos.y < self.min_y:
            new_pos.y = self.min_y + (self.min_y - new_pos.y)
            new_vel.y = -new_vel.y
        elif new_pos.y > self.max_y:
            new_pos.y = self.max_y - (new_pos.y - self.max_y)
            new_vel.y = -new_vel.y
            
        return new_pos, new_vel


@dataclass
class GridSystem:
    """
    Grid-based coordinate system for terrain and spatial partitioning.
    
    Attributes:
        world_bounds: The world bounds this grid covers
        cell_size: Size of each grid cell in pixels
        rows: Number of rows in the grid
        cols: Number of columns in the grid
    """
    world_bounds: WorldBounds
    cell_size: float = 32.0
    
    def __post_init__(self):
        """Calculate grid dimensions."""
        self.cols = int(math.ceil(self.world_bounds.width / self.cell_size))
        self.rows = int(math.ceil(self.world_bounds.height / self.cell_size))
        self.total_cells = self.rows * self.cols
    
    def world_to_grid(self, position: Vector2D) -> Tuple[int, int]:
        """Convert world coordinates to grid coordinates."""
        col = int((position.x - self.world_bounds.min_x) // self.cell_size)
        row = int((position.y - self.world_bounds.min_y) // self.cell_size)
        
        # Clamp to valid grid range
        col = max(0, min(self.cols - 1, col))
        row = max(0, min(self.rows - 1, row))
        
        return (row, col)
    
    def grid_to_world(self, row: int, col: int) -> Vector2D:
        """Convert grid coordinates to world coordinates (cell center)."""
        x = self.world_bounds.min_x + (col + 0.5) * self.cell_size
        y = self.world_bounds.min_y + (row + 0.5) * self.cell_size
        return Vector2D(x, y)
    
    def get_cell_bounds(self, row: int, col: int) -> Tuple[Vector2D, Vector2D]:
        """Get the world bounds of a specific grid cell."""
        min_x = self.world_bounds.min_x + col * self.cell_size
        min_y = self.world_bounds.min_y + row * self.cell_size
        max_x = min_x + self.cell_size
        max_y = min_y + self.cell_size
        
        return (Vector2D(min_x, min_y), Vector2D(max_x, max_y))
    
    def get_neighbors(self, row: int, col: int, include_diagonal: bool = True) -> List[Tuple[int, int]]:
        """Get neighboring grid cells."""
        neighbors = []
        offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        
        if not include_diagonal:
            offsets = [(-1, 0), (0, -1), (0, 1), (1, 0)]
        
        for dr, dc in offsets:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < self.rows and 0 <= new_col < self.cols:
                neighbors.append((new_row, new_col))
        
        return neighbors


class CoordinateSystem:
    """
    Central coordinate system manager for the Battle AI simulation.
    
    This class provides a unified interface for coordinate transformations,
    boundary checking, and spatial calculations throughout the simulation.
    """
    
    def __init__(self, config: Optional[dict] = None):
        """
        Initialize the coordinate system.
        
        Args:
            config: Optional configuration dictionary
        """
        self.logger = get_logger(__name__)
        
        # Load configuration
        if config is None:
            config_manager = ConfigManager()
            default_config = config_manager.get_config()
            config = {
                'battlefield_width': default_config.simulation.battlefield_width,
                'battlefield_height': default_config.simulation.battlefield_height,
                'grid_cell_size': 32.0,
                'boundary_behavior': 'clamp'
            }
        
        # Initialize world bounds
        self.world_bounds = WorldBounds(
            width=config['battlefield_width'],
            height=config['battlefield_height'],
            boundary_behavior=BoundaryBehavior(config['boundary_behavior'])
        )
        
        # Initialize grid system
        self.grid = GridSystem(self.world_bounds, config['grid_cell_size'])
        
        self.logger.info(f"🗺️ Coordinate system initialized:")
        self.logger.info(f"   World: {self.world_bounds.width}x{self.world_bounds.height}")
        self.logger.info(f"   Grid: {self.grid.rows}x{self.grid.cols} cells ({self.grid.cell_size}px)")
        self.logger.info(f"   Boundary: {self.world_bounds.boundary_behavior.value}")
    
    def apply_boundary_behavior(self, position: Vector2D, velocity: Optional[Vector2D] = None) -> Optional[Union[Vector2D, Tuple[Vector2D, Vector2D]]]:
        """
        Apply boundary behavior to a position (and optionally velocity).
        
        Args:
            position: Current position
            velocity: Current velocity (required for bounce behavior)
            
        Returns:
            New position, or (new_position, new_velocity) for bounce behavior
        """
        if self.world_bounds.boundary_behavior == BoundaryBehavior.CLAMP:
            return self.world_bounds.clamp_position(position)
        
        elif self.world_bounds.boundary_behavior == BoundaryBehavior.WRAP:
            return self.world_bounds.wrap_position(position)
        
        elif self.world_bounds.boundary_behavior == BoundaryBehavior.BOUNCE:
            if velocity is None:
                raise ValueError("Velocity required for bounce boundary behavior")
            return self.world_bounds.reflect_position(position, velocity)
        
        elif self.world_bounds.boundary_behavior == BoundaryBehavior.DESTROY:
            # Return None to indicate object should be destroyed
            if not self.world_bounds.contains_point(position):
                return None
            return position
        
        else:
            return position
    
    def is_valid_position(self, position: Vector2D, radius: float = 0.0) -> bool:
        """
        Check if a position (with optional radius) is valid within world bounds.
        
        Args:
            position: Position to check
            radius: Object radius for collision checking
            
        Returns:
            True if position is valid
        """
        if radius > 0:
            return self.world_bounds.contains_circle(position, radius)
        else:
            return self.world_bounds.contains_point(position)
    
    def get_distance_to_boundary(self, position: Vector2D) -> float:
        """Get minimum distance from position to any boundary."""
        return self.world_bounds.distance_to_boundary(position)
    
    def normalize_coordinates(self, position: Vector2D) -> Vector2D:
        """Convert world coordinates to normalized 0-1 coordinates."""
        x = (position.x - self.world_bounds.min_x) / self.world_bounds.width
        y = (position.y - self.world_bounds.min_y) / self.world_bounds.height
        return Vector2D(x, y)
    
    def denormalize_coordinates(self, normalized_pos: Vector2D) -> Vector2D:
        """Convert normalized 0-1 coordinates to world coordinates."""
        x = self.world_bounds.min_x + normalized_pos.x * self.world_bounds.width
        y = self.world_bounds.min_y + normalized_pos.y * self.world_bounds.height
        return Vector2D(x, y)
    
    def get_random_position(self, border_margin: float = 0.0) -> Vector2D:
        """
        Generate a random position within world bounds.
        
        Args:
            border_margin: Minimum distance from boundaries
            
        Returns:
            Random position within bounds
        """
        import random
        
        min_x = self.world_bounds.min_x + border_margin
        max_x = self.world_bounds.max_x - border_margin
        min_y = self.world_bounds.min_y + border_margin
        max_y = self.world_bounds.max_y - border_margin
        
        x = random.uniform(min_x, max_x)
        y = random.uniform(min_y, max_y)
        
        return Vector2D(x, y)
    
    def get_spawn_positions(self, count: int, formation: str = "random", 
                          center: Optional[Vector2D] = None, spacing: float = 50.0) -> List[Vector2D]:
        """
        Generate spawn positions for multiple objects.
        
        Args:
            count: Number of positions to generate
            formation: Formation type ("random", "circle", "line", "grid")
            center: Center point for formation (defaults to world center)
            spacing: Spacing between positions
            
        Returns:
            List of spawn positions
        """
        if center is None:
            center = self.world_bounds.center
        
        positions = []
        
        if formation == "random":
            for _ in range(count):
                positions.append(self.get_random_position(spacing))
        
        elif formation == "circle":
            if count == 1:
                positions.append(center)
            else:
                angle_step = 2 * math.pi / count
                for i in range(count):
                    angle = i * angle_step
                    x = center.x + spacing * math.cos(angle)
                    y = center.y + spacing * math.sin(angle)
                    pos = self.apply_boundary_behavior(Vector2D(x, y))
                    if isinstance(pos, Vector2D):  # Not destroyed
                        positions.append(pos)
        
        elif formation == "line":
            start_x = center.x - (count - 1) * spacing / 2
            for i in range(count):
                x = start_x + i * spacing
                pos = self.apply_boundary_behavior(Vector2D(x, center.y))
                if isinstance(pos, Vector2D):  # Not destroyed
                    positions.append(pos)
        
        elif formation == "grid":
            cols = int(math.ceil(math.sqrt(count)))
            rows = int(math.ceil(count / cols))
            
            start_x = center.x - (cols - 1) * spacing / 2
            start_y = center.y - (rows - 1) * spacing / 2
            
            for i in range(count):
                row = i // cols
                col = i % cols
                x = start_x + col * spacing
                y = start_y + row * spacing
                pos = self.apply_boundary_behavior(Vector2D(x, y))
                if isinstance(pos, Vector2D):  # Not destroyed
                    positions.append(pos)
        
        return positions


# Global coordinate system instance
_coordinate_system: Optional[CoordinateSystem] = None


def get_coordinate_system() -> CoordinateSystem:
    """Get the global coordinate system instance."""
    global _coordinate_system
    if _coordinate_system is None:
        _coordinate_system = CoordinateSystem()
    return _coordinate_system


def initialize_coordinate_system(config: Optional[dict] = None) -> CoordinateSystem:
    """Initialize the global coordinate system with custom configuration."""
    global _coordinate_system
    _coordinate_system = CoordinateSystem(config)
    return _coordinate_system


def reset_coordinate_system() -> None:
    """Reset the global coordinate system (useful for testing)."""
    global _coordinate_system
    _coordinate_system = None

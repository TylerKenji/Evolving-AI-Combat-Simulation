"""
Test suite for coordinate system and world bounds.
Tests coordinate transformations, boundary behaviors, and spatial calculations.
"""

import pytest
import math
from src.utils import (
    CoordinateSystem, 
    WorldBounds, 
    GridSystem, 
    BoundaryBehavior, 
    CoordinateSpace,
    Vector2D,
    get_coordinate_system,
    initialize_coordinate_system,
    reset_coordinate_system
)


class TestBoundaryBehavior:
    """Test BoundaryBehavior enum."""
    
    def test_boundary_behaviors(self):
        """Test all boundary behavior types exist."""
        assert BoundaryBehavior.CLAMP
        assert BoundaryBehavior.WRAP
        assert BoundaryBehavior.BOUNCE
        assert BoundaryBehavior.DESTROY


class TestCoordinateSpace:
    """Test CoordinateSpace enum."""
    
    def test_coordinate_spaces(self):
        """Test all coordinate space types exist."""
        assert CoordinateSpace.WORLD
        assert CoordinateSpace.SCREEN
        assert CoordinateSpace.GRID
        assert CoordinateSpace.NORMALIZED


class TestWorldBounds:
    """Test WorldBounds functionality."""
    
    def setup_method(self):
        """Set up test world bounds."""
        self.bounds = WorldBounds(800, 600)
    
    def test_bounds_initialization(self):
        """Test world bounds initialization."""
        assert self.bounds.width == 800
        assert self.bounds.height == 600
        assert self.bounds.min_x == 0.0
        assert self.bounds.min_y == 0.0
        assert self.bounds.max_x == 800.0
        assert self.bounds.max_y == 600.0
        assert self.bounds.center == Vector2D(400, 300)
        assert self.bounds.area == 480000
    
    def test_bounds_rect_property(self):
        """Test bounds rectangle property."""
        rect = self.bounds.bounds_rect
        assert rect == (0.0, 0.0, 800.0, 600.0)
    
    def test_size_property(self):
        """Test size property."""
        size = self.bounds.size
        assert size == Vector2D(800, 600)
    
    def test_contains_point(self):
        """Test point containment checking."""
        # Points inside bounds
        assert self.bounds.contains_point(Vector2D(400, 300))
        assert self.bounds.contains_point(Vector2D(0, 0))
        assert self.bounds.contains_point(Vector2D(800, 600))
        
        # Points outside bounds
        assert not self.bounds.contains_point(Vector2D(-1, 300))
        assert not self.bounds.contains_point(Vector2D(801, 300))
        assert not self.bounds.contains_point(Vector2D(400, -1))
        assert not self.bounds.contains_point(Vector2D(400, 601))
    
    def test_contains_circle(self):
        """Test circle containment checking."""
        # Circle entirely inside
        assert self.bounds.contains_circle(Vector2D(400, 300), 50)
        assert self.bounds.contains_circle(Vector2D(100, 100), 10)
        
        # Circle touching boundaries
        assert not self.bounds.contains_circle(Vector2D(50, 300), 51)
        assert not self.bounds.contains_circle(Vector2D(750, 300), 51)
        
        # Circle outside bounds
        assert not self.bounds.contains_circle(Vector2D(-50, 300), 10)
        assert not self.bounds.contains_circle(Vector2D(850, 300), 10)
    
    def test_distance_to_boundary(self):
        """Test distance to boundary calculation."""
        # Center point - equidistant from all boundaries
        center_dist = self.bounds.distance_to_boundary(Vector2D(400, 300))
        assert center_dist == 300  # Distance to top/bottom boundaries
        
        # Near left boundary
        left_dist = self.bounds.distance_to_boundary(Vector2D(50, 300))
        assert left_dist == 50
        
        # Near right boundary
        right_dist = self.bounds.distance_to_boundary(Vector2D(750, 300))
        assert right_dist == 50
        
        # Point outside bounds should give 0 for closest boundary
        outside_dist = self.bounds.distance_to_boundary(Vector2D(-10, 300))
        assert outside_dist == 0  # Outside left boundary
    
    def test_clamp_position(self):
        """Test position clamping."""
        # Position inside bounds - no change
        inside_pos = Vector2D(400, 300)
        clamped = self.bounds.clamp_position(inside_pos)
        assert clamped == inside_pos
        
        # Position outside bounds - clamped
        outside_left = Vector2D(-50, 300)
        clamped_left = self.bounds.clamp_position(outside_left)
        assert clamped_left == Vector2D(0, 300)
        
        outside_right = Vector2D(850, 300)
        clamped_right = self.bounds.clamp_position(outside_right)
        assert clamped_right == Vector2D(800, 300)
        
        outside_top = Vector2D(400, -50)
        clamped_top = self.bounds.clamp_position(outside_top)
        assert clamped_top == Vector2D(400, 0)
        
        outside_bottom = Vector2D(400, 650)
        clamped_bottom = self.bounds.clamp_position(outside_bottom)
        assert clamped_bottom == Vector2D(400, 600)
    
    def test_wrap_position(self):
        """Test position wrapping."""
        # Position inside bounds - no change
        inside_pos = Vector2D(400, 300)
        wrapped = self.bounds.wrap_position(inside_pos)
        assert wrapped == inside_pos
        
        # Position outside left - wrap to right
        outside_left = Vector2D(-50, 300)
        wrapped_left = self.bounds.wrap_position(outside_left)
        assert wrapped_left.x == 750  # 800 - 50
        assert wrapped_left.y == 300
        
        # Position outside right - wrap to left
        outside_right = Vector2D(850, 300)
        wrapped_right = self.bounds.wrap_position(outside_right)
        assert wrapped_right.x == 50  # 850 - 800
        assert wrapped_right.y == 300
    
    def test_reflect_position(self):
        """Test position and velocity reflection."""
        # Moving towards right boundary
        pos = Vector2D(850, 300)
        vel = Vector2D(50, 0)
        new_pos, new_vel = self.bounds.reflect_position(pos, vel)
        
        assert new_pos.x == 750  # Reflected back into bounds
        assert new_pos.y == 300
        assert new_vel.x == -50  # Velocity reversed
        assert new_vel.y == 0
        
        # Moving towards bottom boundary
        pos = Vector2D(400, 650)
        vel = Vector2D(0, 30)
        new_pos, new_vel = self.bounds.reflect_position(pos, vel)
        
        assert new_pos.x == 400
        assert new_pos.y == 550  # Reflected back
        assert new_vel.x == 0
        assert new_vel.y == -30  # Velocity reversed


class TestGridSystem:
    """Test GridSystem functionality."""
    
    def setup_method(self):
        """Set up test grid system."""
        bounds = WorldBounds(800, 600)
        self.grid = GridSystem(bounds, cell_size=32)
    
    def test_grid_initialization(self):
        """Test grid system initialization."""
        assert self.grid.cell_size == 32
        assert self.grid.cols == 25  # ceil(800/32)
        assert self.grid.rows == 19  # ceil(600/32)
        assert self.grid.total_cells == 475  # 25 * 19
    
    def test_world_to_grid(self):
        """Test world to grid coordinate conversion."""
        # Top-left corner
        row, col = self.grid.world_to_grid(Vector2D(0, 0))
        assert row == 0 and col == 0
        
        # Center of first cell
        row, col = self.grid.world_to_grid(Vector2D(16, 16))
        assert row == 0 and col == 0
        
        # Second cell
        row, col = self.grid.world_to_grid(Vector2D(32, 0))
        assert row == 0 and col == 1
        
        # Second row
        row, col = self.grid.world_to_grid(Vector2D(0, 32))
        assert row == 1 and col == 0
        
        # Position outside bounds should clamp
        row, col = self.grid.world_to_grid(Vector2D(1000, 1000))
        assert row == 18 and col == 24  # Clamped to max valid
    
    def test_grid_to_world(self):
        """Test grid to world coordinate conversion."""
        # First cell center
        pos = self.grid.grid_to_world(0, 0)
        assert pos == Vector2D(16, 16)  # Center of 32x32 cell
        
        # Second column center
        pos = self.grid.grid_to_world(0, 1)
        assert pos == Vector2D(48, 16)  # 32 + 16
        
        # Second row center
        pos = self.grid.grid_to_world(1, 0)
        assert pos == Vector2D(16, 48)  # 32 + 16
    
    def test_get_cell_bounds(self):
        """Test getting cell boundaries."""
        min_pos, max_pos = self.grid.get_cell_bounds(0, 0)
        assert min_pos == Vector2D(0, 0)
        assert max_pos == Vector2D(32, 32)
        
        min_pos, max_pos = self.grid.get_cell_bounds(1, 2)
        assert min_pos == Vector2D(64, 32)  # col 2 * 32, row 1 * 32
        assert max_pos == Vector2D(96, 64)  # + 32
    
    def test_get_neighbors(self):
        """Test getting neighbor cells."""
        # Corner cell (0,0) - should have 3 neighbors
        neighbors = self.grid.get_neighbors(0, 0)
        expected = [(0, 1), (1, 0), (1, 1)]
        assert set(neighbors) == set(expected)
        
        # Middle cell - should have 8 neighbors
        neighbors = self.grid.get_neighbors(5, 5)
        assert len(neighbors) == 8
        
        # Test without diagonals
        neighbors = self.grid.get_neighbors(5, 5, include_diagonal=False)
        expected = [(4, 5), (5, 4), (5, 6), (6, 5)]
        assert set(neighbors) == set(expected)


class TestCoordinateSystem:
    """Test CoordinateSystem main class."""
    
    def setup_method(self):
        """Set up test coordinate system."""
        config = {
            'battlefield_width': 800,
            'battlefield_height': 600,
            'grid_cell_size': 32,
            'boundary_behavior': 'clamp'
        }
        self.coord_sys = CoordinateSystem(config)
    
    def test_coordinate_system_initialization(self):
        """Test coordinate system initialization."""
        assert self.coord_sys.world_bounds.width == 800
        assert self.coord_sys.world_bounds.height == 600
        assert self.coord_sys.grid.cell_size == 32
        assert self.coord_sys.world_bounds.boundary_behavior == BoundaryBehavior.CLAMP
    
    def test_boundary_behavior_clamp(self):
        """Test clamp boundary behavior."""
        outside_pos = Vector2D(-50, 700)
        result = self.coord_sys.apply_boundary_behavior(outside_pos)
        assert result == Vector2D(0, 600)
    
    def test_boundary_behavior_wrap(self):
        """Test wrap boundary behavior."""
        # Create system with wrap behavior
        config = {
            'battlefield_width': 800,
            'battlefield_height': 600,
            'grid_cell_size': 32,
            'boundary_behavior': 'wrap'
        }
        wrap_sys = CoordinateSystem(config)
        
        outside_pos = Vector2D(-50, 300)
        result = wrap_sys.apply_boundary_behavior(outside_pos)
        assert isinstance(result, Vector2D)
        assert result.x == 750  # Wrapped
        assert result.y == 300
    
    def test_boundary_behavior_bounce(self):
        """Test bounce boundary behavior."""
        # Create system with bounce behavior
        config = {
            'battlefield_width': 800,
            'battlefield_height': 600,
            'grid_cell_size': 32,
            'boundary_behavior': 'bounce'
        }
        bounce_sys = CoordinateSystem(config)
        
        outside_pos = Vector2D(850, 300)
        velocity = Vector2D(50, 0)
        result = bounce_sys.apply_boundary_behavior(outside_pos, velocity)
        
        assert isinstance(result, tuple)
        new_pos, new_vel = result
        assert new_pos.x == 750  # Reflected
        assert new_vel.x == -50  # Velocity reversed
    
    def test_boundary_behavior_destroy(self):
        """Test destroy boundary behavior."""
        # Create system with destroy behavior
        config = {
            'battlefield_width': 800,
            'battlefield_height': 600,
            'grid_cell_size': 32,
            'boundary_behavior': 'destroy'
        }
        destroy_sys = CoordinateSystem(config)
        
        # Position inside bounds
        inside_pos = Vector2D(400, 300)
        result = destroy_sys.apply_boundary_behavior(inside_pos)
        assert result == inside_pos
        
        # Position outside bounds
        outside_pos = Vector2D(-50, 300)
        result = destroy_sys.apply_boundary_behavior(outside_pos)
        assert result is None
    
    def test_is_valid_position(self):
        """Test position validation."""
        # Valid positions
        assert self.coord_sys.is_valid_position(Vector2D(400, 300))
        assert self.coord_sys.is_valid_position(Vector2D(0, 0))
        
        # Invalid positions
        assert not self.coord_sys.is_valid_position(Vector2D(-1, 300))
        assert not self.coord_sys.is_valid_position(Vector2D(801, 300))
        
        # Test with radius
        assert self.coord_sys.is_valid_position(Vector2D(400, 300), radius=50)
        assert not self.coord_sys.is_valid_position(Vector2D(50, 300), radius=60)
    
    def test_normalize_coordinates(self):
        """Test coordinate normalization."""
        # Center should be (0.5, 0.5)
        center = Vector2D(400, 300)
        normalized = self.coord_sys.normalize_coordinates(center)
        assert normalized == Vector2D(0.5, 0.5)
        
        # Origin should be (0, 0)
        origin = Vector2D(0, 0)
        normalized = self.coord_sys.normalize_coordinates(origin)
        assert normalized == Vector2D(0, 0)
        
        # Max bounds should be (1, 1)
        max_pos = Vector2D(800, 600)
        normalized = self.coord_sys.normalize_coordinates(max_pos)
        assert normalized == Vector2D(1, 1)
    
    def test_denormalize_coordinates(self):
        """Test coordinate denormalization."""
        # (0.5, 0.5) should be center
        normalized = Vector2D(0.5, 0.5)
        world_pos = self.coord_sys.denormalize_coordinates(normalized)
        assert world_pos == Vector2D(400, 300)
        
        # (0, 0) should be origin
        normalized = Vector2D(0, 0)
        world_pos = self.coord_sys.denormalize_coordinates(normalized)
        assert world_pos == Vector2D(0, 0)
        
        # (1, 1) should be max bounds
        normalized = Vector2D(1, 1)
        world_pos = self.coord_sys.denormalize_coordinates(normalized)
        assert world_pos == Vector2D(800, 600)
    
    def test_get_random_position(self):
        """Test random position generation."""
        # Generate several random positions
        for _ in range(10):
            pos = self.coord_sys.get_random_position()
            assert self.coord_sys.is_valid_position(pos)
        
        # Test with border margin
        margin_pos = self.coord_sys.get_random_position(border_margin=50)
        assert margin_pos.x >= 50
        assert margin_pos.x <= 750
        assert margin_pos.y >= 50
        assert margin_pos.y <= 550
    
    def test_get_spawn_positions_random(self):
        """Test random spawn position generation."""
        positions = self.coord_sys.get_spawn_positions(5, "random")
        assert len(positions) == 5
        for pos in positions:
            assert self.coord_sys.is_valid_position(pos)
    
    def test_get_spawn_positions_circle(self):
        """Test circle spawn position generation."""
        positions = self.coord_sys.get_spawn_positions(4, "circle", spacing=50)
        assert len(positions) == 4
        
        # Check they're arranged in a circle
        center = self.coord_sys.world_bounds.center
        for pos in positions:
            distance = center.distance_to(pos)
            assert abs(distance - 50) < 1.0  # Should be on circle radius
    
    def test_get_spawn_positions_line(self):
        """Test line spawn position generation."""
        positions = self.coord_sys.get_spawn_positions(3, "line", spacing=50)
        assert len(positions) == 3
        
        # Check they're in a line
        if len(positions) >= 2:
            # All should have same Y coordinate
            y_values = [pos.y for pos in positions]
            assert all(abs(y - y_values[0]) < 1.0 for y in y_values)
    
    def test_get_spawn_positions_grid(self):
        """Test grid spawn position generation."""
        positions = self.coord_sys.get_spawn_positions(6, "grid", spacing=50)
        assert len(positions) == 6


class TestGlobalCoordinateSystem:
    """Test global coordinate system management."""
    
    def teardown_method(self):
        """Clean up after each test."""
        reset_coordinate_system()
    
    def test_get_coordinate_system_default(self):
        """Test getting default coordinate system."""
        coord_sys = get_coordinate_system()
        assert isinstance(coord_sys, CoordinateSystem)
        
        # Should return same instance on subsequent calls
        coord_sys2 = get_coordinate_system()
        assert coord_sys is coord_sys2
    
    def test_initialize_coordinate_system(self):
        """Test initializing coordinate system with custom config."""
        config = {
            'battlefield_width': 1024,
            'battlefield_height': 768,
            'grid_cell_size': 64,
            'boundary_behavior': 'wrap'
        }
        
        coord_sys = initialize_coordinate_system(config)
        assert coord_sys.world_bounds.width == 1024
        assert coord_sys.world_bounds.height == 768
        assert coord_sys.grid.cell_size == 64
        assert coord_sys.world_bounds.boundary_behavior == BoundaryBehavior.WRAP
    
    def test_reset_coordinate_system(self):
        """Test resetting the global coordinate system."""
        # Get initial system
        coord_sys1 = get_coordinate_system()
        
        # Reset and get new system
        reset_coordinate_system()
        coord_sys2 = get_coordinate_system()
        
        # Should be different instances
        assert coord_sys1 is not coord_sys2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

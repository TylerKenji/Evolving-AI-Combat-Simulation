"""
Tests for common utility functions
Task 1.3.5: Implement basic utility functions

This module tests all the utility functions in src.utils.common to ensure
they work correctly and handle edge cases properly.
"""

import pytest
import math
from src.utils.common import *
from src.utils.vector2d import Vector2D


class TestMathematicalUtilities:
    """Test mathematical utility functions."""
    
    def test_clamp(self):
        """Test value clamping."""
        assert clamp(5, 0, 10) == 5
        assert clamp(-5, 0, 10) == 0
        assert clamp(15, 0, 10) == 10
        assert clamp(5.5, 3.0, 7.0) == 5.5
        assert clamp(2.0, 3.0, 7.0) == 3.0
        assert clamp(8.0, 3.0, 7.0) == 7.0
    
    def test_lerp(self):
        """Test linear interpolation."""
        assert lerp(0, 10, 0.0) == 0
        assert lerp(0, 10, 1.0) == 10
        assert lerp(0, 10, 0.5) == 5
        assert lerp(10, 20, 0.25) == 12.5
        
        # Test clamping
        assert lerp(0, 10, -0.5) == 0
        assert lerp(0, 10, 1.5) == 10
    
    def test_inverse_lerp(self):
        """Test inverse linear interpolation."""
        assert inverse_lerp(0, 10, 0) == 0.0
        assert inverse_lerp(0, 10, 10) == 1.0
        assert inverse_lerp(0, 10, 5) == 0.5
        assert inverse_lerp(10, 20, 15) == 0.5
        
        # Test edge cases
        assert inverse_lerp(5, 5, 5) == 0.0  # Zero range
        assert inverse_lerp(0, 10, -5) == 0.0  # Below range
        assert inverse_lerp(0, 10, 15) == 1.0  # Above range
    
    def test_remap(self):
        """Test value remapping."""
        # Remap 0-10 to 0-100
        assert remap(5, 0, 10, 0, 100) == 50
        assert remap(0, 0, 10, 0, 100) == 0
        assert remap(10, 0, 10, 0, 100) == 100
        
        # Remap with different ranges
        assert remap(15, 10, 20, 0, 1) == 0.5
    
    def test_smooth_step(self):
        """Test smooth step function."""
        assert smooth_step(0.0) == 0.0
        assert smooth_step(1.0) == 1.0
        assert smooth_step(0.5) == 0.5
        
        # Test that it's smoother than linear
        linear_quarter = 0.25
        smooth_quarter = smooth_step(0.25)
        assert smooth_quarter < linear_quarter  # Should be less steep at start
    
    def test_smoother_step(self):
        """Test smoother step function."""
        assert smoother_step(0.0) == 0.0
        assert smoother_step(1.0) == 1.0
        assert smoother_step(0.5) == 0.5
    
    def test_ease_functions(self):
        """Test easing functions."""
        # Test boundary values
        assert ease_in_quad(0.0) == 0.0
        assert ease_in_quad(1.0) == 1.0
        assert ease_out_quad(0.0) == 0.0
        assert ease_out_quad(1.0) == 1.0
        assert ease_in_out_quad(0.0) == 0.0
        assert ease_in_out_quad(1.0) == 1.0
        
        # Test mid values
        assert ease_in_quad(0.5) == 0.25
        assert ease_out_quad(0.5) == 0.75
    
    def test_interpolate(self):
        """Test general interpolation function."""
        # Linear interpolation
        assert interpolate(0, 10, 0.5, InterpolationType.LINEAR) == 5.0
        
        # Ease in should be less than linear at 0.5
        ease_in_result = interpolate(0, 10, 0.5, InterpolationType.EASE_IN)
        assert ease_in_result < 5.0
        
        # Ease out should be more than linear at 0.5
        ease_out_result = interpolate(0, 10, 0.5, InterpolationType.EASE_OUT)
        assert ease_out_result > 5.0


class TestAngleUtilities:
    """Test angle and rotation utilities."""
    
    def test_normalize_angle_radians(self):
        """Test radian angle normalization."""
        assert abs(normalize_angle_radians(0)) < 1e-10
        assert abs(normalize_angle_radians(math.pi) - math.pi) < 1e-10
        assert abs(normalize_angle_radians(-math.pi) - (-math.pi)) < 1e-10
        
        # Test wrapping
        assert abs(normalize_angle_radians(3 * math.pi) - (-math.pi)) < 1e-10
        assert abs(normalize_angle_radians(-3 * math.pi) - math.pi) < 1e-10
    
    def test_normalize_angle_degrees(self):
        """Test degree angle normalization."""
        assert abs(normalize_angle_degrees(0)) < 1e-10
        assert abs(normalize_angle_degrees(180) - 180) < 1e-10
        assert abs(normalize_angle_degrees(-180) - (-180)) < 1e-10
        
        # Test wrapping
        assert abs(normalize_angle_degrees(540) - (-180)) < 1e-10
        assert abs(normalize_angle_degrees(-540) - 180) < 1e-10
    
    def test_angle_conversion(self):
        """Test angle conversion between degrees and radians."""
        assert abs(degrees_to_radians(180) - math.pi) < 1e-10
        assert abs(degrees_to_radians(90) - math.pi/2) < 1e-10
        assert abs(radians_to_degrees(math.pi) - 180) < 1e-10
        assert abs(radians_to_degrees(math.pi/2) - 90) < 1e-10
    
    def test_angle_difference(self):
        """Test angle difference calculation."""
        # Radians
        diff = angle_difference(0, math.pi/2, AngleUnit.RADIANS)
        assert abs(diff - math.pi/2) < 1e-10
        
        # Should take shortest path
        diff = angle_difference(0, 3*math.pi/2, AngleUnit.RADIANS)
        assert abs(diff - (-math.pi/2)) < 1e-10
        
        # Degrees
        diff = angle_difference(0, 90, AngleUnit.DEGREES)
        assert abs(diff - 90) < 1e-10
        
        diff = angle_difference(0, 270, AngleUnit.DEGREES)
        assert abs(diff - (-90)) < 1e-10
    
    def test_lerp_angle(self):
        """Test angle interpolation."""
        # Radians
        result = lerp_angle(0, math.pi/2, 0.5, AngleUnit.RADIANS)
        assert abs(result - math.pi/4) < 1e-10
        
        # Should take shortest path
        result = lerp_angle(0, 3*math.pi/2, 0.5, AngleUnit.RADIANS)
        assert abs(result - (-math.pi/4)) < 1e-10
        
        # Degrees
        result = lerp_angle(0, 90, 0.5, AngleUnit.DEGREES)
        assert abs(result - 45) < 1e-10


class TestRandomUtilities:
    """Test random utility functions."""
    
    def test_random_float(self):
        """Test random float generation."""
        for _ in range(100):
            val = random_float(0.0, 1.0)
            assert 0.0 <= val <= 1.0
            
        for _ in range(100):
            val = random_float(-5.0, 5.0)
            assert -5.0 <= val <= 5.0
    
    def test_random_int(self):
        """Test random integer generation."""
        for _ in range(100):
            val = random_int(1, 10)
            assert 1 <= val <= 10
            assert isinstance(val, int)
    
    def test_random_bool(self):
        """Test random boolean generation."""
        # Test extreme probabilities
        assert random_bool(0.0) == False
        assert random_bool(1.0) == True
        
        # Test default (should be roughly 50/50 over many trials)
        true_count = sum(random_bool() for _ in range(1000))
        assert 400 <= true_count <= 600  # Should be roughly half
    
    def test_random_choice(self):
        """Test random choice from list."""
        choices = [1, 2, 3, 4, 5]
        for _ in range(100):
            choice = random_choice(choices)
            assert choice in choices
        
        # Test error on empty list
        with pytest.raises(ValueError):
            random_choice([])
    
    def test_random_weighted_choice(self):
        """Test weighted random choice."""
        choices = ['a', 'b', 'c']
        weights = [1.0, 2.0, 1.0]  # 'b' should be chosen twice as often
        
        # Test that it runs without error
        for _ in range(100):
            choice = random_weighted_choice(choices, weights)
            assert choice in choices
        
        # Test error conditions
        with pytest.raises(ValueError):
            random_weighted_choice([], [])
        
        with pytest.raises(ValueError):
            random_weighted_choice(['a'], [1.0, 2.0])  # Mismatched lengths
    
    def test_random_gaussian(self):
        """Test Gaussian random generation."""
        # Generate many samples and check they're reasonable
        samples = [random_gaussian(0.0, 1.0) for _ in range(1000)]
        mean = sum(samples) / len(samples)
        assert -0.5 <= mean <= 0.5  # Should be close to 0
    
    def test_random_vector2d(self):
        """Test random Vector2D generation."""
        for _ in range(100):
            vec = random_vector2d(-1.0, 1.0, -2.0, 2.0)
            assert -1.0 <= vec.x <= 1.0
            assert -2.0 <= vec.y <= 2.0
    
    def test_random_unit_vector(self):
        """Test random unit vector generation."""
        for _ in range(100):
            vec = random_unit_vector()
            assert abs(vec.magnitude() - 1.0) < 1e-10


class TestDistanceUtilities:
    """Test distance and spatial utilities."""
    
    def test_distance_2d(self):
        """Test 2D distance calculation."""
        assert distance_2d(0, 0, 3, 4) == 5.0
        assert distance_2d(0, 0, 0, 0) == 0.0
        assert distance_squared_2d(0, 0, 3, 4) == 25.0
    
    def test_manhattan_distance_2d(self):
        """Test Manhattan distance."""
        assert manhattan_distance_2d(0, 0, 3, 4) == 7.0
        assert manhattan_distance_2d(0, 0, -3, -4) == 7.0
    
    def test_is_point_in_circle(self):
        """Test point in circle detection."""
        assert is_point_in_circle(0, 0, 0, 0, 1) == True  # Center
        assert is_point_in_circle(1, 0, 0, 0, 1) == True  # On edge
        assert is_point_in_circle(2, 0, 0, 0, 1) == False  # Outside
    
    def test_is_point_in_rectangle(self):
        """Test point in rectangle detection."""
        assert is_point_in_rectangle(5, 5, 0, 0, 10, 10) == True
        assert is_point_in_rectangle(0, 0, 0, 0, 10, 10) == True  # Corner
        assert is_point_in_rectangle(15, 5, 0, 0, 10, 10) == False
    
    def test_point_to_line_distance(self):
        """Test point to line distance calculation."""
        # Point to horizontal line
        point = Vector2D(5, 5)
        line_start = Vector2D(0, 0)
        line_end = Vector2D(10, 0)
        distance = point_to_line_distance(point, line_start, line_end)
        assert abs(distance - 5.0) < 1e-10
        
        # Point on line
        point = Vector2D(5, 0)
        distance = point_to_line_distance(point, line_start, line_end)
        assert abs(distance) < 1e-10
        
        # Zero-length line
        point = Vector2D(5, 5)
        line_start = Vector2D(0, 0)
        line_end = Vector2D(0, 0)
        distance = point_to_line_distance(point, line_start, line_end)
        assert abs(distance - math.sqrt(50)) < 1e-10


class TestCollectionUtilities:
    """Test collection utility functions."""
    
    def test_find_closest_point(self):
        """Test finding closest point."""
        target = Vector2D(5, 5)
        points = [Vector2D(0, 0), Vector2D(3, 4), Vector2D(10, 10)]
        
        index, closest, distance = find_closest_point(target, points)
        assert index == 1
        assert closest == Vector2D(3, 4)
        assert abs(distance - Vector2D(5, 5).distance_to(Vector2D(3, 4))) < 1e-10
        
        # Test error on empty list
        with pytest.raises(ValueError):
            find_closest_point(target, [])
    
    def test_find_points_in_range(self):
        """Test finding points in range."""
        center = Vector2D(0, 0)
        points = [Vector2D(1, 0), Vector2D(2, 0), Vector2D(5, 0)]
        
        results = find_points_in_range(center, points, 2.5)
        assert len(results) == 2
        
        # Check that distances are correct
        for index, point, distance in results:
            assert abs(distance - center.distance_to(point)) < 1e-10
    
    def test_sort_points_by_distance(self):
        """Test sorting points by distance."""
        target = Vector2D(0, 0)
        points = [Vector2D(5, 0), Vector2D(1, 0), Vector2D(3, 0)]
        
        sorted_points = sort_points_by_distance(target, points)
        
        # Should be sorted by distance
        assert sorted_points[0][1] == Vector2D(1, 0)  # Closest
        assert sorted_points[1][1] == Vector2D(3, 0)  # Middle
        assert sorted_points[2][1] == Vector2D(5, 0)  # Farthest
        
        # Check distances are in order
        assert sorted_points[0][2] <= sorted_points[1][2] <= sorted_points[2][2]


class TestTimingUtilities:
    """Test timing utilities."""
    
    def test_timer(self):
        """Test Timer class."""
        timer = Timer()
        import time
        time.sleep(0.01)  # Sleep for 10ms
        
        elapsed = timer.elapsed()
        assert elapsed >= 0.01
        
        lap_time = timer.lap()
        assert lap_time >= 0.0
        
        timer.reset()
        new_elapsed = timer.elapsed()
        assert new_elapsed < elapsed
    
    def test_time_function(self):
        """Test function timing."""
        def test_func(x, y):
            return x + y
        
        result, exec_time = time_function(test_func, 2, 3)
        assert result == 5
        assert exec_time >= 0.0


class TestDataUtilities:
    """Test data structure utilities."""
    
    def test_safe_divide(self):
        """Test safe division."""
        assert safe_divide(10, 2) == 5.0
        assert safe_divide(10, 0) == 0.0
        assert safe_divide(10, 0, -1) == -1.0
        assert safe_divide(10, 1e-15) == 0.0  # Near-zero
    
    def test_percentage(self):
        """Test percentage calculation."""
        assert percentage(25, 100) == 25.0
        assert percentage(0, 100) == 0.0
        assert percentage(50, 0) == 0.0  # Safe division
    
    def test_flatten_list(self):
        """Test list flattening."""
        nested = [[1, 2], [3, 4], [5]]
        flat = flatten_list(nested)
        assert flat == [1, 2, 3, 4, 5]
        
        # Test empty
        assert flatten_list([]) == []
        assert flatten_list([[], []]) == []
    
    def test_chunk_list(self):
        """Test list chunking."""
        items = [1, 2, 3, 4, 5, 6, 7]
        chunks = chunk_list(items, 3)
        assert chunks == [[1, 2, 3], [4, 5, 6], [7]]
        
        # Test exact division
        items = [1, 2, 3, 4]
        chunks = chunk_list(items, 2)
        assert chunks == [[1, 2], [3, 4]]
        
        # Test error
        with pytest.raises(ValueError):
            chunk_list([1, 2, 3], 0)
    
    def test_unique_list(self):
        """Test removing duplicates."""
        items = [1, 2, 2, 3, 1, 4]
        unique = unique_list(items)
        assert unique == [1, 2, 3, 4]
        
        # Test order preservation
        items = [3, 1, 2, 1, 3]
        unique = unique_list(items)
        assert unique == [3, 1, 2]


class TestStringUtilities:
    """Test string and formatting utilities."""
    
    def test_format_float(self):
        """Test float formatting."""
        assert format_float(3.14159, 2) == "3.14"
        assert format_float(3.14159, 4) == "3.1416"
        assert format_float(3.0, 1) == "3.0"
    
    def test_format_percentage(self):
        """Test percentage formatting."""
        assert format_percentage(25.5, 1) == "25.5%"
        assert format_percentage(25.567, 2) == "25.57%"
    
    def test_format_time(self):
        """Test time formatting."""
        assert format_time(30) == "30.0s"
        assert format_time(90) == "1m 30.0s"
        assert format_time(3665) == "1h 1m 5.0s"
    
    def test_truncate_string(self):
        """Test string truncation."""
        text = "Hello, World!"
        assert truncate_string(text, 20) == text  # No truncation needed
        assert truncate_string(text, 10) == "Hello, ..."
        assert truncate_string(text, 5, "..") == "Hel.."
        
        # Test edge cases
        assert truncate_string(text, 3, "...") == "Hel"  # Suffix too long
        assert truncate_string("Hi", 10) == "Hi"  # Short text


class TestValidationUtilities:
    """Test validation utilities."""
    
    def test_is_numeric(self):
        """Test numeric validation."""
        assert is_numeric(5) == True
        assert is_numeric(5.5) == True
        assert is_numeric("5") == False
        assert is_numeric(True) == False  # bool is not numeric
        assert is_numeric(None) == False
    
    def test_is_positive(self):
        """Test positive validation."""
        assert is_positive(5) == True
        assert is_positive(0.1) == True
        assert is_positive(0) == False
        assert is_positive(-5) == False
        assert is_positive("5") == False
    
    def test_is_in_range(self):
        """Test range validation."""
        assert is_in_range(5, 0, 10) == True
        assert is_in_range(0, 0, 10) == True  # Inclusive
        assert is_in_range(10, 0, 10) == True  # Inclusive
        assert is_in_range(-1, 0, 10) == False
        assert is_in_range(11, 0, 10) == False
        
        # Exclusive
        assert is_in_range(0, 0, 10, inclusive=False) == False
        assert is_in_range(5, 0, 10, inclusive=False) == True
        assert is_in_range(10, 0, 10, inclusive=False) == False
        
        # Non-numeric
        assert is_in_range("5", 0, 10) == False
    
    def test_validate_probability(self):
        """Test probability validation."""
        assert validate_probability(0.0) == True
        assert validate_probability(0.5) == True
        assert validate_probability(1.0) == True
        assert validate_probability(-0.1) == False
        assert validate_probability(1.1) == False
        assert validate_probability("0.5") == False


class TestIntegration:
    """Integration tests for utility functions."""
    
    def test_movement_interpolation(self):
        """Test utilities working together for movement interpolation."""
        start_pos = Vector2D(0, 0)
        end_pos = Vector2D(10, 10)
        
        # Interpolate using different methods
        linear_pos = Vector2D(
            lerp(start_pos.x, end_pos.x, 0.5),
            lerp(start_pos.y, end_pos.y, 0.5)
        )
        assert linear_pos == Vector2D(5, 5)
        
        # Test smooth interpolation
        t = smooth_step(0.5)
        smooth_pos = Vector2D(
            lerp(start_pos.x, end_pos.x, t),
            lerp(start_pos.y, end_pos.y, t)
        )
        assert smooth_pos == Vector2D(5, 5)  # smooth_step(0.5) == 0.5
    
    def test_spatial_queries(self):
        """Test spatial query utilities working together."""
        # Create a grid of points
        points = []
        for x in range(5):
            for y in range(5):
                points.append(Vector2D(x, y))
        
        center = Vector2D(2, 2)
        
        # Find nearby points
        nearby = find_points_in_range(center, points, 1.5)
        assert len(nearby) >= 5  # At least center + 4 neighbors
        
        # Sort by distance
        sorted_points = sort_points_by_distance(center, points)
        closest = sorted_points[0][1]
        assert closest == center  # Center should be closest to itself
    
    def test_angle_and_movement(self):
        """Test angle utilities with movement calculations."""
        # Start facing right
        current_angle = 0.0
        target_angle = math.pi / 2  # Face up
        
        # Smoothly rotate
        rotation_progress = 0.3
        new_angle = lerp_angle(current_angle, target_angle, rotation_progress)
        
        # Create movement vector from angle
        movement_vec = Vector2D.from_angle(new_angle, 5.0)
        
        # Verify the result makes sense
        assert new_angle > 0  # Should be rotating toward target
        assert new_angle < target_angle  # But not there yet
        assert movement_vec.magnitude() == 5.0  # Correct magnitude

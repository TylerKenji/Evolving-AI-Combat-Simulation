"""
Basic Utility Functions for Battle AI
Task 1.3.5: Implement basic utility functions

This module provides essential utility functions for mathematical calculations,
data transformations, and common operations needed throughout the Battle AI system.
"""

import math
import random
import time
from typing import List, Tuple, Union, Optional, Any, Dict, TypeVar, Callable
from enum import Enum

from src.utils.vector2d import Vector2D


# Type variables for generic functions
T = TypeVar('T')
Numeric = Union[int, float]


class InterpolationType(Enum):
    """Types of interpolation for smooth transitions."""
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    SMOOTH_STEP = "smooth_step"


class AngleUnit(Enum):
    """Units for angle measurements."""
    RADIANS = "radians"
    DEGREES = "degrees"


# ============================================================================
# Mathematical Utilities
# ============================================================================

def clamp(value: Numeric, min_val: Numeric, max_val: Numeric) -> Numeric:
    """
    Clamp a value between minimum and maximum bounds.
    
    Args:
        value: Value to clamp
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        Clamped value within [min_val, max_val]
    """
    return max(min_val, min(max_val, value))


def lerp(start: Numeric, end: Numeric, t: float) -> float:
    """
    Linear interpolation between two values.
    
    Args:
        start: Starting value
        end: Ending value
        t: Interpolation factor (0.0 to 1.0)
        
    Returns:
        Interpolated value
    """
    return start + (end - start) * clamp(t, 0.0, 1.0)


def inverse_lerp(start: Numeric, end: Numeric, value: Numeric) -> float:
    """
    Get the interpolation factor for a value between start and end.
    
    Args:
        start: Starting value
        end: Ending value
        value: Value to find factor for
        
    Returns:
        Interpolation factor (0.0 to 1.0)
    """
    if abs(end - start) < 1e-10:
        return 0.0
    return clamp((value - start) / (end - start), 0.0, 1.0)


def remap(value: Numeric, from_min: Numeric, from_max: Numeric, 
          to_min: Numeric, to_max: Numeric) -> float:
    """
    Remap a value from one range to another.
    
    Args:
        value: Value to remap
        from_min: Original range minimum
        from_max: Original range maximum
        to_min: Target range minimum
        to_max: Target range maximum
        
    Returns:
        Remapped value
    """
    t = inverse_lerp(from_min, from_max, value)
    return lerp(to_min, to_max, t)


def smooth_step(t: float) -> float:
    """
    Smooth step interpolation (3t² - 2t³).
    
    Args:
        t: Input value (0.0 to 1.0)
        
    Returns:
        Smoothed value
    """
    t = clamp(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def smoother_step(t: float) -> float:
    """
    Smoother step interpolation (6t⁵ - 15t⁴ + 10t³).
    
    Args:
        t: Input value (0.0 to 1.0)
        
    Returns:
        Smoothed value
    """
    t = clamp(t, 0.0, 1.0)
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def ease_in_quad(t: float) -> float:
    """Quadratic ease-in function."""
    return t * t


def ease_out_quad(t: float) -> float:
    """Quadratic ease-out function."""
    return 1.0 - (1.0 - t) * (1.0 - t)


def ease_in_out_quad(t: float) -> float:
    """Quadratic ease-in-out function."""
    if t < 0.5:
        return 2.0 * t * t
    else:
        return 1.0 - pow(-2.0 * t + 2.0, 2.0) / 2.0


def interpolate(start: Numeric, end: Numeric, t: float, 
               interpolation_type: InterpolationType = InterpolationType.LINEAR) -> float:
    """
    Interpolate between two values using specified interpolation type.
    
    Args:
        start: Starting value
        end: Ending value
        t: Interpolation factor (0.0 to 1.0)
        interpolation_type: Type of interpolation to use
        
    Returns:
        Interpolated value
    """
    t = clamp(t, 0.0, 1.0)
    
    if interpolation_type == InterpolationType.LINEAR:
        factor = t
    elif interpolation_type == InterpolationType.EASE_IN:
        factor = ease_in_quad(t)
    elif interpolation_type == InterpolationType.EASE_OUT:
        factor = ease_out_quad(t)
    elif interpolation_type == InterpolationType.EASE_IN_OUT:
        factor = ease_in_out_quad(t)
    elif interpolation_type == InterpolationType.SMOOTH_STEP:
        factor = smooth_step(t)
    else:
        factor = t
    
    return lerp(start, end, factor)


# ============================================================================
# Angle and Rotation Utilities
# ============================================================================

def normalize_angle_radians(angle: float) -> float:
    """
    Normalize angle to range [-π, π].
    
    Args:
        angle: Angle in radians
        
    Returns:
        Normalized angle in radians
    """
    # Handle exact boundary cases first
    if abs(angle - math.pi) < 1e-10:
        return math.pi
    if abs(angle + math.pi) < 1e-10:
        return -math.pi
    
    # First normalize using modulo
    normalized = angle % (2 * math.pi)
    
    # If the result is exactly π and the original was wrapped from a positive value
    if abs(normalized - math.pi) < 1e-10 and angle > math.pi:
        return -math.pi
    
    # Regular normalization to [-π, π]
    if normalized > math.pi:
        normalized -= 2 * math.pi
    
    return normalized


def normalize_angle_degrees(angle: float) -> float:
    """
    Normalize angle to range [-180, 180].
    
    Args:
        angle: Angle in degrees
        
    Returns:
        Normalized angle in degrees
    """
    # Handle exact boundary cases first
    if abs(angle - 180) < 1e-10:
        return 180
    if abs(angle + 180) < 1e-10:
        return -180
    
    # First normalize using modulo
    normalized = angle % 360
    
    # If the result is exactly 180 and the original was wrapped from a positive value
    if abs(normalized - 180) < 1e-10 and angle > 180:
        return -180
    
    # Regular normalization to [-180, 180]
    if normalized > 180:
        normalized -= 360
    
    return normalized


def degrees_to_radians(degrees: float) -> float:
    """Convert degrees to radians."""
    return degrees * math.pi / 180.0


def radians_to_degrees(radians: float) -> float:
    """Convert radians to degrees."""
    return radians * 180.0 / math.pi


def angle_difference(angle1: float, angle2: float, unit: AngleUnit = AngleUnit.RADIANS) -> float:
    """
    Calculate the smallest difference between two angles.
    
    Args:
        angle1: First angle
        angle2: Second angle
        unit: Unit of measurement (radians or degrees)
        
    Returns:
        Smallest angle difference
    """
    if unit == AngleUnit.RADIANS:
        diff = normalize_angle_radians(angle2 - angle1)
    else:
        diff = normalize_angle_degrees(angle2 - angle1)
    return diff


def lerp_angle(start_angle: float, end_angle: float, t: float, 
              unit: AngleUnit = AngleUnit.RADIANS) -> float:
    """
    Interpolate between two angles taking the shortest path.
    
    Args:
        start_angle: Starting angle
        end_angle: Ending angle
        t: Interpolation factor (0.0 to 1.0)
        unit: Unit of measurement
        
    Returns:
        Interpolated angle
    """
    diff = angle_difference(start_angle, end_angle, unit)
    return start_angle + diff * clamp(t, 0.0, 1.0)


# ============================================================================
# Random Utilities
# ============================================================================

def random_float(min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Generate a random float in the specified range."""
    return random.uniform(min_val, max_val)


def random_int(min_val: int, max_val: int) -> int:
    """Generate a random integer in the specified range (inclusive)."""
    return random.randint(min_val, max_val)


def random_bool(probability: float = 0.5) -> bool:
    """
    Generate a random boolean with specified probability of True.
    
    Args:
        probability: Probability of returning True (0.0 to 1.0)
        
    Returns:
        Random boolean value
    """
    return random.random() < probability


def random_choice(choices: List[T]) -> T:
    """Select a random element from a list."""
    if not choices:
        raise ValueError("Cannot choose from empty list")
    return random.choice(choices)


def random_weighted_choice(choices: List[T], weights: List[float]) -> T:
    """
    Select a random element from a list with weighted probabilities.
    
    Args:
        choices: List of choices
        weights: List of weights for each choice
        
    Returns:
        Randomly selected choice
    """
    if len(choices) != len(weights):
        raise ValueError("Choices and weights must have same length")
    if not choices:
        raise ValueError("Cannot choose from empty list")
    
    return random.choices(choices, weights=weights)[0]


def random_gaussian(mean: float = 0.0, std_dev: float = 1.0) -> float:
    """Generate a random number from Gaussian (normal) distribution."""
    return random.gauss(mean, std_dev)


def random_vector2d(min_x: float = -1.0, max_x: float = 1.0, 
                   min_y: float = -1.0, max_y: float = 1.0) -> Vector2D:
    """
    Generate a random Vector2D within specified bounds.
    
    Args:
        min_x: Minimum X value
        max_x: Maximum X value
        min_y: Minimum Y value
        max_y: Maximum Y value
        
    Returns:
        Random Vector2D
    """
    return Vector2D(
        random_float(min_x, max_x),
        random_float(min_y, max_y)
    )


def random_unit_vector() -> Vector2D:
    """Generate a random unit vector (magnitude = 1.0)."""
    angle = random_float(0, 2 * math.pi)
    return Vector2D.from_angle(angle, 1.0)


# ============================================================================
# Distance and Spatial Utilities
# ============================================================================

def distance_2d(x1: float, y1: float, x2: float, y2: float) -> float:
    """Calculate 2D distance between two points."""
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def distance_squared_2d(x1: float, y1: float, x2: float, y2: float) -> float:
    """Calculate squared 2D distance between two points (faster)."""
    return (x2 - x1) ** 2 + (y2 - y1) ** 2


def manhattan_distance_2d(x1: float, y1: float, x2: float, y2: float) -> float:
    """Calculate Manhattan distance between two points."""
    return abs(x2 - x1) + abs(y2 - y1)


def is_point_in_circle(point_x: float, point_y: float, 
                      circle_x: float, circle_y: float, radius: float) -> bool:
    """Check if a point is inside a circle."""
    return distance_squared_2d(point_x, point_y, circle_x, circle_y) <= radius * radius


def is_point_in_rectangle(point_x: float, point_y: float,
                         rect_x: float, rect_y: float, 
                         rect_width: float, rect_height: float) -> bool:
    """Check if a point is inside a rectangle."""
    return (rect_x <= point_x <= rect_x + rect_width and
            rect_y <= point_y <= rect_y + rect_height)


def point_to_line_distance(point: Vector2D, line_start: Vector2D, line_end: Vector2D) -> float:
    """
    Calculate the shortest distance from a point to a line segment.
    
    Args:
        point: Point to measure from
        line_start: Start of line segment
        line_end: End of line segment
        
    Returns:
        Shortest distance to line segment
    """
    # Vector from line start to end
    line_vec = line_end - line_start
    line_length_sq = line_vec.magnitude_squared()
    
    # If line has zero length, return distance to start point
    if line_length_sq < 1e-10:
        return point.distance_to(line_start)
    
    # Project point onto line
    t = max(0.0, min(1.0, (point - line_start).dot(line_vec) / line_length_sq))
    projection = line_start + line_vec * t
    
    return point.distance_to(projection)


# ============================================================================
# Collection Utilities
# ============================================================================

def find_closest_point(target: Vector2D, points: List[Vector2D]) -> Tuple[int, Vector2D, float]:
    """
    Find the closest point to a target from a list of points.
    
    Args:
        target: Target point
        points: List of candidate points
        
    Returns:
        Tuple of (index, closest_point, distance)
    """
    if not points:
        raise ValueError("Cannot find closest point in empty list")
    
    closest_index = 0
    closest_point = points[0]
    closest_distance = target.distance_to(closest_point)
    
    for i, point in enumerate(points[1:], 1):
        distance = target.distance_to(point)
        if distance < closest_distance:
            closest_index = i
            closest_point = point
            closest_distance = distance
    
    return closest_index, closest_point, closest_distance


def find_points_in_range(center: Vector2D, points: List[Vector2D], 
                        max_distance: float) -> List[Tuple[int, Vector2D, float]]:
    """
    Find all points within a specified range of a center point.
    
    Args:
        center: Center point
        points: List of candidate points
        max_distance: Maximum distance to include
        
    Returns:
        List of (index, point, distance) tuples for points in range
    """
    results = []
    max_distance_sq = max_distance * max_distance
    
    for i, point in enumerate(points):
        distance_sq = center.distance_squared_to(point)
        if distance_sq <= max_distance_sq:
            distance = math.sqrt(distance_sq)
            results.append((i, point, distance))
    
    return results


def sort_points_by_distance(target: Vector2D, points: List[Vector2D]) -> List[Tuple[int, Vector2D, float]]:
    """
    Sort points by distance from target.
    
    Args:
        target: Target point
        points: List of points to sort
        
    Returns:
        List of (original_index, point, distance) tuples sorted by distance
    """
    distances = [(i, point, target.distance_to(point)) for i, point in enumerate(points)]
    distances.sort(key=lambda x: x[2])
    return distances


# ============================================================================
# Timing Utilities
# ============================================================================

class Timer:
    """Simple timer for measuring elapsed time."""
    
    def __init__(self):
        self.start_time = time.time()
        self.last_time = self.start_time
    
    def reset(self) -> None:
        """Reset the timer."""
        self.start_time = time.time()
        self.last_time = self.start_time
    
    def elapsed(self) -> float:
        """Get total elapsed time since timer creation/reset."""
        return time.time() - self.start_time
    
    def lap(self) -> float:
        """Get time since last lap call."""
        current_time = time.time()
        lap_time = current_time - self.last_time
        self.last_time = current_time
        return lap_time


def time_function(func: Callable, *args, **kwargs) -> Tuple[Any, float]:
    """
    Time the execution of a function.
    
    Args:
        func: Function to time
        *args: Function arguments
        **kwargs: Function keyword arguments
        
    Returns:
        Tuple of (function_result, execution_time_seconds)
    """
    start_time = time.time()
    result = func(*args, **kwargs)
    execution_time = time.time() - start_time
    return result, execution_time


# ============================================================================
# Data Structure Utilities
# ============================================================================

def safe_divide(numerator: Numeric, denominator: Numeric, default: Numeric = 0.0) -> float:
    """
    Safely divide two numbers, returning default if denominator is zero.
    
    Args:
        numerator: Number to divide
        denominator: Number to divide by
        default: Value to return if denominator is zero
        
    Returns:
        Division result or default value
    """
    if abs(denominator) < 1e-10:
        return float(default)
    return float(numerator) / float(denominator)


def percentage(part: Numeric, total: Numeric) -> float:
    """
    Calculate percentage safely.
    
    Args:
        part: Part value
        total: Total value
        
    Returns:
        Percentage (0.0 to 100.0)
    """
    return safe_divide(part, total, 0.0) * 100.0


def flatten_list(nested_list: List[List[T]]) -> List[T]:
    """Flatten a nested list into a single list."""
    result = []
    for sublist in nested_list:
        result.extend(sublist)
    return result


def chunk_list(items: List[T], chunk_size: int) -> List[List[T]]:
    """
    Split a list into chunks of specified size.
    
    Args:
        items: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive")
    
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def unique_list(items: List[T]) -> List[T]:
    """Remove duplicates from list while preserving order."""
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


# ============================================================================
# String and Formatting Utilities
# ============================================================================

def format_float(value: float, precision: int = 2) -> str:
    """Format a float with specified precision."""
    return f"{value:.{precision}f}"


def format_percentage(value: float, precision: int = 1) -> str:
    """Format a value as a percentage."""
    return f"{value:.{precision}f}%"


def format_time(seconds: float) -> str:
    """
    Format time in seconds to human-readable string.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted time string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs:.1f}s"


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate a string to maximum length with optional suffix.
    
    Args:
        text: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    
    if len(suffix) >= max_length:
        return text[:max_length]
    
    return text[:max_length - len(suffix)] + suffix


# ============================================================================
# Validation Utilities
# ============================================================================

def is_numeric(value: Any) -> bool:
    """Check if a value is numeric (int or float)."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_positive(value: Any) -> bool:
    """Check if a numeric value is positive."""
    return is_numeric(value) and value > 0


def is_in_range(value: Any, min_val: Numeric, max_val: Numeric, inclusive: bool = True) -> bool:
    """
    Check if a value is within a specified range.
    
    Args:
        value: Value to check
        min_val: Minimum value
        max_val: Maximum value
        inclusive: Whether to include boundaries
        
    Returns:
        True if value is in range
    """
    if not is_numeric(value):
        return False
    
    if inclusive:
        return min_val <= value <= max_val
    else:
        return min_val < value < max_val


def validate_probability(value: Any) -> bool:
    """Check if a value is a valid probability (0.0 to 1.0)."""
    return is_numeric(value) and 0.0 <= value <= 1.0

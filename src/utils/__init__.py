"""
Utility functions and classes for Battle AI
"""

from .vector2d import Vector2D
from .config import Config, ConfigManager, config_manager
from .logging_config import BattleAILogger, get_logger, setup_logging_from_config, initialize_logging
from .coordinate_system import (
    CoordinateSystem, 
    WorldBounds, 
    GridSystem, 
    BoundaryBehavior, 
    CoordinateSpace,
    get_coordinate_system,
    initialize_coordinate_system,
    reset_coordinate_system
)
from .common import (
    # Mathematical utilities
    clamp, lerp, inverse_lerp, remap, smooth_step, smoother_step,
    ease_in_quad, ease_out_quad, ease_in_out_quad, interpolate,
    InterpolationType,
    
    # Angle utilities
    normalize_angle_radians, normalize_angle_degrees,
    degrees_to_radians, radians_to_degrees,
    angle_difference, lerp_angle, AngleUnit,
    
    # Random utilities
    random_float, random_int, random_bool, random_choice,
    random_weighted_choice, random_gaussian, random_vector2d, random_unit_vector,
    
    # Distance utilities
    distance_2d, distance_squared_2d, manhattan_distance_2d,
    is_point_in_circle, is_point_in_rectangle, point_to_line_distance,
    
    # Collection utilities
    find_closest_point, find_points_in_range, sort_points_by_distance,
    
    # Timing utilities
    Timer, time_function,
    
    # Data utilities
    safe_divide, percentage, flatten_list, chunk_list, unique_list,
    
    # String utilities
    format_float, format_percentage, format_time, truncate_string,
    
    # Validation utilities
    is_numeric, is_positive, is_in_range, validate_probability
)

__all__ = [
    # Core utilities
    "Vector2D",
    "Config",
    "ConfigManager", 
    "config_manager",
    "BattleAILogger",
    "get_logger",
    "setup_logging_from_config",
    "initialize_logging",
    
    # Coordinate system
    "CoordinateSystem",
    "WorldBounds",
    "GridSystem",
    "BoundaryBehavior",
    "CoordinateSpace",
    "get_coordinate_system",
    "initialize_coordinate_system",
    "reset_coordinate_system",
    
    # Mathematical utilities
    "clamp", "lerp", "inverse_lerp", "remap", "smooth_step", "smoother_step",
    "ease_in_quad", "ease_out_quad", "ease_in_out_quad", "interpolate",
    "InterpolationType",
    
    # Angle utilities
    "normalize_angle_radians", "normalize_angle_degrees",
    "degrees_to_radians", "radians_to_degrees",
    "angle_difference", "lerp_angle", "AngleUnit",
    
    # Random utilities
    "random_float", "random_int", "random_bool", "random_choice",
    "random_weighted_choice", "random_gaussian", "random_vector2d", "random_unit_vector",
    
    # Distance utilities
    "distance_2d", "distance_squared_2d", "manhattan_distance_2d",
    "is_point_in_circle", "is_point_in_rectangle", "point_to_line_distance",
    
    # Collection utilities
    "find_closest_point", "find_points_in_range", "sort_points_by_distance",
    
    # Timing utilities
    "Timer", "time_function",
    
    # Data utilities
    "safe_divide", "percentage", "flatten_list", "chunk_list", "unique_list",
    
    # String utilities
    "format_float", "format_percentage", "format_time", "truncate_string",
    
    # Validation utilities
    "is_numeric", "is_positive", "is_in_range", "validate_probability"
]

"""
Vector2D - 2D Vector mathematics for Battle AI
Task 1.3.1: Implement Vector2D class for positions/velocities
"""

import math
from typing import Union, Tuple


class Vector2D:
    """
    A 2D vector class for handling positions, velocities, and directions.
    Supports basic vector operations needed for agent movement and physics.
    """
    
    def __init__(self, x: float = 0.0, y: float = 0.0):
        """Initialize a 2D vector with x and y components."""
        self.x = float(x)
        self.y = float(y)
    
    def __str__(self) -> str:
        """String representation of the vector."""
        return f"Vector2D({self.x:.2f}, {self.y:.2f})"
    
    def __repr__(self) -> str:
        """Official string representation of the vector."""
        return f"Vector2D({self.x}, {self.y})"
    
    def __eq__(self, other: 'Vector2D') -> bool:
        """Check equality with another vector."""
        if not isinstance(other, Vector2D):
            return False
        return abs(self.x - other.x) < 1e-10 and abs(self.y - other.y) < 1e-10
    
    def __add__(self, other: 'Vector2D') -> 'Vector2D':
        """Add two vectors."""
        return Vector2D(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: 'Vector2D') -> 'Vector2D':
        """Subtract two vectors."""
        return Vector2D(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar: float) -> 'Vector2D':
        """Multiply vector by a scalar."""
        return Vector2D(self.x * scalar, self.y * scalar)
    
    def __rmul__(self, scalar: float) -> 'Vector2D':
        """Right multiplication by a scalar."""
        return self.__mul__(scalar)
    
    def __truediv__(self, scalar: float) -> 'Vector2D':
        """Divide vector by a scalar."""
        if abs(scalar) < 1e-10:
            raise ValueError("Division by zero or near-zero value")
        return Vector2D(self.x / scalar, self.y / scalar)
    
    def magnitude(self) -> float:
        """Calculate the magnitude (length) of the vector."""
        return math.sqrt(self.x * self.x + self.y * self.y)
    
    def magnitude_squared(self) -> float:
        """Calculate the squared magnitude (faster than magnitude)."""
        return self.x * self.x + self.y * self.y
    
    def normalize(self) -> 'Vector2D':
        """Return a normalized (unit) vector in the same direction."""
        mag = self.magnitude()
        if mag < 1e-10:
            return Vector2D(0, 0)
        return self / mag
    
    def normalize_in_place(self) -> None:
        """Normalize this vector in place."""
        mag = self.magnitude()
        if mag > 1e-10:
            self.x /= mag
            self.y /= mag
        else:
            self.x = 0.0
            self.y = 0.0
    
    def distance_to(self, other: 'Vector2D') -> float:
        """Calculate distance to another vector."""
        return (self - other).magnitude()
    
    def distance_squared_to(self, other: 'Vector2D') -> float:
        """Calculate squared distance to another vector (faster)."""
        return (self - other).magnitude_squared()
    
    def dot(self, other: 'Vector2D') -> float:
        """Calculate dot product with another vector."""
        return self.x * other.x + self.y * other.y
    
    def cross(self, other: 'Vector2D') -> float:
        """Calculate 2D cross product (returns scalar)."""
        return self.x * other.y - self.y * other.x
    
    def angle(self) -> float:
        """Get the angle of this vector in radians."""
        return math.atan2(self.y, self.x)
    
    def angle_to(self, other: 'Vector2D') -> float:
        """Calculate angle to another vector in radians."""
        return math.atan2(other.y - self.y, other.x - self.x)
    
    def rotate(self, angle_radians: float) -> 'Vector2D':
        """Rotate vector by given angle in radians."""
        cos_a = math.cos(angle_radians)
        sin_a = math.sin(angle_radians)
        return Vector2D(
            self.x * cos_a - self.y * sin_a,
            self.x * sin_a + self.y * cos_a
        )
    
    def clamp_magnitude(self, max_magnitude: float) -> 'Vector2D':
        """Clamp the vector's magnitude to a maximum value."""
        mag = self.magnitude()
        if mag > max_magnitude:
            return self.normalize() * max_magnitude
        return Vector2D(self.x, self.y)
    
    def to_tuple(self) -> Tuple[float, float]:
        """Convert to tuple for compatibility with other libraries."""
        return (self.x, self.y)
    
    def to_int_tuple(self) -> Tuple[int, int]:
        """Convert to integer tuple (useful for pixel coordinates)."""
        return (int(self.x), int(self.y))
    
    @classmethod
    def from_tuple(cls, t: Tuple[float, float]) -> 'Vector2D':
        """Create vector from tuple."""
        return cls(t[0], t[1])
    
    @classmethod
    def from_angle(cls, angle_radians: float, magnitude: float = 1.0) -> 'Vector2D':
        """Create vector from angle and magnitude."""
        return cls(
            magnitude * math.cos(angle_radians),
            magnitude * math.sin(angle_radians)
        )
    
    @classmethod
    def zero(cls) -> 'Vector2D':
        """Create a zero vector."""
        return cls(0.0, 0.0)
    
    @classmethod
    def up(cls) -> 'Vector2D':
        """Create an up vector (0, 1)."""
        return cls(0.0, 1.0)
    
    @classmethod
    def down(cls) -> 'Vector2D':
        """Create a down vector (0, -1)."""
        return cls(0.0, -1.0)
    
    @classmethod
    def left(cls) -> 'Vector2D':
        """Create a left vector (-1, 0)."""
        return cls(-1.0, 0.0)
    
    @classmethod
    def right(cls) -> 'Vector2D':
        """Create a right vector (1, 0)."""
        return cls(1.0, 0.0)

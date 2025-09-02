"""
Test suite for Vector2D class
Task 1.9.1: Create unit tests for core classes
"""

import pytest
import math
from src.utils.vector2d import Vector2D


class TestVector2D:
    """Test cases for Vector2D class."""
    
    def test_initialization(self):
        """Test vector initialization."""
        v1 = Vector2D()
        assert v1.x == 0.0
        assert v1.y == 0.0
        
        v2 = Vector2D(3, 4)
        assert v2.x == 3.0
        assert v2.y == 4.0
    
    def test_string_representation(self):
        """Test string representations."""
        v = Vector2D(1.5, 2.5)
        assert str(v) == "Vector2D(1.50, 2.50)"
        assert repr(v) == "Vector2D(1.5, 2.5)"
    
    def test_equality(self):
        """Test vector equality."""
        v1 = Vector2D(1, 2)
        v2 = Vector2D(1, 2)
        v3 = Vector2D(1, 3)
        
        assert v1 == v2
        assert v1 != v3
        assert v1 != "not a vector"
    
    def test_addition(self):
        """Test vector addition."""
        v1 = Vector2D(1, 2)
        v2 = Vector2D(3, 4)
        v3 = v1 + v2
        
        assert v3.x == 4
        assert v3.y == 6
    
    def test_subtraction(self):
        """Test vector subtraction."""
        v1 = Vector2D(5, 7)
        v2 = Vector2D(2, 3)
        v3 = v1 - v2
        
        assert v3.x == 3
        assert v3.y == 4
    
    def test_scalar_multiplication(self):
        """Test scalar multiplication."""
        v1 = Vector2D(2, 3)
        v2 = v1 * 2
        v3 = 2 * v1
        
        assert v2.x == 4
        assert v2.y == 6
        assert v3.x == 4
        assert v3.y == 6
    
    def test_scalar_division(self):
        """Test scalar division."""
        v1 = Vector2D(6, 8)
        v2 = v1 / 2
        
        assert v2.x == 3
        assert v2.y == 4
        
        # Test division by zero
        with pytest.raises(ValueError):
            _ = v1 / 0
    
    def test_magnitude(self):
        """Test magnitude calculation."""
        v1 = Vector2D(3, 4)
        assert v1.magnitude() == 5.0
        
        v2 = Vector2D(0, 0)
        assert v2.magnitude() == 0.0
    
    def test_magnitude_squared(self):
        """Test squared magnitude calculation."""
        v1 = Vector2D(3, 4)
        assert v1.magnitude_squared() == 25.0
    
    def test_normalize(self):
        """Test vector normalization."""
        v1 = Vector2D(3, 4)
        v2 = v1.normalize()
        
        assert abs(v2.magnitude() - 1.0) < 1e-10
        assert abs(v2.x - 0.6) < 1e-10
        assert abs(v2.y - 0.8) < 1e-10
        
        # Test zero vector normalization
        v3 = Vector2D(0, 0)
        v4 = v3.normalize()
        assert v4.x == 0
        assert v4.y == 0
    
    def test_normalize_in_place(self):
        """Test in-place normalization."""
        v = Vector2D(3, 4)
        v.normalize_in_place()
        
        assert abs(v.magnitude() - 1.0) < 1e-10
    
    def test_distance(self):
        """Test distance calculations."""
        v1 = Vector2D(0, 0)
        v2 = Vector2D(3, 4)
        
        assert v1.distance_to(v2) == 5.0
        assert v1.distance_squared_to(v2) == 25.0
    
    def test_dot_product(self):
        """Test dot product."""
        v1 = Vector2D(1, 2)
        v2 = Vector2D(3, 4)
        
        assert v1.dot(v2) == 11  # 1*3 + 2*4
    
    def test_cross_product(self):
        """Test 2D cross product."""
        v1 = Vector2D(1, 2)
        v2 = Vector2D(3, 4)
        
        assert v1.cross(v2) == -2  # 1*4 - 2*3
    
    def test_angle(self):
        """Test angle calculations."""
        v1 = Vector2D(1, 0)
        assert v1.angle() == 0
        
        v2 = Vector2D(0, 1)
        assert abs(v2.angle() - math.pi/2) < 1e-10
    
    def test_rotation(self):
        """Test vector rotation."""
        v1 = Vector2D(1, 0)
        v2 = v1.rotate(math.pi/2)
        
        assert abs(v2.x) < 1e-10
        assert abs(v2.y - 1) < 1e-10
    
    def test_clamp_magnitude(self):
        """Test magnitude clamping."""
        v1 = Vector2D(3, 4)  # magnitude = 5
        v2 = v1.clamp_magnitude(3)
        
        assert abs(v2.magnitude() - 3) < 1e-10
        
        v3 = v1.clamp_magnitude(10)
        assert v3.magnitude() == v1.magnitude()
    
    def test_tuple_conversion(self):
        """Test tuple conversions."""
        v = Vector2D(1.7, 2.3)
        
        assert v.to_tuple() == (1.7, 2.3)
        assert v.to_int_tuple() == (1, 2)
    
    def test_class_methods(self):
        """Test class methods."""
        v1 = Vector2D.from_tuple((2, 3))
        assert v1.x == 2
        assert v1.y == 3
        
        v2 = Vector2D.from_angle(0, 5)
        assert abs(v2.x - 5) < 1e-10
        assert abs(v2.y) < 1e-10
        
        assert Vector2D.zero() == Vector2D(0, 0)
        assert Vector2D.up() == Vector2D(0, 1)
        assert Vector2D.down() == Vector2D(0, -1)
        assert Vector2D.left() == Vector2D(-1, 0)
        assert Vector2D.right() == Vector2D(1, 0)

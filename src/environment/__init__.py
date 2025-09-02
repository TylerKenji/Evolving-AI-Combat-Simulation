"""
Environment Module

This module contains all environment implementations for the Battle AI system.
It provides the base environment interface and various specialized environment types
for different battle scenarios and simulation needs.

Key Components:
- BaseEnvironment: Abstract base class for all environments
- EnvironmentState: Enumeration of environment states
- CollisionType: Types of collisions that can occur
- TerrainType: Types of terrain tiles
- CollisionEvent: Collision event data structure
- EnvironmentMetrics: Performance and state metrics
- TerrainTile: Individual terrain tile data

Future environment types (to be implemented):
- SimpleEnvironment: Basic 2D battlefield with minimal features
- TerrainEnvironment: Environment with complex terrain systems
- PhysicsEnvironment: Environment with advanced physics simulation
- MultiLayerEnvironment: Environment with multiple battlefield layers
"""

from .base_environment import (
    BaseEnvironment,
    EnvironmentState,
    CollisionType,
    TerrainType,
    CollisionEvent,
    EnvironmentMetrics,
    TerrainTile
)
from .simple_environment import SimpleEnvironment

__all__ = [
    'BaseEnvironment',
    'SimpleEnvironment',
    'EnvironmentState',
    'CollisionType', 
    'TerrainType',
    'CollisionEvent',
    'EnvironmentMetrics',
    'TerrainTile'
]

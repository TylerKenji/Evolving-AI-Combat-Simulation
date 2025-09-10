"""
Environment Module

This module contains all environment implementations for the Battle AI system.
It provides the base environment interface and various specialized environment types
for different battle scenarios and simulation needs.

Key Components:
- BaseEnvironment: Abstract base class for all environments
- BattleEnvironment: Advanced combat environment with teams and tactical features
- SimpleEnvironment: Basic 2D battlefield with minimal features
- EnvironmentState: Enumeration of environment states
- CollisionType: Types of collisions that can occur
- TerrainType: Types of terrain tiles
- CollisionEvent: Collision event data structure
- EnvironmentMetrics: Performance and state metrics
- TerrainTile: Individual terrain tile data

Environment Implementations:
- BattleEnvironment: Primary combat environment with advanced features
- SimpleEnvironment: Basic 2D battlefield for testing and development
- Future: TerrainEnvironment, PhysicsEnvironment
"""

from .base_environment import (
    BaseEnvironment,
    EnvironmentState,
    CollisionType,
    CollisionEvent,
    TerrainType,
    TerrainTile,
    EnvironmentMetrics
)

from .battle_environment import (
    BattleEnvironment,
    SpawnStrategy,
    BattlePhase,
    TeamInfo
)

from .simple_environment import SimpleEnvironment

__all__ = [
    # Base classes and enums
    'BaseEnvironment',
    'EnvironmentState', 
    'CollisionType',
    'CollisionEvent',
    'TerrainType',
    'TerrainTile',
    'EnvironmentMetrics',
    
    # Environment implementations
    'BattleEnvironment',
    'SimpleEnvironment',
    
    # Battle environment specific
    'SpawnStrategy',
    'BattlePhase', 
    'TeamInfo'
]

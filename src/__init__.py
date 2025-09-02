"""
Evolving Battle AI - Core Package
Foundation & Architecture Phase (Phase 1)

This package contains the core components for the evolving battle AI system,
including agents, environment, evolution algorithms, events, simulation, and utilities.
"""

__version__ = "0.1.0"
__author__ = "Battle AI Development Team"

# Core utilities
from .utils.vector2d import Vector2D
from .utils.config import Config, ConfigManager
from .utils.coordinate_system import (
    CoordinateSpace, BoundaryBehavior, WorldBounds, GridSystem, CoordinateSystem,
    get_coordinate_system, initialize_coordinate_system, reset_coordinate_system
)
from .utils.logging_config import get_logger, setup_logging_from_config

# Agent system
from .agents.base_agent import BaseAgent, AgentStats, AgentGenome, AgentMemory
from .agents.agent_state import (
    ActionType, CombatStatus, MovementStatus, ObjectiveType,
    AgentObjective, CombatState, MovementState, SensorData,
    AgentStateSnapshot, StateTransition, StateManager
)

# Environment system
from .environment.base_environment import BaseEnvironment, EnvironmentState, CollisionType, TerrainType
from .environment.simple_environment import SimpleEnvironment

# Event system
from .events import (
    EventType, EventPriority, Event, CombatEvent, MovementEvent, CommunicationEvent,
    EventHandler, EventFilter, EventBus, global_event_bus,
    create_combat_event, create_movement_event, create_communication_event
)

# Simulation system
from .simulation import (
    SimulationState, LoopPhase, SimulationMetrics, SimulationConfig,
    SimulationPhase, SimulationContext, SimulationEngine,
    InputProcessingPhase, AgentDecisionPhase, AgentActionPhase,
    PhysicsUpdatePhase, EnvironmentUpdatePhase, EventProcessingPhase,
    create_default_simulation
)

__all__ = [
    # Core utilities
    "Vector2D",
    "Config", "ConfigManager",
    "CoordinateSpace", "BoundaryBehavior", "WorldBounds", "GridSystem", "CoordinateSystem",
    "get_coordinate_system", "initialize_coordinate_system", "reset_coordinate_system",
    "get_logger", "setup_logging_from_config",
    
    # Agent system
    "BaseAgent", "AgentStats", "AgentGenome", "AgentMemory",
    "ActionType", "CombatStatus", "MovementStatus", "ObjectiveType",
    "AgentObjective", "CombatState", "MovementState", "SensorData",
    "AgentStateSnapshot", "StateTransition", "StateManager",
    
    # Environment system
    "BaseEnvironment", "EnvironmentState", "CollisionType", "TerrainType",
    "SimpleEnvironment",
    
    # Event system
    "EventType", "EventPriority", "Event", "CombatEvent", "MovementEvent", "CommunicationEvent",
    "EventHandler", "EventFilter", "EventBus", "global_event_bus",
    "create_combat_event", "create_movement_event", "create_communication_event",
    
    # Simulation system
    "SimulationState", "LoopPhase", "SimulationMetrics", "SimulationConfig",
    "SimulationPhase", "SimulationContext", "SimulationEngine",
    "InputProcessingPhase", "AgentDecisionPhase", "AgentActionPhase",
    "PhysicsUpdatePhase", "EnvironmentUpdatePhase", "EventProcessingPhase",
    "create_default_simulation",
]

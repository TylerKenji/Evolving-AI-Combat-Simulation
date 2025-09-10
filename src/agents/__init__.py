"""
Agents Module

This module contains all agent implementations for the Battle AI system.
It provides the base agent interface and various specialized agent types
for different combat strategies and roles.

Key Components:
- BaseAgent: Abstract base class for all agents
- AgentState: Enumeration of possible agent states  
- AgentRole: Enumeration of agent specializations
- CombatAction: Enumeration of possible combat actions
- AgentStats: Core statistics and capabilities
- AgentGenome: Genetic representation for evolution
- AgentMemory: Learning and adaptation tracking

Future agent types (to be implemented):
- SimpleAgent: Basic AI with hardcoded behaviors
- GeneticAgent: Agent driven by genetic algorithms
- RLAgent: Agent using reinforcement learning
- HybridAgent: Combination of genetic and RL approaches
- HumanAgent: Human-controlled agent for testing
"""

"""
Agents Module

This module contains all agent implementations for the Battle AI system.
It provides the base agent interface and various specialized agent types
for different combat strategies and roles.

Key Components:
- BaseAgent: Abstract base class for all agents
- AgentState: Enumeration of possible agent states  
- AgentRole: Enumeration of agent specializations
- CombatAction: Enumeration of possible combat actions
- AgentStats: Core statistics and capabilities
- AgentGenome: Genetic representation for evolution
- AgentMemory: Learning and adaptation tracking

State Management (Task 1.2.5):
- AgentStateSnapshot: Complete state capture at specific time
- CombatState: Detailed combat status and statistics
- MovementState: Movement tracking and pathfinding
- SensorData: Environmental perception and awareness
- StateManager: State history and behavior analysis

Future agent types (to be implemented):
- SimpleAgent: Basic AI with hardcoded behaviors
- GeneticAgent: Agent driven by genetic algorithms
- RLAgent: Agent using reinforcement learning
- HybridAgent: Combination of genetic and RL approaches
- HumanAgent: Human-controlled agent for testing
"""

from .base_agent import (
    BaseAgent,
    AgentState,
    AgentRole,
    CombatAction,
    AgentStats,
    AgentGenome,
    AgentMemory
)

from .random_agent import RandomAgent
from .idle_agent import IdleAgent
from .simple_chase_agent import SimpleChaseAgent

from .decision_framework import (
    DecisionMaker,
    DecisionContext,
    ActionEvaluator,
    DefaultActionEvaluator,
    ActionValidator,
    ActionScore,
    DecisionPriority,
    ContextType,
    create_decision_maker
)

from .agent_state import (
    # Action and status enums
    ActionType,
    CombatStatus,
    MovementStatus,
    ObjectiveType,
    
    # Core state structures
    AgentObjective,
    CombatState,
    MovementState,
    SensorData,
    
    # State management
    AgentStateSnapshot,
    StateTransition,
    StateManager
)

__all__ = [
    # Base agent components
    'BaseAgent',
    'AgentState', 
    'AgentRole',
    'CombatAction',
    'AgentStats',
    'AgentGenome',
    'AgentMemory',
    
    # Concrete agent implementations
    'RandomAgent',
    'IdleAgent',
    'SimpleChaseAgent',
    
    # Decision-making framework
    'DecisionMaker',
    'DecisionContext',
    'ActionEvaluator',
    'DefaultActionEvaluator',
    'ActionValidator',
    'ActionScore',
    'DecisionPriority',
    'ContextType',
    'create_decision_maker',
    
    # State management enums
    'ActionType',
    'CombatStatus', 
    'MovementStatus',
    'ObjectiveType',
    
    # State data structures
    'AgentObjective',
    'CombatState',
    'MovementState',
    'SensorData',
    'AgentStateSnapshot',
    'StateTransition',
    'StateManager'
]

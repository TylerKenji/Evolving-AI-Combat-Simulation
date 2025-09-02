"""
Agent State Data Structures
Task 1.2.5: Create data structures for agent state

This module provides comprehensive data structures for managing agent state
throughout the simulation, including combat status, movement state, objectives,
and historical tracking.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from src.utils.vector2d import Vector2D


class ActionType(Enum):
    """Types of actions an agent can perform."""
    MOVE = "move"
    ATTACK = "attack"
    DEFEND = "defend"
    DODGE = "dodge"
    RETREAT = "retreat"
    COOPERATE = "cooperate"
    PATROL = "patrol"
    SEARCH = "search"
    HEAL = "heal"
    USE_ABILITY = "use_ability"
    IDLE = "idle"


class CombatStatus(Enum):
    """Current combat engagement status."""
    NOT_IN_COMBAT = "not_in_combat"
    ENGAGING = "engaging"
    UNDER_ATTACK = "under_attack"
    RETREATING = "retreating"
    FLANKING = "flanking"
    DEFENDING = "defending"
    STUNNED = "stunned"


class MovementStatus(Enum):
    """Current movement state."""
    STATIONARY = "stationary"
    MOVING = "moving"
    RUNNING = "running"
    DODGING = "dodging"
    STUCK = "stuck"
    FOLLOWING = "following"
    PATROLLING = "patrolling"


class ObjectiveType(Enum):
    """Types of objectives an agent can have."""
    ELIMINATE_TARGET = "eliminate_target"
    DEFEND_POSITION = "defend_position"
    PATROL_AREA = "patrol_area"
    FOLLOW_ALLY = "follow_ally"
    RETREAT_TO_SAFETY = "retreat_to_safety"
    COLLECT_ITEM = "collect_item"
    SUPPORT_ALLY = "support_ally"
    EXPLORE_AREA = "explore_area"


@dataclass
class AgentObjective:
    """Represents a specific objective for an agent."""
    objective_type: ObjectiveType
    target_position: Optional[Vector2D] = None
    target_agent_id: Optional[str] = None
    priority: float = 1.0
    created_time: datetime = field(default_factory=datetime.now)
    completion_threshold: float = 10.0  # Distance or other metric for completion
    timeout: Optional[float] = None  # Seconds until objective expires
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if objective has timed out."""
        if self.timeout is None:
            return False
        elapsed = (datetime.now() - self.created_time).total_seconds()
        return elapsed > self.timeout
    
    def distance_to_target(self, current_position: Vector2D) -> float:
        """Calculate distance to target position."""
        if self.target_position is None:
            return float('inf')
        return current_position.distance_to(self.target_position)


@dataclass
class CombatState:
    """Comprehensive combat state information."""
    status: CombatStatus = CombatStatus.NOT_IN_COMBAT
    last_attack_time: Optional[datetime] = None
    last_damage_time: Optional[datetime] = None
    current_target_id: Optional[str] = None
    threat_level: float = 0.0  # 0.0 = no threat, 1.0 = maximum threat
    
    # Combat statistics
    total_damage_dealt: float = 0.0
    total_damage_taken: float = 0.0
    attacks_attempted: int = 0
    attacks_hit: int = 0
    dodges_attempted: int = 0
    dodges_successful: int = 0
    
    # Cooldowns and timers
    attack_cooldown_remaining: float = 0.0
    special_ability_cooldown: float = 0.0
    stun_remaining: float = 0.0
    
    def can_attack(self) -> bool:
        """Check if agent can perform an attack."""
        return (self.attack_cooldown_remaining <= 0.0 and 
                self.stun_remaining <= 0.0 and
                self.status != CombatStatus.STUNNED)
    
    def get_accuracy_rate(self) -> float:
        """Calculate current accuracy rate."""
        if self.attacks_attempted == 0:
            return 0.0
        return self.attacks_hit / self.attacks_attempted
    
    def get_dodge_rate(self) -> float:
        """Calculate current dodge success rate."""
        if self.dodges_attempted == 0:
            return 0.0
        return self.dodges_successful / self.dodges_attempted


@dataclass
class MovementState:
    """Comprehensive movement state information."""
    status: MovementStatus = MovementStatus.STATIONARY
    current_velocity: Vector2D = field(default_factory=Vector2D)
    target_position: Optional[Vector2D] = None
    path: List[Vector2D] = field(default_factory=list)
    current_path_index: int = 0
    
    # Movement statistics
    total_distance_moved: float = 0.0
    movement_efficiency: float = 1.0  # Ratio of direct distance to actual distance
    stuck_counter: int = 0
    last_position_change: Optional[datetime] = None
    
    def is_moving(self) -> bool:
        """Check if agent is currently in motion."""
        return (self.status in [MovementStatus.MOVING, MovementStatus.RUNNING, 
                               MovementStatus.DODGING, MovementStatus.FOLLOWING] and
                self.current_velocity.magnitude() > 0.1)
    
    def has_target(self) -> bool:
        """Check if agent has a movement target."""
        return self.target_position is not None
    
    def get_next_waypoint(self) -> Optional[Vector2D]:
        """Get the next waypoint in the current path."""
        if (self.current_path_index < len(self.path) and 
            self.current_path_index >= 0):
            return self.path[self.current_path_index]
        return None
    
    def advance_path(self) -> bool:
        """Move to the next waypoint in the path."""
        if self.current_path_index < len(self.path) - 1:
            self.current_path_index += 1
            return True
        return False


@dataclass
class SensorData:
    """Information from agent sensors and perception."""
    visible_agents: List[str] = field(default_factory=list)
    visible_enemies: List[str] = field(default_factory=list)
    visible_allies: List[str] = field(default_factory=list)
    detected_threats: Dict[str, float] = field(default_factory=dict)  # agent_id -> threat_level
    
    # Environmental awareness
    nearby_obstacles: List[Vector2D] = field(default_factory=list)
    safe_positions: List[Vector2D] = field(default_factory=list)
    last_update_time: datetime = field(default_factory=datetime.now)
    
    def get_nearest_enemy(self, current_position: Vector2D, 
                         agent_positions: Dict[str, Vector2D]) -> Optional[Tuple[str, float]]:
        """Find the nearest enemy and return (id, distance)."""
        if not self.visible_enemies:
            return None
        
        nearest_id = None
        nearest_distance = float('inf')
        
        for enemy_id in self.visible_enemies:
            if enemy_id in agent_positions:
                distance = current_position.distance_to(agent_positions[enemy_id])
                if distance < nearest_distance:
                    nearest_distance = distance
                    nearest_id = enemy_id
        
        return (nearest_id, nearest_distance) if nearest_id else None
    
    def get_highest_threat(self) -> Optional[Tuple[str, float]]:
        """Get the agent ID with the highest threat level."""
        if not self.detected_threats:
            return None
        
        max_threat_id = max(self.detected_threats.keys(), 
                           key=lambda x: self.detected_threats[x])
        return (max_threat_id, self.detected_threats[max_threat_id])


@dataclass
class AgentStateSnapshot:
    """Complete state snapshot of an agent at a specific time."""
    timestamp: datetime = field(default_factory=datetime.now)
    agent_id: str = ""
    position: Vector2D = field(default_factory=Vector2D)
    health: float = 100.0
    
    # State components
    action_type: ActionType = ActionType.IDLE
    combat_state: CombatState = field(default_factory=CombatState)
    movement_state: MovementState = field(default_factory=MovementState)
    sensor_data: SensorData = field(default_factory=SensorData)
    current_objectives: List[AgentObjective] = field(default_factory=list)
    
    # Performance metrics
    decision_time: float = 0.0  # Time taken to make last decision (ms)
    energy_level: float = 1.0   # 0.0 = exhausted, 1.0 = full energy
    morale: float = 0.5         # 0.0 = demoralized, 1.0 = highly motivated
    
    def get_primary_objective(self) -> Optional[AgentObjective]:
        """Get the highest priority objective."""
        if not self.current_objectives:
            return None
        return max(self.current_objectives, key=lambda x: x.priority)
    
    def is_healthy(self) -> bool:
        """Check if agent is in good health."""
        return self.health > 30.0
    
    def is_in_danger(self) -> bool:
        """Check if agent is in immediate danger."""
        return (self.health < 25.0 or 
                self.combat_state.threat_level > 0.7 or
                len(self.sensor_data.visible_enemies) > 2)
    
    def get_state_summary(self) -> str:
        """Get a human-readable summary of the agent state."""
        objective = self.get_primary_objective()
        obj_str = f"{objective.objective_type.value}" if objective else "none"
        
        return (f"Agent {self.agent_id[:8]}: {self.action_type.value} | "
                f"HP:{self.health:.1f} | Combat:{self.combat_state.status.value} | "
                f"Move:{self.movement_state.status.value} | Objective:{obj_str}")


@dataclass 
class StateTransition:
    """Records a state change for analysis and debugging."""
    timestamp: datetime = field(default_factory=datetime.now)
    agent_id: str = ""
    from_state: ActionType = ActionType.IDLE
    to_state: ActionType = ActionType.IDLE
    trigger: str = ""  # What caused the transition
    context: Dict[str, Any] = field(default_factory=dict)
    
    def get_transition_description(self) -> str:
        """Get human-readable transition description."""
        return (f"{self.agent_id[:8]}: {self.from_state.value} → "
                f"{self.to_state.value} ({self.trigger})")


class StateManager:
    """Manages agent state snapshots and transitions."""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.state_history: Dict[str, List[AgentStateSnapshot]] = {}
        self.transition_history: List[StateTransition] = []
    
    def record_state(self, agent_id: str, state: AgentStateSnapshot) -> None:
        """Record a state snapshot for an agent."""
        if agent_id not in self.state_history:
            self.state_history[agent_id] = []
        
        self.state_history[agent_id].append(state)
        
        # Limit history size
        if len(self.state_history[agent_id]) > self.max_history:
            self.state_history[agent_id] = self.state_history[agent_id][-self.max_history:]
    
    def record_transition(self, transition: StateTransition) -> None:
        """Record a state transition."""
        self.transition_history.append(transition)
        
        # Limit history size
        if len(self.transition_history) > self.max_history:
            self.transition_history = self.transition_history[-self.max_history:]
    
    def get_latest_state(self, agent_id: str) -> Optional[AgentStateSnapshot]:
        """Get the most recent state for an agent."""
        if agent_id in self.state_history and self.state_history[agent_id]:
            return self.state_history[agent_id][-1]
        return None
    
    def get_state_history(self, agent_id: str, count: int = 10) -> List[AgentStateSnapshot]:
        """Get recent state history for an agent."""
        if agent_id not in self.state_history:
            return []
        return self.state_history[agent_id][-count:]
    
    def get_recent_transitions(self, agent_id: Optional[str] = None, 
                             count: int = 10) -> List[StateTransition]:
        """Get recent state transitions, optionally filtered by agent."""
        transitions = self.transition_history
        if agent_id:
            transitions = [t for t in transitions if t.agent_id == agent_id]
        return transitions[-count:]
    
    def analyze_agent_behavior(self, agent_id: str) -> Dict[str, Any]:
        """Analyze an agent's behavior patterns from state history."""
        states = self.get_state_history(agent_id, 100)
        if not states:
            return {}
        
        # Calculate behavior statistics
        action_counts = {}
        total_damage_dealt = 0.0
        total_damage_taken = 0.0
        total_distance = 0.0
        
        for state in states:
            action = state.action_type.value
            action_counts[action] = action_counts.get(action, 0) + 1
            total_damage_dealt += state.combat_state.total_damage_dealt
            total_damage_taken += state.combat_state.total_damage_taken
            total_distance += state.movement_state.total_distance_moved
        
        return {
            'action_distribution': action_counts,
            'total_damage_dealt': total_damage_dealt,
            'total_damage_taken': total_damage_taken,
            'total_distance_moved': total_distance,
            'average_health': sum(s.health for s in states) / len(states),
            'average_energy': sum(s.energy_level for s in states) / len(states),
            'average_morale': sum(s.morale for s in states) / len(states)
        }

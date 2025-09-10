"""
Agent Action Validation and Execution System

This module provides comprehensive validation and execution of agent actions,
ensuring that actions are safely executed with proper error handling, state
management, and consistency checking.

Key Components:
- ActionExecutor: Core action execution with validation
- ActionResult: Detailed result information for each action
- ExecutionContext: Comprehensive execution environment
- ActionSequencer: Handles action conflicts and ordering
- SafetyValidator: Advanced safety and consistency checks
- PerformanceTracker: Action execution performance monitoring

This system bridges the gap between decision-making (from decision_framework)
and actual action execution, providing safety, validation, and detailed
feedback for all agent actions.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple, Set, Sequence, Union
from dataclasses import dataclass, field
import logging
import time
import traceback
import math
from datetime import datetime

from src.utils.vector2d import Vector2D
from src.utils.logging_config import get_logger
from src.agents.base_agent import CombatAction, BaseAgent, AgentState


class ActionStatus(Enum):
    """Status of action execution."""
    PENDING = "pending"         # Action queued but not yet executed
    VALIDATING = "validating"   # Action being validated
    EXECUTING = "executing"     # Action currently being executed
    SUCCESS = "success"         # Action completed successfully
    FAILED = "failed"           # Action failed during execution
    BLOCKED = "blocked"         # Action blocked by validation or conflicts
    CANCELLED = "cancelled"     # Action cancelled before execution
    PARTIAL = "partial"         # Action partially completed


class ValidationLevel(Enum):
    """Levels of validation to perform."""
    BASIC = 1       # Basic state and legality checks
    STANDARD = 2    # Standard validation including range and constraints
    STRICT = 3      # Strict validation with safety and consistency checks
    PARANOID = 4    # Paranoid validation with extensive error checking


class ExecutionError(Exception):
    """Exception raised during action execution."""
    
    def __init__(self, message: str, action: CombatAction, agent_id: str, 
                 error_code: str = "EXECUTION_ERROR"):
        super().__init__(message)
        self.action = action
        self.agent_id = agent_id
        self.error_code = error_code
        self.timestamp = datetime.now()


@dataclass
class ActionResult:
    """
    Comprehensive result of action execution.
    
    Provides detailed information about what happened during action execution,
    including success/failure, performance metrics, side effects, and errors.
    """
    
    # Basic result information
    action: CombatAction
    agent_id: str
    status: ActionStatus
    success: bool
    execution_time: float  # Time taken to execute in seconds
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Detailed results
    primary_result: Any = None          # Main result (e.g., damage dealt, distance moved)
    secondary_effects: Dict[str, Any] = field(default_factory=dict)  # Side effects
    target_agent_id: Optional[str] = None    # Target of the action (if applicable)
    
    # Validation and error information
    validation_passed: bool = True
    validation_errors: List[str] = field(default_factory=list)
    execution_error: Optional[str] = None
    error_code: Optional[str] = None
    
    # Performance metrics
    validation_time: float = 0.0       # Time spent in validation
    actual_execution_time: float = 0.0 # Time spent in actual execution
    total_time: float = 0.0            # Total time including overhead
    
    # Context information
    pre_execution_state: Dict[str, Any] = field(default_factory=dict)
    post_execution_state: Dict[str, Any] = field(default_factory=dict)
    battlefield_context: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        status_icon = "✅" if self.success else "❌"
        agent_display = self.agent_id[:8] if self.agent_id else "Unknown"
        return (f"{status_icon} {self.action.value} by {agent_display} "
                f"({self.status.value}, {self.execution_time:.3f}s)")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            'action': self.action.value,
            'agent_id': self.agent_id,
            'status': self.status.value,
            'success': self.success,
            'execution_time': self.execution_time,
            'timestamp': self.timestamp.isoformat(),
            'primary_result': self.primary_result,
            'secondary_effects': self.secondary_effects,
            'target_agent_id': self.target_agent_id,
            'validation_passed': self.validation_passed,
            'validation_errors': self.validation_errors,
            'execution_error': self.execution_error,
            'error_code': self.error_code,
            'performance': {
                'validation_time': self.validation_time,
                'actual_execution_time': self.actual_execution_time,
                'total_time': self.total_time
            }
        }


@dataclass
class ExecutionContext:
    """
    Comprehensive context for action execution.
    
    Contains all information needed for safe and validated action execution,
    including agent state, battlefield information, and execution parameters.
    """
    
    # Core execution information
    agent: 'BaseAgent'
    action: CombatAction
    target_agent: Optional['BaseAgent'] = None
    target_position: Optional[Vector2D] = None
    action_parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Battlefield context
    visible_agents: Sequence['BaseAgent'] = field(default_factory=list)
    battlefield_info: Dict[str, Any] = field(default_factory=dict)
    dt: float = 1.0
    
    # Execution settings
    validation_level: ValidationLevel = ValidationLevel.STANDARD
    allow_partial_execution: bool = False
    timeout_seconds: float = 5.0
    
    # State snapshots
    pre_execution_snapshot: Dict[str, Any] = field(default_factory=dict)
    
    def create_pre_execution_snapshot(self) -> None:
        """Create snapshot of agent state before execution."""
        self.pre_execution_snapshot = {
            'position': Vector2D(self.agent.position.x, self.agent.position.y),
            'health': self.agent.stats.current_health,
            'state': self.agent.state,
            'last_attack_time': self.agent.last_attack_time,
            'is_alive': self.agent.is_alive,
            'can_attack': self.agent.can_attack
        }


class SafetyValidator:
    """
    Advanced safety and consistency validation for action execution.
    
    Provides multiple levels of validation to ensure actions are safe,
    consistent, and will not cause system errors or invalid states.
    """
    
    def __init__(self):
        self.logger = get_logger("SafetyValidator")
    
    def validate_action_safety(self, context: ExecutionContext) -> Tuple[bool, List[str]]:
        """
        Perform comprehensive safety validation.
        
        Args:
            context: Execution context to validate
            
        Returns:
            Tuple of (is_safe, error_messages)
        """
        errors = []
        
        # Basic safety checks
        basic_errors = self._validate_basic_safety(context)
        errors.extend(basic_errors)
        
        # Action-specific safety checks
        action_errors = self._validate_action_specific_safety(context)
        errors.extend(action_errors)
        
        # State consistency checks
        if context.validation_level.value >= ValidationLevel.STRICT.value:
            consistency_errors = self._validate_state_consistency(context)
            errors.extend(consistency_errors)
        
        # Paranoid safety checks
        if context.validation_level.value >= ValidationLevel.PARANOID.value:
            paranoid_errors = self._validate_paranoid_safety(context)
            errors.extend(paranoid_errors)
        
        is_safe = len(errors) == 0
        return is_safe, errors
    
    def _validate_basic_safety(self, context: ExecutionContext) -> List[str]:
        """Basic safety validation."""
        errors = []
        
        # Agent existence and validity
        if context.agent is None:
            errors.append("Agent is None")
            return errors
        
        # Agent alive check
        if not context.agent.is_alive:
            errors.append(f"Agent {context.agent.agent_id} is not alive")
        
        # Action validity
        if context.action is None:
            errors.append("Action is None")
        elif not isinstance(context.action, CombatAction):
            errors.append(f"Invalid action type: {type(context.action)}")
        
        # Basic state consistency
        if hasattr(context.agent, 'stats') and context.agent.stats is None:
            errors.append("Agent stats are None")
        
        if hasattr(context.agent, 'position') and context.agent.position is None:
            errors.append("Agent position is None")
        
        return errors
    
    def _validate_action_specific_safety(self, context: ExecutionContext) -> List[str]:
        """Action-specific safety validation."""
        errors = []
        
        if context.action == CombatAction.ATTACK_MELEE or context.action == CombatAction.ATTACK_RANGED:
            errors.extend(self._validate_attack_safety(context))
        elif context.action == CombatAction.MOVE:
            errors.extend(self._validate_movement_safety(context))
        elif context.action == CombatAction.RETREAT:
            errors.extend(self._validate_retreat_safety(context))
        
        return errors
    
    def _validate_attack_safety(self, context: ExecutionContext) -> List[str]:
        """Validate attack action safety."""
        errors = []
        
        # Target validation
        if context.target_agent is None:
            errors.append("Attack requires a target agent")
        elif context.target_agent == context.agent:
            errors.append("Agent cannot attack itself")
        elif not context.target_agent.is_alive:
            errors.append(f"Target agent {context.target_agent.agent_id} is not alive")
        
        # Range validation
        if context.target_agent:
            distance = context.agent.position.distance_to(context.target_agent.position)
            if distance > context.agent.stats.attack_range:
                errors.append(f"Target out of range: {distance:.1f} > {context.agent.stats.attack_range}")
        
        # Attack capability validation
        if not context.agent.can_attack:
            errors.append("Agent cannot attack (cooldown or status effect)")
        
        return errors
    
    def _validate_movement_safety(self, context: ExecutionContext) -> List[str]:
        """Validate movement action safety."""
        errors = []
        
        # Basic movement validation
        if not hasattr(context.agent, 'stats') or context.agent.stats.speed <= 0:
            errors.append("Agent has invalid movement speed")
        
        # Battlefield bounds validation
        bounds = context.battlefield_info.get('bounds')
        if bounds and context.target_position:
            min_x = bounds.get('min_x', -1000)
            max_x = bounds.get('max_x', 1000)
            min_y = bounds.get('min_y', -1000)
            max_y = bounds.get('max_y', 1000)
            
            if not (min_x <= context.target_position.x <= max_x):
                errors.append(f"Target X position {context.target_position.x} outside bounds [{min_x}, {max_x}]")
            if not (min_y <= context.target_position.y <= max_y):
                errors.append(f"Target Y position {context.target_position.y} outside bounds [{min_y}, {max_y}]")
        
        return errors
    
    def _validate_retreat_safety(self, context: ExecutionContext) -> List[str]:
        """Validate retreat action safety."""
        errors = []
        
        # Check if there are threats to retreat from
        if not context.visible_agents:
            errors.append("No agents visible to retreat from")
        
        # Ensure agent can move
        if hasattr(context.agent, 'stats') and context.agent.stats.speed <= 0:
            errors.append("Agent cannot retreat (no movement speed)")
        
        return errors
    
    def _validate_state_consistency(self, context: ExecutionContext) -> List[str]:
        """Validate state consistency."""
        errors = []
        
        # Health consistency
        if context.agent.stats.current_health > context.agent.stats.max_health:
            errors.append("Current health exceeds maximum health")
        
        if context.agent.stats.current_health <= 0 and context.agent.is_alive:
            errors.append("Agent claims to be alive but has no health")
        
        # Position consistency
        if context.agent.position.x != context.agent.position.x:  # NaN check
            errors.append("Agent position X is NaN")
        if context.agent.position.y != context.agent.position.y:  # NaN check
            errors.append("Agent position Y is NaN")
        
        return errors
    
    def _validate_paranoid_safety(self, context: ExecutionContext) -> List[str]:
        """Paranoid safety validation (extensive checks)."""
        errors = []
        
        # Memory and reference validation
        try:
            # Test agent attribute access
            _ = context.agent.agent_id
            _ = context.agent.position
            _ = context.agent.stats
        except AttributeError as e:
            errors.append(f"Agent missing required attribute: {e}")
        except Exception as e:
            errors.append(f"Unexpected error accessing agent: {e}")
        
        # Target agent validation (if applicable)
        if context.target_agent:
            try:
                _ = context.target_agent.agent_id
                _ = context.target_agent.position
                _ = context.target_agent.is_alive
            except Exception as e:
                errors.append(f"Invalid target agent: {e}")
        
        return errors


class ActionExecutor:
    """
    Core action execution system with comprehensive validation and error handling.
    
    This class handles the safe execution of all agent actions, providing
    detailed validation, error handling, performance tracking, and result
    reporting.
    """
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.STANDARD):
        self.validation_level = validation_level
        self.safety_validator = SafetyValidator()
        self.logger = get_logger("ActionExecutor")
        
        # Performance tracking
        self.execution_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'blocked_executions': 0,
            'total_execution_time': 0.0
        }
    
    def execute_action(self, context: ExecutionContext) -> ActionResult:
        """
        Execute an action with comprehensive validation and error handling.
        
        Args:
            context: Execution context containing all necessary information
            
        Returns:
            ActionResult with detailed execution information
        """
        start_time = time.time()
        
        # Create result object
        result = ActionResult(
            action=context.action,
            agent_id=context.agent.agent_id,
            status=ActionStatus.PENDING,
            success=False,
            execution_time=0.0
        )
        
        try:
            # Create pre-execution snapshot
            context.create_pre_execution_snapshot()
            result.pre_execution_state = context.pre_execution_snapshot.copy()
            
            # Validation phase
            result.status = ActionStatus.VALIDATING
            validation_start = time.time()
            
            is_valid, validation_errors = self._validate_execution(context)
            validation_time = time.time() - validation_start
            result.validation_time = validation_time
            
            if not is_valid:
                result.status = ActionStatus.BLOCKED
                result.success = False
                result.validation_passed = False
                result.validation_errors = validation_errors
                result.execution_error = f"Validation failed: {'; '.join(validation_errors)}"
                self.logger.warning(f"Action {context.action} blocked for {context.agent.agent_id}: {result.execution_error}")
                self.execution_stats['blocked_executions'] += 1
                return result
            
            result.validation_passed = True
            
            # Execution phase
            result.status = ActionStatus.EXECUTING
            execution_start = time.time()
            
            execution_result = self._execute_action_implementation(context)
            
            execution_time = time.time() - execution_start
            result.actual_execution_time = execution_time
            
            # Process execution result
            result.success = execution_result.get('success', False)
            result.primary_result = execution_result.get('primary_result')
            result.secondary_effects = execution_result.get('secondary_effects', {})
            result.target_agent_id = execution_result.get('target_agent_id')
            
            if result.success:
                result.status = ActionStatus.SUCCESS
                self.execution_stats['successful_executions'] += 1
            else:
                result.status = ActionStatus.FAILED
                result.execution_error = execution_result.get('error', 'Unknown execution error')
                result.error_code = execution_result.get('error_code', 'EXECUTION_FAILED')
                self.execution_stats['failed_executions'] += 1
            
            # Create post-execution snapshot
            result.post_execution_state = self._create_post_execution_snapshot(context.agent)
            
        except Exception as e:
            # Handle unexpected errors
            result.status = ActionStatus.FAILED
            result.success = False
            result.execution_error = f"Unexpected error: {str(e)}"
            result.error_code = "UNEXPECTED_ERROR"
            self.execution_stats['failed_executions'] += 1
            
            self.logger.error(f"Unexpected error executing {context.action} for {context.agent.agent_id}: {e}")
            self.logger.debug(f"Traceback: {traceback.format_exc()}")
        
        finally:
            # Finalize timing
            total_time = time.time() - start_time
            result.execution_time = total_time
            result.total_time = total_time
            
            self.execution_stats['total_executions'] += 1
            self.execution_stats['total_execution_time'] += total_time
            
            # Log execution result
            self.logger.debug(f"Action execution complete: {result}")
        
        return result
    
    def _validate_execution(self, context: ExecutionContext) -> Tuple[bool, List[str]]:
        """Validate action execution context."""
        # Use the configured validation level
        context.validation_level = self.validation_level
        
        # Perform safety validation
        is_safe, safety_errors = self.safety_validator.validate_action_safety(context)
        
        return is_safe, safety_errors
    
    def _execute_action_implementation(self, context: ExecutionContext) -> Dict[str, Any]:
        """
        Execute the actual action implementation.
        
        Args:
            context: Execution context
            
        Returns:
            Dictionary with execution results
        """
        if context.action == CombatAction.ATTACK_MELEE:
            return self._execute_melee_attack(context)
        elif context.action == CombatAction.ATTACK_RANGED:
            return self._execute_ranged_attack(context)
        elif context.action == CombatAction.MOVE:
            return self._execute_movement(context)
        elif context.action == CombatAction.DODGE:
            return self._execute_dodge(context)
        elif context.action == CombatAction.DEFEND:
            return self._execute_defend(context)
        elif context.action == CombatAction.RETREAT:
            return self._execute_retreat(context)
        elif context.action == CombatAction.USE_SPECIAL:
            return self._execute_special_ability(context)
        elif context.action == CombatAction.COOPERATE:
            return self._execute_cooperation(context)
        else:
            return {
                'success': False,
                'error': f"Unknown action: {context.action}",
                'error_code': 'UNKNOWN_ACTION'
            }
    
    def _execute_melee_attack(self, context: ExecutionContext) -> Dict[str, Any]:
        """Execute melee attack action."""
        try:
            # Ensure we have a target (validation should have caught this)
            if context.target_agent is None:
                return {
                    'success': False,
                    'error': "No target agent for melee attack",
                    'error_code': 'NO_TARGET'
                }
            
            # Use the agent's built-in attack method
            attack_successful = context.agent.attack(context.target_agent)
            
            return {
                'success': attack_successful,
                'primary_result': {'attack_hit': attack_successful},
                'target_agent_id': context.target_agent.agent_id,
                'secondary_effects': {
                    'action_type': 'melee_attack',
                    'range_used': context.agent.position.distance_to(context.target_agent.position)
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Melee attack failed: {str(e)}",
                'error_code': 'MELEE_ATTACK_ERROR'
            }
    
    def _execute_ranged_attack(self, context: ExecutionContext) -> Dict[str, Any]:
        """Execute ranged attack action."""
        try:
            # Ensure we have a target (validation should have caught this)
            if context.target_agent is None:
                return {
                    'success': False,
                    'error': "No target agent for ranged attack",
                    'error_code': 'NO_TARGET'
                }
            
            # Use the agent's built-in attack method (same as melee for now)
            attack_successful = context.agent.attack(context.target_agent)
            
            return {
                'success': attack_successful,
                'primary_result': {'attack_hit': attack_successful},
                'target_agent_id': context.target_agent.agent_id,
                'secondary_effects': {
                    'action_type': 'ranged_attack',
                    'range_used': context.agent.position.distance_to(context.target_agent.position)
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Ranged attack failed: {str(e)}",
                'error_code': 'RANGED_ATTACK_ERROR'
            }
    
    def _execute_movement(self, context: ExecutionContext) -> Dict[str, Any]:
        """Execute movement action."""
        try:
            # Calculate movement velocity
            if context.target_position:
                # Move toward target position
                direction = context.target_position - context.agent.position
                if direction.magnitude() > 0:
                    velocity = direction.normalize() * context.agent.stats.speed
                else:
                    velocity = Vector2D(0, 0)
            else:
                # Use calculate_movement if no specific target
                velocity = context.agent.calculate_movement(context.visible_agents, context.battlefield_info)
            
            # Get battlefield bounds
            bounds = context.battlefield_info.get('bounds', {})
            battlefield_width = bounds.get('max_x', 1000) - bounds.get('min_x', -1000)
            battlefield_height = bounds.get('max_y', 1000) - bounds.get('min_y', -1000)
            battlefield_bounds = (battlefield_width, battlefield_height)
            
            # Store old position for distance calculation
            old_position = Vector2D(context.agent.position.x, context.agent.position.y)
            
            # Execute movement
            context.agent.move(context.dt, velocity, battlefield_bounds)
            
            # Calculate distance moved
            distance_moved = old_position.distance_to(context.agent.position)
            
            return {
                'success': True,
                'primary_result': {'distance_moved': distance_moved},
                'secondary_effects': {
                    'action_type': 'movement',
                    'velocity_magnitude': velocity.magnitude(),
                    'old_position': {'x': old_position.x, 'y': old_position.y},
                    'new_position': {'x': context.agent.position.x, 'y': context.agent.position.y}
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Movement failed: {str(e)}",
                'error_code': 'MOVEMENT_ERROR'
            }
    
    def _execute_dodge(self, context: ExecutionContext) -> Dict[str, Any]:
        """Execute dodge action."""
        try:
            # Dodging increases dodge chance temporarily
            old_dodge_chance = context.agent.stats.dodge_chance
            context.agent.stats.dodge_chance = min(1.0, old_dodge_chance * 2.0)  # Double dodge chance
            
            # Set agent state
            context.agent.state = AgentState.MOVING  # Dodging is a type of movement
            
            return {
                'success': True,
                'primary_result': {'dodge_bonus': context.agent.stats.dodge_chance - old_dodge_chance},
                'secondary_effects': {
                    'action_type': 'dodge',
                    'old_dodge_chance': old_dodge_chance,
                    'new_dodge_chance': context.agent.stats.dodge_chance
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Dodge failed: {str(e)}",
                'error_code': 'DODGE_ERROR'
            }
    
    def _execute_defend(self, context: ExecutionContext) -> Dict[str, Any]:
        """Execute defend action."""
        try:
            # Defending increases defense temporarily
            old_defense = context.agent.stats.defense
            defense_bonus = old_defense * 0.5  # 50% defense bonus while defending
            context.agent.stats.defense += defense_bonus
            
            # Set agent state
            context.agent.state = AgentState.DEFENDING
            
            return {
                'success': True,
                'primary_result': {'defense_bonus': defense_bonus},
                'secondary_effects': {
                    'action_type': 'defend',
                    'old_defense': old_defense,
                    'new_defense': context.agent.stats.defense
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Defend failed: {str(e)}",
                'error_code': 'DEFEND_ERROR'
            }
    
    def _execute_retreat(self, context: ExecutionContext) -> Dict[str, Any]:
        """Execute retreat action."""
        try:
            # Calculate retreat direction (away from threats)
            if context.visible_agents:
                # Find average position of visible threats
                threat_center = Vector2D(0, 0)
                for agent in context.visible_agents:
                    if agent != context.agent:  # Don't include self
                        threat_center += agent.position
                threat_center /= len(context.visible_agents) - 1 if len(context.visible_agents) > 1 else 1
                
                # Move away from threat center
                retreat_direction = (context.agent.position - threat_center).normalize()
            else:
                # No threats visible, move randomly
                import random
                angle = random.uniform(0, 2 * 3.14159)
                retreat_direction = Vector2D(math.cos(angle), math.sin(angle))
            
            # Execute retreat movement with increased speed
            retreat_velocity = retreat_direction * context.agent.stats.speed * 1.5  # 50% speed boost
            
            # Get battlefield bounds
            bounds = context.battlefield_info.get('bounds', {})
            battlefield_width = bounds.get('max_x', 1000) - bounds.get('min_x', -1000)
            battlefield_height = bounds.get('max_y', 1000) - bounds.get('min_y', -1000)
            battlefield_bounds = (battlefield_width, battlefield_height)
            
            # Store old position
            old_position = Vector2D(context.agent.position.x, context.agent.position.y)
            
            # Execute retreat movement
            context.agent.move(context.dt, retreat_velocity, battlefield_bounds)
            
            # Calculate distance moved
            distance_moved = old_position.distance_to(context.agent.position)
            
            return {
                'success': True,
                'primary_result': {'distance_moved': distance_moved},
                'secondary_effects': {
                    'action_type': 'retreat',
                    'retreat_direction': {'x': retreat_direction.x, 'y': retreat_direction.y},
                    'speed_boost': 1.5
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Retreat failed: {str(e)}",
                'error_code': 'RETREAT_ERROR'
            }
    
    def _execute_special_ability(self, context: ExecutionContext) -> Dict[str, Any]:
        """Execute special ability action."""
        try:
            # For now, implement a basic "special" effect
            # In future versions, this could be more sophisticated
            
            # Restore some health as special ability
            old_health = context.agent.stats.current_health
            healing_amount = context.agent.stats.max_health * 0.2  # Heal 20% of max health
            context.agent.heal(healing_amount)
            actual_healing = context.agent.stats.current_health - old_health
            
            return {
                'success': True,
                'primary_result': {'healing_amount': actual_healing},
                'secondary_effects': {
                    'action_type': 'special_ability',
                    'ability_used': 'healing',
                    'old_health': old_health,
                    'new_health': context.agent.stats.current_health
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Special ability failed: {str(e)}",
                'error_code': 'SPECIAL_ABILITY_ERROR'
            }
    
    def _execute_cooperation(self, context: ExecutionContext) -> Dict[str, Any]:
        """Execute cooperation action."""
        try:
            # For now, implement basic cooperation as information sharing
            # In future versions, this could involve coordination, buffs, etc.
            
            allies = [agent for agent in context.visible_agents 
                     if hasattr(agent, 'team_id') and hasattr(context.agent, 'team_id') 
                     and agent.team_id == context.agent.team_id and agent != context.agent]
            
            cooperation_benefit = len(allies) * 0.1  # 10% benefit per ally
            
            return {
                'success': True,
                'primary_result': {'cooperation_benefit': cooperation_benefit},
                'secondary_effects': {
                    'action_type': 'cooperation',
                    'allies_count': len(allies),
                    'allies_ids': [ally.agent_id for ally in allies]
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Cooperation failed: {str(e)}",
                'error_code': 'COOPERATION_ERROR'
            }
    
    def _create_post_execution_snapshot(self, agent: 'BaseAgent') -> Dict[str, Any]:
        """Create snapshot of agent state after execution."""
        return {
            'position': Vector2D(agent.position.x, agent.position.y),
            'health': agent.stats.current_health,
            'state': agent.state,
            'last_attack_time': agent.last_attack_time,
            'is_alive': agent.is_alive,
            'can_attack': agent.can_attack
        }
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """Get performance statistics for action execution."""
        total = self.execution_stats['total_executions']
        if total == 0:
            return self.execution_stats.copy()
        
        stats = self.execution_stats.copy()
        stats['success_rate'] = self.execution_stats['successful_executions'] / total
        stats['failure_rate'] = self.execution_stats['failed_executions'] / total
        stats['block_rate'] = self.execution_stats['blocked_executions'] / total
        stats['average_execution_time'] = self.execution_stats['total_execution_time'] / total
        
        return stats


# Convenience functions for easy integration
def execute_agent_action(agent: 'BaseAgent', action: CombatAction, 
                        target_agent: Optional['BaseAgent'] = None,
                        target_position: Optional[Vector2D] = None,
                        visible_agents: Optional[Sequence['BaseAgent']] = None,
                        battlefield_info: Optional[Dict[str, Any]] = None,
                        validation_level: ValidationLevel = ValidationLevel.STANDARD) -> ActionResult:
    """
    Convenience function to execute an agent action with validation.
    
    Args:
        agent: Agent performing the action
        action: Action to perform
        target_agent: Target agent (for attacks, etc.)
        target_position: Target position (for movement, etc.)
        visible_agents: Agents visible to the acting agent
        battlefield_info: Battlefield information
        validation_level: Level of validation to perform
        
    Returns:
        ActionResult with execution details
    """
    executor = ActionExecutor(validation_level)
    
    context = ExecutionContext(
        agent=agent,
        action=action,
        target_agent=target_agent,
        target_position=target_position,
        visible_agents=visible_agents or [],
        battlefield_info=battlefield_info or {},
        validation_level=validation_level
    )
    
    return executor.execute_action(context)


def create_action_executor(validation_level: ValidationLevel = ValidationLevel.STANDARD) -> ActionExecutor:
    """
    Create an action executor with specified validation level.
    
    Args:
        validation_level: Level of validation to perform
        
    Returns:
        Configured ActionExecutor instance
    """
    return ActionExecutor(validation_level)

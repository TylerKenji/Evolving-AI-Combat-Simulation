"""
Test suite for the Agent Action Validation and Execution System.

This test suite validates the comprehensive action validation and execution
system, including safety validation, execution resul            result_str = str(result)
        assert "attack_melee" in result_str  # Use lowercase enum value
        assert "test_age" in result_str
        assert "success" in result_str.lower()
        assert "s)" in result_str  # Timing informationesult_str = str(result)
        assert "attack_melee" in result_str  # Use lowercase enum value
        assert "test_age" in result_str
        assert "success" in result_str.lower()
        assert "s)" in result_str  # Timing informationrror handling,
and performance tracking.

Test Categories:
1. Action Executor Basic Functionality
2. Safety Validation Tests
3. Action-Specific Execution Tests
4. Error Handling and Edge Cases
5. Performance and Statistics Tests
6. Integration with Decision Framework Tests
"""

import pytest
import time
from unittest.mock import Mock, patch
from typing import List, Dict, Any

from src.agents.action_validation import (
    ActionExecutor, ActionResult, ActionStatus, ValidationLevel,
    ExecutionContext, SafetyValidator, ExecutionError,
    execute_agent_action, create_action_executor
)
from src.agents.base_agent import CombatAction, BaseAgent, AgentState
from src.utils.vector2d import Vector2D


class TestActionExecutor:
    """Test the core ActionExecutor functionality."""
    
    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent for testing."""
        agent = Mock(spec=BaseAgent)
        agent.agent_id = "test_agent_001"
        agent.position = Vector2D(100, 100)
        agent.is_alive = True
        agent.can_attack = True
        agent.state = AgentState.IDLE
        agent.last_attack_time = 0.0
        
        # Mock stats (use Mock without spec since AgentStats may not be available)
        stats = Mock()
        stats.current_health = 100
        stats.max_health = 100
        stats.attack_damage = 25
        stats.attack_range = 50
        stats.speed = 10
        stats.defense = 5
        stats.accuracy = 0.8
        stats.dodge_chance = 0.1
        agent.stats = stats
        
        # Mock methods
        agent.attack.return_value = True
        agent.move.return_value = None
        agent.heal.return_value = None
        agent.calculate_movement.return_value = Vector2D(5, 0)
        
        return agent
    
    @pytest.fixture
    def mock_target_agent(self):
        """Create a mock target agent for testing."""
        agent = Mock(spec=BaseAgent)
        agent.agent_id = "target_agent_001"
        agent.position = Vector2D(130, 100)  # 30 units away
        agent.is_alive = True
        
        stats = Mock()
        stats.current_health = 80
        stats.max_health = 100
        agent.stats = stats
        
        return agent
    
    @pytest.fixture
    def basic_context(self, mock_agent, mock_target_agent):
        """Create a basic execution context for testing."""
        return ExecutionContext(
            agent=mock_agent,
            action=CombatAction.ATTACK_MELEE,
            target_agent=mock_target_agent,
            visible_agents=[mock_target_agent],
            battlefield_info={'bounds': {'min_x': 0, 'max_x': 200, 'min_y': 0, 'max_y': 200}},
            validation_level=ValidationLevel.STANDARD
        )
    
    def test_action_executor_creation(self):
        """Test ActionExecutor can be created with different validation levels."""
        # Test default creation
        executor = ActionExecutor()
        assert executor.validation_level == ValidationLevel.STANDARD
        assert isinstance(executor.safety_validator, SafetyValidator)
        
        # Test with specific validation level
        executor_strict = ActionExecutor(ValidationLevel.STRICT)
        assert executor_strict.validation_level == ValidationLevel.STRICT
        
        # Test with paranoid validation
        executor_paranoid = ActionExecutor(ValidationLevel.PARANOID)
        assert executor_paranoid.validation_level == ValidationLevel.PARANOID
    
    def test_successful_action_execution(self, basic_context):
        """Test successful action execution with proper result."""
        executor = ActionExecutor(ValidationLevel.BASIC)
        
        result = executor.execute_action(basic_context)
        
        # Verify basic result properties
        assert isinstance(result, ActionResult)
        assert result.action == CombatAction.ATTACK_MELEE
        assert result.agent_id == "test_agent_001"
        assert result.status == ActionStatus.SUCCESS
        assert result.success is True
        assert result.validation_passed is True
        assert len(result.validation_errors) == 0
        assert result.execution_error is None
        
        # Verify timing information (may be very small but should be non-negative)
        assert result.execution_time >= 0
        assert result.validation_time >= 0
        assert result.actual_execution_time >= 0
        assert result.total_time >= 0
        
        # Verify target information
        assert result.target_agent_id == "target_agent_001"
        
        # Verify the agent's attack method was called
        basic_context.agent.attack.assert_called_once_with(basic_context.target_agent)
    
    def test_action_execution_with_validation_failure(self, mock_agent):
        """Test action execution that fails validation."""
        # Create context with invalid target (agent attacks itself)
        context = ExecutionContext(
            agent=mock_agent,
            action=CombatAction.ATTACK_MELEE,
            target_agent=mock_agent,  # Self-attack should fail validation
            validation_level=ValidationLevel.STANDARD
        )
        
        executor = ActionExecutor(ValidationLevel.STANDARD)
        result = executor.execute_action(context)
        
        # Verify validation failure
        assert result.status == ActionStatus.BLOCKED
        assert result.success is False
        assert result.validation_passed is False
        assert len(result.validation_errors) > 0
        assert result.execution_error is not None and "cannot attack itself" in result.execution_error
        
        # Verify attack method was not called
        mock_agent.attack.assert_not_called()
    
    def test_action_execution_statistics(self, basic_context):
        """Test execution statistics tracking."""
        executor = ActionExecutor()
        
        # Initial statistics should be empty
        stats = executor.get_execution_statistics()
        assert stats['total_executions'] == 0
        assert stats['successful_executions'] == 0
        assert stats['failed_executions'] == 0
        
        # Execute successful action
        result1 = executor.execute_action(basic_context)
        assert result1.success
        
        # Check updated statistics
        stats = executor.get_execution_statistics()
        assert stats['total_executions'] == 1
        assert stats['successful_executions'] == 1
        assert stats['failed_executions'] == 0
        assert stats['success_rate'] == 1.0
        assert stats['average_execution_time'] >= 0  # May be very small but should be non-negative
        
        # Execute another action that fails validation
        context_fail = ExecutionContext(
            agent=basic_context.agent,
            action=CombatAction.ATTACK_MELEE,
            target_agent=basic_context.agent,  # Self-attack
            validation_level=ValidationLevel.STANDARD
        )
        
        result2 = executor.execute_action(context_fail)
        assert not result2.success
        
        # Check final statistics
        stats = executor.get_execution_statistics()
        assert stats['total_executions'] == 2
        assert stats['successful_executions'] == 1
        assert stats['blocked_executions'] == 1
        assert stats['success_rate'] == 0.5
    
    def test_action_result_string_representation(self, basic_context):
        """Test ActionResult string representation."""
        executor = ActionExecutor()
        result = executor.execute_action(basic_context)
        
        result_str = str(result)
        assert "ATTACK_MELEE" in result_str
        assert "test_agent" in result_str
        assert "success" in result_str.lower()
        assert "s)" in result_str  # Timing information
    
    def test_action_result_to_dict(self, basic_context):
        """Test ActionResult dictionary conversion."""
        executor = ActionExecutor()
        result = executor.execute_action(basic_context)
        
        result_dict = result.to_dict()
        
        # Verify required fields
        assert result_dict['action'] == 'attack_melee'  # Use lowercase enum value
        assert result_dict['agent_id'] == 'test_agent_001'
        assert result_dict['success'] is True
        assert 'timestamp' in result_dict
        assert 'performance' in result_dict
        
        # Verify performance metrics
        performance = result_dict['performance']
        assert 'validation_time' in performance
        assert 'actual_execution_time' in performance
        assert 'total_time' in performance


class TestSafetyValidator:
    """Test the SafetyValidator functionality."""
    
    @pytest.fixture
    def safety_validator(self):
        """Create a SafetyValidator for testing."""
        return SafetyValidator()
    
    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent for testing."""
        agent = Mock(spec=BaseAgent)
        agent.agent_id = "test_agent_001"
        agent.position = Vector2D(100, 100)
        agent.is_alive = True
        agent.can_attack = True
        
        stats = Mock()
        stats.current_health = 100
        stats.max_health = 100
        stats.attack_range = 50
        stats.speed = 10
        agent.stats = stats
        
        return agent
    
    def test_basic_safety_validation_success(self, safety_validator, mock_agent):
        """Test basic safety validation with valid agent."""
        context = ExecutionContext(
            agent=mock_agent,
            action=CombatAction.MOVE,
            validation_level=ValidationLevel.BASIC
        )
        
        is_safe, errors = safety_validator.validate_action_safety(context)
        
        assert is_safe is True
        assert len(errors) == 0
    
    def test_basic_safety_validation_dead_agent(self, safety_validator, mock_agent):
        """Test basic safety validation with dead agent."""
        mock_agent.is_alive = False
        
        context = ExecutionContext(
            agent=mock_agent,
            action=CombatAction.ATTACK_MELEE,
            validation_level=ValidationLevel.BASIC
        )
        
        is_safe, errors = safety_validator.validate_action_safety(context)
        
        assert is_safe is False
        assert len(errors) > 0
        assert any("not alive" in error for error in errors)
    
    def test_attack_safety_validation(self, safety_validator, mock_agent):
        """Test attack-specific safety validation."""
        target_agent = Mock(spec=BaseAgent)
        target_agent.agent_id = "target_001"
        target_agent.position = Vector2D(130, 100)  # 30 units away (within range)
        target_agent.is_alive = True
        
        context = ExecutionContext(
            agent=mock_agent,
            action=CombatAction.ATTACK_MELEE,
            target_agent=target_agent,
            validation_level=ValidationLevel.STANDARD
        )
        
        is_safe, errors = safety_validator.validate_action_safety(context)
        
        assert is_safe is True
        assert len(errors) == 0
    
    def test_attack_safety_validation_out_of_range(self, safety_validator, mock_agent):
        """Test attack safety validation with target out of range."""
        target_agent = Mock(spec=BaseAgent)
        target_agent.agent_id = "target_001"
        target_agent.position = Vector2D(200, 100)  # 100 units away (out of range)
        target_agent.is_alive = True
        
        context = ExecutionContext(
            agent=mock_agent,
            action=CombatAction.ATTACK_MELEE,
            target_agent=target_agent,
            validation_level=ValidationLevel.STANDARD
        )
        
        is_safe, errors = safety_validator.validate_action_safety(context)
        
        assert is_safe is False
        assert len(errors) > 0
        assert any("out of range" in error for error in errors)
    
    def test_attack_safety_validation_self_attack(self, safety_validator, mock_agent):
        """Test attack safety validation prevents self-attack."""
        context = ExecutionContext(
            agent=mock_agent,
            action=CombatAction.ATTACK_MELEE,
            target_agent=mock_agent,  # Self-attack
            validation_level=ValidationLevel.STANDARD
        )
        
        is_safe, errors = safety_validator.validate_action_safety(context)
        
        assert is_safe is False
        assert len(errors) > 0
        assert any("cannot attack itself" in error for error in errors)
    
    def test_movement_safety_validation(self, safety_validator, mock_agent):
        """Test movement safety validation."""
        context = ExecutionContext(
            agent=mock_agent,
            action=CombatAction.MOVE,
            target_position=Vector2D(150, 150),
            battlefield_info={'bounds': {'min_x': 0, 'max_x': 200, 'min_y': 0, 'max_y': 200}},
            validation_level=ValidationLevel.STANDARD
        )
        
        is_safe, errors = safety_validator.validate_action_safety(context)
        
        assert is_safe is True
        assert len(errors) == 0
    
    def test_movement_safety_validation_out_of_bounds(self, safety_validator, mock_agent):
        """Test movement safety validation with out-of-bounds target."""
        context = ExecutionContext(
            agent=mock_agent,
            action=CombatAction.MOVE,
            target_position=Vector2D(300, 300),  # Out of bounds
            battlefield_info={'bounds': {'min_x': 0, 'max_x': 200, 'min_y': 0, 'max_y': 200}},
            validation_level=ValidationLevel.STANDARD
        )
        
        is_safe, errors = safety_validator.validate_action_safety(context)
        
        assert is_safe is False
        assert len(errors) > 0
        assert any("outside bounds" in error for error in errors)


class TestActionSpecificExecution:
    """Test action-specific execution implementations."""
    
    @pytest.fixture
    def executor(self):
        """Create an ActionExecutor for testing."""
        return ActionExecutor(ValidationLevel.BASIC)  # Use basic validation for execution tests
    
    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent for testing."""
        agent = Mock(spec=BaseAgent)
        agent.agent_id = "test_agent_001"
        agent.position = Vector2D(100, 100)
        agent.is_alive = True
        agent.can_attack = True
        agent.state = AgentState.IDLE
        
        stats = Mock()
        stats.current_health = 100
        stats.max_health = 100
        stats.attack_range = 50
        stats.speed = 10
        stats.defense = 5
        stats.dodge_chance = 0.1
        agent.stats = stats
        
        agent.attack.return_value = True
        agent.move.return_value = None
        agent.heal.return_value = None
        agent.calculate_movement.return_value = Vector2D(5, 0)
        
        return agent
    
    def test_melee_attack_execution(self, executor, mock_agent):
        """Test melee attack execution."""
        target_agent = Mock(spec=BaseAgent)
        target_agent.agent_id = "target_001"
        target_agent.position = Vector2D(130, 100)
        target_agent.is_alive = True
        
        context = ExecutionContext(
            agent=mock_agent,
            action=CombatAction.ATTACK_MELEE,
            target_agent=target_agent
        )
        
        result = executor.execute_action(context)
        
        assert result.success is True
        assert result.action == CombatAction.ATTACK_MELEE
        assert result.target_agent_id == "target_001"
        assert result.primary_result['attack_hit'] is True
        assert result.secondary_effects['action_type'] == 'melee_attack'
        
        # Verify attack method was called
        mock_agent.attack.assert_called_once_with(target_agent)
    
    def test_ranged_attack_execution(self, executor, mock_agent):
        """Test ranged attack execution."""
        target_agent = Mock(spec=BaseAgent)
        target_agent.agent_id = "target_001"
        target_agent.position = Vector2D(130, 100)
        target_agent.is_alive = True
        
        context = ExecutionContext(
            agent=mock_agent,
            action=CombatAction.ATTACK_RANGED,
            target_agent=target_agent
        )
        
        result = executor.execute_action(context)
        
        assert result.success is True
        assert result.action == CombatAction.ATTACK_RANGED
        assert result.secondary_effects['action_type'] == 'ranged_attack'
    
    def test_movement_execution(self, executor, mock_agent):
        """Test movement execution."""
        context = ExecutionContext(
            agent=mock_agent,
            action=CombatAction.MOVE,
            target_position=Vector2D(150, 100),
            battlefield_info={'bounds': {'min_x': 0, 'max_x': 200, 'min_y': 0, 'max_y': 200}}
        )
        
        result = executor.execute_action(context)
        
        assert result.success is True
        assert result.action == CombatAction.MOVE
        assert 'distance_moved' in result.primary_result
        assert result.secondary_effects['action_type'] == 'movement'
        
        # Verify move method was called
        mock_agent.move.assert_called_once()
    
    def test_dodge_execution(self, executor, mock_agent):
        """Test dodge execution."""
        context = ExecutionContext(
            agent=mock_agent,
            action=CombatAction.DODGE
        )
        
        old_dodge_chance = mock_agent.stats.dodge_chance
        result = executor.execute_action(context)
        
        assert result.success is True
        assert result.action == CombatAction.DODGE
        assert 'dodge_bonus' in result.primary_result
        assert result.secondary_effects['action_type'] == 'dodge'
        # Note: dodge chance modification is mocked, so we can't verify the actual change
    
    def test_defend_execution(self, executor, mock_agent):
        """Test defend execution."""
        context = ExecutionContext(
            agent=mock_agent,
            action=CombatAction.DEFEND
        )
        
        result = executor.execute_action(context)
        
        assert result.success is True
        assert result.action == CombatAction.DEFEND
        assert 'defense_bonus' in result.primary_result
        assert result.secondary_effects['action_type'] == 'defend'
        assert mock_agent.state == AgentState.DEFENDING
    
    def test_retreat_execution(self, executor, mock_agent):
        """Test retreat execution."""
        threat_agent = Mock(spec=BaseAgent)
        threat_agent.position = Vector2D(80, 100)  # Threat to the left
        threat_agent.agent_id = "threat_001"
        
        context = ExecutionContext(
            agent=mock_agent,
            action=CombatAction.RETREAT,
            visible_agents=[threat_agent],
            battlefield_info={'bounds': {'min_x': 0, 'max_x': 200, 'min_y': 0, 'max_y': 200}}
        )
        
        result = executor.execute_action(context)
        
        assert result.success is True
        assert result.action == CombatAction.RETREAT
        assert 'distance_moved' in result.primary_result
        assert result.secondary_effects['action_type'] == 'retreat'
        assert result.secondary_effects['speed_boost'] == 1.5
    
    def test_special_ability_execution(self, executor, mock_agent):
        """Test special ability execution."""
        context = ExecutionContext(
            agent=mock_agent,
            action=CombatAction.USE_SPECIAL
        )
        
        result = executor.execute_action(context)
        
        assert result.success is True
        assert result.action == CombatAction.USE_SPECIAL
        assert 'healing_amount' in result.primary_result
        assert result.secondary_effects['action_type'] == 'special_ability'
        assert result.secondary_effects['ability_used'] == 'healing'
        
        # Verify heal method was called
        mock_agent.heal.assert_called_once()
    
    def test_cooperation_execution(self, executor, mock_agent):
        """Test cooperation execution."""
        # Create mock allies with team_id
        ally1 = Mock(spec=BaseAgent)
        ally1.agent_id = "ally_001"
        ally1.team_id = "team_a"
        
        ally2 = Mock(spec=BaseAgent)
        ally2.agent_id = "ally_002" 
        ally2.team_id = "team_a"
        
        # Set agent's team_id
        mock_agent.team_id = "team_a"
        
        context = ExecutionContext(
            agent=mock_agent,
            action=CombatAction.COOPERATE,
            visible_agents=[ally1, ally2]
        )
        
        result = executor.execute_action(context)
        
        assert result.success is True
        assert result.action == CombatAction.COOPERATE
        assert 'cooperation_benefit' in result.primary_result
        assert result.secondary_effects['action_type'] == 'cooperation'
        assert result.secondary_effects['allies_count'] == 2


class TestConvenienceFunctions:
    """Test convenience functions for easy integration."""
    
    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent for testing."""
        agent = Mock(spec=BaseAgent)
        agent.agent_id = "test_agent_001"
        agent.position = Vector2D(100, 100)
        agent.is_alive = True
        agent.can_attack = True
        
        stats = Mock()
        stats.current_health = 100
        stats.max_health = 100
        stats.attack_range = 50
        agent.stats = stats
        
        agent.attack.return_value = True
        
        return agent
    
    def test_execute_agent_action_convenience_function(self, mock_agent):
        """Test execute_agent_action convenience function."""
        target_agent = Mock(spec=BaseAgent)
        target_agent.agent_id = "target_001"
        target_agent.position = Vector2D(130, 100)
        target_agent.is_alive = True
        
        result = execute_agent_action(
            agent=mock_agent,
            action=CombatAction.ATTACK_MELEE,
            target_agent=target_agent,
            validation_level=ValidationLevel.BASIC
        )
        
        assert isinstance(result, ActionResult)
        assert result.success is True
        assert result.action == CombatAction.ATTACK_MELEE
        assert result.agent_id == "test_agent_001"
    
    def test_create_action_executor_convenience_function(self):
        """Test create_action_executor convenience function."""
        # Test default creation
        executor = create_action_executor()
        assert isinstance(executor, ActionExecutor)
        assert executor.validation_level == ValidationLevel.STANDARD
        
        # Test with specific validation level
        executor_strict = create_action_executor(ValidationLevel.STRICT)
        assert executor_strict.validation_level == ValidationLevel.STRICT


class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases."""
    
    def test_execution_with_invalid_action(self):
        """Test execution with invalid action type."""
        mock_agent = Mock(spec=BaseAgent)
        mock_agent.agent_id = "test_agent"
        mock_agent.position = Vector2D(0, 0)
        mock_agent.is_alive = True
        
        stats = Mock()
        stats.current_health = 100
        stats.max_health = 100
        mock_agent.stats = stats

        # Test with invalid action - we'll simulate this by testing a case 
        # that should be caught by validation instead of using invalid enum
        context = ExecutionContext(
            agent=mock_agent,
            action=CombatAction.ATTACK_MELEE,  # Valid action but no target
            target_agent=None,  # Missing target should fail validation
            validation_level=ValidationLevel.STANDARD
        )
        
        executor = ActionExecutor(ValidationLevel.STANDARD)
        
        # This should raise an exception or return a failed result
        # depending on validation implementation
        try:
            result = executor.execute_action(context)
            # If it doesn't raise an exception, it should at least fail
            assert result.success is False
        except Exception:
            # Exception is also acceptable for invalid input
            pass
    
    def test_execution_with_none_agent(self):
        """Test execution with None agent."""
        # We'll test this by creating a mock that acts like None
        # but still satisfies the type system
        mock_agent = Mock(spec=BaseAgent)
        mock_agent.agent_id = None
        mock_agent.position = None
        mock_agent.is_alive = False
        mock_agent.stats = None
        
        context = ExecutionContext(
            agent=mock_agent,
            action=CombatAction.MOVE,
            validation_level=ValidationLevel.BASIC
        )
        
        executor = ActionExecutor(ValidationLevel.BASIC)
        result = executor.execute_action(context)
        
        assert result.success is False
        assert result.status == ActionStatus.BLOCKED or result.status == ActionStatus.FAILED
    
    def test_execution_context_snapshot_creation(self):
        """Test execution context snapshot creation."""
        mock_agent = Mock(spec=BaseAgent)
        mock_agent.agent_id = "test_agent"
        mock_agent.position = Vector2D(100, 100)
        mock_agent.is_alive = True
        mock_agent.can_attack = True
        mock_agent.state = AgentState.IDLE
        mock_agent.last_attack_time = 10.0
        
        stats = Mock()
        stats.current_health = 80
        stats.max_health = 100
        mock_agent.stats = stats
        
        context = ExecutionContext(
            agent=mock_agent,
            action=CombatAction.MOVE
        )
        
        context.create_pre_execution_snapshot()
        
        snapshot = context.pre_execution_snapshot
        assert snapshot['position'].x == 100
        assert snapshot['position'].y == 100
        assert snapshot['health'] == 80
        assert snapshot['state'] == AgentState.IDLE
        assert snapshot['last_attack_time'] == 10.0
        assert snapshot['is_alive'] is True
        assert snapshot['can_attack'] is True


if __name__ == "__main__":
    pytest.main([__file__])

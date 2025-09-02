"""
Tests for Agent State Data Structures
Task 1.2.5: Create data structures for agent state

This module tests the comprehensive agent state management system including
combat states, movement tracking, objectives, sensor data, and state history.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, List

from src.agents.agent_state import (
    ActionType, CombatStatus, MovementStatus, ObjectiveType,
    AgentObjective, CombatState, MovementState, SensorData,
    AgentStateSnapshot, StateTransition, StateManager
)
from src.utils.vector2d import Vector2D


class TestActionEnums:
    """Test enumeration types."""
    
    def test_action_type_enum(self):
        """Test ActionType enumeration."""
        assert ActionType.MOVE.value == "move"
        assert ActionType.ATTACK.value == "attack"
        assert ActionType.IDLE.value == "idle"
        assert len(ActionType) == 11  # Verify all actions are defined
    
    def test_combat_status_enum(self):
        """Test CombatStatus enumeration."""
        assert CombatStatus.NOT_IN_COMBAT.value == "not_in_combat"
        assert CombatStatus.ENGAGING.value == "engaging"
        assert CombatStatus.UNDER_ATTACK.value == "under_attack"
        assert len(CombatStatus) == 7
    
    def test_movement_status_enum(self):
        """Test MovementStatus enumeration.""" 
        assert MovementStatus.STATIONARY.value == "stationary"
        assert MovementStatus.MOVING.value == "moving"
        assert MovementStatus.RUNNING.value == "running"
        assert len(MovementStatus) == 7
    
    def test_objective_type_enum(self):
        """Test ObjectiveType enumeration."""
        assert ObjectiveType.ELIMINATE_TARGET.value == "eliminate_target"
        assert ObjectiveType.DEFEND_POSITION.value == "defend_position"
        assert ObjectiveType.PATROL_AREA.value == "patrol_area"
        assert len(ObjectiveType) == 8


class TestAgentObjective:
    """Test AgentObjective data structure."""
    
    def test_objective_creation(self):
        """Test basic objective creation."""
        target_pos = Vector2D(100, 200)
        objective = AgentObjective(
            objective_type=ObjectiveType.ELIMINATE_TARGET,
            target_position=target_pos,
            target_agent_id="enemy_123",
            priority=0.8
        )
        
        assert objective.objective_type == ObjectiveType.ELIMINATE_TARGET
        assert objective.target_position == target_pos
        assert objective.target_agent_id == "enemy_123"
        assert objective.priority == 0.8
        assert objective.completion_threshold == 10.0
        assert objective.timeout is None
    
    def test_objective_timeout(self):
        """Test objective timeout functionality."""
        # Create objective with short timeout
        objective = AgentObjective(
            objective_type=ObjectiveType.PATROL_AREA,
            timeout=0.001  # 1ms timeout
        )
        
        # Should not be expired immediately
        assert not objective.is_expired()
        
        # Wait and check expiration
        import time
        time.sleep(0.002)  # 2ms
        assert objective.is_expired()
    
    def test_distance_to_target(self):
        """Test distance calculation to target."""
        target_pos = Vector2D(100, 100)
        objective = AgentObjective(
            objective_type=ObjectiveType.DEFEND_POSITION,
            target_position=target_pos
        )
        
        current_pos = Vector2D(103, 104)  # 5 units away
        distance = objective.distance_to_target(current_pos)
        assert abs(distance - 5.0) < 0.1
        
        # Test with no target position
        objective_no_target = AgentObjective(objective_type=ObjectiveType.PATROL_AREA)
        assert objective_no_target.distance_to_target(current_pos) == float('inf')


class TestCombatState:
    """Test CombatState data structure."""
    
    def test_combat_state_creation(self):
        """Test basic combat state creation."""
        combat_state = CombatState(
            status=CombatStatus.ENGAGING,
            current_target_id="enemy_456",
            threat_level=0.7
        )
        
        assert combat_state.status == CombatStatus.ENGAGING
        assert combat_state.current_target_id == "enemy_456"
        assert combat_state.threat_level == 0.7
        assert combat_state.total_damage_dealt == 0.0
        assert combat_state.attacks_attempted == 0
    
    def test_can_attack_logic(self):
        """Test attack capability logic."""
        combat_state = CombatState()
        
        # Should be able to attack initially
        assert combat_state.can_attack()
        
        # Should not be able to attack on cooldown
        combat_state.attack_cooldown_remaining = 1.0
        assert not combat_state.can_attack()
        
        # Should not be able to attack when stunned
        combat_state.attack_cooldown_remaining = 0.0
        combat_state.stun_remaining = 0.5
        assert not combat_state.can_attack()
        
        # Should not be able to attack with stunned status
        combat_state.stun_remaining = 0.0
        combat_state.status = CombatStatus.STUNNED
        assert not combat_state.can_attack()
    
    def test_accuracy_calculation(self):
        """Test accuracy rate calculation."""
        combat_state = CombatState()
        
        # No attacks attempted
        assert combat_state.get_accuracy_rate() == 0.0
        
        # Some hits
        combat_state.attacks_attempted = 10
        combat_state.attacks_hit = 7
        assert combat_state.get_accuracy_rate() == 0.7
    
    def test_dodge_rate_calculation(self):
        """Test dodge rate calculation."""
        combat_state = CombatState()
        
        # No dodges attempted
        assert combat_state.get_dodge_rate() == 0.0
        
        # Some successful dodges
        combat_state.dodges_attempted = 5
        combat_state.dodges_successful = 3
        assert combat_state.get_dodge_rate() == 0.6


class TestMovementState:
    """Test MovementState data structure."""
    
    def test_movement_state_creation(self):
        """Test basic movement state creation."""
        velocity = Vector2D(10, 5)
        target = Vector2D(200, 300)
        
        movement_state = MovementState(
            status=MovementStatus.MOVING,
            current_velocity=velocity,
            target_position=target
        )
        
        assert movement_state.status == MovementStatus.MOVING
        assert movement_state.current_velocity == velocity
        assert movement_state.target_position == target
        assert movement_state.total_distance_moved == 0.0
    
    def test_is_moving_logic(self):
        """Test movement detection logic."""
        movement_state = MovementState()
        
        # Stationary with no velocity
        assert not movement_state.is_moving()
        
        # Moving status with velocity
        movement_state.status = MovementStatus.MOVING
        movement_state.current_velocity = Vector2D(10, 0)
        assert movement_state.is_moving()
        
        # Moving status but no velocity (stuck)
        movement_state.current_velocity = Vector2D(0, 0)
        assert not movement_state.is_moving()
    
    def test_path_management(self):
        """Test path and waypoint management."""
        path = [Vector2D(0, 0), Vector2D(50, 50), Vector2D(100, 100)]
        movement_state = MovementState(path=path)
        
        # Should have target
        assert movement_state.has_target() is False  # No target_position set
        movement_state.target_position = Vector2D(100, 100)
        assert movement_state.has_target()
        
        # Get next waypoint
        waypoint = movement_state.get_next_waypoint()
        assert waypoint == Vector2D(0, 0)
        
        # Advance path
        assert movement_state.advance_path()
        waypoint = movement_state.get_next_waypoint()
        assert waypoint == Vector2D(50, 50)
        
        # Advance to end
        assert movement_state.advance_path()
        waypoint = movement_state.get_next_waypoint()
        assert waypoint == Vector2D(100, 100)
        
        # Cannot advance past end
        assert not movement_state.advance_path()


class TestSensorData:
    """Test SensorData data structure."""
    
    def test_sensor_data_creation(self):
        """Test basic sensor data creation."""
        sensor_data = SensorData(
            visible_agents=["agent1", "agent2", "agent3"],
            visible_enemies=["agent2"],
            visible_allies=["agent1", "agent3"]
        )
        
        assert len(sensor_data.visible_agents) == 3
        assert len(sensor_data.visible_enemies) == 1
        assert len(sensor_data.visible_allies) == 2
        assert "agent2" in sensor_data.visible_enemies
    
    def test_nearest_enemy_detection(self):
        """Test nearest enemy detection."""
        sensor_data = SensorData(visible_enemies=["enemy1", "enemy2"])
        current_pos = Vector2D(0, 0)
        agent_positions = {
            "enemy1": Vector2D(10, 0),  # 10 units away
            "enemy2": Vector2D(0, 5),   # 5 units away
        }
        
        result = sensor_data.get_nearest_enemy(current_pos, agent_positions)
        assert result is not None
        nearest_id, distance = result
        assert nearest_id == "enemy2"
        assert abs(distance - 5.0) < 0.1
        
        # Test with no enemies
        sensor_data.visible_enemies = []
        result = sensor_data.get_nearest_enemy(current_pos, agent_positions)
        assert result is None
    
    def test_highest_threat_detection(self):
        """Test highest threat detection."""
        sensor_data = SensorData(
            detected_threats={
                "enemy1": 0.3,
                "enemy2": 0.8,
                "enemy3": 0.5
            }
        )
        
        result = sensor_data.get_highest_threat()
        assert result is not None
        threat_id, threat_level = result
        assert threat_id == "enemy2"
        assert threat_level == 0.8
        
        # Test with no threats
        sensor_data.detected_threats = {}
        result = sensor_data.get_highest_threat()
        assert result is None


class TestAgentStateSnapshot:
    """Test AgentStateSnapshot data structure."""
    
    def test_state_snapshot_creation(self):
        """Test basic state snapshot creation."""
        position = Vector2D(150, 200)
        combat_state = CombatState(status=CombatStatus.ENGAGING)
        movement_state = MovementState(status=MovementStatus.RUNNING)
        
        snapshot = AgentStateSnapshot(
            agent_id="test_agent_123",
            position=position,
            health=75.0,
            action_type=ActionType.ATTACK,
            combat_state=combat_state,
            movement_state=movement_state
        )
        
        assert snapshot.agent_id == "test_agent_123"
        assert snapshot.position == position
        assert snapshot.health == 75.0
        assert snapshot.action_type == ActionType.ATTACK
        assert snapshot.combat_state.status == CombatStatus.ENGAGING
        assert snapshot.movement_state.status == MovementStatus.RUNNING
    
    def test_objective_management(self):
        """Test objective management in state snapshot."""
        objectives = [
            AgentObjective(ObjectiveType.ELIMINATE_TARGET, priority=0.8),
            AgentObjective(ObjectiveType.DEFEND_POSITION, priority=0.5),
            AgentObjective(ObjectiveType.PATROL_AREA, priority=0.9)
        ]
        
        snapshot = AgentStateSnapshot(current_objectives=objectives)
        
        primary = snapshot.get_primary_objective()
        assert primary is not None
        assert primary.objective_type == ObjectiveType.PATROL_AREA
        assert primary.priority == 0.9
    
    def test_health_status_checks(self):
        """Test health-based status checks."""
        # Healthy agent
        snapshot_healthy = AgentStateSnapshot(health=80.0)
        assert snapshot_healthy.is_healthy()
        assert not snapshot_healthy.is_in_danger()
        
        # Injured agent
        snapshot_injured = AgentStateSnapshot(health=20.0)
        assert not snapshot_injured.is_healthy()
        assert snapshot_injured.is_in_danger()
        
        # Agent under high threat
        combat_state = CombatState(threat_level=0.8)
        snapshot_threatened = AgentStateSnapshot(
            health=60.0,
            combat_state=combat_state
        )
        assert snapshot_threatened.is_healthy()
        assert snapshot_threatened.is_in_danger()
    
    def test_state_summary(self):
        """Test state summary generation."""
        objectives = [AgentObjective(ObjectiveType.ELIMINATE_TARGET, priority=1.0)]
        snapshot = AgentStateSnapshot(
            agent_id="test_agent_12345",
            health=85.5,
            action_type=ActionType.ATTACK,
            current_objectives=objectives
        )
        
        summary = snapshot.get_state_summary()
        assert "test_age" in summary  # Truncated agent ID
        assert "attack" in summary
        assert "85.5" in summary
        assert "eliminate_target" in summary


class TestStateTransition:
    """Test StateTransition data structure."""
    
    def test_transition_creation(self):
        """Test basic transition creation."""
        transition = StateTransition(
            agent_id="agent_123",
            from_state=ActionType.IDLE,
            to_state=ActionType.ATTACK,
            trigger="enemy_spotted"
        )
        
        assert transition.agent_id == "agent_123"
        assert transition.from_state == ActionType.IDLE
        assert transition.to_state == ActionType.ATTACK
        assert transition.trigger == "enemy_spotted"
    
    def test_transition_description(self):
        """Test transition description generation."""
        transition = StateTransition(
            agent_id="agent_12345",
            from_state=ActionType.MOVE,
            to_state=ActionType.DEFEND,
            trigger="ally_under_attack"
        )
        
        description = transition.get_transition_description()
        assert "agent_12" in description  # Truncated ID
        assert "move → defend" in description
        assert "ally_under_attack" in description


class TestStateManager:
    """Test StateManager functionality."""
    
    def test_state_recording(self):
        """Test state snapshot recording."""
        manager = StateManager(max_history=5)
        agent_id = "test_agent"
        
        # Record multiple states
        for i in range(3):
            snapshot = AgentStateSnapshot(
                agent_id=agent_id,
                health=100.0 - i * 10,
                action_type=ActionType.MOVE
            )
            manager.record_state(agent_id, snapshot)
        
        # Check history
        history = manager.get_state_history(agent_id)
        assert len(history) == 3
        assert history[0].health == 100.0
        assert history[2].health == 80.0
        
        # Get latest state
        latest = manager.get_latest_state(agent_id)
        assert latest is not None
        assert latest.health == 80.0
    
    def test_transition_recording(self):
        """Test state transition recording."""
        manager = StateManager(max_history=10)
        
        transitions = [
            StateTransition(
                agent_id="agent1", 
                from_state=ActionType.IDLE, 
                to_state=ActionType.MOVE, 
                trigger="patrol_start"
            ),
            StateTransition(
                agent_id="agent1", 
                from_state=ActionType.MOVE, 
                to_state=ActionType.ATTACK, 
                trigger="enemy_spotted"
            ),
            StateTransition(
                agent_id="agent2", 
                from_state=ActionType.IDLE, 
                to_state=ActionType.DEFEND, 
                trigger="ally_attacked"
            )
        ]
        
        for transition in transitions:
            manager.record_transition(transition)
        
        # Get all recent transitions
        all_transitions = manager.get_recent_transitions()
        assert len(all_transitions) == 3
        
        # Get agent-specific transitions
        agent1_transitions = manager.get_recent_transitions("agent1")
        assert len(agent1_transitions) == 2
        assert agent1_transitions[0].trigger == "patrol_start"
    
    def test_history_limits(self):
        """Test history size limits."""
        manager = StateManager(max_history=3)
        agent_id = "test_agent"
        
        # Record more states than limit
        for i in range(5):
            snapshot = AgentStateSnapshot(agent_id=agent_id, health=float(i))
            manager.record_state(agent_id, snapshot)
        
        # Should only keep last 3
        history = manager.get_state_history(agent_id, 10)
        assert len(history) == 3
        assert history[0].health == 2.0  # States 2, 3, 4 kept
        assert history[2].health == 4.0
    
    def test_behavior_analysis(self):
        """Test agent behavior analysis."""
        manager = StateManager()
        agent_id = "test_agent"
        
        # Create varied state history
        actions = [ActionType.MOVE, ActionType.ATTACK, ActionType.MOVE, ActionType.DEFEND]
        for i, action in enumerate(actions):
            combat_state = CombatState(total_damage_dealt=float(i * 10))
            movement_state = MovementState(total_distance_moved=float(i * 5))
            
            snapshot = AgentStateSnapshot(
                agent_id=agent_id,
                action_type=action,
                health=100.0 - i * 5,
                energy_level=1.0 - i * 0.1,
                combat_state=combat_state,
                movement_state=movement_state
            )
            manager.record_state(agent_id, snapshot)
        
        # Analyze behavior
        analysis = manager.analyze_agent_behavior(agent_id)
        
        assert 'action_distribution' in analysis
        assert analysis['action_distribution']['move'] == 2
        assert analysis['action_distribution']['attack'] == 1
        assert analysis['action_distribution']['defend'] == 1
        
        assert 'average_health' in analysis
        assert analysis['average_health'] == 92.5  # (100+95+90+85)/4 = 370/4 = 92.5
        
        assert 'total_damage_dealt' in analysis
        assert 'total_distance_moved' in analysis


if __name__ == "__main__":
    pytest.main([__file__])

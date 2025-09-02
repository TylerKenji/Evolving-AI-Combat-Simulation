"""
Tests for simulation loop architecture.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from typing import Any

from src.simulation import (
    SimulationState, LoopPhase, SimulationMetrics, SimulationConfig,
    SimulationPhase, SimulationContext, SimulationEngine,
    InputProcessingPhase, AgentDecisionPhase, AgentActionPhase,
    PhysicsUpdatePhase, EnvironmentUpdatePhase, EventProcessingPhase,
    create_default_simulation
)
from src.events import EventType, EventPriority


class TestSimulationMetrics:
    """Test SimulationMetrics functionality."""
    
    def test_metrics_initialization(self):
        """Test metrics are initialized with default values."""
        metrics = SimulationMetrics()
        
        assert metrics.total_runtime == 0.0
        assert metrics.simulation_time == 0.0
        assert metrics.average_loop_time == 0.0
        assert metrics.target_fps == 60.0
        assert metrics.actual_fps == 0.0
        assert metrics.total_iterations == 0
        assert len(metrics.phase_times) == 0
    
    def test_fps_update(self):
        """Test FPS calculation."""
        metrics = SimulationMetrics()
        
        # Test 60 FPS (16.67ms per frame)
        delta_time = 1.0 / 60.0
        metrics.update_fps(delta_time)
        
        assert abs(metrics.actual_fps - 60.0) < 0.1
        assert abs(metrics.iterations_per_second - 60.0) < 0.1
    
    def test_phase_time_tracking(self):
        """Test phase timing with exponential moving average."""
        metrics = SimulationMetrics()
        
        # Add some phase times
        metrics.add_phase_time(LoopPhase.AGENT_DECISION, 10.0)
        metrics.add_phase_time(LoopPhase.AGENT_DECISION, 20.0)
        
        # Should use exponential moving average
        assert LoopPhase.AGENT_DECISION in metrics.phase_times
        # With alpha=0.1: first time = 10.0, second: 0.1*20 + 0.9*10 = 11.0
        # But since first call initializes to 0.0, it's: 0.1*10 + 0.9*0 = 1.0, then 0.1*20 + 0.9*1 = 2.9
        assert abs(metrics.phase_times[LoopPhase.AGENT_DECISION] - 2.9) < 0.1
    
    def test_performance_summary(self):
        """Test performance summary generation."""
        metrics = SimulationMetrics()
        metrics.actual_fps = 59.5
        metrics.average_loop_time = 0.0167
        metrics.simulation_time = 10.5
        metrics.total_iterations = 630
        metrics.active_agents = 5
        metrics.events_processed_per_loop = 12.3
        metrics.add_phase_time(LoopPhase.AGENT_DECISION, 5.0)
        
        summary = metrics.get_performance_summary()
        
        assert summary['fps'] == 59.5
        assert summary['loop_time_ms'] == 16.7
        assert summary['simulation_time'] == 10.5
        assert summary['total_iterations'] == 630
        assert summary['active_agents'] == 5
        assert summary['events_per_loop'] == 12.3
        assert 'phase_breakdown' in summary
        # Phase starts at 0.0, then 0.1*5.0 + 0.9*0.0 = 0.5
        assert summary['phase_breakdown']['agent_decision'] == 0.5


class TestSimulationConfig:
    """Test SimulationConfig functionality."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = SimulationConfig()
        
        assert config.target_fps == 60.0
        assert config.max_loop_time_ms == 50.0
        assert config.time_scale == 1.0
        assert config.max_simulation_time == 300.0
        assert config.max_agents == 100
        assert config.enable_profiling is True
    
    def test_config_validation_valid(self):
        """Test validation with valid config."""
        config = SimulationConfig()
        assert config.validate() is True
    
    def test_config_validation_invalid_fps(self):
        """Test validation with invalid FPS."""
        config = SimulationConfig(target_fps=0)
        
        with pytest.raises(ValueError, match="target_fps must be positive"):
            config.validate()
    
    def test_config_validation_invalid_time_scale(self):
        """Test validation with invalid time scale."""
        config = SimulationConfig(time_scale=-1.0)
        
        with pytest.raises(ValueError, match="time_scale must be positive"):
            config.validate()
    
    def test_config_validation_multiple_errors(self):
        """Test validation with multiple errors."""
        config = SimulationConfig(target_fps=0, max_agents=-5)
        
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        
        error_msg = str(exc_info.value)
        assert "target_fps must be positive" in error_msg
        assert "max_agents must be positive" in error_msg


class TestSimulationPhase:
    """Test SimulationPhase functionality."""
    
    def test_phase_metrics(self):
        """Test phase metric tracking."""
        
        class MockPhase(SimulationPhase):
            def execute(self, context):
                return True
        
        phase = MockPhase("test_phase")
        assert phase.execution_count == 0
        assert phase.total_execution_time == 0.0
        assert phase.get_average_execution_time() == 0.0
        
        # Simulate execution times
        phase.execution_count = 3
        phase.total_execution_time = 30.0
        
        assert phase.get_average_execution_time() == 10.0
    
    def test_phase_reset_metrics(self):
        """Test phase metric reset."""
        
        class MockPhase(SimulationPhase):
            def execute(self, context):
                return True
        
        phase = MockPhase("test_phase")
        phase.execution_count = 5
        phase.total_execution_time = 50.0
        
        phase.reset_metrics()
        
        assert phase.execution_count == 0
        assert phase.total_execution_time == 0.0


class TestSimulationContext:
    """Test SimulationContext functionality."""
    
    def test_context_initialization(self):
        """Test context initialization."""
        context = SimulationContext()
        
        assert context.environment is None
        assert len(context.agents) == 0
        assert context.current_time == 0.0
        assert context.delta_time == 0.0
        assert context.simulation_time == 0.0
        assert context.iteration_count == 0
        assert context.simulation_state == SimulationState.STOPPED
        assert context.should_continue is True
    
    def test_timing_update(self):
        """Test timing update functionality."""
        config = SimulationConfig(time_scale=2.0)
        context = SimulationContext(config=config)
        
        with patch('time.time', return_value=100.0):
            context.update_timing(0.016)  # 16ms delta
        
        assert context.delta_time == 0.016
        assert context.current_time == 100.0
        assert context.simulation_time == 0.032  # 16ms * 2.0 scale
        assert context.iteration_count == 1
        assert context.metrics.time_step == 0.032
    
    def test_timing_update_without_config(self):
        """Test timing update without config."""
        context = SimulationContext()
        
        with patch('time.time', return_value=100.0):
            context.update_timing(0.016)
        
        assert context.delta_time == 0.016
        assert context.simulation_time == 0.016  # No scaling
        assert context.iteration_count == 1


class TestSimulationEngine:
    """Test SimulationEngine functionality."""
    
    def test_engine_initialization(self):
        """Test engine initialization."""
        config = SimulationConfig(target_fps=30.0)
        engine = SimulationEngine(config)
        
        assert engine.config.target_fps == 30.0
        assert engine.running is False
        assert engine.paused is False
        assert len(engine.phases) == 0
        assert engine.context.simulation_state == SimulationState.STOPPED
    
    def test_add_remove_phases(self):
        """Test adding and removing phases."""
        engine = SimulationEngine()
        
        class MockPhase(SimulationPhase):
            def execute(self, context):
                return True
        
        phase1 = MockPhase("phase1", priority=100)
        phase2 = MockPhase("phase2", priority=50)
        
        engine.add_phase(phase1)
        engine.add_phase(phase2)
        
        assert len(engine.phases) == 2
        # Should be sorted by priority
        assert engine.phases[0].priority == 50
        assert engine.phases[1].priority == 100
        
        engine.remove_phase(phase1)
        assert len(engine.phases) == 1
        assert engine.phases[0] == phase2
    
    def test_agent_management(self):
        """Test agent adding and removal."""
        config = SimulationConfig(max_agents=2)
        engine = SimulationEngine(config)
        
        agent1 = Mock()
        agent1.agent_id = "agent1"
        agent2 = Mock()
        agent2.agent_id = "agent2"
        agent3 = Mock()
        agent3.agent_id = "agent3"
        
        # Add agents within limit
        engine.add_agent(agent1)
        engine.add_agent(agent2)
        assert len(engine.context.agents) == 2
        
        # Try to add beyond limit
        engine.add_agent(agent3)
        assert len(engine.context.agents) == 2  # Should not add
        
        # Remove agent
        engine.remove_agent(agent1)
        assert len(engine.context.agents) == 1
        assert agent2 in engine.context.agents
    
    def test_environment_setting(self):
        """Test environment setting."""
        engine = SimulationEngine()
        mock_env = Mock()
        
        engine.set_environment(mock_env)
        assert engine.context.environment == mock_env
    
    @patch('src.simulation.global_event_bus')
    def test_start_stop_simulation(self, mock_event_bus):
        """Test starting and stopping simulation."""
        engine = SimulationEngine()
        
        # Test start (non-threaded)
        with patch.object(engine, '_main_loop') as mock_main_loop:
            engine.start(threaded=False)
            
            assert engine.running is True
            assert engine.context.simulation_state == SimulationState.RUNNING
            mock_event_bus.create_and_publish.assert_called()
            mock_event_bus.start_processing.assert_called()
            mock_main_loop.assert_called_once()
        
        # Reset for stop test
        engine.running = True
        
        # Test stop
        engine.stop()
        
        assert engine.running is False
        assert engine.context.should_continue is False
        assert engine.context.simulation_state == SimulationState.STOPPED
        mock_event_bus.stop_processing.assert_called()
    
    def test_pause_resume_simulation(self):
        """Test pausing and resuming simulation."""
        engine = SimulationEngine()
        engine.running = True
        engine.context.simulation_state = SimulationState.RUNNING
        
        # Test pause
        with patch.object(engine.event_bus, 'create_and_publish'):
            engine.pause()
            
            assert engine.paused is True
            assert engine.context.simulation_state == SimulationState.PAUSED
        
        # Test resume
        with patch('time.time', return_value=100.0):
            engine.resume()
            
            assert engine.paused is False
            assert engine.context.simulation_state == SimulationState.RUNNING
            assert engine.last_frame_time == 100.0
    
    def test_single_step_execution(self):
        """Test single step execution."""
        engine = SimulationEngine()
        
        class MockPhase(SimulationPhase):
            def __init__(self, name):
                super().__init__(name)
                self.executed = False
            
            def execute(self, context):
                self.executed = True
                return True
        
        phase1 = MockPhase("phase1")
        phase2 = MockPhase("phase2")
        engine.add_phase(phase1)
        engine.add_phase(phase2)
        
        engine.running = True
        
        with patch('time.time', return_value=100.0):
            success = engine.step()
        
        assert success is True
        assert phase1.executed is True
        assert phase2.executed is True
        assert engine.context.iteration_count == 1
    
    def test_phase_error_handling(self):
        """Test error handling in phases."""
        engine = SimulationEngine()
        
        class FailingPhase(SimulationPhase):
            def execute(self, context):
                raise RuntimeError("Phase failed")
        
        failing_phase = FailingPhase("failing_phase")
        engine.add_phase(failing_phase)
        engine.running = True
        
        with patch('time.time', return_value=100.0):
            success = engine.step()
        
        assert success is False
        assert engine.context.consecutive_errors == 1
        assert isinstance(engine.context.last_error, RuntimeError)
    
    def test_status_reporting(self):
        """Test status reporting."""
        engine = SimulationEngine()
        engine.running = True
        engine.paused = True
        engine.context.simulation_state = SimulationState.PAUSED
        engine.context.simulation_time = 10.5
        engine.context.iteration_count = 630
        engine.context.agents = [Mock(), Mock(), Mock()]
        engine.context.consecutive_errors = 2
        
        status = engine.get_status()
        
        assert status['state'] == 'paused'
        assert status['running'] is True
        assert status['paused'] is True
        assert status['simulation_time'] == 10.5
        assert status['iteration_count'] == 630
        assert status['agent_count'] == 3
        assert status['consecutive_errors'] == 2
        assert 'metrics' in status


class TestDefaultPhases:
    """Test default simulation phases."""
    
    def test_input_processing_phase(self):
        """Test input processing phase."""
        phase = InputProcessingPhase()
        context = SimulationContext()
        
        assert phase.name == "input_processing"
        assert phase.priority == 10
        assert phase.execute(context) is True
    
    def test_agent_decision_phase(self):
        """Test agent decision phase."""
        phase = AgentDecisionPhase()
        context = SimulationContext()
        context.delta_time = 0.016
        context.agents = [Mock(), Mock()]
        
        assert phase.name == "agent_decision"
        assert phase.priority == 20
        
        result = phase.execute(context)
        
        assert result is True
        assert context.metrics.decisions_per_second > 0
    
    def test_agent_action_phase(self):
        """Test agent action phase."""
        phase = AgentActionPhase()
        context = SimulationContext()
        context.delta_time = 0.016
        context.agents = [Mock(), Mock(), Mock()]
        
        assert phase.name == "agent_action"
        assert phase.priority == 30
        
        result = phase.execute(context)
        
        assert result is True
        assert context.metrics.actions_per_second > 0
    
    def test_physics_update_phase(self):
        """Test physics update phase."""
        phase = PhysicsUpdatePhase()
        context = SimulationContext()
        
        assert phase.name == "physics_update"
        assert phase.priority == 40
        assert phase.execute(context) is True
    
    def test_environment_update_phase(self):
        """Test environment update phase."""
        phase = EnvironmentUpdatePhase()
        context = SimulationContext()
        
        assert phase.name == "environment_update"
        assert phase.priority == 50
        assert phase.execute(context) is True
    
    def test_event_processing_phase(self):
        """Test event processing phase."""
        phase = EventProcessingPhase()
        context = SimulationContext()
        context.config = SimulationConfig()
        
        mock_event_bus = Mock()
        mock_event_bus.process_events.return_value = 0  # No events to process
        context.event_bus = mock_event_bus
        
        assert phase.name == "event_processing"
        assert phase.priority == 60
        
        result = phase.execute(context)
        
        assert result is True
        mock_event_bus.process_events.assert_called()
    
    def test_event_processing_phase_no_config(self):
        """Test event processing phase without config."""
        phase = EventProcessingPhase()
        context = SimulationContext()
        context.config = None
        
        result = phase.execute(context)
        assert result is True


class TestDefaultSimulation:
    """Test default simulation creation."""
    
    def test_create_default_simulation(self):
        """Test creating a simulation with default phases."""
        engine = create_default_simulation()
        
        assert isinstance(engine, SimulationEngine)
        assert len(engine.phases) == 6
        
        # Check that all default phases are present
        phase_names = [phase.name for phase in engine.phases]
        expected_phases = [
            "input_processing", "agent_decision", "agent_action",
            "physics_update", "environment_update", "event_processing"
        ]
        
        for expected_phase in expected_phases:
            assert expected_phase in phase_names
        
        # Check phases are sorted by priority
        priorities = [phase.priority for phase in engine.phases]
        assert priorities == sorted(priorities)
    
    def test_default_simulation_integration(self):
        """Test basic integration of default simulation."""
        engine = create_default_simulation()
        
        # Add some mock agents
        for i in range(3):
            mock_agent = Mock()
            mock_agent.agent_id = f"agent_{i}"
            engine.add_agent(mock_agent)
        
        # Set mock environment
        mock_env = Mock()
        engine.set_environment(mock_env)
        
        # Execute one step
        engine.running = True
        
        with patch('time.time', return_value=100.0):
            success = engine.step()
        
        assert success is True
        assert engine.context.iteration_count == 1
        assert len(engine.context.agents) == 3
        assert engine.context.environment == mock_env


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

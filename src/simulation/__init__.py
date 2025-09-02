"""
Simulation Loop Architecture
Task 1.2.7: Plan simulation loop architecture

This module provides the core simulation engine that orchestrates all systems
including agents, environment, events, and time management for the Battle AI
simulation framework.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Set
from datetime import datetime, timedelta
import time
import threading
from queue import Queue
import logging

from src.utils.vector2d import Vector2D
from src.utils.config import Config
from src.utils.logging_config import get_logger
from src.events import EventBus, Event, EventType, EventPriority, global_event_bus

# Import battle result components
from .battle_result import (
    BattleResult,
    AgentBattleResult,
    CombatStatistics,
    BattleOutcome,
    BattleEndReason
)


class SimulationState(Enum):
    """Current state of the simulation."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"
    COMPLETED = "completed"


class LoopPhase(Enum):
    """Phases within each simulation loop iteration."""
    INPUT_PROCESSING = "input_processing"
    AGENT_DECISION = "agent_decision"
    AGENT_ACTION = "agent_action"
    PHYSICS_UPDATE = "physics_update"
    ENVIRONMENT_UPDATE = "environment_update"
    EVENT_PROCESSING = "event_processing"
    STATE_VALIDATION = "state_validation"
    VISUALIZATION_UPDATE = "visualization_update"


@dataclass
class SimulationMetrics:
    """Performance and operational metrics for the simulation."""
    
    # Timing metrics
    total_runtime: float = 0.0
    simulation_time: float = 0.0  # Virtual simulation time
    average_loop_time: float = 0.0
    target_fps: float = 60.0
    actual_fps: float = 0.0
    
    # Loop iteration metrics
    total_iterations: int = 0
    iterations_per_second: float = 0.0
    time_step: float = 1.0 / 60.0  # Default 60 FPS
    
    # Phase timing (in milliseconds)
    phase_times: Dict[LoopPhase, float] = field(default_factory=dict)
    
    # Agent metrics
    active_agents: int = 0
    decisions_per_second: float = 0.0
    actions_per_second: float = 0.0
    
    # Event metrics
    events_processed_per_loop: float = 0.0
    event_queue_size: int = 0
    
    # System health
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    
    def update_fps(self, delta_time: float) -> None:
        """Update FPS calculation."""
        if delta_time > 0:
            self.actual_fps = 1.0 / delta_time
            self.iterations_per_second = self.actual_fps
    
    def add_phase_time(self, phase: LoopPhase, time_ms: float) -> None:
        """Add timing data for a specific phase."""
        if phase not in self.phase_times:
            self.phase_times[phase] = 0.0
        
        # Use exponential moving average for smoothing
        alpha = 0.1
        self.phase_times[phase] = (alpha * time_ms + 
                                  (1 - alpha) * self.phase_times[phase])
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of performance metrics."""
        return {
            'fps': round(self.actual_fps, 2),
            'loop_time_ms': round(self.average_loop_time * 1000, 2),
            'simulation_time': round(self.simulation_time, 2),
            'total_iterations': self.total_iterations,
            'active_agents': self.active_agents,
            'events_per_loop': round(self.events_processed_per_loop, 1),
            'phase_breakdown': {phase.value: round(time_ms, 2) 
                               for phase, time_ms in self.phase_times.items()}
        }


@dataclass
class SimulationConfig:
    """Configuration for simulation execution."""
    
    # Timing configuration
    target_fps: float = 60.0
    max_loop_time_ms: float = 50.0  # Max time per loop iteration
    time_scale: float = 1.0  # 1.0 = real-time, 2.0 = 2x speed, etc.
    
    # Simulation limits
    max_simulation_time: float = 300.0  # 5 minutes default
    max_iterations: int = 0  # 0 = unlimited
    
    # Agent limits
    max_agents: int = 100
    agent_update_rate: float = 60.0  # Hz
    
    # Event processing
    max_events_per_loop: int = 1000
    event_processing_time_budget_ms: float = 10.0
    
    # Performance monitoring
    enable_profiling: bool = True
    metrics_update_interval: float = 1.0  # seconds
    
    # Error handling
    max_consecutive_errors: int = 5
    error_recovery_delay: float = 1.0
    
    def validate(self) -> bool:
        """Validate configuration parameters."""
        errors = []
        
        if self.target_fps <= 0:
            errors.append("target_fps must be positive")
        if self.max_loop_time_ms <= 0:
            errors.append("max_loop_time_ms must be positive")
        if self.time_scale <= 0:
            errors.append("time_scale must be positive")
        if self.max_agents <= 0:
            errors.append("max_agents must be positive")
        
        if errors:
            raise ValueError(f"Simulation config validation failed: {'; '.join(errors)}")
        
        return True


class SimulationPhase(ABC):
    """Abstract base class for simulation phases."""
    
    def __init__(self, name: str, priority: int = 100):
        self.name = name
        self.priority = priority
        self.enabled = True
        self.last_execution_time = 0.0
        self.execution_count = 0
        self.total_execution_time = 0.0
        self.logger = get_logger(f"sim_phase_{name}")
    
    @abstractmethod
    def execute(self, context: 'SimulationContext') -> bool:
        """Execute this phase. Return True if successful."""
        pass
    
    def get_average_execution_time(self) -> float:
        """Get average execution time in milliseconds."""
        if self.execution_count == 0:
            return 0.0
        return self.total_execution_time / self.execution_count
    
    def reset_metrics(self) -> None:
        """Reset performance metrics."""
        self.execution_count = 0
        self.total_execution_time = 0.0


@dataclass
class SimulationContext:
    """Context passed to each simulation phase."""
    
    # Core systems
    environment: Optional[Any] = None  # Will be BaseEnvironment when implemented
    agents: List[Any] = field(default_factory=list)  # Will be List[BaseAgent]
    event_bus: EventBus = field(default_factory=lambda: global_event_bus)
    
    # Timing information
    current_time: float = 0.0
    delta_time: float = 0.0
    simulation_time: float = 0.0
    iteration_count: int = 0
    
    # Configuration
    config: Optional[SimulationConfig] = None
    
    # Metrics and monitoring
    metrics: SimulationMetrics = field(default_factory=SimulationMetrics)
    
    # State tracking
    simulation_state: SimulationState = SimulationState.STOPPED
    should_continue: bool = True
    
    # Error tracking
    consecutive_errors: int = 0
    last_error: Optional[Exception] = None
    
    def update_timing(self, real_delta_time: float) -> None:
        """Update timing information."""
        self.delta_time = real_delta_time
        self.current_time = time.time()
        
        # Apply time scale
        if self.config:
            scaled_delta = real_delta_time * self.config.time_scale
            self.simulation_time += scaled_delta
            self.metrics.time_step = scaled_delta
        else:
            self.simulation_time += real_delta_time
        
        self.iteration_count += 1
        self.metrics.total_iterations = self.iteration_count


class SimulationEngine:
    """Main simulation engine that orchestrates all systems."""
    
    def __init__(self, config: Optional[SimulationConfig] = None):
        self.config = config or SimulationConfig()
        self.config.validate()
        
        # Core components
        self.context = SimulationContext(config=self.config)
        self.phases: List[SimulationPhase] = []
        self.event_bus = global_event_bus
        
        # Threading and control
        self.simulation_thread: Optional[threading.Thread] = None
        self.running = False
        self.paused = False
        
        # Timing control
        self.target_frame_time = 1.0 / self.config.target_fps
        self.last_frame_time = 0.0
        self.frame_time_accumulator = 0.0
        
        # Callbacks
        self.on_iteration_complete: Optional[Callable[[SimulationContext], None]] = None
        self.on_state_changed: Optional[Callable[[SimulationState], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None
        
        # Performance monitoring
        self.last_metrics_update = 0.0
        
        self.logger = get_logger("simulation_engine")
        self.logger.info("🎮 Simulation engine initialized")
    
    def add_phase(self, phase: SimulationPhase) -> None:
        """Add a simulation phase."""
        self.phases.append(phase)
        self.phases.sort(key=lambda p: p.priority)
        self.logger.debug(f"➕ Added simulation phase: {phase.name}")
    
    def remove_phase(self, phase: SimulationPhase) -> None:
        """Remove a simulation phase."""
        if phase in self.phases:
            self.phases.remove(phase)
            self.logger.debug(f"➖ Removed simulation phase: {phase.name}")
    
    def set_environment(self, environment: Any) -> None:
        """Set the simulation environment."""
        self.context.environment = environment
        self.logger.info("🌍 Environment set for simulation")
    
    def add_agent(self, agent: Any) -> None:
        """Add an agent to the simulation."""
        if len(self.context.agents) < self.config.max_agents:
            self.context.agents.append(agent)
            self.logger.debug(f"🤖 Added agent to simulation: {getattr(agent, 'agent_id', 'unknown')}")
        else:
            self.logger.warning(f"⚠️ Cannot add agent: maximum limit ({self.config.max_agents}) reached")
    
    def remove_agent(self, agent: Any) -> None:
        """Remove an agent from the simulation."""
        if agent in self.context.agents:
            self.context.agents.remove(agent)
            self.logger.debug(f"🗑️ Removed agent from simulation: {getattr(agent, 'agent_id', 'unknown')}")
    
    def start(self, threaded: bool = True) -> None:
        """Start the simulation."""
        if self.running:
            self.logger.warning("⚠️ Simulation is already running")
            return
        
        self.logger.info("🚀 Starting simulation...")
        self._change_state(SimulationState.STARTING)
        
        # Initialize timing
        self.last_frame_time = time.time()
        self.context.current_time = self.last_frame_time
        
        # Publish start event
        self.event_bus.create_and_publish(
            EventType.SIMULATION_STARTED,
            source_id="simulation_engine",
            priority=EventPriority.HIGH
        )
        
        # Start event bus processing
        self.event_bus.start_processing()
        
        self.running = True
        self._change_state(SimulationState.RUNNING)
        
        if threaded:
            self.simulation_thread = threading.Thread(target=self._main_loop, daemon=True)
            self.simulation_thread.start()
        else:
            self._main_loop()
    
    def stop(self) -> None:
        """Stop the simulation."""
        if not self.running:
            return
        
        self.logger.info("🛑 Stopping simulation...")
        self._change_state(SimulationState.STOPPING)
        
        self.running = False
        self.context.should_continue = False
        
        # Wait for simulation thread to finish
        if self.simulation_thread and self.simulation_thread.is_alive():
            self.simulation_thread.join(timeout=2.0)
        
        # Stop event bus
        self.event_bus.stop_processing()
        
        # Publish stop event
        self.event_bus.create_and_publish(
            EventType.SIMULATION_ENDED,
            source_id="simulation_engine",
            priority=EventPriority.HIGH
        )
        
        self._change_state(SimulationState.STOPPED)
        self.logger.info("✅ Simulation stopped")
    
    def pause(self) -> None:
        """Pause the simulation."""
        if self.running and not self.paused:
            self.paused = True
            self._change_state(SimulationState.PAUSED)
            
            self.event_bus.create_and_publish(
                EventType.SIMULATION_PAUSED,
                source_id="simulation_engine"
            )
            self.logger.info("⏸️ Simulation paused")
    
    def resume(self) -> None:
        """Resume the simulation."""
        if self.running and self.paused:
            self.paused = False
            self.last_frame_time = time.time()  # Reset timing
            self._change_state(SimulationState.RUNNING)
            self.logger.info("▶️ Simulation resumed")
    
    def step(self) -> bool:
        """Execute one simulation step."""
        if not self.running:
            return False
        
        return self._execute_single_iteration()
    
    def _main_loop(self) -> None:
        """Main simulation loop."""
        self.logger.info("🔄 Entering main simulation loop")
        
        try:
            while self.running and self.context.should_continue:
                # Handle pause state
                if self.paused:
                    time.sleep(0.01)  # Small sleep to prevent busy waiting
                    continue
                
                # Execute one iteration
                if not self._execute_single_iteration():
                    break
                
                # Frame rate control
                self._control_frame_rate()
                
                # Check termination conditions
                if self._should_terminate():
                    break
            
        except Exception as e:
            self.logger.error(f"💥 Critical error in simulation loop: {e}")
            self._handle_error(e)
        
        finally:
            self._change_state(SimulationState.COMPLETED)
            self.logger.info("🏁 Simulation loop completed")
    
    def _execute_single_iteration(self) -> bool:
        """Execute a single simulation iteration."""
        iteration_start_time = time.time()
        
        try:
            # Update timing
            current_time = time.time()
            delta_time = current_time - self.last_frame_time
            self.last_frame_time = current_time
            
            self.context.update_timing(delta_time)
            self.context.metrics.update_fps(delta_time)
            
            # Execute all phases
            for phase in self.phases:
                if not phase.enabled:
                    continue
                
                phase_start_time = time.time()
                
                try:
                    success = phase.execute(self.context)
                    if not success:
                        self.logger.warning(f"⚠️ Phase {phase.name} reported failure")
                
                except Exception as e:
                    self.logger.error(f"💥 Error in phase {phase.name}: {e}")
                    self._handle_error(e)
                    return False
                
                finally:
                    # Record phase timing
                    phase_time = (time.time() - phase_start_time) * 1000  # Convert to ms
                    phase.last_execution_time = phase_time
                    phase.execution_count += 1
                    phase.total_execution_time += phase_time
                    
                    # Update metrics
                    loop_phase = getattr(LoopPhase, phase.name.upper(), None)
                    if loop_phase:
                        self.context.metrics.add_phase_time(loop_phase, phase_time)
            
            # Update metrics
            total_iteration_time = time.time() - iteration_start_time
            self.context.metrics.average_loop_time = total_iteration_time
            self.context.metrics.active_agents = len(self.context.agents)
            
            # Call iteration complete callback
            if self.on_iteration_complete:
                self.on_iteration_complete(self.context)
            
            # Update performance metrics periodically
            if (current_time - self.last_metrics_update > 
                self.config.metrics_update_interval):
                self._update_performance_metrics()
                self.last_metrics_update = current_time
            
            # Reset error counter on successful iteration
            self.context.consecutive_errors = 0
            
            return True
            
        except Exception as e:
            self.logger.error(f"💥 Critical error in iteration: {e}")
            self._handle_error(e)
            return False
    
    def _control_frame_rate(self) -> None:
        """Control simulation frame rate."""
        frame_time = time.time() - self.last_frame_time + self.target_frame_time
        
        if frame_time < self.target_frame_time:
            sleep_time = self.target_frame_time - frame_time
            time.sleep(sleep_time)
    
    def _should_terminate(self) -> bool:
        """Check if simulation should terminate."""
        # Check time limit
        if (self.config.max_simulation_time > 0 and 
            self.context.simulation_time >= self.config.max_simulation_time):
            self.logger.info("⏰ Simulation time limit reached")
            return True
        
        # Check iteration limit
        if (self.config.max_iterations > 0 and 
            self.context.iteration_count >= self.config.max_iterations):
            self.logger.info("🔢 Simulation iteration limit reached")
            return True
        
        # Check for excessive errors
        if (self.context.consecutive_errors >= 
            self.config.max_consecutive_errors):
            self.logger.error("❌ Too many consecutive errors, terminating")
            return True
        
        return False
    
    def _handle_error(self, error: Exception) -> None:
        """Handle simulation errors."""
        self.context.consecutive_errors += 1
        self.context.last_error = error
        
        # Call error callback
        if self.on_error:
            self.on_error(error)
        
        # Publish error event
        self.event_bus.create_and_publish(
            EventType.ERROR_OCCURRED,
            source_id="simulation_engine",
            data={'error_type': type(error).__name__, 'error_message': str(error)},
            priority=EventPriority.HIGH
        )
        
        if self.context.consecutive_errors >= self.config.max_consecutive_errors:
            self._change_state(SimulationState.ERROR)
        else:
            # Brief pause for error recovery
            time.sleep(self.config.error_recovery_delay)
    
    def _change_state(self, new_state: SimulationState) -> None:
        """Change simulation state and notify listeners."""
        old_state = self.context.simulation_state
        self.context.simulation_state = new_state
        
        self.logger.info(f"🔄 State changed: {old_state.value} → {new_state.value}")
        
        if self.on_state_changed:
            self.on_state_changed(new_state)
    
    def _update_performance_metrics(self) -> None:
        """Update performance metrics."""
        # Get system metrics (simplified - would use psutil in real implementation)
        self.context.metrics.memory_usage_mb = 0.0  # Placeholder
        self.context.metrics.cpu_usage_percent = 0.0  # Placeholder
        
        # Get event bus metrics
        event_stats = self.event_bus.get_statistics()
        self.context.metrics.event_queue_size = event_stats['queue_size']
        
        # Publish performance metrics
        self.event_bus.create_and_publish(
            EventType.PERFORMANCE_METRIC,
            source_id="simulation_engine",
            data=self.context.metrics.get_performance_summary(),
            priority=EventPriority.BACKGROUND
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get current simulation status."""
        return {
            'state': self.context.simulation_state.value,
            'running': self.running,
            'paused': self.paused,
            'simulation_time': self.context.simulation_time,
            'iteration_count': self.context.iteration_count,
            'agent_count': len(self.context.agents),
            'consecutive_errors': self.context.consecutive_errors,
            'metrics': self.context.metrics.get_performance_summary()
        }


# Default simulation phases (to be implemented)

class InputProcessingPhase(SimulationPhase):
    """Phase for processing user input and external commands."""
    
    def __init__(self):
        super().__init__("input_processing", priority=10)
    
    def execute(self, context: SimulationContext) -> bool:
        """Process input events and commands."""
        # Placeholder - would process user input, network commands, etc.
        return True


class AgentDecisionPhase(SimulationPhase):
    """Phase for agent AI decision making."""
    
    def __init__(self):
        super().__init__("agent_decision", priority=20)
    
    def execute(self, context: SimulationContext) -> bool:
        """Update agent AI decisions."""
        # Placeholder - would call agent.update() or agent.decide()
        decisions_made = 0
        
        for agent in context.agents:
            # Would call agent decision logic here
            decisions_made += 1
        
        if context.delta_time > 0:
            context.metrics.decisions_per_second = decisions_made / context.delta_time
        else:
            context.metrics.decisions_per_second = 0.0
        return True


class AgentActionPhase(SimulationPhase):
    """Phase for executing agent actions."""
    
    def __init__(self):
        super().__init__("agent_action", priority=30)
    
    def execute(self, context: SimulationContext) -> bool:
        """Execute agent actions."""
        # Placeholder - would execute movement, attacks, etc.
        actions_executed = 0
        
        for agent in context.agents:
            # Would execute agent actions here
            actions_executed += 1
        
        if context.delta_time > 0:
            context.metrics.actions_per_second = actions_executed / context.delta_time
        else:
            context.metrics.actions_per_second = 0.0
        return True


class PhysicsUpdatePhase(SimulationPhase):
    """Phase for physics and collision detection."""
    
    def __init__(self):
        super().__init__("physics_update", priority=40)
    
    def execute(self, context: SimulationContext) -> bool:
        """Update physics simulation."""
        # Placeholder - would handle movement, collisions, etc.
        return True


class EnvironmentUpdatePhase(SimulationPhase):
    """Phase for environment updates."""
    
    def __init__(self):
        super().__init__("environment_update", priority=50)
    
    def execute(self, context: SimulationContext) -> bool:
        """Update environment state."""
        # Placeholder - would update terrain, spawn items, etc.
        if context.environment:
            # Would call environment.update()
            pass
        return True


class EventProcessingPhase(SimulationPhase):
    """Phase for processing events."""
    
    def __init__(self):
        super().__init__("event_processing", priority=60)
    
    def execute(self, context: SimulationContext) -> bool:
        """Process pending events."""
        if not context.config:
            return True
            
        start_time = time.time()
        max_time = context.config.event_processing_time_budget_ms / 1000.0
        
        events_processed = 0
        while (time.time() - start_time < max_time and 
               events_processed < context.config.max_events_per_loop):
            
            processed = context.event_bus.process_events(10)
            if processed == 0:
                break
            events_processed += processed
        
        context.metrics.events_processed_per_loop = events_processed
        return True


def create_default_simulation() -> SimulationEngine:
    """Create a simulation engine with default phases."""
    config = SimulationConfig()
    engine = SimulationEngine(config)
    
    # Add default phases
    engine.add_phase(InputProcessingPhase())
    engine.add_phase(AgentDecisionPhase())
    engine.add_phase(AgentActionPhase())
    engine.add_phase(PhysicsUpdatePhase())
    engine.add_phase(EnvironmentUpdatePhase())
    engine.add_phase(EventProcessingPhase())
    
    return engine

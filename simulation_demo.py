#!/usr/bin/env python3
"""
Simple Simulation Demo
Demonstrates the basic simulation loop architecture for the Battle AI system.
"""

import time
from typing import List, Optional
from src.simulation import create_default_simulation
from src.agents.base_agent import BaseAgent
from src.environment.simple_environment import SimpleEnvironment
from src.utils.vector2d import Vector2D
from src.utils.coordinate_system import initialize_coordinate_system
from src.utils.logging_config import get_logger


class DemoAgent(BaseAgent):
    """Simple demo agent that moves randomly."""
    
    def update(self, delta_time: float, visible_agents: List['BaseAgent'], 
               environment_info: dict) -> None:
        """Update agent state."""
        # Simple random movement for demo
        import random
        if random.random() < 0.1:  # 10% chance to change direction
            self.velocity = Vector2D(
                random.uniform(-50, 50),
                random.uniform(-50, 50)
            )
    
    def decide_action(self, visible_agents: List['BaseAgent'], 
                     environment_info: dict) -> str:
        """Decide what action to take."""
        return "move"  # Always just move
    
    def take_action(self, action: str, target: Optional['BaseAgent'] = None) -> bool:
        """Execute an action."""
        if action == "move":
            return True
        return False
    
    def get_desired_position(self, delta_time: float) -> Vector2D:
        """Get the position this agent wants to move to."""
        return self.position + self.velocity * delta_time
    
    def select_target(self, visible_agents: List['BaseAgent']) -> Optional['BaseAgent']:
        """Select a target from visible agents."""
        # Demo agent doesn't target anyone
        return None
    
    def calculate_movement(self, delta_time: float, 
                          environment_info: dict) -> Vector2D:
        """Calculate movement for this frame."""
        return self.velocity * delta_time


def main():
    """Demonstrate the simulation system."""
    logger = get_logger("simulation_demo")
    logger.info("🚀 Starting Battle AI Simulation Demo")
    
    # Initialize coordinate system
    coordinate_config = {
        'battlefield_width': 1000,
        'battlefield_height': 800,
        'grid_cell_size': 32.0,
        'boundary_behavior': 'clamp'
    }
    initialize_coordinate_system(coordinate_config)
    
    # Create simulation engine with default phases
    engine = create_default_simulation()
    logger.info(f"✅ Created simulation engine with {len(engine.phases)} phases")
    
    # Create and set up environment
    environment = SimpleEnvironment()
    engine.set_environment(environment)
    logger.info("🌍 Environment set up")
    
    # Create some demo agents
    for i in range(3):
        agent = DemoAgent(
            position=Vector2D(100 + i * 200, 400),
            agent_id=f"demo_agent_{i}",
            team_id="team_alpha" if i < 2 else "team_beta"
        )
        engine.add_agent(agent)
        environment.add_agent(agent)
    
    logger.info(f"🤖 Added {len(engine.context.agents)} agents to simulation")
    
    # Configure simulation for demo
    engine.config.max_simulation_time = 5.0  # Run for 5 seconds
    engine.config.target_fps = 10.0  # Slower for demo visibility
    
    # Set up callbacks for monitoring
    def on_iteration_complete(context):
        if context.iteration_count % 10 == 0:  # Log every 10 iterations
            logger.info(f"🔄 Iteration {context.iteration_count}: "
                       f"Time={context.simulation_time:.2f}s, "
                       f"FPS={context.metrics.actual_fps:.1f}")
    
    def on_state_changed(new_state):
        logger.info(f"🔄 Simulation state changed to: {new_state.value}")
    
    engine.on_iteration_complete = on_iteration_complete
    engine.on_state_changed = on_state_changed
    
    # Run simulation
    logger.info("▶️ Starting simulation (non-threaded for demo)")
    start_time = time.time()
    
    try:
        engine.start(threaded=False)  # Run in main thread for demo
    except KeyboardInterrupt:
        logger.info("⏹️ Simulation interrupted by user")
    finally:
        engine.stop()
    
    # Show final statistics
    duration = time.time() - start_time
    status = engine.get_status()
    
    logger.info("📊 Simulation Complete!")
    logger.info(f"   Real time: {duration:.2f}s")
    logger.info(f"   Simulation time: {status['simulation_time']:.2f}s")
    logger.info(f"   Total iterations: {status['iteration_count']}")
    logger.info(f"   Average FPS: {status['metrics']['fps']}")
    logger.info(f"   Agents processed: {status['agent_count']}")
    
    # Show phase breakdown
    logger.info("⏱️ Phase Performance:")
    for phase_name, time_ms in status['metrics']['phase_breakdown'].items():
        logger.info(f"   {phase_name}: {time_ms:.2f}ms")


if __name__ == "__main__":
    main()

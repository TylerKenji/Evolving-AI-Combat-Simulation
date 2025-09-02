"""
Debug utilities for Battle AI project
This file is used to test debugging configuration and explore the project structure.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils import Vector2D, Config, config_manager


def test_vector_operations():
    """Test Vector2D operations with debugging."""
    print("🧪 Testing Vector2D operations...")
    
    # Create test vectors
    v1 = Vector2D(3, 4)
    v2 = Vector2D(1, 2)
    
    # Basic operations
    print(f"v1 = {v1}")
    print(f"v2 = {v2}")
    print(f"v1 + v2 = {v1 + v2}")
    print(f"v1 - v2 = {v1 - v2}")
    print(f"v1 * 2 = {v1 * 2}")
    print(f"v1.magnitude() = {v1.magnitude()}")
    print(f"v1.normalize() = {v1.normalize()}")
    print(f"v1.distance_to(v2) = {v1.distance_to(v2)}")
    
    # Set breakpoint here to inspect variables
    breakpoint_marker = "Set breakpoint on this line"
    print(f"🔍 {breakpoint_marker}")
    
    return v1, v2


def test_configuration():
    """Test configuration system with debugging."""
    print("\n⚙️ Testing Configuration system...")
    
    # Load default configuration
    config = config_manager.get_config()
    
    print(f"Simulation config:")
    print(f"  max_agents: {config.simulation.max_agents}")
    print(f"  battlefield_size: {config.simulation.battlefield_width}x{config.simulation.battlefield_height}")
    print(f"  time_step: {config.simulation.time_step}")
    print(f"  fps: {config.simulation.fps}")
    
    print(f"\nAgent config:")
    print(f"  default_health: {config.agents.default_health}")
    print(f"  default_speed: {config.agents.default_speed}")
    print(f"  collision_radius: {config.agents.collision_radius}")
    print(f"  vision_range: {config.agents.vision_range}")
    
    # Set breakpoint here to inspect configuration
    breakpoint_marker = "Inspect config object here"
    print(f"🔍 {breakpoint_marker}")
    
    return config


def simulate_agent_positions():
    """Simulate some agent positions for debugging visualization."""
    print("\n🤖 Simulating agent positions...")
    
    config = config_manager.get_config()
    
    # Create some test agent positions
    agents = []
    for i in range(5):
        x = (i + 1) * config.simulation.battlefield_width / 6
        y = config.simulation.battlefield_height / 2
        position = Vector2D(x, y)
        
        # Create simple velocity
        velocity = Vector2D.from_angle(i * 1.2, config.agents.default_speed)
        
        agent_data = {
            'id': i,
            'position': position,
            'velocity': velocity,
            'health': config.agents.default_health
        }
        agents.append(agent_data)
        
        print(f"Agent {i}: pos={position}, vel={velocity}")
    
    # Set breakpoint here to inspect agents
    breakpoint_marker = "Inspect agents list here"
    print(f"🔍 {breakpoint_marker}")
    
    return agents


def main():
    """Main debug function - run this to test debugging setup."""
    print("🚀 Battle AI Debug Session Started")
    print("=" * 50)
    
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Project root: {project_root}")
    
    try:
        # Test core components
        vectors = test_vector_operations()
        config = test_configuration()
        agents = simulate_agent_positions()
        
        print("\n✅ All debug tests completed successfully!")
        print("🔍 Set breakpoints in the functions above to debug step-by-step")
        
        # Final breakpoint for inspection
        final_inspection = {
            'vectors': vectors,
            'config': config,
            'agents': agents
        }
        print(f"🎯 Final inspection point - all data available")
        
        return final_inspection
        
    except Exception as e:
        print(f"❌ Error during debug session: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    result = main()
    print("\n🏁 Debug session complete!")

"""
Test script for basic collision detection functionality.

This script tests the collision detection implementation in Task 1.4.6.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agents.base_agent import BaseAgent, AgentStats, AgentGenome, AgentRole, AgentState
from src.utils.vector2d import Vector2D
from typing import Dict, Any, Sequence, Optional


class TestAgent(BaseAgent):
    """Concrete implementation of BaseAgent for testing."""
    
    def update(self, dt: float, battlefield_info: Dict[str, Any]) -> None:
        """Simple update - just call collision detection."""
        all_agents = battlefield_info.get('all_agents', [])
        battlefield_bounds = battlefield_info.get('bounds', (800, 600))
        self.update_collision_state(dt, all_agents, battlefield_bounds)
    
    def decide_action(self, visible_agents: Sequence[BaseAgent], 
                     battlefield_info: Dict[str, Any]) -> str:
        """Simple action decision."""
        return "idle"
    
    def select_target(self, visible_enemies: Sequence[BaseAgent]) -> Optional[BaseAgent]:
        """Simple target selection."""
        return None
    
    def calculate_movement(self, visible_agents: Sequence[BaseAgent], 
                         battlefield_info: Dict[str, Any]) -> Vector2D:
        """Simple movement calculation."""
        return Vector2D(0, 0)


def test_basic_collision_detection():
    """Test basic collision detection functionality."""
    print("🧪 Testing Basic Collision Detection")
    print("=" * 50)
    
    # Test 1: Agent-Agent collision detection
    print("\n1. Testing agent-agent collision detection...")
    
    agent1 = TestAgent(position=Vector2D(100, 100))
    agent2 = TestAgent(position=Vector2D(110, 100))  # Close enough to collide
    agent3 = TestAgent(position=Vector2D(150, 100))  # Far enough away
    
    # Test collision detection
    assert agent1.check_collision_with_agent(agent2), "Agents should be colliding"
    assert not agent1.check_collision_with_agent(agent3), "Agents should not be colliding"
    print("✅ Agent-agent collision detection working")
    
    # Test 2: Boundary collision detection
    print("\n2. Testing boundary collision detection...")
    
    agent_center = TestAgent(position=Vector2D(400, 300))
    agent_edge = TestAgent(position=Vector2D(5, 300))  # Near left boundary
    agent_outside = TestAgent(position=Vector2D(-5, 300))  # Past left boundary
    
    battlefield_bounds = (800, 600)
    
    assert not agent_center.check_collision_with_bounds(battlefield_bounds), "Center agent should not collide with bounds"
    assert agent_edge.check_collision_with_bounds(battlefield_bounds), "Edge agent should collide with bounds"
    assert agent_outside.check_collision_with_bounds(battlefield_bounds), "Outside agent should collide with bounds"
    print("✅ Boundary collision detection working")
    
    # Test 3: Collision resolution
    print("\n3. Testing collision resolution...")
    
    agent1.position = Vector2D(100, 100)
    agent2.position = Vector2D(105, 100)  # Overlapping
    
    initial_distance = agent1.position.distance_to(agent2.position)
    agent1.resolve_collision_with_agent(agent2)
    final_distance = agent1.position.distance_to(agent2.position)
    
    assert final_distance > initial_distance, "Agents should be pushed apart"
    assert final_distance >= agent1.collision_radius + agent2.collision_radius, "Agents should not be overlapping"
    print("✅ Collision resolution working")
    
    # Test 4: Boundary normal calculation
    print("\n4. Testing boundary normal calculation...")
    
    agent_left = TestAgent(position=Vector2D(5, 300))
    agent_right = TestAgent(position=Vector2D(795, 300))
    agent_top = TestAgent(position=Vector2D(400, 5))
    agent_bottom = TestAgent(position=Vector2D(400, 595))
    
    left_normal = agent_left.get_collision_boundary_normal(battlefield_bounds)
    right_normal = agent_right.get_collision_boundary_normal(battlefield_bounds)
    top_normal = agent_top.get_collision_boundary_normal(battlefield_bounds)
    bottom_normal = agent_bottom.get_collision_boundary_normal(battlefield_bounds)
    
    assert left_normal == Vector2D(1, 0), f"Left normal should be (1,0), got {left_normal}"
    assert right_normal == Vector2D(-1, 0), f"Right normal should be (-1,0), got {right_normal}"
    assert top_normal == Vector2D(0, 1), f"Top normal should be (0,1), got {top_normal}"
    assert bottom_normal == Vector2D(0, -1), f"Bottom normal should be (0,-1), got {bottom_normal}"
    print("✅ Boundary normal calculation working")
    
    # Test 5: Collision event recording
    print("\n5. Testing collision event recording...")
    
    agent1.position = Vector2D(100, 100)
    agent2.position = Vector2D(105, 100)
    agents = [agent1, agent2]
    
    battlefield_info = {
        'all_agents': agents,
        'bounds': battlefield_bounds
    }
    
    agent1.update(0.1, battlefield_info)
    
    assert len(agent1.collision_events) > 0, "Should have recorded collision events"
    assert agent1.has_recent_collision('agent'), "Should detect recent agent collision"
    print("✅ Collision event recording working")
    
    # Test 6: Point collision detection
    print("\n6. Testing point collision detection...")
    
    agent = TestAgent(position=Vector2D(100, 100))
    close_point = Vector2D(105, 100)
    far_point = Vector2D(150, 100)
    
    assert agent.check_collision_with_point(close_point), "Should collide with close point"
    assert not agent.check_collision_with_point(far_point), "Should not collide with far point"
    print("✅ Point collision detection working")
    
    print("\n🎉 All collision detection tests passed!")
    print("Task 1.4.6 - Basic collision detection implemented successfully!")


def test_collision_properties():
    """Test collision-related properties and serialization."""
    print("\n🔧 Testing Collision Properties")
    print("=" * 50)
    
    agent = TestAgent(position=Vector2D(100, 100))
    
    # Test default collision radius
    assert agent.collision_radius == 10.0, f"Default collision radius should be 10.0, got {agent.collision_radius}"
    print("✅ Default collision radius set correctly")
    
    # Test collision events list
    assert isinstance(agent.collision_events, list), "Collision events should be a list"
    assert len(agent.collision_events) == 0, "Collision events should start empty"
    print("✅ Collision events list initialized correctly")
    
    # Test serialization includes collision properties
    agent_dict = agent.to_dict()
    assert 'collision_radius' in agent_dict, "Serialization should include collision_radius"
    assert 'collision_events' in agent_dict, "Serialization should include collision_events"
    assert agent_dict['collision_radius'] == 10.0, "Serialized collision radius should match"
    print("✅ Collision properties included in serialization")
    
    print("\n🎉 All collision property tests passed!")


if __name__ == "__main__":
    try:
        test_basic_collision_detection()
        test_collision_properties()
        print("\n" + "=" * 60)
        print("🚀 TASK 1.4.6 COMPLETED SUCCESSFULLY!")
        print("Basic collision detection has been implemented in BaseAgent")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

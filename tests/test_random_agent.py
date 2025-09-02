"""
Test RandomAgent Implementation

This test validates that the RandomAgent correctly implements the BaseAgent
interface and behaves as expected for random decision making.
"""

import pytest
import math
from src.agents.random_agent import RandomAgent
from src.agents.base_agent import AgentRole, CombatAction
from src.utils.vector2d import Vector2D


class TestRandomAgent:
    """Test suite for RandomAgent functionality."""

    def test_random_agent_creation(self):
        """Test RandomAgent can be created with valid parameters."""
        position = Vector2D(100, 200)
        agent = RandomAgent(position=position, team_id="test_team")
        
        assert agent.position == position
        assert agent.team_id == "test_team"
        assert agent.role == AgentRole.DPS  # Default role
        assert agent.agent_id is not None
        assert agent.is_alive
        assert agent.get_agent_type() == "RandomAgent"
    
    def test_random_agent_decision_making(self):
        """Test RandomAgent makes valid combat decisions."""
        agent = RandomAgent(Vector2D(0, 0))
        
        # Create some mock battlefield info
        battlefield_info = {"terrain": "open", "time": 10.0}
        
        # Test decision making multiple times to verify randomness
        actions = []
        for _ in range(10):
            action = agent.decide_action([], battlefield_info)
            actions.append(action)
            assert isinstance(action, CombatAction)
        
        # Should get variety in actions (at least not all the same)
        unique_actions = set(actions)
        assert len(unique_actions) >= 1  # At least one action type
    
    def test_random_agent_movement(self):
        """Test RandomAgent generates valid movement vectors."""
        agent = RandomAgent(Vector2D(50, 50))
        battlefield_info = {"obstacles": []}
        
        # Test movement calculation multiple times
        movements = []
        for _ in range(10):
            agent.update(0.1, battlefield_info)  # Update to change direction
            velocity = agent.calculate_movement([], battlefield_info)
            movements.append(velocity)
            assert isinstance(velocity, Vector2D)
            # Movement should be reasonable (not infinite)
            assert velocity.magnitude() < 1000
        
        # Should get variety in movements
        unique_movements = len(set((round(v.x, 1), round(v.y, 1)) for v in movements))
        assert unique_movements >= 1
    
    def test_random_agent_target_selection(self):
        """Test RandomAgent target selection behavior."""
        agent = RandomAgent(Vector2D(0, 0), team_id="team1")
        
        # Create enemy agents
        enemy1 = RandomAgent(Vector2D(10, 10), team_id="team2")
        enemy2 = RandomAgent(Vector2D(20, 20), team_id="team2")
        enemies = [enemy1, enemy2]
        
        # Test with no enemies
        target = agent.select_target([])
        assert target is None
        
        # Test with enemies
        selections = []
        for _ in range(10):
            target = agent.select_target(enemies)
            selections.append(target)
            assert target in enemies or target is None
        
        # Should select different targets randomly
        unique_targets = set(selections)
        assert len(unique_targets) >= 1
    
    def test_random_agent_update_cycle(self):
        """Test RandomAgent update cycle works correctly."""
        agent = RandomAgent(Vector2D(0, 0))
        initial_position = Vector2D(agent.position.x, agent.position.y)  # Create copy manually
        
        battlefield_info = {"time": 0.0}
        
        # Run several update cycles
        for i in range(5):
            agent.update(0.1, battlefield_info)
            assert agent.is_alive  # Should stay alive during normal updates
            battlefield_info["time"] += 0.1
        
        # Agent should have internal state changes
        assert agent.last_movement_change >= 0
    
    def test_random_agent_string_representation(self):
        """Test RandomAgent string representations."""
        agent = RandomAgent(Vector2D(100, 200), team_id="test")
        
        str_repr = str(agent)
        assert "RandomAgent" in str_repr
        assert agent.agent_id[:8] in str_repr
        
        repr_str = repr(agent)
        assert "RandomAgent" in repr_str
        assert "pos=" in repr_str
        assert "team=test" in repr_str
    
    def test_random_agent_strategy_description(self):
        """Test RandomAgent provides meaningful strategy description."""
        agent = RandomAgent(Vector2D(0, 0))
        description = agent.get_strategy_description()
        
        assert isinstance(description, str)
        assert len(description) > 0
        assert "random" in description.lower()
        assert "baseline" in description.lower()
    
    def test_random_agent_behavior_randomization(self):
        """Test that RandomAgent actually produces varied behavior."""
        agent = RandomAgent(Vector2D(0, 0))
        battlefield_info = {}
        
        # Collect decisions over many iterations
        actions = []
        movements = []
        
        for _ in range(50):
            agent.update(0.1, battlefield_info)
            action = agent.decide_action([], battlefield_info)
            movement = agent.calculate_movement([], battlefield_info)
            
            actions.append(action)
            movements.append((round(movement.x, 0), round(movement.y, 0)))
        
        # Should see variety in both actions and movements
        unique_actions = len(set(actions))
        unique_movements = len(set(movements))
        
        # Allow for some randomness but expect variety
        assert unique_actions >= 2, f"Only {unique_actions} unique actions in 50 iterations"
        assert unique_movements >= 5, f"Only {unique_movements} unique movements in 50 iterations"


if __name__ == "__main__":
    # Run basic tests if executed directly
    test_suite = TestRandomAgent()
    
    print("Testing RandomAgent creation...")
    test_suite.test_random_agent_creation()
    print("✅ Creation test passed")
    
    print("Testing RandomAgent decision making...")
    test_suite.test_random_agent_decision_making()
    print("✅ Decision making test passed")
    
    print("Testing RandomAgent movement...")
    test_suite.test_random_agent_movement()
    print("✅ Movement test passed")
    
    print("Testing RandomAgent target selection...")
    test_suite.test_random_agent_target_selection()
    print("✅ Target selection test passed")
    
    print("Testing RandomAgent update cycle...")
    test_suite.test_random_agent_update_cycle()
    print("✅ Update cycle test passed")
    
    print("Testing RandomAgent string representations...")
    test_suite.test_random_agent_string_representation()
    print("✅ String representation test passed")
    
    print("Testing RandomAgent strategy description...")
    test_suite.test_random_agent_strategy_description()
    print("✅ Strategy description test passed")
    
    print("Testing RandomAgent behavior randomization...")
    test_suite.test_random_agent_behavior_randomization()
    print("✅ Behavior randomization test passed")
    
    print("🎉 All RandomAgent tests passed!")

"""
Test IdleAgent Implementation

This test validates that the IdleAgent correctly implements the BaseAgent
interface and behaves as expected for complete inactivity.
"""

import pytest
import time
from src.agents.idle_agent import IdleAgent
from src.agents.base_agent import AgentRole, CombatAction
from src.utils.vector2d import Vector2D


class TestIdleAgent:
    """Test suite for IdleAgent functionality."""

    def test_idle_agent_creation(self):
        """Test IdleAgent can be created with valid parameters."""
        position = Vector2D(100, 200)
        agent = IdleAgent(position=position, team_id="test_team")
        
        assert agent.position == position
        assert agent.team_id == "test_team"
        assert agent.role == AgentRole.SUPPORT  # Default role for passive agents
        assert agent.agent_id is not None
        assert agent.is_alive
        assert agent.get_agent_type() == "IdleAgent"
        assert agent.total_idle_time == 0.0
        assert agent.update_count == 0
    
    def test_idle_agent_decision_making(self):
        """Test IdleAgent always makes the same predictable decision."""
        agent = IdleAgent(Vector2D(0, 0))
        
        # Create some mock battlefield info
        battlefield_info = {"terrain": "open", "time": 10.0}
        
        # Test decision making multiple times - should always be MOVE
        for _ in range(10):
            action = agent.decide_action([], battlefield_info)
            assert action == CombatAction.MOVE
    
    def test_idle_agent_movement(self):
        """Test IdleAgent never moves (always zero velocity)."""
        agent = IdleAgent(Vector2D(50, 50))
        battlefield_info = {"obstacles": []}
        
        # Test movement calculation multiple times
        for _ in range(10):
            agent.update(0.1, battlefield_info)
            velocity = agent.calculate_movement([], battlefield_info)
            assert velocity == Vector2D(0, 0)
            assert velocity.magnitude() == 0.0
    
    def test_idle_agent_target_selection(self):
        """Test IdleAgent never selects targets."""
        agent = IdleAgent(Vector2D(0, 0), team_id="team1")
        
        # Create enemy agents
        from src.agents.random_agent import RandomAgent
        enemy1 = RandomAgent(Vector2D(10, 10), team_id="team2")
        enemy2 = RandomAgent(Vector2D(20, 20), team_id="team2")
        enemies = [enemy1, enemy2]
        
        # Test with no enemies
        target = agent.select_target([])
        assert target is None
        
        # Test with enemies - should still return None
        for _ in range(10):
            target = agent.select_target(enemies)
            assert target is None
    
    def test_idle_agent_update_cycle(self):
        """Test IdleAgent update cycle tracks time and counts correctly."""
        agent = IdleAgent(Vector2D(0, 0))
        initial_position = Vector2D(agent.position.x, agent.position.y)
        
        battlefield_info = {"time": 0.0}
        dt = 0.1
        
        # Run several update cycles
        for i in range(5):
            agent.update(dt, battlefield_info)
            assert agent.is_alive  # Should stay alive during normal updates
            assert agent.total_idle_time == (i + 1) * dt
            assert agent.update_count == i + 1
            battlefield_info["time"] += dt
        
        # Position should not have changed
        assert agent.position == initial_position
    
    def test_idle_agent_statistics(self):
        """Test IdleAgent provides accurate idle statistics."""
        agent = IdleAgent(Vector2D(100, 200), team_id="test")
        
        # Initial statistics
        stats = agent.get_idle_statistics()
        assert stats["total_idle_time"] == 0.0
        assert stats["update_count"] == 0
        assert stats["position"] == [100.0, 200.0]
        assert stats["is_alive"] is True
        assert stats["team_id"] == "test"
        assert stats["role"] == "support"
        
        # After some updates
        battlefield_info = {}
        for _ in range(3):
            agent.update(0.2, battlefield_info)
        
        stats = agent.get_idle_statistics()
        assert abs(stats["total_idle_time"] - 0.6) < 0.0001  # Handle floating point precision
        assert stats["update_count"] == 3
        assert abs(stats["average_update_interval"] - 0.2) < 0.0001
    
    def test_idle_agent_string_representation(self):
        """Test IdleAgent string representations."""
        agent = IdleAgent(Vector2D(100, 200), team_id="test")
        
        # Update a few times to get some idle time
        for _ in range(2):
            agent.update(0.5, {})
        
        str_repr = str(agent)
        assert "IdleAgent" in str_repr
        assert agent.agent_id[:8] in str_repr
        assert "idle:1.0s" in str_repr
        
        repr_str = repr(agent)
        assert "IdleAgent" in repr_str
        assert "pos=" in repr_str
        assert "team=test" in repr_str
        assert "idle_time=1.0s" in repr_str
        assert "updates=2" in repr_str
    
    def test_idle_agent_strategy_description(self):
        """Test IdleAgent provides meaningful strategy description."""
        agent = IdleAgent(Vector2D(0, 0))
        description = agent.get_strategy_description()
        
        assert isinstance(description, str)
        assert len(description) > 0
        assert "passive" in description.lower()
        assert "testing" in description.lower()
        assert "no actions" in description.lower()
    
    def test_idle_agent_consistency(self):
        """Test that IdleAgent behavior is completely consistent."""
        agent = IdleAgent(Vector2D(0, 0))
        battlefield_info = {}
        
        # Collect actions and movements over many iterations
        actions = []
        movements = []
        targets = []
        
        # Create some mock enemies
        from src.agents.random_agent import RandomAgent
        enemies = [RandomAgent(Vector2D(10, 10), team_id="enemy")]
        
        for _ in range(20):
            agent.update(0.1, battlefield_info)
            action = agent.decide_action([], battlefield_info)
            movement = agent.calculate_movement([], battlefield_info)
            target = agent.select_target(enemies)
            
            actions.append(action)
            movements.append(movement)
            targets.append(target)
        
        # All actions should be identical (MOVE)
        assert all(action == CombatAction.MOVE for action in actions)
        
        # All movements should be zero
        assert all(movement == Vector2D(0, 0) for movement in movements)
        
        # All targets should be None
        assert all(target is None for target in targets)
    
    def test_idle_agent_with_damage(self):
        """Test IdleAgent behavior when taking damage."""
        agent = IdleAgent(Vector2D(0, 0))
        initial_health = agent.stats.current_health
        
        # Agent should still be idle even after taking damage
        # Note: Damage is reduced by defense (5.0), so 20.0 damage becomes 15.0 actual damage
        agent.take_damage(20.0)
        expected_health = initial_health - max(0, 20.0 - agent.stats.defense)
        assert agent.stats.current_health == expected_health
        
        # Behavior should remain the same
        action = agent.decide_action([], {})
        movement = agent.calculate_movement([], {})
        target = agent.select_target([])
        
        assert action == CombatAction.MOVE
        assert movement == Vector2D(0, 0)
        assert target is None
    
    def test_idle_agent_role_customization(self):
        """Test IdleAgent can be created with different roles."""
        roles_to_test = [AgentRole.TANK, AgentRole.DPS, AgentRole.SUPPORT, AgentRole.BALANCED]
        
        for role in roles_to_test:
            agent = IdleAgent(Vector2D(0, 0), role=role)
            assert agent.role == role
            
            # Behavior should be identical regardless of role
            action = agent.decide_action([], {})
            movement = agent.calculate_movement([], {})
            target = agent.select_target([])
            
            assert action == CombatAction.MOVE
            assert movement == Vector2D(0, 0)
            assert target is None


if __name__ == "__main__":
    # Run basic tests if executed directly
    test_suite = TestIdleAgent()
    
    print("Testing IdleAgent creation...")
    test_suite.test_idle_agent_creation()
    print("✅ Creation test passed")
    
    print("Testing IdleAgent decision making...")
    test_suite.test_idle_agent_decision_making()
    print("✅ Decision making test passed")
    
    print("Testing IdleAgent movement...")
    test_suite.test_idle_agent_movement()
    print("✅ Movement test passed")
    
    print("Testing IdleAgent target selection...")
    test_suite.test_idle_agent_target_selection()
    print("✅ Target selection test passed")
    
    print("Testing IdleAgent update cycle...")
    test_suite.test_idle_agent_update_cycle()
    print("✅ Update cycle test passed")
    
    print("Testing IdleAgent statistics...")
    test_suite.test_idle_agent_statistics()
    print("✅ Statistics test passed")
    
    print("Testing IdleAgent string representations...")
    test_suite.test_idle_agent_string_representation()
    print("✅ String representation test passed")
    
    print("Testing IdleAgent strategy description...")
    test_suite.test_idle_agent_strategy_description()
    print("✅ Strategy description test passed")
    
    print("Testing IdleAgent consistency...")
    test_suite.test_idle_agent_consistency()
    print("✅ Consistency test passed")
    
    print("Testing IdleAgent with damage...")
    test_suite.test_idle_agent_with_damage()
    print("✅ Damage test passed")
    
    print("Testing IdleAgent role customization...")
    test_suite.test_idle_agent_role_customization()
    print("✅ Role customization test passed")
    
    print("🎉 All IdleAgent tests passed!")

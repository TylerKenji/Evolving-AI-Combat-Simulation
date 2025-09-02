"""
Test SimpleChaseAgent Implementation

This test validates that the SimpleChaseAgent correctly implements the BaseAgent
interface and behaves as expected for pursuit and combat behavior.
"""

import pytest
import math
from src.agents.simple_chase_agent import SimpleChaseAgent
from src.agents.idle_agent import IdleAgent
from src.agents.base_agent import AgentRole, CombatAction
from src.utils.vector2d import Vector2D


class TestSimpleChaseAgent:
    """Test suite for SimpleChaseAgent functionality."""

    def test_simple_chase_agent_creation(self):
        """Test SimpleChaseAgent can be created with valid parameters."""
        position = Vector2D(100, 200)
        agent = SimpleChaseAgent(position=position, team_id="test_team")
        
        assert agent.position == position
        assert agent.team_id == "test_team"
        assert agent.role == AgentRole.DPS  # Default role
        assert agent.agent_id is not None
        assert agent.is_alive
        assert agent.get_agent_type() == "SimpleChaseAgent"
        assert agent.current_target is None
        assert agent.chase_distance_threshold == 200.0
    
    def test_chase_agent_target_selection(self):
        """Test SimpleChaseAgent selects appropriate targets."""
        agent = SimpleChaseAgent(Vector2D(0, 0), team_id="team1")
        
        # Create enemies at different distances
        close_enemy = IdleAgent(Vector2D(50, 0), team_id="team2")  # 50 units away
        far_enemy = IdleAgent(Vector2D(150, 0), team_id="team2")   # 150 units away
        very_far_enemy = IdleAgent(Vector2D(300, 0), team_id="team2")  # 300 units away (beyond threshold)
        
        enemies = [close_enemy, far_enemy, very_far_enemy]
        
        # Should select closest enemy within threshold
        target = agent.select_target(enemies)
        assert target == close_enemy
        
        # Remove close enemy, should select next closest
        target = agent.select_target([far_enemy, very_far_enemy])
        assert target == far_enemy
        
        # Only very far enemy (beyond threshold) should return None
        target = agent.select_target([very_far_enemy])
        assert target is None
    
    def test_chase_agent_movement_toward_target(self):
        """Test SimpleChaseAgent moves toward selected target."""
        agent = SimpleChaseAgent(Vector2D(0, 0), team_id="team1")
        
        # Create target enemy
        target_enemy = IdleAgent(Vector2D(100, 0), team_id="team2")
        agent.current_target = target_enemy
        
        # Calculate movement
        movement = agent.calculate_movement([target_enemy], {})
        
        # Should move toward target (positive X direction)
        assert movement.x > 0
        assert abs(movement.y) < 0.1  # Should be minimal Y movement
        assert movement.magnitude() > 0
    
    def test_chase_agent_attack_decisions(self):
        """Test SimpleChaseAgent makes appropriate attack decisions."""
        agent = SimpleChaseAgent(Vector2D(0, 0), team_id="team1")
        
        # Create enemy within attack range
        close_enemy = IdleAgent(Vector2D(20, 0), team_id="team2")  # Within default attack range (30)
        
        # Test when agent can attack
        agent.last_attack_time = 0.0  # Reset cooldown
        action = agent.decide_action([close_enemy], {})
        assert action in [CombatAction.ATTACK_MELEE, CombatAction.ATTACK_RANGED]
        
        # Create enemy outside attack range
        far_enemy = IdleAgent(Vector2D(100, 0), team_id="team2")
        action = agent.decide_action([far_enemy], {})
        assert action == CombatAction.MOVE  # Should move to get closer
    
    def test_chase_agent_retreat_behavior(self):
        """Test SimpleChaseAgent retreats when health is low."""
        agent = SimpleChaseAgent(Vector2D(0, 0), team_id="team1")
        
        # Reduce health below retreat threshold (account for defense)
        agent.take_damage(90)  # Health should be around 10% (below 20% threshold)
        assert agent.health_percentage < agent.retreat_health_threshold
        
        # Create nearby enemy
        enemy = IdleAgent(Vector2D(30, 0), team_id="team2")
        
        # Should decide to retreat
        action = agent.decide_action([enemy], {})
        assert action == CombatAction.RETREAT
        
        # Movement should be away from enemy
        movement = agent.calculate_movement([enemy], {})
        # Should move in negative X direction (away from enemy at positive X)
        assert movement.x < 0
    
    def test_chase_agent_target_persistence(self):
        """Test SimpleChaseAgent maintains target focus appropriately."""
        agent = SimpleChaseAgent(Vector2D(0, 0), team_id="team1")
        
        # Create enemies
        enemy1 = IdleAgent(Vector2D(50, 0), team_id="team2")
        enemy2 = IdleAgent(Vector2D(60, 0), team_id="team2")
        
        # Select initial target
        target1 = agent.select_target([enemy1, enemy2])
        assert target1 == enemy1  # Should select closer enemy
        
        # Set as current target
        agent.current_target = target1
        
        # Select again with same enemies - should prefer current target due to persistence bonus
        target2 = agent.select_target([enemy1, enemy2])
        assert target2 == enemy1  # Should maintain same target
    
    def test_chase_agent_no_target_behavior(self):
        """Test SimpleChaseAgent behavior when no targets are available."""
        agent = SimpleChaseAgent(Vector2D(0, 0), team_id="team1")
        
        # No enemies visible
        action = agent.decide_action([], {})
        assert action == CombatAction.MOVE
        
        # Movement should be minimal search pattern
        movement = agent.calculate_movement([], {})
        assert movement.magnitude() > 0  # Should move to search
        assert movement.magnitude() < agent._get_effective_speed() * 0.5  # But slowly
    
    def test_chase_agent_update_cycle(self):
        """Test SimpleChaseAgent update cycle works correctly."""
        agent = SimpleChaseAgent(Vector2D(0, 0), team_id="team1")
        
        battlefield_info = {"time": 0.0}
        
        # Run several update cycles
        for i in range(5):
            agent.update(0.1, battlefield_info)
            assert agent.is_alive
            battlefield_info["time"] += 0.1
        
        # Should have tracking variables
        assert hasattr(agent, '_update_count')
        assert agent._update_count == 5
    
    def test_chase_agent_target_tracking(self):
        """Test SimpleChaseAgent tracks target positions correctly."""
        agent = SimpleChaseAgent(Vector2D(0, 0), team_id="team1")
        
        # Create and set target
        target = IdleAgent(Vector2D(100, 100), team_id="team2")
        agent.current_target = target
        
        # Update should record target position
        agent._update_target_tracking(0.1)
        assert agent.last_target_position is not None
        assert agent.last_target_position.x == 100
        assert agent.last_target_position.y == 100
        assert agent.target_lost_time == 0.0
        
        # Lose target
        agent.current_target = None
        agent._update_target_tracking(0.5)
        assert agent.target_lost_time == 0.5
    
    def test_chase_agent_statistics(self):
        """Test SimpleChaseAgent provides accurate statistics."""
        agent = SimpleChaseAgent(Vector2D(100, 200), team_id="test")
        
        # Create target
        target = IdleAgent(Vector2D(150, 200), team_id="enemy")
        agent.current_target = target
        agent._update_target_tracking(0.1)
        
        stats = agent.get_chase_statistics()
        assert stats["current_target"] == target.agent_id[:8]
        assert abs(stats["target_distance"] - 50.0) < 0.1  # Distance should be 50
        assert stats["last_target_position"] == [150.0, 200.0]
        assert stats["target_lost_time"] == 0.0
        assert stats["health_percentage"] == 1.0
        assert stats["in_retreat_mode"] is False
        assert stats["can_attack"] is True
        assert stats["chase_distance_threshold"] == 200.0
    
    def test_chase_agent_string_representation(self):
        """Test SimpleChaseAgent string representations."""
        agent = SimpleChaseAgent(Vector2D(100, 200), team_id="test")
        
        str_repr = str(agent)
        assert "SimpleChaseAgent" in str_repr
        assert agent.agent_id[:8] in str_repr
        
        # Test with target
        target = IdleAgent(Vector2D(150, 200), team_id="enemy")
        agent.current_target = target
        
        str_repr_with_target = str(agent)
        assert "chasing:" in str_repr_with_target
        assert target.agent_id[:8] in str_repr_with_target
        
        repr_str = repr(agent)
        assert "SimpleChaseAgent" in repr_str
        assert "target=" in repr_str
    
    def test_chase_agent_strategy_description(self):
        """Test SimpleChaseAgent provides meaningful strategy description."""
        agent = SimpleChaseAgent(Vector2D(0, 0))
        description = agent.get_strategy_description()
        
        assert isinstance(description, str)
        assert len(description) > 0
        assert "chase" in description.lower()
        assert "pursuit" in description.lower()
        assert "aggressive" in description.lower()
    
    def test_chase_agent_speed_factors(self):
        """Test SimpleChaseAgent adjusts speed based on distance to target."""
        agent = SimpleChaseAgent(Vector2D(0, 0))
        
        # Close distance (within attack range)
        close_factor = agent._calculate_speed_factor(20)  # Within attack range (30)
        assert close_factor == 0.5
        
        # Medium distance
        medium_factor = agent._calculate_speed_factor(50)  # 2x attack range
        assert medium_factor == 0.8
        
        # Far distance
        far_factor = agent._calculate_speed_factor(100)  # Beyond 2x attack range
        assert far_factor == 1.0
    
    def test_chase_agent_role_customization(self):
        """Test SimpleChaseAgent can be created with different roles."""
        roles_to_test = [AgentRole.TANK, AgentRole.DPS, AgentRole.SUPPORT, AgentRole.BALANCED]
        
        for role in roles_to_test:
            agent = SimpleChaseAgent(Vector2D(0, 0), role=role)
            assert agent.role == role
            
            # Should still exhibit chase behavior regardless of role
            enemy = IdleAgent(Vector2D(100, 0), team_id="enemy")
            action = agent.decide_action([enemy], {})
            assert action == CombatAction.MOVE  # Should move toward distant enemy
    
    def test_chase_agent_combat_preferences(self):
        """Test SimpleChaseAgent combat preference settings."""
        agent = SimpleChaseAgent(Vector2D(0, 0), team_id="team1")
        
        # Test melee preference
        assert agent.attack_preference_melee is True
        
        # Create enemy at close range (within half attack range for melee preference)
        close_enemy = IdleAgent(Vector2D(10, 0), team_id="team2")
        agent.current_target = close_enemy
        
        # Should prefer melee when very close
        action = agent._determine_best_action([close_enemy], [close_enemy])
        assert action == CombatAction.ATTACK_MELEE
        
        # Create enemy at medium range
        medium_enemy = IdleAgent(Vector2D(25, 0), team_id="team2")
        agent.current_target = medium_enemy
        
        # Should use ranged when not very close
        action = agent._determine_best_action([medium_enemy], [medium_enemy])
        assert action == CombatAction.ATTACK_RANGED


if __name__ == "__main__":
    # Run basic tests if executed directly
    test_suite = TestSimpleChaseAgent()
    
    print("Testing SimpleChaseAgent creation...")
    test_suite.test_simple_chase_agent_creation()
    print("✅ Creation test passed")
    
    print("Testing SimpleChaseAgent target selection...")
    test_suite.test_chase_agent_target_selection()
    print("✅ Target selection test passed")
    
    print("Testing SimpleChaseAgent movement...")
    test_suite.test_chase_agent_movement_toward_target()
    print("✅ Movement test passed")
    
    print("Testing SimpleChaseAgent attack decisions...")
    test_suite.test_chase_agent_attack_decisions()
    print("✅ Attack decisions test passed")
    
    print("Testing SimpleChaseAgent retreat behavior...")
    test_suite.test_chase_agent_retreat_behavior()
    print("✅ Retreat behavior test passed")
    
    print("Testing SimpleChaseAgent target persistence...")
    test_suite.test_chase_agent_target_persistence()
    print("✅ Target persistence test passed")
    
    print("Testing SimpleChaseAgent no target behavior...")
    test_suite.test_chase_agent_no_target_behavior()
    print("✅ No target behavior test passed")
    
    print("Testing SimpleChaseAgent update cycle...")
    test_suite.test_chase_agent_update_cycle()
    print("✅ Update cycle test passed")
    
    print("Testing SimpleChaseAgent target tracking...")
    test_suite.test_chase_agent_target_tracking()
    print("✅ Target tracking test passed")
    
    print("Testing SimpleChaseAgent statistics...")
    test_suite.test_chase_agent_statistics()
    print("✅ Statistics test passed")
    
    print("Testing SimpleChaseAgent string representations...")
    test_suite.test_chase_agent_string_representation()
    print("✅ String representation test passed")
    
    print("Testing SimpleChaseAgent strategy description...")
    test_suite.test_chase_agent_strategy_description()
    print("✅ Strategy description test passed")
    
    print("Testing SimpleChaseAgent speed factors...")
    test_suite.test_chase_agent_speed_factors()
    print("✅ Speed factors test passed")
    
    print("Testing SimpleChaseAgent role customization...")
    test_suite.test_chase_agent_role_customization()
    print("✅ Role customization test passed")
    
    print("Testing SimpleChaseAgent combat preferences...")
    test_suite.test_chase_agent_combat_preferences()
    print("✅ Combat preferences test passed")
    
    print("🎉 All SimpleChaseAgent tests passed!")

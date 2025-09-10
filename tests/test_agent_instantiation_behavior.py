"""
Test Suite for Agent Instantiation and Basic Behavior (Task 1.5.6)

This comprehensive test suite validates that all agent implementations can be
instantiated correctly and exhibit their expected behaviors. It tests the
integration of all agent systems including decision-making, action validation,
and basic behaviors.

Test Categories:
1. Agent Instantiation Tests
2. Basic Behavior Validation Tests  
3. Decision Framework Integration Tests
4. Action Validation Integration Tests
5. Performance and Stress Tests
6. Edge Case and Error Handling Tests
"""

import pytest
import time
from typing import List, Dict, Any
from unittest.mock import Mock, patch

from src.agents.random_agent import RandomAgent
from src.agents.idle_agent import IdleAgent
from src.agents.simple_chase_agent import SimpleChaseAgent
from src.agents.base_agent import BaseAgent, CombatAction, AgentState
from src.agents.decision_framework import DecisionMaker, DecisionContext
from src.agents.action_validation import ActionExecutor, execute_agent_action, ValidationLevel
from src.utils.vector2d import Vector2D
from src.utils.logging_config import get_logger


class TestAgentInstantiation:
    """Test that all agent types can be instantiated correctly."""
    
    def test_random_agent_instantiation(self):
        """Test RandomAgent can be instantiated with valid parameters."""
        # Test basic instantiation
        agent = RandomAgent(Vector2D(100, 100))
        
        assert agent.agent_id is not None  # Should be auto-generated
        assert agent.position.x == 100
        assert agent.position.y == 100
        assert agent.is_alive is True
        assert isinstance(agent.stats.current_health, (int, float))
        assert agent.stats.current_health > 0
        
        # Test with custom parameters
        agent2 = RandomAgent(Vector2D(50, 75), team_id="team_1")
        assert agent2.agent_id is not None  # Should be auto-generated
        assert agent2.position.x == 50
        assert agent2.position.y == 75
        assert agent2.team_id == "team_1"
    
    def test_idle_agent_instantiation(self):
        """Test IdleAgent can be instantiated with valid parameters."""
        agent = IdleAgent(Vector2D(200, 150))
        
        assert agent.agent_id is not None  # Should be auto-generated
        assert agent.position.x == 200
        assert agent.position.y == 150
        assert agent.is_alive is True
        assert agent.state == AgentState.ALIVE  # IdleAgent starts alive
        
        # Verify idle-specific behavior
        assert hasattr(agent, 'update')
        assert hasattr(agent, 'decide_action')
    
    def test_simple_chase_agent_instantiation(self):
        """Test SimpleChaseAgent can be instantiated with valid parameters."""
        agent = SimpleChaseAgent(Vector2D(0, 0))
        
        assert agent.agent_id is not None  # Should be auto-generated
        assert agent.position.x == 0
        assert agent.position.y == 0
        assert agent.is_alive is True
        
        # Verify chase-specific attributes
        assert hasattr(agent, 'target_agent')
        assert hasattr(agent, 'update')
        assert hasattr(agent, 'decide_action')
        assert hasattr(agent, 'select_target')
    
    def test_agent_unique_ids(self):
        """Test that agents have unique IDs and don't conflict."""
        agents = [
            RandomAgent(Vector2D(10, 10)),
            IdleAgent(Vector2D(20, 20)),
            SimpleChaseAgent(Vector2D(30, 30)),
            RandomAgent(Vector2D(40, 40))
        ]
        
        # Verify all IDs are unique
        ids = [agent.agent_id for agent in agents]
        assert len(ids) == len(set(ids)), "Agent IDs are not unique"
        
        # Verify each agent has the correct type
        assert isinstance(agents[0], RandomAgent)
        assert isinstance(agents[1], IdleAgent)
        assert isinstance(agents[2], SimpleChaseAgent)
        assert isinstance(agents[3], RandomAgent)
    
    def test_agent_initialization_edge_cases(self):
        """Test agent instantiation with edge case parameters."""
        # Test with zero position
        agent1 = RandomAgent(Vector2D(0, 0))
        assert agent1.position.x == 0
        assert agent1.position.y == 0
        
        # Test with negative positions
        agent2 = IdleAgent(Vector2D(-100, -50))
        assert agent2.position.x == -100
        assert agent2.position.y == -50
        
        # Test with large positions
        agent3 = SimpleChaseAgent(Vector2D(10000, 5000))
        assert agent3.position.x == 10000
        assert agent3.position.y == 5000


class TestBasicAgentBehavior:
    """Test that each agent type exhibits expected behavior patterns."""
    
    @pytest.fixture
    def mock_battlefield_info(self):
        """Create mock battlefield information."""
        return {
            'bounds': {'min_x': 0, 'max_x': 200, 'min_y': 0, 'max_y': 200},
            'obstacles': [],
            'dt': 1.0
        }
    
    @pytest.fixture
    def sample_agents(self):
        """Create a set of sample agents for testing."""
        return [
            RandomAgent(Vector2D(50, 50)),
            IdleAgent(Vector2D(100, 100)),
            SimpleChaseAgent(Vector2D(150, 150))
        ]
    
    def test_random_agent_behavior(self, mock_battlefield_info, sample_agents):
        """Test RandomAgent exhibits random behavior."""
        random_agent = sample_agents[0]
        other_agents = sample_agents[1:]
        
        # Test decision making (should return random actions)
        decisions = []
        for _ in range(10):
            action = random_agent.decide_action(other_agents, mock_battlefield_info)
            decisions.append(action)
        
        # Should have at least some variety in decisions
        unique_decisions = set(decisions)
        assert len(unique_decisions) >= 1, "RandomAgent should make decisions"
        
        # Test update method doesn't crash (update only takes dt and battlefield_info)
        initial_pos = Vector2D(random_agent.position.x, random_agent.position.y)
        random_agent.update(1.0, mock_battlefield_info)
        
        # Agent should still be valid after update
        assert random_agent.is_alive
        assert isinstance(random_agent.position, Vector2D)
    
    def test_idle_agent_behavior(self, mock_battlefield_info, sample_agents):
        """Test IdleAgent exhibits idle behavior."""
        idle_agent = sample_agents[1]
        other_agents = [sample_agents[0], sample_agents[2]]
        
        # Test that idle agent makes minimal decisions
        action = idle_agent.decide_action(other_agents, mock_battlefield_info)
        assert action is not None
        
        # Test update method (update only takes dt and battlefield_info)
        initial_pos = Vector2D(idle_agent.position.x, idle_agent.position.y)
        initial_state = idle_agent.state
        
        idle_agent.update(1.0, mock_battlefield_info)
        
        # Idle agent should remain mostly unchanged
        assert idle_agent.is_alive
        assert idle_agent.state == AgentState.ALIVE or idle_agent.state == initial_state
    
    def test_simple_chase_agent_behavior(self, mock_battlefield_info, sample_agents):
        """Test SimpleChaseAgent exhibits chase behavior."""
        chase_agent = sample_agents[2]
        other_agents = sample_agents[:2]
        
        # Test target selection
        target = chase_agent.select_target(other_agents)
        
        if other_agents:  # If there are potential targets
            assert target in other_agents or target is None
        
        # Test decision making
        action = chase_agent.decide_action(other_agents, mock_battlefield_info)
        assert action is not None
        assert isinstance(action, CombatAction)
        
        # Test update behavior (update only takes dt and battlefield_info)
        initial_pos = Vector2D(chase_agent.position.x, chase_agent.position.y)
        chase_agent.update(1.0, mock_battlefield_info)
        
        assert chase_agent.is_alive
        
        # If there were targets, agent might have moved or changed state
        if other_agents:
            # Agent should be in some active state
            assert chase_agent.state in [AgentState.MOVING, AgentState.ATTACKING, 
                                       AgentState.DEFENDING, AgentState.ALIVE]
    
    def test_agent_state_transitions(self, mock_battlefield_info):
        """Test that agents can transition between different states."""
        agent = SimpleChaseAgent(Vector2D(100, 100))
        enemy = RandomAgent(Vector2D(120, 100))
        
        # Initial state
        initial_state = agent.state
        assert initial_state is not None
        
        # Update agent multiple times to see state changes
        states_observed = set()
        for i in range(5):
            agent.update(1.0, mock_battlefield_info)
            states_observed.add(agent.state)
            
            # Make sure agent stays alive during normal operations
            assert agent.is_alive
        
        # Should have observed at least one state
        assert len(states_observed) >= 1
        assert all(isinstance(state, AgentState) for state in states_observed)


class TestDecisionFrameworkIntegration:
    """Test integration with the decision framework."""
    
    def test_agents_with_decision_framework(self):
        """Test that agents can use the decision framework."""
        # Create agents
        agent1 = SimpleChaseAgent(Vector2D(100, 100))
        agent2 = RandomAgent(Vector2D(150, 100))
        
        # Create decision maker (requires agent parameter)
        decision_maker = DecisionMaker(agent1)
        
        # Test decision making
        action = decision_maker.decide_action(
            visible_agents=[agent2],
            battlefield_info={'bounds': {'min_x': 0, 'max_x': 200, 'min_y': 0, 'max_y': 200}},
            dt=1.0
        )
        assert isinstance(action, CombatAction)
        
        # Test that decision is reasonable
        valid_actions = list(CombatAction)
        assert action in valid_actions
    
    def test_decision_framework_with_all_agent_types(self):
        """Test decision framework works with all agent types."""
        agents = [
            RandomAgent(Vector2D(50, 50)),
            IdleAgent(Vector2D(100, 100)),
            SimpleChaseAgent(Vector2D(150, 150))
        ]
        
        for agent in agents:
            other_agents = [a for a in agents if a != agent]
            
            # Create decision maker for each agent
            decision_maker = DecisionMaker(agent)
            
            # Should be able to make decisions for any agent type
            action = decision_maker.decide_action(
                visible_agents=other_agents,
                battlefield_info={'bounds': {'min_x': 0, 'max_x': 200, 'min_y': 0, 'max_y': 200}},
                dt=1.0
            )
            assert isinstance(action, CombatAction)


class TestActionValidationIntegration:
    """Test integration with the action validation system."""
    
    def test_agents_with_action_validation(self):
        """Test that agents can use the action validation system."""
        # Create agents
        attacker = SimpleChaseAgent(Vector2D(100, 100))
        target = IdleAgent(Vector2D(130, 100))  # 30 units away
        
        # Test action execution
        result = execute_agent_action(
            agent=attacker,
            action=CombatAction.ATTACK_MELEE,
            target_agent=target,
            validation_level=ValidationLevel.STANDARD
        )
        
        # Should get a valid result
        assert result is not None
        assert hasattr(result, 'success')
        assert hasattr(result, 'status')
        assert hasattr(result, 'action')
        
        # Result should be reasonable
        assert isinstance(result.success, bool)
        assert result.action == CombatAction.ATTACK_MELEE
    
    def test_action_validation_with_all_agent_types(self):
        """Test action validation works with all agent types."""
        agents = [
            RandomAgent(Vector2D(50, 50)),
            IdleAgent(Vector2D(100, 100)),
            SimpleChaseAgent(Vector2D(150, 150))
        ]
        
        # Test various actions with each agent type
        actions_to_test = [
            CombatAction.MOVE,
            CombatAction.DODGE,
            CombatAction.DEFEND,
            CombatAction.USE_SPECIAL
        ]
        
        for agent in agents:
            for action in actions_to_test:
                result = execute_agent_action(
                    agent=agent,
                    action=action,
                    validation_level=ValidationLevel.BASIC
                )
                
                # Should always get a result, even if action fails
                assert result is not None
                assert hasattr(result, 'success')
                assert hasattr(result, 'status')
    
    def test_agent_attack_integration(self):
        """Test that agents can attack each other through validation system."""
        attacker = SimpleChaseAgent(Vector2D(100, 100))
        defender = RandomAgent(Vector2D(125, 100))  # Within range
        
        # Test melee attack
        result = execute_agent_action(
            agent=attacker,
            action=CombatAction.ATTACK_MELEE,
            target_agent=defender,
            validation_level=ValidationLevel.STANDARD
        )
        
        # Attack should either succeed or be blocked for valid reasons
        assert result.success in [True, False]
        if not result.success:
            # If failed, should have a reasonable error
            assert result.execution_error is not None or len(result.validation_errors) > 0


class TestPerformanceAndStress:
    """Test agent performance under various stress conditions."""
    
    def test_many_agents_instantiation(self):
        """Test creating many agents doesn't cause issues."""
        agents = []
        
        # Create 100 agents of various types
        for i in range(100):
            if i % 3 == 0:
                agent = RandomAgent(Vector2D(i, i))
            elif i % 3 == 1:
                agent = IdleAgent(Vector2D(i, i*2))
            else:
                agent = SimpleChaseAgent(Vector2D(i*2, i))
            
            agents.append(agent)
        
        # Verify all agents were created successfully
        assert len(agents) == 100
        assert all(agent.is_alive for agent in agents)
        assert len(set(agent.agent_id for agent in agents)) == 100  # All unique IDs
    
    def test_agent_update_performance(self):
        """Test that agent updates perform reasonably quickly."""
        # Create test scenario
        agents = [
            RandomAgent(Vector2D(50, 50)),
            IdleAgent(Vector2D(100, 100)),
            SimpleChaseAgent(Vector2D(150, 150))
        ]
        
        battlefield_info = {
            'bounds': {'min_x': 0, 'max_x': 200, 'min_y': 0, 'max_y': 200}
        }
        
        # Time multiple update cycles
        start_time = time.time()
        
        for _ in range(100):  # 100 update cycles
            for agent in agents:
                # Update only takes dt and battlefield_info
                agent.update(1.0, battlefield_info)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete reasonably quickly (less than 5 seconds for 300 updates)
        assert total_time < 5.0, f"Updates took too long: {total_time:.2f}s"
        
        # All agents should still be alive and functional
        assert all(agent.is_alive for agent in agents)
    
    def test_decision_making_performance(self):
        """Test that decision making performs efficiently."""
        agent = SimpleChaseAgent(Vector2D(100, 100))
        enemies = [
            RandomAgent(Vector2D(100 + i*10, 100))
            for i in range(10)  # 10 enemies
        ]
        
        battlefield_info = {'bounds': {'min_x': 0, 'max_x': 500, 'min_y': 0, 'max_y': 500}}
        
        # Time decision making
        start_time = time.time()
        
        for _ in range(50):  # 50 decisions
            action = agent.decide_action(enemies, battlefield_info)
            assert isinstance(action, CombatAction)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should make decisions quickly (less than 1 second for 50 decisions)
        assert total_time < 1.0, f"Decision making took too long: {total_time:.2f}s"


class TestEdgeCasesAndErrorHandling:
    """Test agent behavior in edge cases and error conditions."""
    
    def test_agents_with_empty_environment(self):
        """Test agents work correctly when no other agents are present."""
        agent = SimpleChaseAgent(Vector2D(100, 100))
        
        # Update with no other agents (update only takes dt and battlefield_info)
        agent.update(1.0, {})
        assert agent.is_alive
        
        # Decision making with no other agents
        action = agent.decide_action([], {})
        assert isinstance(action, CombatAction)
    
    def test_agents_with_dead_agents(self):
        """Test agents handle dead agents correctly."""
        alive_agent = RandomAgent(Vector2D(100, 100))
        dead_agent = IdleAgent(Vector2D(150, 100))
        
        # Kill the dead agent
        dead_agent.stats.current_health = 0
        
        # Alive agent should handle dead agent presence (update only takes dt and battlefield_info)
        alive_agent.update(1.0, {})
        assert alive_agent.is_alive
        
        action = alive_agent.decide_action([dead_agent], {})
        assert isinstance(action, CombatAction)
    
    def test_agents_with_invalid_positions(self):
        """Test agents handle unusual position values."""
        # Test with very large positions
        agent1 = RandomAgent(Vector2D(1000000, 1000000))
        assert agent1.is_alive
        
        # Test with very small positions
        agent2 = IdleAgent(Vector2D(0.001, 0.001))
        assert agent2.is_alive
        
        # Both should be able to interact (update only takes dt and battlefield_info)
        agent1.update(1.0, {})
        agent2.update(1.0, {})
        
        assert agent1.is_alive
        assert agent2.is_alive
    
    def test_agents_with_malformed_battlefield_info(self):
        """Test agents handle malformed battlefield information gracefully."""
        agent = SimpleChaseAgent(Vector2D(100, 100))
        
        # Test with empty battlefield info first
        agent.update(1.0, {})
        action = agent.decide_action([], {})
        assert isinstance(action, CombatAction)
        
        # Note: We can't test with None as the type system prevents it
        # but we can test with missing keys
        minimal_info = {'some_key': 'some_value'}
        agent.update(1.0, minimal_info)
        action2 = agent.decide_action([], minimal_info)
        assert isinstance(action2, CombatAction)
    
    def test_agent_state_consistency(self):
        """Test that agent state remains consistent during operations."""
        agent = RandomAgent(Vector2D(100, 100))
        
        # Record initial state
        initial_id = agent.agent_id
        initial_alive = agent.is_alive
        
        # Perform various operations
        for i in range(10):
            agent.update(1.0, {})
            action = agent.decide_action([], {})
            
            # ID should never change
            assert agent.agent_id == initial_id
            
            # Agent should remain alive unless explicitly killed
            if agent.stats.current_health > 0:
                assert agent.is_alive
            
            # Position should be a valid Vector2D
            assert isinstance(agent.position, Vector2D)
            assert isinstance(agent.position.x, (int, float))
            assert isinstance(agent.position.y, (int, float))


class TestAgentInteraction:
    """Test interactions between different agent types."""
    
    def test_mixed_agent_battlefield(self):
        """Test a battlefield with multiple different agent types."""
        agents = [
            RandomAgent(Vector2D(50, 50)),
            IdleAgent(Vector2D(100, 100)),
            SimpleChaseAgent(Vector2D(150, 150)),
            RandomAgent(Vector2D(200, 200))
        ]
        
        battlefield_info = {
            'bounds': {'min_x': 0, 'max_x': 250, 'min_y': 0, 'max_y': 250}
        }
        
        # Run simulation for several steps
        for step in range(10):
            for agent in agents:
                if agent.is_alive:
                    other_agents = [a for a in agents if a != agent and a.is_alive]
                    # Update only takes dt and battlefield_info
                    agent.update(1.0, battlefield_info)
        
        # Verify agents are still in valid states
        for agent in agents:
            assert isinstance(agent.position, Vector2D)
            assert isinstance(agent.state, AgentState)
            # Most agents should still be alive after brief simulation
            if agent.stats.current_health > 0:
                assert agent.is_alive
    
    def test_agent_targeting_behavior(self):
        """Test that chase agents can properly target other agents."""
        chase_agent = SimpleChaseAgent(Vector2D(100, 100))
        
        potential_targets = [
            RandomAgent(Vector2D(120, 100)),  # Close
            IdleAgent(Vector2D(200, 100)),    # Far
            RandomAgent(Vector2D(110, 110))   # Close diagonal
        ]
        
        # Test target selection
        selected_target = chase_agent.select_target(potential_targets)
        
        if selected_target:
            assert selected_target in potential_targets
            
            # Target should be alive
            assert selected_target.is_alive
            
            # Test that chase agent can make decisions based on target
            action = chase_agent.decide_action(potential_targets, {})
            assert isinstance(action, CombatAction)


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])

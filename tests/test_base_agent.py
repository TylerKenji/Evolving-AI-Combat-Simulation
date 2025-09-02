"""
Tests for the Agent Base Class

This module tests the core functionality of the BaseAgent abstract class,
including combat mechanics, movement, evolution support, and memory systems.
"""

import pytest
import time
from unittest.mock import Mock, patch
from typing import Optional, List, cast

from src.agents.base_agent import (
    BaseAgent, AgentState, AgentRole, CombatAction,
    AgentStats, AgentGenome, AgentMemory
)
from src.agents.agent_state import MovementState, MovementStatus
from src.utils.vector2d import Vector2D


class TestAgentStats:
    """Test AgentStats dataclass."""
    
    def test_default_stats(self):
        """Test default stat values."""
        stats = AgentStats()
        assert stats.max_health == 100.0
        assert stats.current_health == 100.0
        assert stats.speed == 50.0
        assert stats.attack_damage == 20.0
        assert stats.defense == 5.0
        assert stats.accuracy == 0.8
        assert stats.dodge_chance == 0.1
        assert stats.vision_range == 150.0
        assert stats.attack_range == 30.0
        assert stats.attack_cooldown == 1.0
    
    def test_custom_stats(self):
        """Test custom stat initialization."""
        stats = AgentStats(
            max_health=200.0,
            speed=75.0,
            attack_damage=30.0
        )
        assert stats.max_health == 200.0
        assert stats.current_health == 200.0  # Should match max_health by default
        assert stats.speed == 75.0
        assert stats.attack_damage == 30.0


class TestAgentGenome:
    """Test AgentGenome and genetic operations."""
    
    def test_default_genome(self):
        """Test default genome values."""
        genome = AgentGenome()
        assert genome.movement_aggression == 0.5
        assert genome.attack_aggression == 0.5
        assert genome.retreat_threshold == 0.3
        assert genome.mutation_rate == 0.1
        assert genome.mutation_strength == 0.1
    
    def test_genome_mutation(self):
        """Test genome mutation functionality."""
        genome = AgentGenome(movement_aggression=0.5, mutation_rate=1.0)  # Always mutate
        mutated = genome.mutate()
        
        # Should be a new instance
        assert mutated is not genome
        
        # Values should be different (with very high probability)
        # Note: There's a tiny chance this could fail due to randomness
        assert mutated.movement_aggression != genome.movement_aggression
    
    def test_genome_crossover(self):
        """Test genome crossover functionality."""
        parent1 = AgentGenome(movement_aggression=0.2, attack_aggression=0.8)
        parent2 = AgentGenome(movement_aggression=0.8, attack_aggression=0.2)
        
        child = parent1.crossover(parent2)
        
        # Child should be a new instance
        assert child is not parent1 and child is not parent2
        
        # Child values should come from one of the parents
        assert child.movement_aggression in [0.2, 0.8]
        assert child.attack_aggression in [0.2, 0.8]
    
    def test_mutation_bounds(self):
        """Test that mutations stay within valid bounds."""
        genome = AgentGenome(
            movement_aggression=0.0,  # At minimum
            attack_aggression=1.0,    # At maximum
            mutation_rate=1.0,        # Always mutate
            mutation_strength=2.0     # Large mutations
        )
        
        for _ in range(10):  # Test multiple mutations
            mutated = genome.mutate()
            
            # All values should be between 0 and 1
            assert 0.0 <= mutated.movement_aggression <= 1.0
            assert 0.0 <= mutated.attack_aggression <= 1.0
            assert 0.0 <= mutated.retreat_threshold <= 1.0


class TestAgentMemory:
    """Test AgentMemory and fitness calculation."""
    
    def test_default_memory(self):
        """Test default memory values."""
        memory = AgentMemory()
        assert memory.battles_fought == 0
        assert memory.victories == 0
        assert memory.defeats == 0
        assert memory.damage_dealt == 0.0
        assert memory.damage_taken == 0.0
        assert memory.generation == 0
    
    def test_fitness_calculation_no_battles(self):
        """Test fitness calculation with no battle history."""
        memory = AgentMemory()
        fitness = memory.calculate_fitness()
        assert fitness == 0.0
    
    def test_fitness_calculation_with_battles(self):
        """Test fitness calculation with battle history."""
        memory = AgentMemory(
            battles_fought=10,
            victories=7,
            defeats=3,
            damage_dealt=200.0,
            damage_taken=100.0
        )
        
        fitness = memory.calculate_fitness()
        
        # Should be a value between 0 and 1
        assert 0.0 <= fitness <= 1.0
        
        # Should be fairly high given the good stats
        assert fitness > 0.5
    
    def test_fitness_calculation_poor_performance(self):
        """Test fitness calculation with poor performance."""
        memory = AgentMemory(
            battles_fought=10,
            victories=2,
            defeats=8,
            damage_dealt=50.0,
            damage_taken=300.0
        )
        
        fitness = memory.calculate_fitness()
        
        # Should be low but not negative
        assert 0.0 <= fitness <= 1.0
        assert fitness < 0.5


# Create a concrete test implementation of BaseAgent
class ConcreteTestAgent(BaseAgent):
    """Concrete implementation of BaseAgent for testing."""
    
    def update(self, dt: float, battlefield_info: dict) -> None:
        """Test implementation of update method."""
        pass
    
    def decide_action(self, visible_agents: list, battlefield_info: dict) -> CombatAction:
        """Test implementation of decide_action method."""
        return CombatAction.MOVE
    
    def select_target(self, visible_enemies: list) -> Optional[BaseAgent]:
        """Test implementation of select_target method."""
        return visible_enemies[0] if visible_enemies else None
    
    def calculate_movement(self, visible_agents: list, battlefield_info: dict) -> Vector2D:
        """Test implementation of calculate_movement method."""
        return Vector2D(1, 0)


class TestBaseAgent:
    """Test BaseAgent core functionality."""
    
    def test_cannot_instantiate_abstract_base_agent(self):
        """Test that BaseAgent cannot be instantiated directly due to abstract methods."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseAgent()
    
    def test_agent_initialization(self):
        """Test agent initialization with default values."""
        agent = ConcreteTestAgent()
        
        assert agent.agent_id is not None
        assert len(agent.agent_id) > 0
        assert agent.position == Vector2D(0, 0)
        assert agent.state == AgentState.ALIVE
        assert agent.role == AgentRole.BALANCED
        assert agent.is_alive is True
        assert agent.health_percentage == 1.0
    
    def test_agent_initialization_with_params(self):
        """Test agent initialization with custom parameters."""
        position = Vector2D(100, 200)
        stats = AgentStats(max_health=150.0, speed=60.0)
        genome = AgentGenome(movement_aggression=0.8)
        
        agent = ConcreteTestAgent(
            agent_id="test_agent",
            position=position,
            stats=stats,
            genome=genome,
            role=AgentRole.TANK,
            team_id="team1"
        )
        
        assert agent.agent_id == "test_agent"
        assert agent.position == position
        assert agent.stats.max_health == 150.0
        assert agent.stats.speed == 60.0
        assert agent.genome.movement_aggression == 0.8
        assert agent.role == AgentRole.TANK
        assert agent.team_id == "team1"
    
    def test_health_properties(self):
        """Test health-related properties."""
        agent = ConcreteTestAgent()
        
        # Initial state
        assert agent.is_alive is True
        assert agent.health_percentage == 1.0
        
        # After taking damage
        agent.stats.current_health = 50.0
        assert agent.is_alive is True
        assert agent.health_percentage == 0.5
        
        # After dying
        agent.stats.current_health = 0.0
        assert agent.is_alive is False
        assert agent.health_percentage == 0.0
    
    def test_attack_cooldown(self):
        """Test attack cooldown functionality."""
        agent = ConcreteTestAgent()
        
        # Should be able to attack initially
        assert agent.can_attack is True
        
        # After attacking
        agent.last_attack_time = time.time()
        assert agent.can_attack is False
        
        # After cooldown expires
        agent.last_attack_time = time.time() - 2.0  # 2 seconds ago
        assert agent.can_attack is True
    
    def test_take_damage(self):
        """Test damage application."""
        agent = ConcreteTestAgent()
        agent.stats.dodge_chance = 0.0  # Disable dodging for predictable test
        initial_health = agent.stats.current_health
        
        # Apply damage
        died = agent.take_damage(30.0)
        
        assert died is False
        assert agent.stats.current_health < initial_health
        assert agent.memory.damage_taken > 0
        assert agent.is_alive is True
    
    @patch('random.random', return_value=0.5)  # No dodge (above 0.1 dodge chance)
    def test_take_damage_with_defense(self, mock_random):
        """Test damage reduction from defense."""
        agent = ConcreteTestAgent()
        agent.stats.defense = 10.0
        initial_health = agent.stats.current_health
        
        # Apply damage that should be reduced
        agent.take_damage(20.0)  # Should be reduced to 10.0
        
        expected_health = initial_health - 10.0
        assert agent.stats.current_health == expected_health
    
    @patch('random.random', return_value=0.05)  # Always dodge
    def test_take_damage_with_dodge(self, mock_random):
        """Test damage dodging."""
        agent = ConcreteTestAgent()
        agent.stats.dodge_chance = 0.1  # 10% dodge chance
        initial_health = agent.stats.current_health
        
        # Should dodge the attack
        died = agent.take_damage(50.0)
        
        assert died is False
        assert agent.stats.current_health == initial_health  # No damage taken
        assert agent.memory.damage_taken == 0.0
    
    @patch('random.random', return_value=0.5)  # No dodge (above 0.1 dodge chance)
    def test_take_damage_fatal(self, mock_random):
        """Test fatal damage."""
        agent = ConcreteTestAgent()
        
        # Apply massive damage
        died = agent.take_damage(200.0)
        
        assert died is True
        assert agent.stats.current_health <= 0
        assert agent.state == AgentState.DEAD
        assert agent.is_alive is False
    
    @patch('random.random', return_value=0.5)  # Ensure accuracy hits (0.5 < 0.8 accuracy)
    def test_attack_success(self, mock_random):
        """Test successful attack."""
        attacker = ConcreteTestAgent(position=Vector2D(0, 0))
        target = ConcreteTestAgent(position=Vector2D(20, 0))  # Within range
        target.stats.dodge_chance = 0.0  # Disable dodging for predictable test
        
        initial_target_health = target.stats.current_health
        
        # Perform attack
        success = attacker.attack(target)
        
        assert success is True
        assert target.stats.current_health < initial_target_health
        assert attacker.memory.damage_dealt > 0
        assert target.memory.damage_taken > 0
    
    def test_attack_out_of_range(self):
        """Test attack failure due to range."""
        attacker = ConcreteTestAgent(position=Vector2D(0, 0))
        target = ConcreteTestAgent(position=Vector2D(100, 0))  # Out of range
        
        success = attacker.attack(target)
        
        assert success is False
        assert attacker.memory.damage_dealt == 0.0
    
    def test_attack_on_cooldown(self):
        """Test attack failure due to cooldown."""
        attacker = ConcreteTestAgent(position=Vector2D(0, 0))
        target = ConcreteTestAgent(position=Vector2D(20, 0))
        
        # Set recent attack time
        attacker.last_attack_time = time.time()
        
        success = attacker.attack(target)
        
        assert success is False
    
    def test_heal(self):
        """Test healing functionality."""
        agent = ConcreteTestAgent()
        
        # Damage agent first
        agent.stats.current_health = 50.0
        
        # Heal agent
        agent.heal(30.0)
        
        assert agent.stats.current_health == 80.0
    
    def test_heal_over_max(self):
        """Test that healing doesn't exceed max health."""
        agent = ConcreteTestAgent()
        
        # Try to overheal
        agent.heal(50.0)
        
        assert agent.stats.current_health == agent.stats.max_health
    
    def test_get_visible_agents(self):
        """Test visibility detection."""
        agent1 = ConcreteTestAgent(position=Vector2D(0, 0))
        agent2 = ConcreteTestAgent(position=Vector2D(100, 0))  # Within vision range
        agent3 = ConcreteTestAgent(position=Vector2D(200, 0))  # Outside vision range
        
        all_agents = [agent1, agent2, agent3]
        visible = agent1.get_visible_agents(all_agents)
        
        assert agent2 in visible
        assert agent3 not in visible
        assert agent1 not in visible  # Shouldn't see self
    
    def test_get_enemies_and_allies(self):
        """Test enemy and ally detection."""
        agent1 = ConcreteTestAgent(team_id="team1", position=Vector2D(0, 0))
        agent2 = ConcreteTestAgent(team_id="team1", position=Vector2D(50, 0))  # Ally
        agent3 = ConcreteTestAgent(team_id="team2", position=Vector2D(100, 0))  # Enemy
        
        visible_agents = [agent2, agent3]
        
        enemies = agent1.get_enemies(visible_agents)
        allies = agent1.get_allies(visible_agents)
        
        assert agent3 in enemies
        assert agent2 not in enemies
        assert agent2 in allies
        assert agent3 not in allies
    
    def test_movement(self):
        """Test agent movement."""
        agent = ConcreteTestAgent(position=Vector2D(100, 100))
        velocity = Vector2D(10, 0)  # Move right
        
        agent.move(1.0, velocity, (800, 600))  # 1 second, battlefield bounds
        
        assert agent.position.x == 110.0
        assert agent.position.y == 100.0
        assert agent.velocity == velocity
        assert agent.state == AgentState.MOVING
    
    def test_movement_speed_limit(self):
        """Test movement speed limiting."""
        agent = ConcreteTestAgent(position=Vector2D(100, 100))
        agent.stats.speed = 50.0
        
        # Try to move faster than max speed
        fast_velocity = Vector2D(100, 0)  # Faster than agent's speed
        agent.move(1.0, fast_velocity, (800, 600))
        
        # Should have moved at max speed, not requested speed
        expected_distance = 50.0  # max_speed * time
        actual_distance = Vector2D(100, 100).distance_to(agent.position)
        assert abs(actual_distance - expected_distance) < 0.1
    
    def test_movement_boundary_clamping(self):
        """Test that movement respects battlefield boundaries."""
        agent = ConcreteTestAgent(position=Vector2D(790, 590))
        velocity = Vector2D(50, 50)  # Would go out of bounds
        
        agent.move(1.0, velocity, (800, 600))
        
        # Should be clamped to boundaries
        assert agent.position.x <= 800
        assert agent.position.y <= 600
        assert agent.position.x >= 0
        assert agent.position.y >= 0
    
    def test_should_retreat(self):
        """Test retreat decision logic."""
        agent = ConcreteTestAgent()
        agent.genome.retreat_threshold = 0.3  # Retreat at 30% health
        
        # High health - shouldn't retreat
        agent.stats.current_health = 80.0
        assert agent.should_retreat() is False
        
        # Low health - should retreat
        agent.stats.current_health = 20.0
        assert agent.should_retreat() is True
    
    def test_fitness_update(self):
        """Test fitness tracking."""
        agent = ConcreteTestAgent()
        
        # Add some battle data
        agent.memory.battles_fought = 5
        agent.memory.victories = 3
        agent.memory.damage_dealt = 100.0
        agent.memory.damage_taken = 50.0
        
        agent.update_fitness()
        
        assert len(agent.memory.fitness_history) == 1
        assert agent.memory.fitness_history[0] > 0.0
    
    def test_clone(self):
        """Test agent cloning for evolution."""
        original = ConcreteTestAgent(
            agent_id="original",
            position=Vector2D(100, 100),
            role=AgentRole.TANK,
            team_id="team1"
        )
        
        clone = original.clone(mutate=False)
        
        # Should be a new instance
        assert clone is not original
        assert clone.agent_id != original.agent_id
        
        # Should have similar properties
        assert clone.role == original.role
        assert clone.team_id == original.team_id
        assert clone.memory.generation == original.memory.generation + 1
    
    def test_string_representation(self):
        """Test string representation methods."""
        agent = ConcreteTestAgent(agent_id="test123", role=AgentRole.SCOUT, team_id="alpha")
        
        str_repr = str(agent)
        assert "test123"[:8] in str_repr  # ID should be present (possibly truncated)
        assert "scout" in str_repr
        assert "alpha" in str_repr
        
        repr_repr = repr(agent)
        assert repr_repr == str_repr


class TestAdvancedStatusManagement:
    """Test advanced health and status management features."""
    
    def test_status_effect_application(self):
        """Test applying status effects."""
        agent = ConcreteTestAgent()
        
        # Apply a stun effect
        agent.apply_status_effect('stun', duration=2.0, intensity=1.0)
        
        assert agent.has_status_effect('stun')
        assert agent.is_stunned()
        assert agent.state == AgentState.STUNNED
        assert agent.get_status_effect_intensity('stun') == 1.0
    
    def test_status_effect_removal(self):
        """Test removing status effects."""
        agent = ConcreteTestAgent()
        
        # Apply effect then remove it
        agent.apply_status_effect('damage_boost', duration=5.0, intensity=0.8)
        assert agent.has_status_effect('damage_boost')
        
        success = agent.remove_status_effect('damage_boost')
        assert success is True
        assert not agent.has_status_effect('damage_boost')
        
        # Try to remove non-existent effect
        success = agent.remove_status_effect('nonexistent')
        assert success is False
    
    def test_status_effect_expiration(self):
        """Test status effects expiring over time."""
        agent = ConcreteTestAgent()
        
        # Apply short-duration effect
        agent.apply_status_effect('speed_boost', duration=0.1, intensity=1.0)
        assert agent.has_status_effect('speed_boost')
        
        # Update with enough time to expire
        agent.update_status_effects(0.2)
        assert not agent.has_status_effect('speed_boost')
    
    def test_damage_with_shield_effect(self):
        """Test damage reduction from shield status effect."""
        agent = ConcreteTestAgent()
        agent.stats.dodge_chance = 0.0  # Disable dodging for predictable test

        # Apply shield effect
        agent.apply_status_effect('shield', duration=10.0, intensity=1.0)

        initial_health = agent.stats.current_health

        # Take damage with shield active
        agent.take_damage(40.0)

        # Should take reduced damage (after defense, then shield reduction)
        # 40 damage - 5 defense = 35, then 35 * 0.5 (shield) = 17.5 actual damage
        after_defense = 40.0 - agent.stats.defense  # 35.0
        expected_damage = after_defense * 0.5  # 17.5 (50% reduction from shield)
        expected_health = initial_health - expected_damage
        assert agent.stats.current_health == expected_health

    def test_attack_with_damage_boost(self):
        """Test attack damage increased by damage boost status effect."""
        attacker = ConcreteTestAgent(position=Vector2D(0, 0))
        target = ConcreteTestAgent(position=Vector2D(20, 0))
        target.stats.dodge_chance = 0.0  # Disable dodging
        
        # Apply damage boost to attacker
        attacker.apply_status_effect('damage_boost', duration=10.0, intensity=1.0)
        
        with patch('random.random', return_value=0.5), \
             patch('random.uniform', return_value=0.0):  # No damage variance
            
            initial_target_health = target.stats.current_health
            
            # Perform attack
            success = attacker.attack(target)
            
            assert success is True
            
            # Should deal boosted damage (base 20 * 1.5 = 30, then minus 5 defense = 25)
            base_damage = attacker.stats.attack_damage  # 20
            boosted_damage = base_damage * 1.5  # 30 (50% boost)
            actual_damage = boosted_damage - target.stats.defense  # 30 - 5 = 25
            expected_health = initial_target_health - actual_damage
            assert target.stats.current_health == expected_health
    
    def test_combat_statistics_tracking(self):
        """Test combat statistics are properly tracked."""
        agent = ConcreteTestAgent()
        
        # Test attack statistics
        agent.update_combat_statistics('attack', success=True)
        agent.update_combat_statistics('attack', success=False)
        
        assert agent.combat_state.attacks_attempted == 2
        assert agent.combat_state.attacks_hit == 1
        assert agent.combat_state.get_accuracy_rate() == 0.5
        
        # Test dodge statistics
        agent.update_combat_statistics('dodge', success=True)
        agent.update_combat_statistics('dodge', success=False)
        
        assert agent.combat_state.dodges_attempted == 2
        assert agent.combat_state.dodges_successful == 1
        assert agent.combat_state.get_dodge_rate() == 0.5
    
    def test_stun_prevents_actions(self):
        """Test that stunned agents cannot attack."""
        attacker = ConcreteTestAgent(position=Vector2D(0, 0))
        target = ConcreteTestAgent(position=Vector2D(20, 0))
        
        # Stun the attacker
        attacker.apply_status_effect('stun', duration=5.0, intensity=1.0)
        
        # Try to attack while stunned
        success = attacker.attack(target)
        
        assert success is False
        assert attacker.is_stunned()
        assert not attacker.can_attack
    
    def test_advanced_status_system_integration(self):
        """Test integration of advanced status system with existing functionality."""
        agent = ConcreteTestAgent()
        
        # Verify advanced status components are initialized
        assert agent.combat_state is not None
        assert agent.movement_state is not None
        assert agent.sensor_data is not None
        assert isinstance(agent.status_effects, dict)
        assert isinstance(agent.status_timers, dict)
        
        # Test status effects dictionary tracking
        active_effects = agent.get_active_status_effects()
        assert isinstance(active_effects, dict)
        assert len(active_effects) == 0
        
        # Add effect and verify tracking
        agent.apply_status_effect('test_effect', duration=1.0, intensity=0.5)
        active_effects = agent.get_active_status_effects()
        assert len(active_effects) == 1
        assert 'test_effect' in active_effects
        assert active_effects['test_effect'][0] == 0.5  # intensity
        assert active_effects['test_effect'][1] <= 1.0  # remaining time


class TestAdvancedMovementMechanics:
    """Test suite for advanced movement mechanics."""
    
    def test_movement_with_speed_boost(self):
        """Test movement with speed boost status effect."""
        agent = ConcreteTestAgent(position=Vector2D(100, 100))
        base_speed = agent.stats.speed
        
        # Apply speed boost
        agent.apply_status_effect('speed_boost', duration=10.0, intensity=1.0)
        
        # Move with speed boost
        velocity = Vector2D(base_speed, 0)  # Full speed
        agent.move(1.0, velocity, (800, 600))
        
        # Should have moved faster than normal
        distance_moved = Vector2D(100, 100).distance_to(agent.position)
        expected_boosted_distance = base_speed * 1.5  # 50% boost
        assert abs(distance_moved - expected_boosted_distance) < 0.1
    
    def test_movement_with_stun(self):
        """Test that stunned agents cannot move."""
        agent = ConcreteTestAgent(position=Vector2D(100, 100))
        
        # Apply stun effect
        agent.apply_status_effect('stun', duration=5.0, intensity=1.0)
        
        # Try to move while stunned
        velocity = Vector2D(50, 0)
        initial_position = Vector2D(agent.position.x, agent.position.y)
        agent.move(1.0, velocity, (800, 600))
        
        # Should not have moved
        assert agent.position.x == initial_position.x
        assert agent.position.y == initial_position.y
    
    def test_seek_behavior(self):
        """Test seeking behavior toward a target."""
        agent = ConcreteTestAgent(position=Vector2D(100, 100))
        agent.velocity = Vector2D(0, 0)  # Start stationary
        
        target = Vector2D(200, 100)  # Target to the right
        steering_force = agent.seek(target)
        
        # Should produce rightward force
        assert steering_force.x > 0
        assert abs(steering_force.y) < 0.1  # Minimal Y component
        
        # Force should be reasonable magnitude
        assert 0 < steering_force.magnitude() <= agent.stats.speed
    
    def test_flee_behavior(self):
        """Test fleeing behavior from a threat."""
        agent = ConcreteTestAgent(position=Vector2D(100, 100))
        agent.velocity = Vector2D(0, 0)  # Start stationary
        
        threat = Vector2D(50, 100)  # Threat to the left
        steering_force = agent.flee(threat)
        
        # Should produce rightward force (away from threat)
        assert steering_force.x > 0
        assert abs(steering_force.y) < 0.1  # Minimal Y component
    
    def test_wander_behavior(self):
        """Test wandering behavior produces valid movement."""
        agent = ConcreteTestAgent(position=Vector2D(100, 100))
        
        # Test multiple wander calls
        for _ in range(10):
            wander_force = agent.wander()
            # Should produce some movement force
            assert isinstance(wander_force, Vector2D)
            # Force should be reasonable
            assert wander_force.magnitude() <= agent.stats.speed
    
    def test_obstacle_avoidance(self):
        """Test obstacle avoidance behavior."""
        agent = ConcreteTestAgent(position=Vector2D(100, 100))
        
        # Place obstacle nearby
        obstacles = [Vector2D(120, 100)]  # Obstacle to the right
        avoidance_force = agent.avoid_obstacles(obstacles, avoidance_radius=50.0)
        
        # Should produce leftward force (away from obstacle)
        assert avoidance_force.x < 0
        assert avoidance_force.magnitude() > 0
    
    def test_path_following(self):
        """Test path following behavior."""
        agent = ConcreteTestAgent(position=Vector2D(100, 100))
        
        # Create a simple path
        path = [Vector2D(150, 100), Vector2D(200, 150), Vector2D(250, 100)]
        
        # Test following path
        steering_force = agent.follow_path(path, path_radius=10.0)
        
        # Should produce force toward first waypoint
        assert steering_force.x > 0  # Moving right toward first waypoint
        assert steering_force.magnitude() > 0
        
        # Verify path was stored in movement state
        assert agent.movement_state.path == path
    
    def test_movement_target_system(self):
        """Test movement target setting and tracking."""
        agent = ConcreteTestAgent(position=Vector2D(100, 100))
        
        # Set a movement target
        target = Vector2D(200, 150)
        agent.set_movement_target(target)
        
        # Verify target was set
        assert agent.movement_state.target_position == target
        assert agent.movement_state.status == MovementStatus.MOVING
        assert not agent.is_near_target(tolerance=10.0)
        
        # Clear target
        agent.clear_movement_target()
        assert agent.movement_state.target_position is None
        assert agent.is_near_target()  # Should return True when no target
    
    def test_agent_separation(self):
        """Test separation behavior with other agents."""
        agent1 = ConcreteTestAgent(position=Vector2D(100, 100))
        agent2 = ConcreteTestAgent(position=Vector2D(110, 100))  # Very close
        agent3 = ConcreteTestAgent(position=Vector2D(200, 100))  # Far away
        
        nearby_agents = cast(List[BaseAgent], [agent2, agent3])
        separation_force = agent1.calculate_separation(nearby_agents, separation_radius=30.0)
        
        # Should produce leftward force (away from agent2)
        assert separation_force.x < 0
        assert separation_force.magnitude() > 0
    
    def test_agent_alignment(self):
        """Test alignment behavior with other agents."""
        agent1 = ConcreteTestAgent(position=Vector2D(100, 100))
        agent1.velocity = Vector2D(0, 0)
        
        agent2 = ConcreteTestAgent(position=Vector2D(120, 100))
        agent2.velocity = Vector2D(20, 10)  # Moving right and up
        
        nearby_agents = cast(List[BaseAgent], [agent2])
        alignment_force = agent1.calculate_alignment(nearby_agents, alignment_radius=50.0)
        
        # Should align with agent2's velocity
        assert alignment_force.x > 0  # Rightward
        assert alignment_force.y > 0  # Upward
    
    def test_agent_cohesion(self):
        """Test cohesion behavior with other agents."""
        agent1 = ConcreteTestAgent(position=Vector2D(100, 100))
        agent2 = ConcreteTestAgent(position=Vector2D(150, 100))
        agent3 = ConcreteTestAgent(position=Vector2D(130, 120))
        
        nearby_agents = cast(List[BaseAgent], [agent2, agent3])
        cohesion_force = agent1.calculate_cohesion(nearby_agents, cohesion_radius=100.0)
        
        # Should move toward center of mass of nearby agents
        assert cohesion_force.x > 0  # Rightward toward center
        assert cohesion_force.magnitude() > 0
    
    def test_movement_state_updates(self):
        """Test movement state tracking and updates."""
        agent = ConcreteTestAgent(position=Vector2D(100, 100))
        
        # Set target and move
        target = Vector2D(200, 100)
        agent.set_movement_target(target)
        
        # Simulate movement
        agent.move(1.0, Vector2D(20, 0), (800, 600))
        agent.update_movement_state(1.0)
        
        # Verify movement tracking
        assert agent.movement_state.total_distance_moved > 0
        assert agent.movement_state.current_velocity.magnitude() > 0
        assert agent.movement_state.movement_efficiency > 0
        
        # Test stuck detection
        for _ in range(5):
            agent.update_movement_state(1.0)
        # Should detect stuck if not moving toward target
        assert agent.movement_state.stuck_counter >= 0

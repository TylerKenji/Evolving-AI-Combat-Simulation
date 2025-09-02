"""
Test serialization functionality for Task 1.4.5.
"""

import pytest
import json
import tempfile
import os
from typing import Dict, Any, Sequence, Optional

from src.agents.base_agent import BaseAgent, AgentRole, CombatAction, AgentStats, AgentGenome, AgentMemory
from src.utils.vector2d import Vector2D


class ConcreteTestAgent(BaseAgent):
    """Concrete implementation for testing serialization."""
    
    def update(self, dt: float, battlefield_info: Dict[str, Any]) -> None:
        pass
    
    def decide_action(self, visible_agents: Sequence['BaseAgent'], 
                     battlefield_info: Dict[str, Any]) -> CombatAction:
        return CombatAction.MOVE
    
    def select_target(self, visible_enemies: Sequence['BaseAgent']) -> Optional['BaseAgent']:
        return visible_enemies[0] if visible_enemies else None
    
    def calculate_movement(self, visible_agents: Sequence['BaseAgent'], 
                         battlefield_info: Dict[str, Any]) -> Vector2D:
        return Vector2D(1, 0)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConcreteTestAgent':
        """Override to create concrete agent instance."""
        # Create the agent with basic parameters
        position_data = data['position']
        position = Vector2D(position_data['x'], position_data['y'])
        
        role = AgentRole(data['role'])
        team_id = data.get('team_id')
        agent_id = data['agent_id']
        
        # Create stats
        stats_data = data['stats']
        stats = AgentStats(
            max_health=stats_data['max_health'],
            current_health=stats_data['current_health'],
            speed=stats_data['speed'],
            attack_damage=stats_data['attack_damage'],
            attack_range=stats_data['attack_range'],
            attack_cooldown=stats_data['attack_cooldown'],
            defense=stats_data['defense'],
            vision_range=stats_data['vision_range'],
            dodge_chance=stats_data['dodge_chance'],
            accuracy=stats_data['accuracy']
        )
        
        # Create genome
        genome_data = data['genome']
        genome = AgentGenome(
            movement_aggression=genome_data['movement_aggression'],
            movement_cooperation=genome_data['movement_cooperation'],
            positioning_preference=genome_data['positioning_preference'],
            attack_aggression=genome_data['attack_aggression'],
            defense_priority=genome_data['defense_priority'],
            target_selection=genome_data['target_selection'],
            dodge_tendency=genome_data['dodge_tendency'],
            retreat_threshold=genome_data['retreat_threshold'],
            cooperation_willingness=genome_data['cooperation_willingness'],
            risk_tolerance=genome_data['risk_tolerance'],
            mutation_rate=genome_data['mutation_rate'],
            mutation_strength=genome_data['mutation_strength'],
            weapon_preferences=genome_data['weapon_preferences']
        )
        
        # Create agent instance
        agent = cls(
            agent_id=agent_id,
            position=position,
            stats=stats,
            genome=genome,
            role=role,
            team_id=team_id
        )
        
        # Restore additional state
        velocity_data = data['velocity']
        agent.velocity = Vector2D(velocity_data['x'], velocity_data['y'])
        
        facing_data = data['facing_direction']
        agent.facing_direction = Vector2D(facing_data['x'], facing_data['y'])
        
        agent.last_attack_time = data['last_attack_time']
        agent.is_defending = data['is_defending']
        
        # Restore memory
        memory_data = data['memory']
        agent.memory.battles_fought = memory_data['battles_fought']
        agent.memory.victories = memory_data['victories']
        agent.memory.defeats = memory_data['defeats']
        agent.memory.damage_dealt = memory_data['damage_dealt']
        agent.memory.damage_taken = memory_data['damage_taken']
        agent.memory.generation = memory_data['generation']
        agent.memory.enemy_encounters = memory_data['enemy_encounters']
        agent.memory.successful_strategies = memory_data['successful_strategies']
        agent.memory.failed_strategies = memory_data['failed_strategies']
        agent.memory.fitness_history = memory_data['fitness_history']
        
        # Restore status effects
        for effect_name, effect_data in data['status_effects'].items():
            agent.status_effects[effect_name] = effect_data['intensity']
            agent.status_timers[effect_name] = effect_data['remaining_time']
        
        return agent


class TestAgentSerialization:
    """Test suite for agent serialization functionality."""
    
    def test_to_dict_basic(self):
        """Test basic serialization to dictionary."""
        agent = ConcreteTestAgent(
            agent_id="test_agent_123",
            position=Vector2D(100, 50),
            role=AgentRole.SCOUT,
            team_id="alpha"
        )
        
        agent_dict = agent.to_dict()
        
        # Verify basic fields
        assert agent_dict['agent_id'] == "test_agent_123"
        assert agent_dict['position']['x'] == 100
        assert agent_dict['position']['y'] == 50
        assert agent_dict['role'] == "scout"
        assert agent_dict['team_id'] == "alpha"
        assert 'timestamp' in agent_dict
        
        # Verify complex structures
        assert 'stats' in agent_dict
        assert 'genome' in agent_dict
        assert 'memory' in agent_dict
        assert 'combat_state' in agent_dict
        assert 'movement_state' in agent_dict
        assert 'status_effects' in agent_dict
    
    def test_serialization_roundtrip(self):
        """Test full serialization and deserialization roundtrip."""
        # Create agent with custom properties
        original = ConcreteTestAgent(
            agent_id="roundtrip_test",
            position=Vector2D(200, 150),
            role=AgentRole.DPS,
            team_id="beta"
        )
        
        # Modify some state
        original.velocity = Vector2D(10, -5)
        original.facing_direction = Vector2D(0.7, 0.7)
        original.last_attack_time = 123.45
        original.is_defending = True
        original.memory.battles_fought = 5
        original.memory.victories = 3
        original.memory.defeats = 2
        original.apply_status_effect("speed_boost", duration=10.0, intensity=1.5)
        
        # Serialize to dict
        agent_dict = original.to_dict()
        
        # Deserialize back
        restored = ConcreteTestAgent.from_dict(agent_dict)
        
        # Verify basic properties
        assert restored.agent_id == original.agent_id
        assert restored.position.x == original.position.x
        assert restored.position.y == original.position.y
        assert restored.role == original.role
        assert restored.team_id == original.team_id
        
        # Verify state
        assert restored.velocity.x == original.velocity.x
        assert restored.velocity.y == original.velocity.y
        assert restored.facing_direction.x == original.facing_direction.x
        assert restored.facing_direction.y == original.facing_direction.y
        assert restored.last_attack_time == original.last_attack_time
        assert restored.is_defending == original.is_defending
        
        # Verify memory
        assert restored.memory.battles_fought == original.memory.battles_fought
        assert restored.memory.victories == original.memory.victories
        assert restored.memory.defeats == original.memory.defeats
        
        # Verify status effects
        assert "speed_boost" in restored.status_effects
        assert restored.status_effects["speed_boost"] == 1.5  # intensity
        assert "speed_boost" in restored.status_timers
    
    def test_save_and_load_file(self):
        """Test saving to and loading from file."""
        agent = ConcreteTestAgent(
            agent_id="file_test",
            position=Vector2D(300, 200),
            role=AgentRole.TANK,
            team_id="gamma"
        )
        
        # Modify agent state
        agent.stats.current_health = 75.0
        agent.memory.damage_dealt = 150.0
        agent.apply_status_effect("shield", duration=5.0, intensity=0.8)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = os.path.join(temp_dir, "test_agent.json")
            
            # Save to file
            agent.save_to_file(filepath)
            assert os.path.exists(filepath)
            
            # Load from file
            loaded_agent = ConcreteTestAgent.load_from_file(filepath)
            
            # Verify loaded agent
            assert loaded_agent.agent_id == agent.agent_id
            assert loaded_agent.position.x == agent.position.x
            assert loaded_agent.position.y == agent.position.y
            assert loaded_agent.stats.current_health == 75.0
            assert loaded_agent.memory.damage_dealt == 150.0
            assert "shield" in loaded_agent.status_effects
    
    def test_json_serializable(self):
        """Test that serialized data is valid JSON."""
        agent = ConcreteTestAgent(
            position=Vector2D(50, 75),
            role=AgentRole.SUPPORT
        )
        
        agent_dict = agent.to_dict()
        
        # Should be able to convert to JSON and back
        json_str = json.dumps(agent_dict)
        loaded_dict = json.loads(json_str)
        
        # Basic verification
        assert loaded_dict['position']['x'] == 50
        assert loaded_dict['position']['y'] == 75
        assert loaded_dict['role'] == "support"
    
    def test_base_agent_from_dict_raises_error(self):
        """Test that BaseAgent.from_dict raises NotImplementedError."""
        agent = ConcreteTestAgent()
        agent_dict = agent.to_dict()
        
        with pytest.raises(NotImplementedError):
            BaseAgent.from_dict(agent_dict)
    
    def test_serialization_with_complex_genome(self):
        """Test serialization with complex genome data."""
        # Create custom genome
        genome = AgentGenome(
            movement_aggression=0.8,
            attack_aggression=0.6,
            risk_tolerance=0.9,
            retreat_threshold=0.2,
            weapon_preferences={"sword": 0.7, "bow": 0.3}
        )
        
        agent = ConcreteTestAgent(
            position=Vector2D(0, 0),
            genome=genome,
            role=AgentRole.BALANCED
        )
        
        agent_dict = agent.to_dict()
        restored = ConcreteTestAgent.from_dict(agent_dict)
        
        # Verify genome properties
        assert restored.genome.movement_aggression == 0.8
        assert restored.genome.attack_aggression == 0.6
        assert restored.genome.risk_tolerance == 0.9
        assert restored.genome.retreat_threshold == 0.2
        assert restored.genome.weapon_preferences == {"sword": 0.7, "bow": 0.3}


if __name__ == "__main__":
    # Run basic tests
    test_suite = TestAgentSerialization()
    
    print("=== Task 1.4.5: Agent State Serialization Test ===")
    
    try:
        test_suite.test_to_dict_basic()
        print("✅ Basic to_dict serialization")
        
        test_suite.test_serialization_roundtrip()
        print("✅ Full serialization roundtrip")
        
        test_suite.test_save_and_load_file()
        print("✅ File save/load operations")
        
        test_suite.test_json_serializable()
        print("✅ JSON serialization compatibility")
        
        test_suite.test_base_agent_from_dict_raises_error()
        print("✅ BaseAgent.from_dict error handling")
        
        test_suite.test_serialization_with_complex_genome()
        print("✅ Complex genome serialization")
        
        print("\n🎉 Task 1.4.5 'Add agent state serialization/deserialization' is COMPLETE! ✅")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise

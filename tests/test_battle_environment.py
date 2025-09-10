"""
Test Suite for BattleEnvironment Class

This module provides comprehensive tests for the BattleEnvironment implementation,
validating all core functionality including team management, agent spawning,
collision detection, spatial partitioning, and battle management.

Test Coverage:
- Environment initialization and configuration
- Team creation and management
- Agent spawning with different strategies
- Spatial partitioning optimization
- Collision detection and handling
- Battle lifecycle management
- Battlefield information system
- Performance characteristics
"""

import pytest
import time
from typing import List, Dict, Any

from src.environment.battle_environment import (
    BattleEnvironment, SpawnStrategy, BattlePhase, TeamInfo
)
from src.agents.random_agent import RandomAgent
from src.agents.idle_agent import IdleAgent
from src.agents.simple_chase_agent import SimpleChaseAgent
from src.utils.vector2d import Vector2D


class TestBattleEnvironmentInitialization:
    """Test battle environment initialization and configuration."""
    
    def test_default_initialization(self):
        """Test environment initialization with default settings."""
        env = BattleEnvironment()
        
        assert env.width == 1000.0
        assert env.height == 800.0
        assert env.battle_phase == BattlePhase.PREPARATION
        assert env.collision_radius == 12.0
        assert env.spawn_strategy == SpawnStrategy.TEAMS_OPPOSITE
        assert env.spatial_grid_enabled == True
        assert len(env.teams) == 0
        assert len(env.agents) == 0
        
    def test_custom_configuration(self):
        """Test environment initialization with custom configuration."""
        config = {
            'collision_radius': 15.0,
            'spawn_strategy': 'circle',
            'spatial_partitioning': False,
            'max_teams': 4,
            'friendly_fire': True,
            'vision_range': 300.0
        }
        
        env = BattleEnvironment(width=1200, height=900, config=config)
        
        assert env.width == 1200.0
        assert env.height == 900.0
        assert env.collision_radius == 15.0
        assert env.spawn_strategy == SpawnStrategy.CIRCLE
        assert env.spatial_grid_enabled == False
        assert env.config['max_teams'] == 4
        assert env.friendly_fire == True
        assert env.vision_range == 300.0
    
    def test_spawn_points_initialization(self):
        """Test that spawn points are properly initialized."""
        env = BattleEnvironment()
        
        assert len(env.agent_spawn_points) > 0
        # Should have 8x8 grid = 64 spawn points
        assert len(env.agent_spawn_points) == 64
        
        # Spawn points should be within bounds with margin
        for point in env.agent_spawn_points:
            assert env.spawn_margin <= point.x <= env.width - env.spawn_margin
            assert env.spawn_margin <= point.y <= env.height - env.spawn_margin


class TestTeamManagement:
    """Test team creation and management functionality."""
    
    def test_create_team(self):
        """Test basic team creation."""
        env = BattleEnvironment()
        
        success = env.create_team("team1", "Red Team", "#FF0000")
        assert success == True
        assert "team1" in env.teams
        assert env.teams["team1"].name == "Red Team"
        assert env.teams["team1"].color == "#FF0000"
        assert env.teams["team1"].agent_count == 0
    
    def test_duplicate_team_creation(self):
        """Test that duplicate team IDs are rejected."""
        env = BattleEnvironment()
        
        env.create_team("team1", "Red Team")
        success = env.create_team("team1", "Blue Team")
        
        assert success == False
        assert len(env.teams) == 1
    
    def test_team_spawn_area_assignment(self):
        """Test that teams are assigned appropriate spawn areas."""
        env = BattleEnvironment()
        
        env.create_team("team1", "Red Team")
        env.create_team("team2", "Blue Team")
        
        team1 = env.teams["team1"]
        team2 = env.teams["team2"]
        
        # Teams should have spawn areas
        assert team1.spawn_area is not None
        assert team2.spawn_area is not None
        
        # Spawn areas should not overlap (opposite sides)
        min1, max1 = team1.spawn_area
        min2, max2 = team2.spawn_area
        
        # Team 1 should be on left side, Team 2 on right side
        assert max1.x <= env.width * 0.5  # Team 1 on left
        assert min2.x >= env.width * 0.5  # Team 2 on right
    
    def test_maximum_teams_limit(self):
        """Test that maximum team limit is enforced."""
        config = {'max_teams': 2}
        env = BattleEnvironment(config=config)
        
        env.create_team("team1")
        env.create_team("team2")
        success = env.create_team("team3")
        
        assert success == False
        assert len(env.teams) == 2


class TestAgentSpawning:
    """Test agent spawning with different strategies and team assignments."""
    
    def test_basic_agent_spawning(self):
        """Test basic agent spawning without teams."""
        env = BattleEnvironment()
        agent = RandomAgent(position=Vector2D(100, 100))
        
        success = env.add_agent(agent)
        
        assert success == True
        assert agent.agent_id in env.agents
        assert agent.position.x <= env.width
        assert agent.position.y <= env.height
        assert env.agent_count == 1
    
    def test_team_based_spawning(self):
        """Test agent spawning with team assignment."""
        env = BattleEnvironment()
        env.create_team("team1", "Red Team")
        
        agent = RandomAgent(position=Vector2D(100, 100))
        success = env.add_agent(agent, team_id="team1")
        
        assert success == True
        assert env.get_agent_team(agent.agent_id) == "team1"
        assert agent.agent_id in env.teams["team1"].agent_ids
        assert env.teams["team1"].agent_count == 1
    
    def test_team_spawn_area_usage(self):
        """Test that agents spawn within their team's area."""
        env = BattleEnvironment()
        env.create_team("team1", "Red Team")
        
        # Spawn multiple agents to test consistency
        for i in range(5):
            agent = RandomAgent(position=Vector2D(0, 0))  # Will be overridden
            env.add_agent(agent, team_id="team1")
            
            # Agent should spawn within team's spawn area
            spawn_area = env.teams["team1"].spawn_area
            if spawn_area is not None:
                min_pos, max_pos = spawn_area
                assert min_pos.x <= agent.position.x <= max_pos.x
                assert min_pos.y <= agent.position.y <= max_pos.y
    
    def test_different_spawn_strategies(self):
        """Test different spawn strategies."""
        # Test CIRCLE strategy
        config = {'spawn_strategy': 'circle'}
        env = BattleEnvironment(config=config)
        
        agent = RandomAgent(position=Vector2D(0, 0))
        env.add_agent(agent)
        
        # Agent should be spawned within reasonable distance of center
        center = env.center
        distance = agent.position.distance_to(center)
        assert distance <= min(env.width, env.height) * 0.4
    
    def test_maximum_agent_limit(self):
        """Test that maximum agent limit is enforced."""
        config = {'max_agents': 2}
        env = BattleEnvironment(config=config)
        
        agent1 = RandomAgent(position=Vector2D(100, 100))
        agent2 = IdleAgent(position=Vector2D(200, 200))
        agent3 = SimpleChaseAgent(position=Vector2D(300, 300))
        
        assert env.add_agent(agent1) == True
        assert env.add_agent(agent2) == True
        assert env.add_agent(agent3) == False  # Should fail due to limit


class TestSpatialPartitioning:
    """Test spatial partitioning optimization system."""
    
    def test_spatial_grid_operations(self):
        """Test spatial grid add/remove operations."""
        env = BattleEnvironment()
        agent = RandomAgent(position=Vector2D(100, 100))
        
        env.add_agent(agent)
        
        # Agent should be in spatial grid
        cell = env._get_grid_cell(agent.position)
        assert agent.agent_id in env.spatial_grid[cell]
        
        # Remove agent
        env.remove_agent(agent.agent_id)
        
        # Agent should be removed from spatial grid
        assert agent.agent_id not in env.spatial_grid[cell]
    
    def test_nearby_agent_search(self):
        """Test efficient nearby agent search using spatial partitioning."""
        env = BattleEnvironment()
        
        # Add agents at known positions
        agents = []
        positions = [
            Vector2D(100, 100),
            Vector2D(120, 110),  # Close to first
            Vector2D(500, 500),  # Far from first
            Vector2D(105, 95),   # Close to first
        ]
        
        for i, pos in enumerate(positions):
            agent = RandomAgent(position=pos)
            env.add_agent(agent)
            agents.append(agent)
        
        # Search for agents near first position
        nearby = env.get_nearby_agents(Vector2D(100, 100), radius=30)
        
        # Should find agents 0, 1, and 3 (not 2 which is far away)
        nearby_ids = {agent.agent_id for agent in nearby}
        assert agents[0].agent_id in nearby_ids
        assert agents[1].agent_id in nearby_ids
        assert agents[3].agent_id in nearby_ids
        assert agents[2].agent_id not in nearby_ids
    
    def test_spatial_grid_updates(self):
        """Test that spatial grid is updated when agents move."""
        env = BattleEnvironment()
        agent = RandomAgent(position=Vector2D(100, 100))
        env.add_agent(agent)
        
        old_cell = env._get_grid_cell(agent.position)
        
        # Move agent to different grid cell
        agent.position = Vector2D(300, 300)
        env._update_agent_spatial_grid(agent.agent_id, Vector2D(100, 100), agent.position)
        
        new_cell = env._get_grid_cell(agent.position)
        
        # Agent should be removed from old cell and added to new cell
        assert agent.agent_id not in env.spatial_grid[old_cell]
        assert agent.agent_id in env.spatial_grid[new_cell]


class TestCollisionDetection:
    """Test collision detection and handling."""
    
    def test_agent_collision_detection(self):
        """Test that agent collisions are properly detected."""
        env = BattleEnvironment()
        
        # Create two agents close enough to collide
        agent1 = RandomAgent(position=Vector2D(100, 100))
        agent2 = IdleAgent(position=Vector2D(105, 105))  # Within collision radius
        
        env.add_agent(agent1)
        env.add_agent(agent2)
        
        collisions = env.check_collisions()
        
        assert len(collisions) == 1
        assert collisions[0].primary_object in [agent1, agent2]
        assert collisions[0].secondary_object in [agent1, agent2]
    
    def test_collision_handling(self):
        """Test that collisions are properly handled."""
        env = BattleEnvironment()
        
        # Create two agents at exactly the same position
        agent1 = RandomAgent(position=Vector2D(100, 100))
        agent2 = IdleAgent(position=Vector2D(100, 100))
        
        env.add_agent(agent1)
        env.add_agent(agent2)
        
        original_distance = agent1.position.distance_to(agent2.position)
        
        # Run collision detection and handling
        collisions = env.check_collisions()
        for collision in collisions:
            env._handle_collision(collision)
        
        new_distance = agent1.position.distance_to(agent2.position)
        
        # Agents should be pushed apart
        assert new_distance > original_distance
        assert new_distance >= env.collision_radius
    
    def test_no_collision_when_far_apart(self):
        """Test that distant agents don't generate collisions."""
        env = BattleEnvironment()
        
        agent1 = RandomAgent(position=Vector2D(100, 100))
        agent2 = IdleAgent(position=Vector2D(500, 500))
        
        env.add_agent(agent1)
        env.add_agent(agent2)
        
        collisions = env.check_collisions()
        
        assert len(collisions) == 0


class TestBattleManagement:
    """Test battle lifecycle and management functionality."""
    
    def test_battle_lifecycle(self):
        """Test complete battle lifecycle."""
        env = BattleEnvironment()
        
        # Initial state
        assert env.battle_phase == BattlePhase.PREPARATION
        
        # Start battle
        env.start_battle()
        assert env.battle_phase == BattlePhase.ACTIVE_COMBAT
        assert env.is_running == True
        
        # End battle
        env.end_battle()
        assert env.battle_phase == BattlePhase.COMPLETED
        assert env.is_running == False
    
    def test_battle_end_conditions(self):
        """Test automatic battle end when only one team remains."""
        env = BattleEnvironment()
        
        env.create_team("team1")
        env.create_team("team2")
        
        agent1 = RandomAgent(position=Vector2D(100, 100))
        agent2 = IdleAgent(position=Vector2D(200, 200))
        
        env.add_agent(agent1, team_id="team1")
        env.add_agent(agent2, team_id="team2")
        
        env.start_battle()
        
        # Remove one team's agents
        env.remove_agent(agent2.agent_id)
        
        # Check battle end conditions
        env._check_battle_end_conditions()
        
        assert env.battle_phase == BattlePhase.COMPLETED
    
    def test_battle_statistics(self):
        """Test battle statistics collection."""
        env = BattleEnvironment()
        env.create_team("team1", "Red Team")
        
        agent = RandomAgent(position=Vector2D(100, 100))
        env.add_agent(agent, team_id="team1")
        
        stats = env.get_battle_statistics()
        
        assert 'battle_phase' in stats
        assert 'total_agents' in stats
        assert 'teams' in stats
        assert 'environment_metrics' in stats
        assert stats['total_agents'] == 1
        assert 'team1' in stats['teams']


class TestBattlefieldInformation:
    """Test battlefield information system for agents."""
    
    def test_battlefield_info_generation(self):
        """Test that battlefield info is properly generated for agents."""
        env = BattleEnvironment()
        env.create_team("team1")
        env.create_team("team2")
        
        agent1 = RandomAgent(position=Vector2D(100, 100))
        agent2 = IdleAgent(position=Vector2D(150, 150))
        
        env.add_agent(agent1, team_id="team1")
        env.add_agent(agent2, team_id="team2")
        
        battlefield_info = env.get_battlefield_info(agent1.agent_id)
        
        assert 'environment_bounds' in battlefield_info
        assert 'agent_position' in battlefield_info
        assert 'agent_team' in battlefield_info
        assert 'visible_agents' in battlefield_info
        assert 'battle_phase' in battlefield_info
        
        assert battlefield_info['agent_team'] == "team1"
        assert len(battlefield_info['visible_agents']) == 1  # Should see agent2
    
    def test_vision_range_limits(self):
        """Test that vision range properly limits visible agents."""
        config = {'vision_range': 100.0}
        env = BattleEnvironment(config=config)
        
        agent1 = RandomAgent(position=Vector2D(100, 100))
        agent2 = IdleAgent(position=Vector2D(150, 150))  # Within range
        agent3 = SimpleChaseAgent(position=Vector2D(300, 300))  # Outside range
        
        env.add_agent(agent1)
        env.add_agent(agent2)
        env.add_agent(agent3)
        
        battlefield_info = env.get_battlefield_info(agent1.agent_id)
        visible_agents = battlefield_info['visible_agents']
        
        # Should only see agent2 (within range), not agent3 (too far)
        visible_ids = {agent['agent_id'] for agent in visible_agents}
        assert agent2.agent_id in visible_ids
        assert agent3.agent_id not in visible_ids


class TestEnvironmentUpdates:
    """Test environment update cycle and agent management."""
    
    def test_environment_update_cycle(self):
        """Test that environment updates work correctly."""
        env = BattleEnvironment()
        
        agent1 = RandomAgent(position=Vector2D(100, 100))
        agent2 = IdleAgent(position=Vector2D(200, 200))
        
        env.add_agent(agent1)
        env.add_agent(agent2)
        env.start()
        
        # Run several update cycles
        for _ in range(5):
            env.update(0.016)  # ~60 FPS
        
        # Environment should have updated metrics
        assert env.metrics.frame_count == 5
        assert env.metrics.simulation_time > 0
        assert len(env.metrics.update_times) == 5
    
    def test_agent_position_tracking(self):
        """Test that agent positions are tracked correctly."""
        env = BattleEnvironment()
        agent = RandomAgent(position=Vector2D(100, 100))
        
        env.add_agent(agent)
        env.start()
        
        original_position = Vector2D(agent.position.x, agent.position.y)
        
        # Update environment (agent might move)
        env.update(0.016)
        
        # Position should be tracked
        assert env.agent_positions[agent.agent_id] == agent.position


class TestPerformanceCharacteristics:
    """Test performance characteristics of the battle environment."""
    
    def test_large_scale_spawning(self):
        """Test performance with many agents."""
        env = BattleEnvironment()
        
        # Spawn 50 agents
        start_time = time.time()
        for i in range(50):
            agent = RandomAgent(position=Vector2D(100 + i, 100 + i))
            env.add_agent(agent)
        spawn_time = time.time() - start_time
        
        assert len(env.agents) == 50
        assert spawn_time < 1.0  # Should complete in under 1 second
    
    def test_update_performance(self):
        """Test update performance with multiple agents."""
        env = BattleEnvironment()
        
        # Add multiple agents
        for i in range(20):
            agent = RandomAgent(position=Vector2D(100 + i * 20, 100 + i * 20))
            env.add_agent(agent)
        
        env.start()
        
        # Measure update performance
        start_time = time.time()
        for _ in range(10):
            env.update(0.016)
        update_time = time.time() - start_time
        
        average_update_time = update_time / 10
        assert average_update_time < 0.05  # Should be under 50ms per update
    
    def test_collision_detection_performance(self):
        """Test collision detection performance with many agents."""
        env = BattleEnvironment()
        
        # Add agents in a cluster to force collision checks
        for i in range(10):
            for j in range(10):
                agent = RandomAgent(position=Vector2D(100 + i * 5, 100 + j * 5))
                env.add_agent(agent)
        
        # Measure collision detection performance
        start_time = time.time()
        for _ in range(5):
            collisions = env.check_collisions()
        collision_time = time.time() - start_time
        
        average_collision_time = collision_time / 5
        assert average_collision_time < 0.1  # Should be under 100ms per check


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

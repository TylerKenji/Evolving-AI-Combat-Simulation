"""
Test suite for environment system.
Tests base environment functionality and simple environment implementation.
"""

import pytest
from unittest.mock import Mock, MagicMock
from src.environment import (
    BaseEnvironment,
    SimpleEnvironment,
    EnvironmentState,
    CollisionType,
    TerrainType,
    CollisionEvent,
    EnvironmentMetrics,
    TerrainTile
)
from src.agents import BaseAgent, AgentStats, AgentGenome, CombatAction
from src.utils import Vector2D
from typing import Any, Dict, Optional, Sequence


class MockAgent(BaseAgent):
    """Mock agent for testing environment interactions."""
    
    def __init__(self, agent_id: str, position: Optional[Vector2D] = None, team_id: str = "blue"):
        if position is None:
            position = Vector2D(0, 0)
        super().__init__(agent_id=agent_id, position=position, team_id=team_id)
        self._mock_action = CombatAction.MOVE
        self._mock_movement = Vector2D(0, 0)
    
    def update(self, dt: float, battlefield_info: Dict[str, Any]) -> None:
        """Mock update method."""
        pass
    
    def decide_action(self, visible_agents: Sequence[BaseAgent], 
                     battlefield_info: Dict[str, Any]) -> CombatAction:
        """Mock action decision."""
        return self._mock_action
    
    def select_target(self, visible_enemies: Sequence[BaseAgent]) -> Optional[BaseAgent]:
        """Mock target selection."""
        return visible_enemies[0] if visible_enemies else None
    
    def calculate_movement(self, visible_agents: Sequence[BaseAgent], 
                         battlefield_info: Dict[str, Any]) -> Vector2D:
        """Mock movement calculation."""
        return self._mock_movement
    
    def set_mock_action(self, action: CombatAction):
        self._mock_action = action
    
    def set_mock_movement(self, movement: Vector2D):
        self._mock_movement = movement


class TestEnvironmentDataClasses:
    """Test environment data classes and enums."""
    
    def test_environment_states(self):
        """Test EnvironmentState enum."""
        assert EnvironmentState.INITIALIZING
        assert EnvironmentState.RUNNING
        assert EnvironmentState.PAUSED
        assert EnvironmentState.FINISHED

    def test_collision_types(self):
        """Test CollisionType enum."""
        assert CollisionType.AGENT_AGENT
        assert CollisionType.AGENT_BOUNDARY
        assert CollisionType.AGENT_OBSTACLE
        assert CollisionType.PROJECTILE_AGENT
        assert CollisionType.PROJECTILE_OBSTACLE

    def test_terrain_types(self):
        """Test TerrainType enum."""
        assert TerrainType.FLAT
        assert TerrainType.WALL
        assert TerrainType.WATER
        assert TerrainType.ROUGH
        assert TerrainType.COVER

    def test_collision_event_creation(self):
        """Test CollisionEvent dataclass."""
        position = Vector2D(10, 20)
        event = CollisionEvent(
            collision_type=CollisionType.AGENT_AGENT,
            primary_object="agent1",
            secondary_object="agent2",
            collision_point=position,
            collision_normal=Vector2D(1, 0)
        )
        
        assert event.collision_type == CollisionType.AGENT_AGENT
        assert event.primary_object == "agent1"
        assert event.secondary_object == "agent2"
        assert event.collision_point == position
        assert event.collision_normal == Vector2D(1, 0)

    def test_environment_metrics_creation(self):
        """Test EnvironmentMetrics dataclass."""
        metrics = EnvironmentMetrics()
        
        assert metrics.frame_count == 0
        assert metrics.agents_alive == 0
        assert metrics.agents_dead == 0
        assert metrics.collisions_detected == 0
        assert metrics.average_fps == 0.0
        assert metrics.simulation_time == 0.0

    def test_terrain_tile_creation(self):
        """Test TerrainTile dataclass."""
        tile = TerrainTile(
            terrain_type=TerrainType.ROUGH,
            movement_modifier=0.5,
            cover_value=0.3,
            passable=True
        )
        
        assert tile.terrain_type == TerrainType.ROUGH
        assert tile.passable is True
        assert tile.movement_modifier == 0.5
        assert tile.cover_value == 0.3


class TestSimpleEnvironment:
    """Test SimpleEnvironment implementation."""
    
    def setup_method(self):
        """Set up test environment."""
        self.width = 100
        self.height = 100
        self.env = SimpleEnvironment(self.width, self.height)
    
    def test_environment_initialization(self):
        """Test environment initializes correctly."""
        assert self.env.width == self.width
        assert self.env.height == self.height
        assert self.env.state == EnvironmentState.INITIALIZING
        assert len(self.env.agents) == 0
        assert self.env.metrics.frame_count == 0
    
    def test_add_agent_basic(self):
        """Test adding agents to environment."""
        agent = MockAgent("test_agent", Vector2D(50, 50))
        
        success = self.env.add_agent(agent)
        
        assert success is True
        assert len(self.env.agents) == 1
        assert "test_agent" in self.env.agents
    
    def test_add_agent_duplicate_id(self):
        """Test adding agent with duplicate ID fails."""
        agent1 = MockAgent("test_agent", Vector2D(25, 25))
        agent2 = MockAgent("test_agent", Vector2D(75, 75))
        
        success1 = self.env.add_agent(agent1)
        success2 = self.env.add_agent(agent2)
        
        assert success1 is True
        assert success2 is False
        assert len(self.env.agents) == 1
    
    def test_remove_agent(self):
        """Test removing agents from environment."""
        agent = MockAgent("test_agent", Vector2D(50, 50))
        self.env.add_agent(agent)
        
        success = self.env.remove_agent("test_agent")
        
        assert success is True
        assert len(self.env.agents) == 0
    
    def test_remove_nonexistent_agent(self):
        """Test removing non-existent agent fails gracefully."""
        success = self.env.remove_agent("nonexistent")
        
        assert success is False
    
    def test_get_agent(self):
        """Test getting agent by ID."""
        agent = MockAgent("test_agent", Vector2D(50, 50))
        self.env.add_agent(agent)
        
        retrieved = self.env.get_agent("test_agent")
        
        assert retrieved == agent
    
    def test_get_nonexistent_agent(self):
        """Test getting non-existent agent returns None."""
        retrieved = self.env.get_agent("nonexistent")
        
        assert retrieved is None
    
    def test_environment_bounds(self):
        """Test environment boundary properties."""
        bounds = self.env.bounds
        center = self.env.center
        
        assert bounds == (self.width, self.height)
        assert center == Vector2D(self.width / 2, self.height / 2)
    
    def test_environment_lifecycle(self):
        """Test environment state management."""
        # Initial state
        assert self.env.state == EnvironmentState.INITIALIZING
        assert not self.env.is_running
        
        # Start environment
        self.env.start()
        assert self.env.state == EnvironmentState.RUNNING
        assert self.env.is_running
        
        # Pause environment
        self.env.pause()
        assert self.env.state == EnvironmentState.PAUSED
        assert not self.env.is_running
        
        # Resume environment
        self.env.resume()
        assert self.env.state == EnvironmentState.RUNNING
        assert self.env.is_running
        
        # Stop environment
        self.env.stop()
        assert self.env.state == EnvironmentState.FINISHED
        assert not self.env.is_running
    
    def test_environment_reset(self):
        """Test environment reset functionality."""
        agent = MockAgent("test_agent", Vector2D(50, 50))
        self.env.add_agent(agent)
        self.env.start()
        
        # Verify agent is added and environment is running
        assert len(self.env.agents) == 1
        assert self.env.state == EnvironmentState.RUNNING
        
        # Reset environment
        self.env.reset()
        
        # Verify reset state
        assert len(self.env.agents) == 0
        assert self.env.state == EnvironmentState.INITIALIZING
        assert self.env.metrics.frame_count == 0
    
    def test_get_battlefield_info(self):
        """Test getting battlefield information for agents."""
        agent1 = MockAgent("agent1", Vector2D(25, 25), "blue")
        agent2 = MockAgent("agent2", Vector2D(75, 75), "red")
        
        self.env.add_agent(agent1)
        self.env.add_agent(agent2)
        
        info = self.env.get_battlefield_info("agent1")
        
        # Check that battlefield info contains expected keys
        assert isinstance(info, dict)
        # The actual content depends on the implementation
        # We're just verifying the method works
    
    def test_update_with_agents(self):
        """Test environment update with agents."""
        agent = MockAgent("test_agent", Vector2D(50, 50))
        self.env.add_agent(agent)
        self.env.start()
        
        initial_time = self.env.simulation_time
        
        # Update environment
        self.env.update(0.1)  # 0.1 second timestep
        
        # Verify time progression
        assert self.env.simulation_time >= initial_time
    
    def test_collision_detection_setup(self):
        """Test collision detection system setup."""
        # Add two agents close together
        agent1 = MockAgent("agent1", Vector2D(50, 50))
        agent2 = MockAgent("agent2", Vector2D(55, 55))  # Close proximity
        
        self.env.add_agent(agent1)
        self.env.add_agent(agent2)
        
        # Check collisions
        collisions = self.env.check_collisions()
        
        # Verify collision detection runs (result depends on implementation)
        assert isinstance(collisions, list)
    
    def test_agent_count_tracking(self):
        """Test agent count tracking."""
        assert self.env.agent_count == 0
        
        agent1 = MockAgent("agent1", Vector2D(25, 25))
        agent2 = MockAgent("agent2", Vector2D(75, 75))
        
        self.env.add_agent(agent1)
        assert self.env.agent_count == 1
        
        self.env.add_agent(agent2)
        assert self.env.agent_count == 2
        
        self.env.remove_agent("agent1")
        assert self.env.agent_count == 1
    
    def test_living_agents_filter(self):
        """Test filtering of living vs dead agents."""
        agent1 = MockAgent("alive_agent", Vector2D(25, 25))
        agent2 = MockAgent("dead_agent", Vector2D(75, 75))
        
        # Kill second agent
        agent2.stats.current_health = 0
        
        self.env.add_agent(agent1)
        self.env.add_agent(agent2)
        
        living_agents = self.env.get_living_agents()
        all_agents = self.env.get_all_agents()
        
        assert len(all_agents) == 2
        assert len(living_agents) == 1
        assert living_agents[0] == agent1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

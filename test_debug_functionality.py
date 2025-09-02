#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced debug and logging functionality for Task 1.4.7.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agents.base_agent import BaseAgent, AgentRole, AgentStats
from src.utils.vector2d import Vector2D
from src.utils.logging_config import get_logger


class TestAgent(BaseAgent):
    """Simple test agent implementation to test debug functionality."""
    
    def update(self, dt: float, battlefield_info: dict) -> None:
        """Simple update that moves randomly."""
        import random
        velocity = Vector2D(random.uniform(-1, 1), random.uniform(-1, 1))
        self.move(dt, velocity, (100, 100))
    
    def decide_action(self, visible_agents, battlefield_info):
        """Simple decision making."""
        from src.agents.base_agent import CombatAction
        return CombatAction.MOVE
    
    def select_target(self, visible_enemies):
        """Select first visible enemy."""
        return visible_enemies[0] if visible_enemies else None
    
    def calculate_movement(self, dt: float, battlefield_info: dict) -> Vector2D:
        """Calculate movement vector."""
        import random
        return Vector2D(random.uniform(-1, 1), random.uniform(-1, 1))


def test_debug_functionality():
    """Test the new debug and logging methods."""
    logger = get_logger(__name__)
    logger.info("🔧 Testing enhanced debug and logging functionality for Task 1.4.7")
    
    # Create test agents
    agent1 = TestAgent(
        position=Vector2D(10, 10),
        role=AgentRole.TANK,
        stats=AgentStats(max_health=100, attack_damage=25, defense=5)
    )
    
    agent2 = TestAgent(
        position=Vector2D(90, 90),
        role=AgentRole.DPS,
        stats=AgentStats(max_health=120, attack_damage=20, defense=8)
    )
    
    logger.info("📊 Testing debug information methods...")
    
    # Test get_debug_info
    print("\n=== Agent 1 Debug Info (Basic) ===")
    debug_info = agent1.get_debug_info()
    for key, value in debug_info.items():
        print(f"{key}: {value}")
    
    print("\n=== Agent 1 Debug Info (Detailed) ===")
    debug_info_detailed = agent1.get_debug_info(include_detailed=True)
    for key, value in debug_info_detailed.items():
        print(f"{key}: {value}")
    
    # Test log_state_summary
    print("\n=== Testing State Summary Logging ===")
    agent1.log_state_summary(log_level="INFO")
    
    # Test get_debug_string
    print("\n=== Debug String Representations ===")
    print(f"Agent 1 (compact): {agent1.get_debug_string()}")
    print(f"Agent 1 (detailed): {agent1.get_debug_string(compact=False)}")
    
    # Test enable_detailed_logging
    print("\n=== Testing Detailed Logging Control ===")
    agent1.enable_detailed_logging(True)
    logger.info("Enabled detailed logging for agent1")
    
    # Test performance metrics logging
    print("\n=== Testing Performance Metrics ===")
    agent1.log_performance_metrics({"test_metric": 42, "efficiency": 0.85})
    
    # Test decision making logging
    print("\n=== Testing Decision Making Logging ===")
    agent1.log_decision_making(
        {"action": "test", "reasoning": "demonstration"}, 
        "Testing decision logging"
    )
    
    # Test status effects with enhanced logging
    print("\n=== Testing Status Effect Logging ===")
    agent1.apply_status_effect("speed_boost", intensity=0.5, duration=5.0)
    agent1.remove_status_effect("speed_boost")
    
    # Test combat with enhanced logging
    print("\n=== Testing Combat Logging ===")
    original_health = agent2.stats.current_health
    damage_dealt = agent1.attack(agent2)
    if damage_dealt:
        logger.info(f"💥 Agent1 attacked Agent2, health: {original_health} -> {agent2.stats.current_health}")
    
    # Test collision logging
    print("\n=== Testing Collision Logging ===")
    agent1.update_collision_state(1.0, [agent2], (100, 100))
    
    # Test movement with logging
    print("\n=== Testing Movement Logging ===")
    agent1.move(1.0, Vector2D(5, 5), (100, 100))
    
    # Test debug assertion
    print("\n=== Testing Debug Assertion ===")
    agent1.debug_assert(agent1.is_alive, "Agent should be alive")
    
    # Test startup info logging
    print("\n=== Testing Startup Info Logging ===")
    agent1.log_startup_info()
    
    print("\n✅ All debug functionality tests completed successfully!")
    logger.info("🎉 Task 1.4.7 debug and logging enhancement testing completed")


if __name__ == "__main__":
    test_debug_functionality()

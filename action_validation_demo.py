"""
Action Validation System Demonstration

This script demonstrates the comprehensive action validation and execution
system, showing how it provides safe, validated action execution with
detailed results and error handling.

Key Demonstrations:
1. Basic action execution with validation
2. Safety validation preventing invalid actions
3. Different validation levels (BASIC, STANDARD, STRICT, PARANOID)
4. Action-specific execution (attacks, movement, special abilities)
5. Error handling and recovery
6. Performance tracking and statistics
7. Integration with decision framework
"""

import sys
import time
import random
from typing import List, Optional

# Add the src directory to the path for imports
sys.path.append('src')

from src.agents.base_agent import BaseAgent, CombatAction, AgentState
from src.agents.action_validation import (
    ActionExecutor, ActionResult, ActionStatus, ValidationLevel,
    ExecutionContext, SafetyValidator, execute_agent_action,
    create_action_executor
)
from src.utils.vector2d import Vector2D
from src.utils.logging_config import get_logger


class DemoAgent(BaseAgent):
    """Demo agent implementation for testing action validation."""
    
    def update(self, dt: float, visible_agents: List['BaseAgent'], battlefield_info: dict) -> None:
        """Update agent state."""
        pass
    
    def decide_action(self, visible_agents: List['BaseAgent'], battlefield_info: dict) -> CombatAction:
        """Simple decision making for demo."""
        return CombatAction.MOVE
    
    def calculate_movement(self, visible_agents: List['BaseAgent'], battlefield_info: dict) -> Vector2D:
        """Calculate movement vector."""
        return Vector2D(0, 0)
    
    def get_state_info(self) -> dict:
        """Get agent state information."""
        return {
            'position': {'x': self.position.x, 'y': self.position.y},
            'health': self.stats.current_health,
            'state': self.state.value
        }
    
    def select_target(self, visible_agents: List['BaseAgent']) -> Optional['BaseAgent']:
        """Select a target from visible agents."""
        for agent in visible_agents:
            if agent != self and agent.is_alive:
                return agent
        return None


def create_demo_agent(agent_id: str, position: Vector2D, health: int = 100) -> DemoAgent:
    """Create a demo agent for testing."""
    agent = DemoAgent(agent_id, position)
    agent.stats.current_health = health
    agent.stats.max_health = 100
    agent.stats.attack_damage = 25
    agent.stats.attack_range = 50
    agent.stats.speed = 15
    agent.stats.accuracy = 0.8
    return agent


def print_action_result(result: ActionResult, detailed: bool = True) -> None:
    """Print action result in a readable format."""
    print(f"\n{'='*60}")
    print(f"Action Result: {result}")
    
    if detailed:
        print(f"  Status: {result.status.value}")
        print(f"  Success: {result.success}")
        print(f"  Validation Passed: {result.validation_passed}")
        
        if result.validation_errors:
            print(f"  Validation Errors: {', '.join(result.validation_errors)}")
        
        if result.execution_error:
            print(f"  Execution Error: {result.execution_error}")
        
        print(f"  Execution Time: {result.execution_time:.3f}s")
        print(f"  Validation Time: {result.validation_time:.3f}s")
        
        if result.primary_result:
            print(f"  Primary Result: {result.primary_result}")
        
        if result.secondary_effects:
            print(f"  Secondary Effects: {result.secondary_effects}")


def demo_basic_action_execution():
    """Demonstrate basic action execution with validation."""
    print("\n🎯 DEMO 1: Basic Action Execution")
    print("-" * 40)
    
    # Create agents
    attacker = create_demo_agent("Warrior_001", Vector2D(100, 100))
    target = create_demo_agent("Enemy_001", Vector2D(130, 100))  # 30 units away
    
    # Execute a basic melee attack
    result = execute_agent_action(
        agent=attacker,
        action=CombatAction.ATTACK_MELEE,
        target_agent=target,
        validation_level=ValidationLevel.STANDARD
    )
    
    print_action_result(result)
    
    print(f"\nAttacker Health: {attacker.stats.current_health}")
    print(f"Target Health: {target.stats.current_health}")


def demo_safety_validation():
    """Demonstrate safety validation preventing invalid actions."""
    print("\n🛡️ DEMO 2: Safety Validation")
    print("-" * 40)
    
    # Create agents
    agent = create_demo_agent("TestAgent_001", Vector2D(100, 100))
    distant_target = create_demo_agent("DistantEnemy", Vector2D(200, 100))  # 100 units away
    
    print("1. Attempting attack on out-of-range target...")
    result = execute_agent_action(
        agent=agent,
        action=CombatAction.ATTACK_MELEE,
        target_agent=distant_target,
        validation_level=ValidationLevel.STANDARD
    )
    print_action_result(result)
    
    print("\n2. Attempting self-attack (should be blocked)...")
    result = execute_agent_action(
        agent=agent,
        action=CombatAction.ATTACK_MELEE,
        target_agent=agent,  # Self-attack
        validation_level=ValidationLevel.STANDARD
    )
    print_action_result(result)
    
    print("\n3. Attempting attack with dead agent...")
    agent.stats.current_health = 0  # Kill the agent
    result = execute_agent_action(
        agent=agent,
        action=CombatAction.ATTACK_MELEE,
        target_agent=distant_target,
        validation_level=ValidationLevel.STANDARD
    )
    print_action_result(result)


def demo_validation_levels():
    """Demonstrate different validation levels."""
    print("\n📏 DEMO 3: Validation Levels")
    print("-" * 40)
    
    # Create agents
    agent = create_demo_agent("TestAgent_002", Vector2D(50, 50))
    target = create_demo_agent("Target_002", Vector2D(80, 50))
    
    validation_levels = [
        ValidationLevel.BASIC,
        ValidationLevel.STANDARD,
        ValidationLevel.STRICT,
        ValidationLevel.PARANOID
    ]
    
    for level in validation_levels:
        print(f"\nTesting with {level.name} validation:")
        
        start_time = time.time()
        result = execute_agent_action(
            agent=agent,
            action=CombatAction.ATTACK_MELEE,
            target_agent=target,
            validation_level=level
        )
        end_time = time.time()
        
        print(f"  Result: {result.status.value}")
        print(f"  Success: {result.success}")
        print(f"  Validation Time: {result.validation_time:.4f}s")
        print(f"  Total Time: {end_time - start_time:.4f}s")


def demo_action_types():
    """Demonstrate different action types."""
    print("\n⚔️ DEMO 4: Different Action Types")
    print("-" * 40)
    
    # Create agents
    agent = create_demo_agent("Versatile_Agent", Vector2D(100, 100))
    enemy1 = create_demo_agent("Enemy_001", Vector2D(130, 100))
    enemy2 = create_demo_agent("Enemy_002", Vector2D(80, 120))
    
    visible_agents = [enemy1, enemy2]
    battlefield_info = {
        'bounds': {'min_x': 0, 'max_x': 200, 'min_y': 0, 'max_y': 200}
    }
    
    actions_to_test = [
        (CombatAction.ATTACK_MELEE, enemy1, None),
        (CombatAction.ATTACK_RANGED, enemy2, None),
        (CombatAction.MOVE, None, Vector2D(120, 120)),
        (CombatAction.DODGE, None, None),
        (CombatAction.DEFEND, None, None),
        (CombatAction.RETREAT, None, None),
        (CombatAction.USE_SPECIAL, None, None),
        (CombatAction.COOPERATE, None, None)
    ]
    
    for action, target, position in actions_to_test:
        print(f"\nExecuting {action.value}:")
        
        result = execute_agent_action(
            agent=agent,
            action=action,
            target_agent=target,
            target_position=position,
            visible_agents=visible_agents,
            battlefield_info=battlefield_info,
            validation_level=ValidationLevel.STANDARD
        )
        
        print(f"  Status: {result.status.value}")
        print(f"  Success: {result.success}")
        if result.primary_result:
            print(f"  Result: {result.primary_result}")
        
        # Brief pause between actions
        time.sleep(0.1)


def demo_performance_tracking():
    """Demonstrate performance tracking and statistics."""
    print("\n📊 DEMO 5: Performance Tracking")
    print("-" * 40)
    
    # Create executor for performance tracking
    executor = create_action_executor(ValidationLevel.STANDARD)
    
    # Create agents
    agent = create_demo_agent("PerformanceAgent", Vector2D(100, 100))
    targets = [
        create_demo_agent(f"Target_{i}", Vector2D(120 + i*10, 100))
        for i in range(5)
    ]
    
    print("Executing multiple actions to gather statistics...")
    
    # Execute multiple actions
    for i, target in enumerate(targets):
        context = ExecutionContext(
            agent=agent,
            action=CombatAction.ATTACK_MELEE,
            target_agent=target,
            validation_level=ValidationLevel.STANDARD
        )
        
        result = executor.execute_action(context)
        print(f"  Action {i+1}: {result.status.value} ({result.execution_time:.3f}s)")
    
    # Execute some failed actions
    print("\nExecuting some invalid actions...")
    for i in range(3):
        context = ExecutionContext(
            agent=agent,
            action=CombatAction.ATTACK_MELEE,
            target_agent=agent,  # Self-attack (invalid)
            validation_level=ValidationLevel.STANDARD
        )
        
        result = executor.execute_action(context)
        print(f"  Invalid Action {i+1}: {result.status.value}")
    
    # Show statistics
    stats = executor.get_execution_statistics()
    print(f"\n📈 Execution Statistics:")
    print(f"  Total Executions: {stats['total_executions']}")
    print(f"  Successful: {stats['successful_executions']}")
    print(f"  Failed: {stats['failed_executions']}")
    print(f"  Blocked: {stats['blocked_executions']}")
    print(f"  Success Rate: {stats.get('success_rate', 0):.1%}")
    print(f"  Average Execution Time: {stats.get('average_execution_time', 0):.4f}s")


def demo_complex_battle_scenario():
    """Demonstrate complex battle scenario with multiple agents and actions."""
    print("\n⚡ DEMO 6: Complex Battle Scenario")
    print("-" * 40)
    
    # Create a small battle scenario
    hero = create_demo_agent("Hero_001", Vector2D(100, 100))
    enemies = [
        create_demo_agent("Orc_001", Vector2D(150, 100)),
        create_demo_agent("Goblin_001", Vector2D(120, 120)),
        create_demo_agent("Skeleton_001", Vector2D(80, 80))
    ]
    
    all_agents = [hero] + enemies
    battlefield_info = {
        'bounds': {'min_x': 0, 'max_x': 200, 'min_y': 0, 'max_y': 200}
    }
    
    executor = create_action_executor(ValidationLevel.STANDARD)
    
    print("Starting battle simulation...")
    
    for turn in range(3):
        print(f"\n--- Turn {turn + 1} ---")
        
        # Hero's turn
        if hero.is_alive:
            # Find closest enemy
            closest_enemy = None
            min_distance = float('inf')
            
            for enemy in enemies:
                if enemy.is_alive:
                    distance = hero.position.distance_to(enemy.position)
                    if distance < min_distance:
                        min_distance = distance
                        closest_enemy = enemy
            
            if closest_enemy:
                # Decide action based on distance and health
                if min_distance <= hero.stats.attack_range:
                    action = CombatAction.ATTACK_MELEE
                    target = closest_enemy
                    position = None
                elif hero.stats.current_health < 30:
                    action = CombatAction.RETREAT
                    target = None
                    position = None
                else:
                    action = CombatAction.MOVE
                    target = None
                    position = closest_enemy.position
                
                context = ExecutionContext(
                    agent=hero,
                    action=action,
                    target_agent=target,
                    target_position=position,
                    visible_agents=enemies,
                    battlefield_info=battlefield_info
                )
                
                result = executor.execute_action(context)
                print(f"Hero: {action.value} -> {result.status.value}")
                
                if result.success and action == CombatAction.ATTACK_MELEE:
                    print(f"  Enemy {closest_enemy.agent_id} health: {closest_enemy.stats.current_health}")
        
        # Enemies' turns (simplified)
        for enemy in enemies:
            if enemy.is_alive and hero.is_alive:
                distance_to_hero = enemy.position.distance_to(hero.position)
                
                if distance_to_hero <= enemy.stats.attack_range:
                    # Attack hero
                    context = ExecutionContext(
                        agent=enemy,
                        action=CombatAction.ATTACK_MELEE,
                        target_agent=hero,
                        visible_agents=[hero],
                        battlefield_info=battlefield_info
                    )
                    
                    result = executor.execute_action(context)
                    print(f"{enemy.agent_id}: Attack -> {result.status.value}")
                    
                    if result.success:
                        print(f"  Hero health: {hero.stats.current_health}")
                else:
                    # Move towards hero
                    context = ExecutionContext(
                        agent=enemy,
                        action=CombatAction.MOVE,
                        target_position=hero.position,
                        visible_agents=[hero],
                        battlefield_info=battlefield_info
                    )
                    
                    result = executor.execute_action(context)
                    print(f"{enemy.agent_id}: Move -> {result.status.value}")
        
        # Check if battle is over
        if not hero.is_alive:
            print("\n💀 Hero has fallen!")
            break
        
        living_enemies = [e for e in enemies if e.is_alive]
        if not living_enemies:
            print("\n🏆 All enemies defeated!")
            break
    
    # Final statistics
    stats = executor.get_execution_statistics()
    print(f"\n📊 Battle Statistics:")
    print(f"  Total Actions: {stats['total_executions']}")
    print(f"  Success Rate: {stats.get('success_rate', 0):.1%}")
    print(f"  Average Action Time: {stats.get('average_execution_time', 0):.4f}s")


def main():
    """Run all demonstrations."""
    # Setup logging
    logger = get_logger("ActionValidationDemo")
    
    print("🔧 Action Validation System Demonstration")
    print("=" * 60)
    print("This demo shows comprehensive action validation and execution")
    print("with safety checks, performance tracking, and error handling.")
    
    try:
        # Run demonstrations
        demo_basic_action_execution()
        demo_safety_validation()
        demo_validation_levels()
        demo_action_types()
        demo_performance_tracking()
        demo_complex_battle_scenario()
        
        print("\n✅ All demonstrations completed successfully!")
        print("\nKey takeaways:")
        print("• Action validation prevents invalid/unsafe actions")
        print("• Multiple validation levels provide flexibility")
        print("• Comprehensive result tracking aids debugging")
        print("• Performance statistics help optimize systems")
        print("• Integration works seamlessly with existing agents")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        logger.error(f"Demo error: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

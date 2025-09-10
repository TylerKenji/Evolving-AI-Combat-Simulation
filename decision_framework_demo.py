"""
Decision Framework Demo

This script demonstrates the basic decision-making framework in action.
It shows how agents can use the framework to make intelligent decisions
based on battlefield context and tactical situations.

The demo includes:
1. Basic decision making with no enemies
2. Combat decision making with enemies present
3. Low health/retreat scenarios
4. Surrounded/defensive scenarios
5. Custom evaluator implementation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.decision_framework import (
    DecisionMaker, DecisionContext, ActionEvaluator, DefaultActionEvaluator,
    ActionValidator, ActionScore, DecisionPriority, create_decision_maker
)
from src.agents.base_agent import CombatAction, AgentState, AgentStats
from src.utils.vector2d import Vector2D
from src.utils.logging_config import get_logger
import time

# Set up logging
logger = get_logger("DecisionFrameworkDemo")


class DemoAgent:
    """Simple agent class for demonstration purposes."""
    
    def __init__(self, agent_id: str, position: Vector2D, health: float = 100.0, team_id: int = 1):
        self.agent_id = agent_id
        self.position = position
        self.state = AgentState.ALIVE
        self.stats = AgentStats(
            max_health=100.0,
            current_health=health,
            speed=50.0,
            attack_damage=20.0,
            attack_range=30.0,
            vision_range=150.0
        )
        self.last_attack_time = 0.0
        self.team_id = team_id
        
        # Mock combat state for demo
        self._combat_state = MockCombatState()
    
    @property
    def is_alive(self) -> bool:
        return self.state == AgentState.ALIVE and self.stats.current_health > 0
    
    @property
    def can_attack(self) -> bool:
        return self.is_alive and time.time() - self.last_attack_time >= self.stats.attack_cooldown
    
    @property
    def combat_state(self):
        return self._combat_state
    
    def __str__(self):
        return f"{self.agent_id}(pos={self.position}, hp={self.stats.current_health:.0f}, team={self.team_id})"


class MockCombatState:
    """Mock combat state for demo."""
    
    def can_attack(self) -> bool:
        return True


class AggressiveEvaluator(ActionEvaluator):
    """
    Custom evaluator that prefers aggressive actions.
    
    This demonstrates how to create specialized decision-making behavior
    by implementing custom evaluation logic.
    """
    
    def evaluate_action(self, action: CombatAction, context: DecisionContext) -> ActionScore:
        """Evaluate actions with aggressive bias."""
        
        if action == CombatAction.ATTACK_MELEE:
            if context.nearest_enemy:
                distance = context.self_agent.position.distance_to(context.nearest_enemy.position)
                if distance <= context.self_agent.stats.attack_range:
                    return ActionScore(
                        action, 0.95, DecisionPriority.HIGH, 0.9,
                        "AGGRESSIVE: Prioritize melee attacks!"
                    )
            return ActionScore(action, 0.3, DecisionPriority.MEDIUM, 0.8, "Melee not viable")
        
        elif action == CombatAction.ATTACK_RANGED:
            if context.nearest_enemy:
                return ActionScore(
                    action, 0.85, DecisionPriority.HIGH, 0.85,
                    "AGGRESSIVE: Attack at range!"
                )
            return ActionScore(action, 0.2, DecisionPriority.LOW, 0.7, "No targets")
        
        elif action == CombatAction.RETREAT:
            # Only retreat if critically wounded
            if context.health_percentage < 0.15:
                return ActionScore(
                    action, 0.9, DecisionPriority.EMERGENCY, 0.95,
                    "CRITICAL: Must retreat to survive"
                )
            else:
                return ActionScore(
                    action, 0.1, DecisionPriority.MINIMAL, 0.8,
                    "AGGRESSIVE: No retreat!"
                )
        
        elif action == CombatAction.MOVE:
            return ActionScore(
                action, 0.6, DecisionPriority.MEDIUM, 0.8,
                "Move to engage enemies"
            )
        
        elif action == CombatAction.DEFEND:
            if len(context.immediate_threats) >= 3:
                return ActionScore(
                    action, 0.7, DecisionPriority.HIGH, 0.8,
                    "Defend against multiple threats"
                )
            else:
                return ActionScore(
                    action, 0.3, DecisionPriority.LOW, 0.7,
                    "AGGRESSIVE: Offense over defense"
                )
        
        elif action == CombatAction.DODGE:
            return ActionScore(
                action, 0.4, DecisionPriority.MEDIUM, 0.7,
                "Dodge to maintain aggression"
            )
        
        else:  # Special abilities, cooperation
            return ActionScore(
                action, 0.5, DecisionPriority.MEDIUM, 0.6,
                "Situational aggressive action"
            )


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_agent_info(agent: DemoAgent):
    """Print agent information."""
    print(f"Agent: {agent}")
    print(f"  Health: {agent.stats.current_health:.0f}/{agent.stats.max_health:.0f} ({agent.stats.current_health/agent.stats.max_health:.1%})")
    print(f"  Position: {agent.position}")
    print(f"  Can Attack: {agent.can_attack}")


def print_decision_result(action: CombatAction, decision_maker: DecisionMaker):
    """Print decision result and reasoning."""
    print(f"  Decision: {action}")
    
    # Get the last decision for reasoning
    if decision_maker.decision_history:
        last_context, last_score = decision_maker.decision_history[-1]
        print(f"  Reasoning: {last_score.reasoning}")
        print(f"  Utility: {last_score.utility:.2f}, Priority: {last_score.priority.name}")
        print(f"  Confidence: {last_score.confidence:.2f}, Weighted Score: {last_score.weighted_score:.2f}")


def demo_basic_decisions():
    """Demonstrate basic decision making with no threats."""
    print_section("Basic Decision Making (No Enemies)")
    
    # Create agent with no threats
    agent = DemoAgent("Hero", Vector2D(0, 0), health=100.0)
    decision_maker = create_decision_maker(agent)  # type: ignore
    
    print_agent_info(agent)
    print("\nScenario: Peaceful battlefield, no enemies visible")
    
    # Make decision with no visible agents
    action = decision_maker.decide_action([], {}, dt=1.0)
    print_decision_result(action, decision_maker)


def demo_combat_decisions():
    """Demonstrate combat decision making."""
    print_section("Combat Decision Making")
    
    # Create agents
    hero = DemoAgent("Hero", Vector2D(0, 0), health=100.0, team_id=1)
    enemy1 = DemoAgent("Enemy1", Vector2D(25, 0), health=80.0, team_id=2)  # In range
    enemy2 = DemoAgent("Enemy2", Vector2D(60, 10), health=90.0, team_id=2)  # Out of range
    
    decision_maker = create_decision_maker(hero)  # type: ignore
    
    print_agent_info(hero)
    print(f"Enemies: {enemy1}, {enemy2}")
    print(f"Enemy1 distance: {hero.position.distance_to(enemy1.position):.1f}")
    print(f"Enemy2 distance: {hero.position.distance_to(enemy2.position):.1f}")
    print(f"Attack range: {hero.stats.attack_range}")
    
    # Make decision with enemies present
    visible_agents = [enemy1, enemy2]
    battlefield_info = {"bounds": {"min_x": -100, "max_x": 100, "min_y": -100, "max_y": 100}}
    
    action = decision_maker.decide_action(visible_agents, battlefield_info, dt=1.0)  # type: ignore
    print_decision_result(action, decision_maker)


def demo_low_health_decisions():
    """Demonstrate decision making with low health."""
    print_section("Low Health Decision Making")
    
    # Create badly wounded agent
    wounded_hero = DemoAgent("WoundedHero", Vector2D(0, 0), health=15.0, team_id=1)
    enemy = DemoAgent("Enemy", Vector2D(20, 0), health=100.0, team_id=2)
    
    decision_maker = create_decision_maker(wounded_hero)  # type: ignore
    
    print_agent_info(wounded_hero)
    print(f"Threatening enemy: {enemy}")
    print("Scenario: Critically wounded agent facing healthy enemy")
    
    # Make decision with low health
    visible_agents = [enemy]
    action = decision_maker.decide_action(visible_agents, {}, dt=1.0)  # type: ignore
    print_decision_result(action, decision_maker)


def demo_surrounded_decisions():
    """Demonstrate decision making when surrounded."""
    print_section("Surrounded Decision Making")
    
    # Create surrounded agent
    surrounded_hero = DemoAgent("SurroundedHero", Vector2D(0, 0), health=60.0, team_id=1)
    enemies = [
        DemoAgent("Enemy_North", Vector2D(0, 25), health=100.0, team_id=2),
        DemoAgent("Enemy_South", Vector2D(0, -25), health=100.0, team_id=2),
        DemoAgent("Enemy_East", Vector2D(25, 0), health=100.0, team_id=2),
    ]
    
    decision_maker = create_decision_maker(surrounded_hero)  # type: ignore
    
    print_agent_info(surrounded_hero)
    print("Enemies surrounding agent:")
    for enemy in enemies:
        distance = surrounded_hero.position.distance_to(enemy.position)
        print(f"  {enemy} (distance: {distance:.1f})")
    
    print("Scenario: Agent surrounded by multiple enemies")
    
    # Make decision when surrounded
    action = decision_maker.decide_action(enemies, {}, dt=1.0)  # type: ignore
    print_decision_result(action, decision_maker)


def demo_aggressive_evaluator():
    """Demonstrate custom aggressive evaluator."""
    print_section("Custom Aggressive Evaluator")
    
    # Create agent with aggressive evaluator
    aggressive_hero = DemoAgent("AggressiveHero", Vector2D(0, 0), health=70.0, team_id=1)
    enemy = DemoAgent("Enemy", Vector2D(20, 0), health=80.0, team_id=2)
    
    # Create decision maker with custom evaluator
    aggressive_evaluator = AggressiveEvaluator(aggressive_hero)  # type: ignore
    decision_maker = DecisionMaker(aggressive_hero, aggressive_evaluator)  # type: ignore
    
    print_agent_info(aggressive_hero)
    print(f"Enemy: {enemy}")
    print("Scenario: Aggressive agent prefers offensive actions")
    
    # Make decision with aggressive evaluator
    visible_agents = [enemy]
    action = decision_maker.decide_action(visible_agents, {}, dt=1.0)  # type: ignore
    print_decision_result(action, decision_maker)
    
    print("\nComparing with default evaluator:")
    default_decision_maker = create_decision_maker(aggressive_hero)  # type: ignore
    default_action = default_decision_maker.decide_action(visible_agents, {}, dt=1.0)  # type: ignore
    print(f"  Default Decision: {default_action}")
    if default_decision_maker.decision_history:
        _, default_score = default_decision_maker.decision_history[-1]
        print(f"  Default Reasoning: {default_score.reasoning}")


def demo_decision_history():
    """Demonstrate decision history tracking."""
    print_section("Decision History Tracking")
    
    agent = DemoAgent("HistoryAgent", Vector2D(0, 0), health=100.0, team_id=1)
    decision_maker = create_decision_maker(agent)  # type: ignore
    
    print_agent_info(agent)
    print("Making multiple decisions to build history...")
    
    # Simulate different scenarios
    scenarios = [
        ([], "No enemies"),
        ([DemoAgent("Enemy1", Vector2D(50, 0), team_id=2)], "Distant enemy"),
        ([DemoAgent("Enemy1", Vector2D(20, 0), team_id=2)], "Close enemy"),
        ([DemoAgent("Enemy1", Vector2D(15, 0), team_id=2), 
          DemoAgent("Enemy2", Vector2D(-15, 0), team_id=2)], "Multiple enemies"),
    ]
    
    for i, (enemies, description) in enumerate(scenarios, 1):
        print(f"\n  Scenario {i}: {description}")
        action = decision_maker.decide_action(enemies, {}, dt=1.0)  # type: ignore
        print(f"    Decision: {action}")
    
    print(f"\nDecision History Summary:")
    print(decision_maker.get_decision_summary(last_n=4))


def main():
    """Run all decision framework demonstrations."""
    print("Decision Framework Demonstration")
    print("This demo shows how the basic decision-making framework works")
    print("with different battlefield scenarios and agent configurations.")
    
    try:
        demo_basic_decisions()
        demo_combat_decisions()
        demo_low_health_decisions()
        demo_surrounded_decisions()
        demo_aggressive_evaluator()
        demo_decision_history()
        
        print_section("Demo Complete")
        print("The decision framework provides:")
        print("✓ Context-aware decision making")
        print("✓ Utility-based action evaluation")
        print("✓ Action validation and filtering")
        print("✓ Customizable evaluation strategies")
        print("✓ Decision history tracking")
        print("✓ Extensible architecture for complex AI behaviors")
        print("\nThe framework is ready for integration with existing agents!")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"Error during demo: {e}")
        raise


if __name__ == "__main__":
    main()

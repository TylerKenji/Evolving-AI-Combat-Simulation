#!/usr/bin/env python3
"""
SimpleChaseAgent Demonstration

This script demonstrates the SimpleChaseAgent behavior in various scenarios,
comparing it to RandomAgent and IdleAgent for contrast.

The SimpleChaseAgent implements aggressive pursuit behavior:
- Actively seeks and chases nearest enemies within range
- Makes tactical decisions based on health and distance
- Shows retreat behavior when health is low
- Maintains target persistence for focused attacks
"""

import time
import math
from typing import List, Optional

from src.agents.simple_chase_agent import SimpleChaseAgent
from src.agents.random_agent import RandomAgent
from src.agents.idle_agent import IdleAgent
from src.utils.vector2d import Vector2D
from src.agents.base_agent import CombatAction, AgentRole


def print_separator(title: str = ""):
    """Print a visual separator with optional title."""
    if title:
        print(f"\n{'='*20} {title} {'='*20}")
    else:
        print(f"\n{'='*60}")


def print_agent_status(agent, enemies: Optional[List] = None):
    """Print detailed status of an agent."""
    agent_type = agent.get_agent_type()
    print(f"🤖 {agent_type} ({agent.agent_id[:8]})")
    print(f"   📍 Position: ({agent.position.x:.1f}, {agent.position.y:.1f})")
    print(f"   ❤️ Health: {agent.stats.current_health:.1f}/{agent.stats.max_health:.1f} ({agent.health_percentage:.1%})")
    print(f"   👥 Team: {agent.team_id}")
    print(f"   🎭 Role: {agent.role.value}")
    
    if hasattr(agent, 'current_target') and agent.current_target:
        distance = agent.position.distance_to(agent.current_target.position)
        print(f"   🎯 Target: {agent.current_target.agent_id[:8]} (distance: {distance:.1f})")
    elif hasattr(agent, 'current_target'):
        print(f"   🎯 Target: None")
    
    if hasattr(agent, 'get_chase_statistics'):
        stats = agent.get_chase_statistics()
        print(f"   📊 Chase Stats:")
        print(f"      - In retreat: {stats['in_retreat_mode']}")
        print(f"      - Can attack: {stats['can_attack']}")
        print(f"      - Chase range: {stats['chase_distance_threshold']:.1f}")


def demonstrate_basic_chase_behavior():
    """Demonstrate basic pursuit behavior of SimpleChaseAgent."""
    print_separator("Basic Chase Behavior")
    
    # Create a SimpleChaseAgent and target
    chase_agent = SimpleChaseAgent(Vector2D(0, 0), team_id="hunters", role=AgentRole.DPS)
    target_agent = IdleAgent(Vector2D(100, 50), team_id="prey")
    
    print("🔬 Scenario: SimpleChaseAgent pursuing stationary target")
    print_agent_status(chase_agent)
    print_agent_status(target_agent)
    
    print("\n📈 Simulation steps:")
    
    # Run simulation steps
    for step in range(5):
        print(f"\n--- Step {step + 1} ---")
        
        # SimpleChaseAgent selects target and makes decisions
        visible_enemies = [target_agent]
        target = chase_agent.select_target(visible_enemies)
        action = chase_agent.decide_action(visible_enemies, {})
        movement = chase_agent.calculate_movement(visible_enemies, {})
        
        print(f"Chase Agent:")
        print(f"  🎯 Selected target: {target.agent_id[:8] if target else 'None'}")
        print(f"  ⚡ Action: {action.value}")
        print(f"  🏃 Movement: ({movement.x:.1f}, {movement.y:.1f}) - magnitude: {movement.magnitude():.1f}")
        
        # Apply movement
        chase_agent.position += movement
        distance = chase_agent.position.distance_to(target_agent.position)
        print(f"  📏 Distance to target: {distance:.1f}")
        
        # Update agent
        chase_agent.update(0.1, {"time": step * 0.1})
        
        if distance <= chase_agent.stats.attack_range:
            print(f"  ⚔️ TARGET IN ATTACK RANGE!")
            break


def demonstrate_target_selection():
    """Demonstrate how SimpleChaseAgent selects targets."""
    print_separator("Target Selection Logic")
    
    chase_agent = SimpleChaseAgent(Vector2D(0, 0), team_id="hunters")
    
    # Create multiple potential targets at different distances
    close_enemy = IdleAgent(Vector2D(30, 0), team_id="enemies")     # 30 units away
    medium_enemy = IdleAgent(Vector2D(80, 0), team_id="enemies")    # 80 units away
    far_enemy = IdleAgent(Vector2D(150, 0), team_id="enemies")      # 150 units away
    very_far_enemy = IdleAgent(Vector2D(250, 0), team_id="enemies") # 250 units away (beyond threshold)
    
    enemies = [close_enemy, medium_enemy, far_enemy, very_far_enemy]
    
    print("🔬 Scenario: Multiple targets at different distances")
    print_agent_status(chase_agent)
    print("\n📍 Available targets:")
    for i, enemy in enumerate(enemies, 1):
        distance = chase_agent.position.distance_to(enemy.position)
        print(f"  {i}. Enemy {enemy.agent_id[:8]} at distance {distance:.1f}")
    
    # Test target selection
    selected_target = chase_agent.select_target(enemies)
    
    if selected_target:
        distance = chase_agent.position.distance_to(selected_target.position)
        print(f"\n🎯 Selected target: {selected_target.agent_id[:8]} (distance: {distance:.1f})")
        print(f"   ✅ Reason: Closest enemy within chase range ({chase_agent.chase_distance_threshold:.1f})")
    else:
        print(f"\n🎯 Selected target: None")
        print(f"   ❌ Reason: No enemies within chase range ({chase_agent.chase_distance_threshold:.1f})")
    
    # Test target persistence
    print(f"\n🔄 Testing target persistence...")
    if selected_target:
        chase_agent.current_target = selected_target
        
        # Select again with same enemies
        new_target = chase_agent.select_target(enemies)
        print(f"   First selection: {selected_target.agent_id[:8]}")
        print(f"   Second selection: {new_target.agent_id[:8] if new_target else 'None'}")
        
        if new_target == selected_target:
            print(f"   ✅ Target persistence maintained!")
        else:
            print(f"   ⚠️ Target changed")


def demonstrate_retreat_behavior():
    """Demonstrate retreat behavior when health is low."""
    print_separator("Retreat Behavior")
    
    chase_agent = SimpleChaseAgent(Vector2D(0, 0), team_id="hunters")
    enemy = IdleAgent(Vector2D(40, 0), team_id="enemies")
    
    print("🔬 Scenario: SimpleChaseAgent with low health")
    
    # Show normal behavior first
    print("\n💪 Normal health behavior:")
    print_agent_status(chase_agent, [enemy])
    action = chase_agent.decide_action([enemy], {})
    print(f"   ⚡ Action: {action.value}")
    
    # Reduce health below retreat threshold
    chase_agent.take_damage(90)  # Should bring health to ~10%
    
    print(f"\n🩸 After taking 90 damage:")
    print_agent_status(chase_agent, [enemy])
    
    # Test retreat behavior
    action = chase_agent.decide_action([enemy], {})
    movement = chase_agent.calculate_movement([enemy], {})
    
    print(f"   ⚡ Action: {action.value}")
    print(f"   🏃 Movement: ({movement.x:.1f}, {movement.y:.1f})")
    
    if action == CombatAction.RETREAT:
        print(f"   ✅ Agent correctly decided to retreat!")
        enemy_direction = (enemy.position - chase_agent.position).normalize()
        retreat_direction = movement.normalize()
        
        # Check if moving away from enemy
        dot_product = enemy_direction.dot(retreat_direction)
        if dot_product < 0:
            print(f"   ✅ Movement is away from enemy (dot product: {dot_product:.2f})")
        else:
            print(f"   ⚠️ Movement not clearly away from enemy (dot product: {dot_product:.2f})")
    else:
        print(f"   ⚠️ Agent did not retreat as expected")


def demonstrate_agent_comparison():
    """Compare behavior of different agent types in the same scenario."""
    print_separator("Agent Behavior Comparison")
    
    print("🔬 Scenario: Three different agents facing the same enemy")
    
    # Create agents at same starting position
    chase_agent = SimpleChaseAgent(Vector2D(0, 0), team_id="team1")
    random_agent = RandomAgent(Vector2D(0, 0), team_id="team1")
    idle_agent = IdleAgent(Vector2D(0, 0), team_id="team1")
    
    # Create enemy
    enemy = IdleAgent(Vector2D(100, 0), team_id="team2")
    
    agents = [
        ("SimpleChaseAgent", chase_agent),
        ("RandomAgent", random_agent),
        ("IdleAgent", idle_agent)
    ]
    
    print(f"\n📍 Enemy position: ({enemy.position.x:.1f}, {enemy.position.y:.1f})")
    print(f"   Distance from origin: {enemy.position.magnitude():.1f}")
    
    print(f"\n🎭 Agent responses:")
    
    for name, agent in agents:
        target = agent.select_target([enemy])
        action = agent.decide_action([enemy], {})
        movement = agent.calculate_movement([enemy], {})
        
        print(f"\n   {name}:")
        print(f"     🎯 Target: {target.agent_id[:8] if target else 'None'}")
        print(f"     ⚡ Action: {action.value}")
        print(f"     🏃 Movement: ({movement.x:.1f}, {movement.y:.1f}) - magnitude: {movement.magnitude():.1f}")
        
        if name == "SimpleChaseAgent":
            if target and action == CombatAction.MOVE and movement.magnitude() > 0:
                print(f"     ✅ Actively pursuing enemy")
            else:
                print(f"     ⚠️ Not pursuing as expected")
        elif name == "RandomAgent":
            print(f"     🎲 Exhibiting random behavior")
        elif name == "IdleAgent":
            if movement.magnitude() < 0.1:
                print(f"     ✅ Remaining idle as expected")
            else:
                print(f"     ⚠️ Unexpected movement")


def demonstrate_role_variations():
    """Demonstrate SimpleChaseAgent with different roles."""
    print_separator("Role Variations")
    
    print("🔬 Scenario: SimpleChaseAgents with different roles")
    
    roles = [AgentRole.TANK, AgentRole.DPS, AgentRole.SUPPORT, AgentRole.BALANCED]
    enemy = IdleAgent(Vector2D(100, 0), team_id="enemies")
    
    for role in roles:
        agent = SimpleChaseAgent(Vector2D(0, 0), team_id="hunters", role=role)
        
        print(f"\n🎭 {role.value.upper()} Role:")
        print(f"   💪 Health: {agent.stats.current_health:.1f}")
        print(f"   🏃 Speed: {agent.stats.speed:.1f}")
        print(f"   ⚔️ Attack: {agent.stats.attack_damage:.1f}")
        print(f"   🛡️ Defense: {agent.stats.defense:.1f}")
        print(f"   👁️ Vision: {agent.stats.vision_range:.1f}")
        
        # Test behavior
        target = agent.select_target([enemy])
        action = agent.decide_action([enemy], {})
        
        print(f"   🎯 Target selection: {'Success' if target else 'None'}")
        print(f"   ⚡ Action: {action.value}")
        
        # All roles should still chase (that's the agent's core behavior)
        if target and action == CombatAction.MOVE:
            print(f"   ✅ Maintains chase behavior regardless of role")


def main():
    """Run all demonstrations."""
    print("🎯 SimpleChaseAgent Demonstration")
    print("=" * 60)
    print("This demonstration showcases the SimpleChaseAgent's aggressive pursuit behavior")
    print("and compares it with RandomAgent and IdleAgent behaviors.")
    
    try:
        demonstrate_basic_chase_behavior()
        time.sleep(1)
        
        demonstrate_target_selection()
        time.sleep(1)
        
        demonstrate_retreat_behavior()
        time.sleep(1)
        
        demonstrate_agent_comparison()
        time.sleep(1)
        
        demonstrate_role_variations()
        
        print_separator("Demonstration Complete")
        print("🎉 SimpleChaseAgent demonstration completed successfully!")
        print("\n📋 Summary of SimpleChaseAgent capabilities:")
        print("   ✅ Aggressive pursuit of nearest enemies")
        print("   ✅ Intelligent target selection with persistence")
        print("   ✅ Tactical retreat when health is low")
        print("   ✅ Distance-based speed adjustment")
        print("   ✅ Combat preference based on range")
        print("   ✅ Consistent behavior across different roles")
        print("   ✅ Comprehensive tracking and statistics")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        raise


if __name__ == "__main__":
    main()

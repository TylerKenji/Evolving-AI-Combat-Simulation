"""
RandomAgent Demo

This demo shows the RandomAgent in action, demonstrating its random
decision-making capabilities and unpredictable behavior patterns.
"""

import time
import random
from src.agents.random_agent import RandomAgent
from src.agents.base_agent import AgentRole, CombatAction
from src.utils.vector2d import Vector2D


def main():
    """Demonstrate RandomAgent behavior."""
    print("🎲 RandomAgent Demo - Chaos and Unpredictability!")
    print("=" * 60)
    
    # Create a few random agents
    agents = [
        RandomAgent(Vector2D(0, 0), team_id="chaos", role=AgentRole.DPS),
        RandomAgent(Vector2D(100, 50), team_id="mayhem", role=AgentRole.TANK),
        RandomAgent(Vector2D(-50, 100), team_id="chaos", role=AgentRole.SUPPORT)
    ]
    
    # Enable detailed logging for the first agent
    agents[0].enable_detailed_logging(True)
    
    print(f"Created {len(agents)} RandomAgents:")
    for i, agent in enumerate(agents):
        print(f"  {i+1}. {agent}")
        print(f"     Strategy: {agent.get_strategy_description()}")
    
    print("\n" + "=" * 60)
    print("Running simulation for 10 steps...")
    print("=" * 60)
    
    # Simulation parameters
    dt = 0.2  # 200ms per step
    battlefield_info = {
        "terrain": "open_field",
        "time": 0.0,
        "obstacles": []
    }
    
    # Run simulation
    for step in range(10):
        print(f"\n--- Step {step + 1} (t={battlefield_info['time']:.1f}s) ---")
        
        # Update each agent
        for i, agent in enumerate(agents):
            # Update agent
            agent.update(dt, battlefield_info)
            
            # Get other agents as visible agents
            other_agents = [a for a in agents if a != agent]
            
            # Make decisions
            action = agent.decide_action(other_agents, battlefield_info)
            movement = agent.calculate_movement(other_agents, battlefield_info)
            target = agent.select_target([a for a in other_agents if a.team_id != agent.team_id])
            
            # Show agent behavior
            print(f"Agent {i+1} ({agent.agent_id[:8]}):")
            print(f"  Position: ({agent.position.x:.1f}, {agent.position.y:.1f})")
            print(f"  Action: {action.value}")
            print(f"  Movement: ({movement.x:.1f}, {movement.y:.1f}) mag={movement.magnitude():.1f}")
            if target:
                print(f"  Target: {target.agent_id[:8]} (team: {target.team_id})")
            else:
                print(f"  Target: None")
            print(f"  Health: {agent.stats.current_health:.0f}/{agent.stats.max_health}")
        
        # Update simulation time
        battlefield_info["time"] += dt
        
        # Small delay for readability
        time.sleep(0.1)
    
    print("\n" + "=" * 60)
    print("Analyzing RandomAgent Behavior Patterns")
    print("=" * 60)
    
    # Collect behavior statistics
    total_actions = {}
    total_movements = 0
    
    for agent in agents:
        print(f"\nAgent {agent.agent_id[:8]} ({agent.role.value}) Final Analysis:")
        
        # Test multiple decisions to show randomness
        test_actions = []
        test_movements = []
        
        for _ in range(20):
            action = agent.decide_action(agents, battlefield_info)
            movement = agent.calculate_movement(agents, battlefield_info)
            test_actions.append(action)
            test_movements.append(movement.magnitude())
        
        # Count action frequencies
        action_counts = {}
        for action in test_actions:
            action_counts[action.value] = action_counts.get(action.value, 0) + 1
        
        print(f"  Action Distribution (20 samples):")
        for action, count in sorted(action_counts.items()):
            percentage = (count / 20) * 100
            print(f"    {action}: {count}/20 ({percentage:.0f}%)")
        
        print(f"  Movement Speed Range: {min(test_movements):.1f} - {max(test_movements):.1f}")
        print(f"  Average Movement Speed: {sum(test_movements)/len(test_movements):.1f}")
        
        # Count unique movements
        unique_movements = len(set(round(m, 1) for m in test_movements))
        print(f"  Movement Variety: {unique_movements}/20 unique speeds")
    
    print("\n" + "=" * 60)
    print("RandomAgent Demo Complete!")
    print("=" * 60)
    print("Key Observations:")
    print("• RandomAgents make unpredictable decisions")
    print("• Movement patterns vary randomly over time")
    print("• Action selection shows statistical variation")
    print("• Perfect for testing system robustness")
    print("• Provides baseline for AI strategy comparison")
    

if __name__ == "__main__":
    main()

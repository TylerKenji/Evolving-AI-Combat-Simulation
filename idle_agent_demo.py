"""
IdleAgent Demo

This demo shows the IdleAgent in action, demonstrating its complete inactivity
and comparing it with the RandomAgent to highlight the contrast between
active and passive behavior.
"""

import time
from src.agents.idle_agent import IdleAgent
from src.agents.random_agent import RandomAgent
from src.agents.base_agent import AgentRole, CombatAction
from src.utils.vector2d import Vector2D


def main():
    """Demonstrate IdleAgent behavior and contrast with RandomAgent."""
    print("😴 IdleAgent Demo - The Art of Doing Nothing!")
    print("=" * 60)
    
    # Create agents for comparison
    idle_agent = IdleAgent(Vector2D(0, 0), team_id="peaceful", role=AgentRole.SUPPORT)
    random_agent = RandomAgent(Vector2D(100, 0), team_id="chaos", role=AgentRole.DPS)
    target_dummy = IdleAgent(Vector2D(50, 50), team_id="targets", role=AgentRole.TANK)
    
    agents = [idle_agent, random_agent, target_dummy]
    
    # Enable detailed logging for the idle agent
    idle_agent.enable_detailed_logging(True)
    
    print("Created agents for comparison:")
    for i, agent in enumerate(agents):
        print(f"  {i+1}. {agent}")
        print(f"     Strategy: {agent.get_strategy_description()}")
    
    print("\n" + "=" * 60)
    print("Running comparative simulation for 8 steps...")
    print("=" * 60)
    
    # Simulation parameters
    dt = 0.25  # 250ms per step
    battlefield_info = {
        "terrain": "testing_ground",
        "time": 0.0,
        "obstacles": []
    }
    
    # Track agent behaviors for analysis
    idle_positions = []
    random_positions = []
    actions_taken = {"idle": [], "random": []}
    
    # Run simulation
    for step in range(8):
        print(f"\n--- Step {step + 1} (t={battlefield_info['time']:.2f}s) ---")
        
        # Update each agent
        for i, agent in enumerate(agents):
            # Get other agents as visible agents
            other_agents = [a for a in agents if a != agent]
            
            # Update agent
            agent.update(dt, battlefield_info)
            
            # Make decisions
            action = agent.decide_action(other_agents, battlefield_info)
            movement = agent.calculate_movement(other_agents, battlefield_info)
            target = agent.select_target([a for a in other_agents if a.team_id != agent.team_id])
            
            # Track positions and actions for later analysis
            if isinstance(agent, IdleAgent) and agent == idle_agent:
                idle_positions.append((agent.position.x, agent.position.y))
                actions_taken["idle"].append(action)
            elif isinstance(agent, RandomAgent):
                random_positions.append((agent.position.x, agent.position.y))
                actions_taken["random"].append(action)
            
            # Show agent behavior
            agent_type = "Idle" if isinstance(agent, IdleAgent) else "Random"
            print(f"{agent_type} Agent {i+1} ({agent.agent_id[:8]}):")
            print(f"  Position: ({agent.position.x:.1f}, {agent.position.y:.1f})")
            print(f"  Action: {action.value}")
            print(f"  Movement Vector: ({movement.x:.1f}, {movement.y:.1f}) mag={movement.magnitude():.1f}")
            if target:
                print(f"  Target: {target.agent_id[:8]} (team: {target.team_id})")
            else:
                print(f"  Target: None")
            print(f"  Health: {agent.stats.current_health:.0f}/{agent.stats.max_health}")
            
            # Show idle-specific stats
            if isinstance(agent, IdleAgent):
                stats = agent.get_idle_statistics()
                print(f"  Idle Time: {stats['total_idle_time']:.2f}s")
                print(f"  Updates: {stats['update_count']}")
        
        # Update simulation time
        battlefield_info["time"] += dt
        
        # Small delay for readability
        time.sleep(0.1)
    
    print("\n" + "=" * 60)
    print("Behavior Analysis: Idle vs Random Agents")
    print("=" * 60)
    
    # Analyze idle agent behavior
    print(f"\n🔍 IdleAgent Analysis:")
    idle_stats = idle_agent.get_idle_statistics()
    print(f"  Total Idle Time: {idle_stats['total_idle_time']:.2f}s")
    print(f"  Total Updates: {idle_stats['update_count']}")
    print(f"  Position Changes: {len(set(idle_positions))} unique positions")
    print(f"  Action Variety: {len(set(actions_taken['idle']))} unique actions")
    print(f"  Consistent Action: {actions_taken['idle'][0].value} (all {len(actions_taken['idle'])} times)")
    print(f"  Movement Distance: 0.0 units (completely stationary)")
    
    # Analyze random agent behavior  
    print(f"\n🎲 RandomAgent Analysis:")
    print(f"  Position Changes: {len(set(random_positions))} unique positions")
    print(f"  Action Variety: {len(set(actions_taken['random']))} unique actions")
    action_counts = {}
    for action in actions_taken['random']:
        action_counts[action.value] = action_counts.get(action.value, 0) + 1
    print(f"  Action Distribution:")
    for action, count in sorted(action_counts.items()):
        print(f"    {action}: {count}/{len(actions_taken['random'])}")
    
    # Calculate movement distance for random agent
    total_distance = 0.0
    for i in range(1, len(random_positions)):
        prev_pos = Vector2D(random_positions[i-1][0], random_positions[i-1][1])
        curr_pos = Vector2D(random_positions[i][0], random_positions[i][1])
        total_distance += prev_pos.distance_to(curr_pos)
    print(f"  Approximate Movement Distance: {total_distance:.1f} units")
    
    print("\n" + "=" * 60)
    print("Demonstrating Idle Agent Use Cases")
    print("=" * 60)
    
    # Test different use cases
    print("\n1. 🎯 Testing Dummy (Target Practice):")
    dummy = IdleAgent(Vector2D(200, 200), team_id="dummies", role=AgentRole.TANK)
    print(f"   Created: {dummy}")
    print(f"   Perfect for: Target practice, damage testing, AI behavior validation")
    print(f"   Behavior: Stands still, takes damage, never retaliates")
    
    print("\n2. 📊 Performance Baseline:")
    baseline = IdleAgent(Vector2D(300, 300), team_id="baseline", role=AgentRole.BALANCED)
    print(f"   Created: {baseline}")
    print(f"   Perfect for: Measuring other agents' activity, performance comparisons")
    print(f"   Behavior: Zero CPU usage for decisions, minimal resource consumption")
    
    print("\n3. 🧪 Simulation Placeholder:")
    placeholder = IdleAgent(Vector2D(400, 400), team_id="placeholders", role=AgentRole.SUPPORT)
    print(f"   Created: {placeholder}")
    print(f"   Perfect for: Incomplete AI implementations, population padding")
    print(f"   Behavior: Maintains agent count without affecting simulation dynamics")
    
    print("\n" + "=" * 60)
    print("IdleAgent Demo Complete!")
    print("=" * 60)
    print("Key Observations:")
    print("• IdleAgents provide complete behavioral predictability")
    print("• Zero movement and action variation - perfect for controlled testing")
    print("• Minimal computational overhead - ideal for performance baselines")
    print("• Excellent contrast agent for highlighting active AI behaviors")
    print("• Essential tool for systematic AI development and validation")
    

if __name__ == "__main__":
    main()

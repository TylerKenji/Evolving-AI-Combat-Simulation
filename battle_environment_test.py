"""
Quick test to validate BattleEnvironment basic functionality
"""

from src.environment.battle_environment import BattleEnvironment
from src.agents.random_agent import RandomAgent
from src.utils.vector2d import Vector2D

def main():
    print("🧪 Testing BattleEnvironment basic functionality...")
    
    # Test 1: Basic initialization
    print("\n1. Testing basic initialization...")
    try:
        env = BattleEnvironment()
        print(f"✅ Environment created: {env.width}x{env.height}")
        print(f"   Battle phase: {env.battle_phase}")
        print(f"   Agent count: {env.agent_count}")
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return
    
    # Test 2: Team creation
    print("\n2. Testing team creation...")
    try:
        success1 = env.create_team("red", "Red Team", "#FF0000")
        success2 = env.create_team("blue", "Blue Team", "#0000FF")
        print(f"✅ Created teams: Red={success1}, Blue={success2}")
        print(f"   Teams count: {len(env.teams)}")
    except Exception as e:
        print(f"❌ Team creation failed: {e}")
        return
    
    # Test 3: Agent spawning
    print("\n3. Testing agent spawning...")
    try:
        agent1 = RandomAgent(position=Vector2D(100, 100))
        agent2 = RandomAgent(position=Vector2D(200, 200))
        
        success1 = env.add_agent(agent1, team_id="red")
        success2 = env.add_agent(agent2, team_id="blue")
        
        print(f"✅ Spawned agents: Agent1={success1}, Agent2={success2}")
        print(f"   Agent count: {env.agent_count}")
        print(f"   Agent1 team: {env.get_agent_team(agent1.agent_id)}")
        print(f"   Agent2 team: {env.get_agent_team(agent2.agent_id)}")
    except Exception as e:
        print(f"❌ Agent spawning failed: {e}")
        return
    
    # Test 4: Battle lifecycle
    print("\n4. Testing battle lifecycle...")
    try:
        env.start_battle()
        print(f"✅ Battle started: {env.battle_phase}")
        
        # Run a few update cycles
        for i in range(3):
            env.update(0.016)
        print(f"✅ Updated 3 cycles, frame count: {env.metrics.frame_count}")
        
        env.end_battle()
        print(f"✅ Battle ended: {env.battle_phase}")
    except Exception as e:
        print(f"❌ Battle lifecycle failed: {e}")
        return
    
    # Test 5: Battlefield information
    print("\n5. Testing battlefield information...")
    try:
        battlefield_info = env.get_battlefield_info(agent1.agent_id)
        print(f"✅ Battlefield info keys: {list(battlefield_info.keys())}")
        print(f"   Visible agents: {len(battlefield_info['visible_agents'])}")
    except Exception as e:
        print(f"❌ Battlefield info failed: {e}")
        return
    
    print("\n🎉 All basic functionality tests passed!")
    print(f"\nBattle Statistics:")
    stats = env.get_battle_statistics()
    print(f"   Battle phase: {stats['battle_phase']}")
    print(f"   Total agents: {stats['total_agents']}")
    print(f"   Living agents: {stats['living_agents']}")
    print(f"   Frame count: {stats['environment_metrics']['frame_count']}")

if __name__ == "__main__":
    main()

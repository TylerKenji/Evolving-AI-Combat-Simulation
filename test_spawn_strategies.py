#!/usr/bin/env python3
"""
Test script to verify all spawn strategies work correctly after fixing spawn area issues.
"""

from src.environment.battle_environment import BattleEnvironment, SpawnStrategy
from src.agents.idle_agent import IdleAgent

def test_spawn_strategies():
    """Test all spawn strategies to ensure spawn areas are properly assigned."""
    strategies = [
        SpawnStrategy.TEAMS_OPPOSITE, 
        SpawnStrategy.CIRCLE, 
        SpawnStrategy.CORNERS, 
        SpawnStrategy.RANDOM,
        SpawnStrategy.PREDEFINED
    ]

    print("🧪 Testing All Spawn Strategies")
    print("=" * 50)

    for strategy in strategies:
        print(f'\n🎯 Testing {strategy.value} spawn strategy...')
        try:
            config = {'spawn_strategy': strategy.value}
            env = BattleEnvironment(width=800, height=600, config=config)
            env.create_team('red', 'Red Team', '#FF0000')
            env.create_team('blue', 'Blue Team', '#0000FF')
            
            from src.utils.vector2d import Vector2D
            agent1 = IdleAgent(position=Vector2D(100, 100))
            agent2 = IdleAgent(position=Vector2D(200, 200))
            
            result1 = env.add_agent(agent1, team_id='red')
            result2 = env.add_agent(agent2, team_id='blue')
            
            red_area = env.teams["red"].spawn_area is not None
            blue_area = env.teams["blue"].spawn_area is not None
            
            print(f'   ✅ Team spawn areas assigned: Red={red_area}, Blue={blue_area}')
            print(f'   ✅ Agents spawned: Agent1={result1}, Agent2={result2}')
            
            if red_area and blue_area and result1 and result2:
                print(f'   🎉 {strategy.value} strategy: SUCCESS')
            else:
                print(f'   ❌ {strategy.value} strategy: FAILED')
                
        except Exception as e:
            print(f'   ❌ Error testing {strategy.value}: {e}')

    print('\n🎉 All spawn strategy tests completed!')

if __name__ == "__main__":
    test_spawn_strategies()

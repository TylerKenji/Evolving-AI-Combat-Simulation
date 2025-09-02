"""
Tests for BattleResult dataclass
Task 1.3.3: Implement BattleResult dataclass

This module tests the BattleResult and related dataclasses to ensure
proper functionality for capturing battle outcomes and statistics.
"""

import pytest
from datetime import datetime, timedelta
from src.simulation.battle_result import (
    BattleResult,
    AgentBattleResult,
    CombatStatistics,
    BattleOutcome,
    BattleEndReason
)
from src.utils.vector2d import Vector2D


class TestCombatStatistics:
    """Test the CombatStatistics dataclass."""
    
    def test_combat_statistics_creation(self):
        """Test basic creation of combat statistics."""
        stats = CombatStatistics()
        assert stats.damage_dealt == 0.0
        assert stats.attacks_attempted == 0
        assert stats.positions_visited == []
    
    def test_accuracy_calculation(self):
        """Test accuracy percentage calculation."""
        stats = CombatStatistics(attacks_attempted=10, attacks_hit=7)
        assert stats.accuracy == 70.0
        
        # Test zero attempts
        empty_stats = CombatStatistics()
        assert empty_stats.accuracy == 0.0
    
    def test_dodge_success_rate(self):
        """Test dodge success rate calculation."""
        stats = CombatStatistics(dodges_attempted=5, dodges_successful=3)
        assert stats.dodge_success_rate == 60.0
        
        # Test zero attempts
        empty_stats = CombatStatistics()
        assert empty_stats.dodge_success_rate == 0.0
    
    def test_block_success_rate(self):
        """Test block success rate calculation."""
        stats = CombatStatistics(blocks_attempted=8, blocks_successful=6)
        assert stats.block_success_rate == 75.0
    
    def test_damage_efficiency(self):
        """Test damage efficiency calculation."""
        # Normal ratio
        stats = CombatStatistics(damage_dealt=100.0, damage_taken=50.0)
        assert stats.damage_efficiency == 2.0
        
        # No damage taken
        stats_no_damage = CombatStatistics(damage_dealt=100.0, damage_taken=0.0)
        assert stats_no_damage.damage_efficiency == float('inf')
        
        # No damage dealt or taken
        empty_stats = CombatStatistics()
        assert empty_stats.damage_efficiency == 0.0


class TestAgentBattleResult:
    """Test the AgentBattleResult dataclass."""
    
    def test_agent_battle_result_creation(self):
        """Test basic creation of agent battle result."""
        result = AgentBattleResult(agent_id="agent_001", agent_type="Aggressive")
        assert result.agent_id == "agent_001"
        assert result.agent_type == "Aggressive"
        assert result.survived is True
        assert result.outcome == BattleOutcome.DRAW
    
    def test_health_calculation(self):
        """Test health lost calculation."""
        result = AgentBattleResult(
            agent_id="agent_001",
            initial_health=100.0,
            final_health=30.0
        )
        result.calculate_health_lost()
        assert result.health_lost == 70.0
    
    def test_survival_percentage(self):
        """Test survival percentage calculation."""
        result = AgentBattleResult(
            agent_id="agent_001",
            initial_health=100.0,
            final_health=25.0
        )
        assert result.survival_percentage == 25.0
        
        # Test zero initial health
        zero_result = AgentBattleResult(agent_id="agent_002", initial_health=0.0)
        assert zero_result.survival_percentage == 0.0
    
    def test_survival_time_calculation(self):
        """Test survival time calculation."""
        result = AgentBattleResult(agent_id="agent_001")
        battle_duration = timedelta(minutes=3, seconds=30)
        
        result.calculate_survival_time(battle_duration)
        assert result.time_alive == battle_duration


class TestBattleResult:
    """Test the main BattleResult dataclass."""
    
    def test_battle_result_creation(self):
        """Test basic creation of battle result."""
        battle = BattleResult(battle_id="battle_001")
        assert battle.battle_id == "battle_001"
        assert battle.battle_type == "individual"
        assert battle.outcome == BattleOutcome.DRAW
        assert len(battle.participants) == 0
    
    def test_add_participant(self):
        """Test adding participants to battle."""
        battle = BattleResult(battle_id="battle_001")
        
        # Add first participant
        result1 = battle.add_participant("agent_001", "Aggressive")
        assert "agent_001" in battle.participants
        assert battle.participants["agent_001"].agent_type == "Aggressive"
        assert result1 == battle.participants["agent_001"]
        
        # Add second participant
        battle.add_participant("agent_002", "Defensive")
        assert len(battle.participants) == 2
    
    def test_factory_creation(self):
        """Test factory method for creating battles."""
        participants = [("agent_001", "Aggressive"), ("agent_002", "Defensive")]
        battle = BattleResult.create_battle("battle_factory", participants, "team")
        
        assert battle.battle_id == "battle_factory"
        assert battle.battle_type == "team"
        assert len(battle.participants) == 2
        assert "agent_001" in battle.participants
        assert "agent_002" in battle.participants
    
    def test_finalize_battle(self):
        """Test battle finalization and statistics calculation."""
        battle = BattleResult(battle_id="battle_001")
        start_time = datetime.now()
        battle.start_time = start_time
        
        # Add participants with some statistics
        agent1 = battle.add_participant("agent_001", "Aggressive")
        agent1.combat_stats.damage_dealt = 50.0
        agent1.combat_stats.attacks_attempted = 10
        agent1.combat_stats.distance_traveled = 100.0
        
        agent2 = battle.add_participant("agent_002", "Defensive")
        agent2.combat_stats.damage_dealt = 30.0
        agent2.combat_stats.attacks_attempted = 5
        agent2.combat_stats.distance_traveled = 80.0
        
        # Finalize battle
        end_time = start_time + timedelta(minutes=2)
        battle.finalize_battle(end_time)
        
        assert battle.end_time == end_time
        assert battle.duration == timedelta(minutes=2)
        assert battle.total_damage_dealt == 80.0
        assert battle.total_attacks_made == 15
        assert battle.total_distance_traveled == 180.0
    
    def test_determine_winner_single_survivor(self):
        """Test winner determination with single survivor."""
        battle = BattleResult(battle_id="battle_001")
        
        # Add participants
        agent1 = battle.add_participant("agent_001", "Aggressive")
        agent1.survived = True
        agent1.final_health = 50.0
        
        agent2 = battle.add_participant("agent_002", "Defensive")
        agent2.survived = False
        agent2.final_health = 0.0
        
        battle.outcome = BattleOutcome.VICTORY
        battle._determine_winner()
        
        assert battle.winner_id == "agent_001"
        assert battle.loser_id == "agent_002"
        assert battle.outcome == BattleOutcome.VICTORY
    
    def test_determine_winner_multiple_survivors(self):
        """Test winner determination with multiple survivors."""
        battle = BattleResult(battle_id="battle_001")
        
        # Add participants - both survive but one has more health
        agent1 = battle.add_participant("agent_001", "Aggressive")
        agent1.survived = True
        agent1.final_health = 30.0
        
        agent2 = battle.add_participant("agent_002", "Defensive")
        agent2.survived = True
        agent2.final_health = 70.0
        
        battle.outcome = BattleOutcome.VICTORY
        battle._determine_winner()
        
        assert battle.winner_id == "agent_002"  # Higher health
        assert battle.outcome == BattleOutcome.VICTORY
    
    def test_determine_winner_no_survivors(self):
        """Test outcome when no agents survive."""
        battle = BattleResult(battle_id="battle_001")
        
        # Add participants - both die
        agent1 = battle.add_participant("agent_001", "Aggressive")
        agent1.survived = False
        agent1.final_health = 0.0
        
        agent2 = battle.add_participant("agent_002", "Defensive")
        agent2.survived = False
        agent2.final_health = 0.0
        
        battle._determine_winner()
        
        assert battle.winner_id is None
        assert battle.loser_id is None
        assert battle.outcome == BattleOutcome.DRAW
    
    def test_get_participant_results(self):
        """Test retrieving participant results."""
        battle = BattleResult(battle_id="battle_001")
        agent1 = battle.add_participant("agent_001", "Aggressive")
        battle.winner_id = "agent_001"
        
        # Test get specific participant
        result = battle.get_participant_result("agent_001")
        assert result == agent1
        
        # Test get non-existent participant
        none_result = battle.get_participant_result("nonexistent")
        assert none_result is None
        
        # Test get winner
        winner_result = battle.get_winner_result()
        assert winner_result == agent1
        
        # Test get loser (none set)
        loser_result = battle.get_loser_result()
        assert loser_result is None
    
    def test_battle_summary(self):
        """Test battle summary generation."""
        battle = BattleResult(battle_id="battle_001", battle_type="tournament")
        battle.duration = timedelta(minutes=3, seconds=15)
        battle.outcome = BattleOutcome.VICTORY
        battle.end_reason = BattleEndReason.ELIMINATION
        
        # Add participants
        agent1 = battle.add_participant("agent_001", "Aggressive")
        agent1.final_health = 25.0
        battle.winner_id = "agent_001"
        
        agent2 = battle.add_participant("agent_002", "Defensive")
        agent2.final_health = 0.0
        battle.loser_id = "agent_002"
        
        battle.total_damage_dealt = 150.0
        battle.total_attacks_made = 25
        battle.total_distance_traveled = 300.0
        
        summary = battle.to_summary()
        
        assert "battle_001" in summary
        assert "tournament" in summary
        assert "victory" in summary
        assert "elimination" in summary
        assert "agent_001" in summary
        assert "25.0" in summary
        assert "150.0" in summary


class TestIntegration:
    """Integration tests for complete battle result workflow."""
    
    def test_complete_battle_workflow(self):
        """Test a complete battle from creation to finalization."""
        # Create battle with participants
        participants = [("warrior_001", "Aggressive"), ("defender_001", "Defensive")]
        battle = BattleResult.create_battle("epic_battle", participants, "duel")
        
        # Set initial conditions
        warrior = battle.participants["warrior_001"]
        warrior.initial_health = 100.0
        warrior.initial_position = Vector2D(0, 0)
        
        defender = battle.participants["defender_001"]
        defender.initial_health = 120.0
        defender.initial_position = Vector2D(100, 100)
        
        # Simulate battle progress - warrior wins
        warrior.final_health = 30.0
        warrior.final_position = Vector2D(50, 30)
        warrior.survived = True
        warrior.outcome = BattleOutcome.VICTORY
        warrior.combat_stats.damage_dealt = 120.0
        warrior.combat_stats.damage_taken = 70.0
        warrior.combat_stats.attacks_attempted = 15
        warrior.combat_stats.attacks_hit = 12
        
        defender.final_health = 0.0
        defender.final_position = Vector2D(80, 90)
        defender.survived = False
        defender.outcome = BattleOutcome.DEFEAT
        defender.combat_stats.damage_dealt = 70.0
        defender.combat_stats.damage_taken = 120.0
        defender.combat_stats.attacks_attempted = 8
        defender.combat_stats.attacks_hit = 7
        
        # Set battle outcome
        battle.winner_id = "warrior_001"
        battle.loser_id = "defender_001"
        battle.outcome = BattleOutcome.VICTORY
        battle.end_reason = BattleEndReason.ELIMINATION
        
        # Finalize battle (simulate some time passing)
        import time
        time.sleep(0.001)  # Small delay to ensure duration > 0
        battle.finalize_battle()
        
        # Verify results
        assert battle.duration > timedelta(0)
        assert battle.winner_id == "warrior_001"
        assert battle.loser_id == "defender_001"
        assert battle.total_damage_dealt == 190.0
        assert battle.total_attacks_made == 23
        
        # Test warrior stats
        assert warrior.health_lost == 70.0
        assert warrior.survival_percentage == 30.0
        assert warrior.combat_stats.accuracy == 80.0
        
        # Test defender stats
        assert defender.health_lost == 120.0
        assert defender.survival_percentage == 0.0
        assert defender.combat_stats.accuracy == 87.5
        
        # Test summary
        summary = battle.to_summary()
        assert "epic_battle" in summary
        assert "warrior_001" in summary
        assert "defender_001" in summary

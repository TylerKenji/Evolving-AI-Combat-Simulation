"""
Battle Result Data Structure
Task 1.3.3: Implement BattleResult dataclass

This module provides the BattleResult dataclass for capturing the outcome
and statistics of individual battles in the Battle AI simulation system.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from src.utils.vector2d import Vector2D


class BattleOutcome(Enum):
    """Possible outcomes of a battle."""
    VICTORY = "victory"          # Clear winner determined
    DEFEAT = "defeat"            # Clear loser determined
    DRAW = "draw"                # No clear winner (tie/timeout)
    INTERRUPTED = "interrupted"  # Battle stopped externally
    ERROR = "error"              # Battle ended due to error


class BattleEndReason(Enum):
    """Reasons why a battle ended."""
    ELIMINATION = "elimination"      # One or more agents died
    TIMEOUT = "timeout"              # Maximum time reached
    SURRENDER = "surrender"          # Agent surrendered
    EVACUATION = "evacuation"        # Agent successfully escaped
    SYSTEM_ERROR = "system_error"    # Technical error occurred
    MANUAL_STOP = "manual_stop"      # Manually stopped by user


@dataclass
class CombatStatistics:
    """Statistics for combat performance during a battle."""
    
    # Damage metrics
    damage_dealt: float = 0.0
    damage_taken: float = 0.0
    damage_blocked: float = 0.0
    
    # Attack metrics
    attacks_attempted: int = 0
    attacks_hit: int = 0
    critical_hits: int = 0
    
    # Defense metrics
    dodges_attempted: int = 0
    dodges_successful: int = 0
    blocks_attempted: int = 0
    blocks_successful: int = 0
    
    # Movement metrics
    distance_traveled: float = 0.0
    positions_visited: List[Vector2D] = field(default_factory=list)
    
    # Special abilities
    special_abilities_used: int = 0
    cooperative_actions: int = 0
    
    @property
    def accuracy(self) -> float:
        """Calculate attack accuracy percentage."""
        if self.attacks_attempted == 0:
            return 0.0
        return (self.attacks_hit / self.attacks_attempted) * 100.0
    
    @property
    def dodge_success_rate(self) -> float:
        """Calculate dodge success rate percentage."""
        if self.dodges_attempted == 0:
            return 0.0
        return (self.dodges_successful / self.dodges_attempted) * 100.0
    
    @property
    def block_success_rate(self) -> float:
        """Calculate block success rate percentage."""
        if self.blocks_attempted == 0:
            return 0.0
        return (self.blocks_successful / self.blocks_attempted) * 100.0
    
    @property
    def damage_efficiency(self) -> float:
        """Calculate damage dealt vs damage taken ratio."""
        if self.damage_taken == 0.0:
            return float('inf') if self.damage_dealt > 0.0 else 0.0
        return self.damage_dealt / self.damage_taken


@dataclass
class AgentBattleResult:
    """Battle result for a single agent."""
    
    # Agent identification
    agent_id: str
    agent_type: str = "Unknown"
    
    # Health status
    initial_health: float = 100.0
    final_health: float = 0.0
    health_lost: float = 0.0
    
    # Position tracking
    initial_position: Vector2D = field(default_factory=Vector2D.zero)
    final_position: Vector2D = field(default_factory=Vector2D.zero)
    
    # Combat statistics
    combat_stats: CombatStatistics = field(default_factory=CombatStatistics)
    
    # Outcome for this agent
    outcome: BattleOutcome = BattleOutcome.DRAW
    survived: bool = True
    
    # Performance metrics
    time_alive: timedelta = field(default_factory=timedelta)
    fitness_score: float = 0.0
    
    def calculate_health_lost(self) -> None:
        """Calculate health lost during battle."""
        self.health_lost = self.initial_health - self.final_health
    
    def calculate_survival_time(self, battle_duration: timedelta) -> None:
        """Set survival time based on battle duration."""
        self.time_alive = battle_duration
    
    @property
    def survival_percentage(self) -> float:
        """Calculate percentage of health remaining."""
        if self.initial_health == 0.0:
            return 0.0
        return (self.final_health / self.initial_health) * 100.0


@dataclass
class BattleResult:
    """
    Complete result of a battle between agents.
    
    Captures all relevant information about the battle outcome,
    participant performance, and statistics for analysis and evolution.
    """
    
    # Battle identification
    battle_id: str
    battle_type: str = "individual"  # individual, team, tournament, etc.
    
    # Timing information
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration: timedelta = field(default_factory=timedelta)
    
    # Battle parameters
    max_duration: timedelta = field(default=timedelta(minutes=5))
    battlefield_size: Tuple[float, float] = (1000.0, 1000.0)
    environment_conditions: Dict[str, Any] = field(default_factory=dict)
    
    # Participants and results
    participants: Dict[str, AgentBattleResult] = field(default_factory=dict)
    winner_id: Optional[str] = None
    loser_id: Optional[str] = None
    
    # Battle outcome
    outcome: BattleOutcome = BattleOutcome.DRAW
    end_reason: BattleEndReason = BattleEndReason.TIMEOUT
    
    # Battle statistics
    total_damage_dealt: float = 0.0
    total_attacks_made: int = 0
    total_distance_traveled: float = 0.0
    
    # Event log (optional detailed tracking)
    significant_events: List[str] = field(default_factory=list)
    
    def add_participant(self, agent_id: str, agent_type: str = "Unknown") -> AgentBattleResult:
        """Add a participant to the battle."""
        result = AgentBattleResult(agent_id=agent_id, agent_type=agent_type)
        self.participants[agent_id] = result
        return result
    
    def finalize_battle(self, end_time: Optional[datetime] = None) -> None:
        """Finalize the battle and calculate results."""
        if end_time is None:
            end_time = datetime.now()
        
        self.end_time = end_time
        self.duration = self.end_time - self.start_time
        
        # Calculate battle-wide statistics
        for agent_result in self.participants.values():
            agent_result.calculate_health_lost()
            agent_result.calculate_survival_time(self.duration)
            
            # Aggregate statistics
            self.total_damage_dealt += agent_result.combat_stats.damage_dealt
            self.total_attacks_made += agent_result.combat_stats.attacks_attempted
            self.total_distance_traveled += agent_result.combat_stats.distance_traveled
        
        # Determine winner/loser if not already set
        if self.winner_id is None and self.outcome == BattleOutcome.VICTORY:
            self._determine_winner()
    
    def _determine_winner(self) -> None:
        """Determine winner based on survival and performance."""
        survivors = [
            (agent_id, result) for agent_id, result in self.participants.items()
            if result.survived and result.final_health > 0
        ]
        
        if len(survivors) == 1:
            # Clear winner - only one survivor
            self.winner_id = survivors[0][0]
            self.outcome = BattleOutcome.VICTORY
            
            # Set loser (first non-survivor found)
            for agent_id, result in self.participants.items():
                if not result.survived or result.final_health <= 0:
                    self.loser_id = agent_id
                    break
                    
        elif len(survivors) > 1:
            # Multiple survivors - determine by remaining health
            best_survivor = max(survivors, key=lambda x: x[1].final_health)
            self.winner_id = best_survivor[0]
            self.outcome = BattleOutcome.VICTORY
            
        else:
            # No survivors - it's a draw
            self.outcome = BattleOutcome.DRAW
    
    def get_participant_result(self, agent_id: str) -> Optional[AgentBattleResult]:
        """Get battle result for a specific participant."""
        return self.participants.get(agent_id)
    
    def get_winner_result(self) -> Optional[AgentBattleResult]:
        """Get the winner's battle result."""
        if self.winner_id:
            return self.participants.get(self.winner_id)
        return None
    
    def get_loser_result(self) -> Optional[AgentBattleResult]:
        """Get the loser's battle result."""
        if self.loser_id:
            return self.participants.get(self.loser_id)
        return None
    
    def to_summary(self) -> str:
        """Generate a human-readable summary of the battle result."""
        summary_lines = [
            f"Battle {self.battle_id} ({self.battle_type})",
            f"Duration: {self.duration}",
            f"Outcome: {self.outcome.value}",
            f"End Reason: {self.end_reason.value}",
            f"Participants: {len(self.participants)}",
        ]
        
        if self.winner_id:
            winner = self.participants[self.winner_id]
            summary_lines.append(f"Winner: {self.winner_id} (Health: {winner.final_health:.1f})")
        
        if self.loser_id:
            loser = self.participants[self.loser_id]
            summary_lines.append(f"Loser: {self.loser_id} (Health: {loser.final_health:.1f})")
        
        summary_lines.extend([
            f"Total Damage: {self.total_damage_dealt:.1f}",
            f"Total Attacks: {self.total_attacks_made}",
            f"Total Movement: {self.total_distance_traveled:.1f}",
        ])
        
        return "\n".join(summary_lines)
    
    @classmethod
    def create_battle(cls, battle_id: str, participants: List[Tuple[str, str]], 
                     battle_type: str = "individual") -> 'BattleResult':
        """Factory method to create a new battle with participants."""
        battle = cls(battle_id=battle_id, battle_type=battle_type)
        
        for agent_id, agent_type in participants:
            battle.add_participant(agent_id, agent_type)
        
        return battle

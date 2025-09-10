"""
Basic Decision-Making Framework for Battle AI Agents

This module provides a structured framework for agent decision-making, including
action evaluation, context analysis, and utility-based action selection.

Key Components:
- DecisionContext: Structured information about the current battlefield state
- ActionEvaluator: Utility-based action scoring system
- DecisionMaker: Core decision-making framework
- ActionValidator: Validation system for legal actions
- PrioritySystem: Action prioritization based on agent state and context

This framework helps agents make more intelligent and contextually appropriate
decisions while maintaining flexibility for different agent implementations.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple, Set, Sequence, Callable
from dataclasses import dataclass, field
import logging
import math

from src.utils.vector2d import Vector2D
from src.utils.logging_config import get_logger
from src.agents.base_agent import CombatAction, BaseAgent


class DecisionPriority(Enum):
    """Priority levels for decision making."""
    EMERGENCY = 5    # Immediate survival needs (very low health, surrounded)
    HIGH = 4        # Important tactical decisions (combat, positioning)
    MEDIUM = 3      # Standard actions (movement, target selection)
    LOW = 2         # Opportunistic actions (special abilities, cooperation)
    MINIMAL = 1     # Background actions (idle, patrol)


class ContextType(Enum):
    """Types of battlefield context."""
    SURVIVAL = "survival"        # Health, safety, escape
    COMBAT = "combat"           # Attacking, defending, tactical
    POSITIONING = "positioning"  # Movement, terrain, distance
    COOPERATION = "cooperation"  # Team play, coordination
    OPPORTUNITY = "opportunity"  # Special abilities, advantageous situations


@dataclass
class DecisionContext:
    """
    Comprehensive context information for decision making.
    
    This class aggregates all relevant information about the current
    battlefield state that an agent needs to make informed decisions.
    """
    
    # Basic agent information
    self_agent: 'BaseAgent'
    visible_agents: Sequence['BaseAgent']
    visible_enemies: Sequence['BaseAgent']
    visible_allies: Sequence['BaseAgent']
    battlefield_info: Dict[str, Any]
    dt: float
    
    # Computed context information
    health_percentage: float = field(init=False)
    nearest_enemy: Optional['BaseAgent'] = field(init=False, default=None)
    nearest_ally: Optional['BaseAgent'] = field(init=False, default=None)
    enemy_count: int = field(init=False, default=0)
    ally_count: int = field(init=False, default=0)
    
    # Threat assessment
    immediate_threats: List['BaseAgent'] = field(init=False, default_factory=list)
    distant_threats: List['BaseAgent'] = field(init=False, default_factory=list)
    
    # Tactical information
    is_outnumbered: bool = field(init=False, default=False)
    is_surrounded: bool = field(init=False, default=False)
    has_tactical_advantage: bool = field(init=False, default=False)
    
    # Environmental factors
    near_boundary: bool = field(init=False, default=False)
    escape_routes: List[Vector2D] = field(init=False, default_factory=list)
    
    def __post_init__(self):
        """Calculate derived context information."""
        self._calculate_basic_context()
        self._assess_threats()
        self._analyze_tactical_situation()
        self._evaluate_environment()
    
    def _calculate_basic_context(self):
        """Calculate basic context information."""
        # Health percentage
        if self.self_agent.stats.max_health > 0:
            self.health_percentage = (self.self_agent.stats.current_health / 
                                    self.self_agent.stats.max_health)
        else:
            self.health_percentage = 0.0
        
        # Count agents
        self.enemy_count = len(self.visible_enemies)
        self.ally_count = len(self.visible_allies)
        
        # Find nearest agents
        if self.visible_enemies:
            self.nearest_enemy = min(
                self.visible_enemies,
                key=lambda enemy: self.self_agent.position.distance_to(enemy.position)
            )
        
        if self.visible_allies:
            self.nearest_ally = min(
                self.visible_allies,
                key=lambda ally: self.self_agent.position.distance_to(ally.position)
            )
    
    def _assess_threats(self):
        """Assess immediate and distant threats."""
        agent_pos = self.self_agent.position
        attack_range = self.self_agent.stats.attack_range
        
        for enemy in self.visible_enemies:
            distance = agent_pos.distance_to(enemy.position)
            
            # Immediate threats are within 1.5x attack range
            if distance <= attack_range * 1.5:
                self.immediate_threats.append(enemy)
            else:
                self.distant_threats.append(enemy)
    
    def _analyze_tactical_situation(self):
        """Analyze tactical advantages and disadvantages."""
        # Outnumbered if facing more enemies than allies + self
        self.is_outnumbered = self.enemy_count > (self.ally_count + 1)
        
        # Surrounded if enemies are in multiple directions
        if len(self.immediate_threats) >= 2:
            agent_pos = self.self_agent.position
            directions = []
            
            for threat in self.immediate_threats:
                direction = (threat.position - agent_pos).normalize()
                directions.append(direction)
            
            # Check if threats are in significantly different directions
            if len(directions) >= 2:
                max_angle = 0
                for i in range(len(directions)):
                    for j in range(i + 1, len(directions)):
                        angle = abs(directions[i].angle_to(directions[j]))
                        max_angle = max(max_angle, angle)
                
                # Surrounded if threats span more than 120 degrees
                self.is_surrounded = max_angle > math.pi * 2 / 3
        
        # Tactical advantage if we have more allies or better positioning
        self.has_tactical_advantage = (
            (self.ally_count > self.enemy_count) or
            (self.health_percentage > 0.8 and len(self.immediate_threats) <= 1)
        )
    
    def _evaluate_environment(self):
        """Evaluate environmental factors."""
        # Check if near boundary (simplified - assumes rectangular battlefield)
        agent_pos = self.self_agent.position
        bounds = self.battlefield_info.get('bounds', {})
        
        if bounds:
            margin = 50.0  # Distance from edge to consider "near boundary"
            min_x = bounds.get('min_x', -500)
            max_x = bounds.get('max_x', 500)
            min_y = bounds.get('min_y', -500)
            max_y = bounds.get('max_y', 500)
            
            self.near_boundary = (
                agent_pos.x - min_x < margin or
                max_x - agent_pos.x < margin or
                agent_pos.y - min_y < margin or
                max_y - agent_pos.y < margin
            )
        
        # Calculate basic escape routes (away from immediate threats)
        if self.immediate_threats:
            # Calculate average threat position
            threat_center = Vector2D(0, 0)
            for threat in self.immediate_threats:
                threat_center += threat.position
            threat_center /= len(self.immediate_threats)
            
            # Escape route is opposite direction from threat center
            escape_direction = (agent_pos - threat_center).normalize()
            self.escape_routes.append(escape_direction)


@dataclass
class ActionScore:
    """Score for a potential action."""
    action: CombatAction
    utility: float
    priority: DecisionPriority
    confidence: float
    reasoning: str
    
    @property
    def weighted_score(self) -> float:
        """Calculate weighted score combining utility, priority, and confidence."""
        priority_weight = self.priority.value * 2.0
        return self.utility * priority_weight * self.confidence


class ActionEvaluator(ABC):
    """
    Abstract base class for action evaluation systems.
    
    Different agent types can implement their own evaluation logic
    while using the common decision-making framework.
    """
    
    def __init__(self, agent: 'BaseAgent'):
        self.agent = agent
        self.logger = get_logger(f"ActionEvaluator_{agent.agent_id}")
    
    @abstractmethod
    def evaluate_action(self, action: CombatAction, context: DecisionContext) -> ActionScore:
        """
        Evaluate the utility of a specific action in the given context.
        
        Args:
            action: The action to evaluate
            context: Current battlefield context
            
        Returns:
            Score object with utility, priority, and reasoning
        """
        pass
    
    def evaluate_all_actions(self, context: DecisionContext) -> List[ActionScore]:
        """Evaluate all possible actions and return sorted list."""
        scores = []
        
        for action in CombatAction:
            try:
                score = self.evaluate_action(action, context)
                scores.append(score)
            except Exception as e:
                self.logger.warning(f"Failed to evaluate action {action}: {e}")
        
        # Sort by weighted score (highest first)
        scores.sort(key=lambda s: s.weighted_score, reverse=True)
        return scores


class DefaultActionEvaluator(ActionEvaluator):
    """
    Default implementation of action evaluation.
    
    Provides reasonable baseline behavior that can be used by simple agents
    or as a fallback for more complex evaluators.
    """
    
    def evaluate_action(self, action: CombatAction, context: DecisionContext) -> ActionScore:
        """Evaluate action using default heuristics."""
        
        if action == CombatAction.ATTACK_MELEE:
            return self._evaluate_melee_attack(context)
        elif action == CombatAction.ATTACK_RANGED:
            return self._evaluate_ranged_attack(context)
        elif action == CombatAction.DODGE:
            return self._evaluate_dodge(context)
        elif action == CombatAction.DEFEND:
            return self._evaluate_defend(context)
        elif action == CombatAction.MOVE:
            return self._evaluate_move(context)
        elif action == CombatAction.RETREAT:
            return self._evaluate_retreat(context)
        elif action == CombatAction.USE_SPECIAL:
            return self._evaluate_special(context)
        elif action == CombatAction.COOPERATE:
            return self._evaluate_cooperate(context)
        else:
            return ActionScore(action, 0.0, DecisionPriority.MINIMAL, 0.1, "Unknown action")
    
    def _evaluate_melee_attack(self, context: DecisionContext) -> ActionScore:
        """Evaluate melee attack action."""
        if not context.nearest_enemy:
            return ActionScore(
                CombatAction.ATTACK_MELEE, 0.0, DecisionPriority.LOW, 0.9,
                "No enemies in range"
            )
        
        distance = context.self_agent.position.distance_to(context.nearest_enemy.position)
        melee_range = context.self_agent.stats.attack_range * 0.8  # Slightly less than max
        
        if distance > melee_range:
            utility = 0.1  # Low utility if out of range
            priority = DecisionPriority.LOW
            reasoning = f"Enemy too far ({distance:.1f} > {melee_range:.1f})"
        else:
            utility = 0.8 + (context.health_percentage * 0.2)  # Higher if healthy
            priority = DecisionPriority.HIGH
            reasoning = f"Enemy in melee range ({distance:.1f})"
        
        confidence = 0.8
        return ActionScore(CombatAction.ATTACK_MELEE, utility, priority, confidence, reasoning)
    
    def _evaluate_ranged_attack(self, context: DecisionContext) -> ActionScore:
        """Evaluate ranged attack action."""
        if not context.nearest_enemy:
            return ActionScore(
                CombatAction.ATTACK_RANGED, 0.0, DecisionPriority.LOW, 0.9,
                "No enemies in range"
            )
        
        distance = context.self_agent.position.distance_to(context.nearest_enemy.position)
        ranged_range = context.self_agent.stats.attack_range
        
        if distance > ranged_range:
            utility = 0.0
            priority = DecisionPriority.LOW
            reasoning = f"Enemy out of range ({distance:.1f} > {ranged_range:.1f})"
        else:
            # Prefer ranged when not in immediate danger
            threat_bonus = 0.3 if len(context.immediate_threats) == 0 else -0.2
            utility = 0.6 + threat_bonus + (context.health_percentage * 0.1)
            priority = DecisionPriority.HIGH if len(context.immediate_threats) == 0 else DecisionPriority.MEDIUM
            reasoning = f"Enemy in ranged range ({distance:.1f})"
        
        confidence = 0.7
        return ActionScore(CombatAction.ATTACK_RANGED, utility, priority, confidence, reasoning)
    
    def _evaluate_dodge(self, context: DecisionContext) -> ActionScore:
        """Evaluate dodge action."""
        threat_level = len(context.immediate_threats)
        
        if threat_level == 0:
            utility = 0.1
            priority = DecisionPriority.MINIMAL
            reasoning = "No immediate threats"
        else:
            utility = 0.5 + (threat_level * 0.2) + ((1.0 - context.health_percentage) * 0.3)
            priority = DecisionPriority.HIGH if context.health_percentage < 0.3 else DecisionPriority.MEDIUM
            reasoning = f"Dodge from {threat_level} threats"
        
        confidence = 0.6
        return ActionScore(CombatAction.DODGE, utility, priority, confidence, reasoning)
    
    def _evaluate_defend(self, context: DecisionContext) -> ActionScore:
        """Evaluate defend action."""
        threat_level = len(context.immediate_threats)
        
        if threat_level == 0:
            utility = 0.2
            priority = DecisionPriority.LOW
            reasoning = "No immediate threats"
        elif context.is_surrounded or threat_level >= 3:
            utility = 0.7 + ((1.0 - context.health_percentage) * 0.2)
            priority = DecisionPriority.HIGH
            reasoning = f"Surrounded by {threat_level} enemies"
        else:
            utility = 0.4 + (threat_level * 0.1)
            priority = DecisionPriority.MEDIUM
            reasoning = f"Defend against {threat_level} threats"
        
        confidence = 0.7
        return ActionScore(CombatAction.DEFEND, utility, priority, confidence, reasoning)
    
    def _evaluate_move(self, context: DecisionContext) -> ActionScore:
        """Evaluate move action."""
        # Movement is almost always useful
        base_utility = 0.5
        
        # Higher utility if need to position better
        if context.nearest_enemy:
            distance = context.self_agent.position.distance_to(context.nearest_enemy.position)
            optimal_range = context.self_agent.stats.attack_range * 0.7
            
            if distance > optimal_range * 1.5:
                utility = base_utility + 0.3  # Need to get closer
                reasoning = "Move closer to enemy"
            elif distance < optimal_range * 0.5:
                utility = base_utility + 0.2  # Need to back up
                reasoning = "Move to better range"
            else:
                utility = base_utility
                reasoning = "Maintain position"
        else:
            utility = base_utility + 0.1
            reasoning = "General movement"
        
        priority = DecisionPriority.MEDIUM
        confidence = 0.8
        return ActionScore(CombatAction.MOVE, utility, priority, confidence, reasoning)
    
    def _evaluate_retreat(self, context: DecisionContext) -> ActionScore:
        """Evaluate retreat action."""
        # High utility when in danger
        if context.health_percentage < 0.3:
            utility = 0.8 + ((1.0 - context.health_percentage) * 0.2)
            priority = DecisionPriority.EMERGENCY
            reasoning = f"Critical health ({context.health_percentage:.1%})"
        elif context.is_surrounded:
            utility = 0.7
            priority = DecisionPriority.HIGH
            reasoning = "Surrounded by enemies"
        elif context.is_outnumbered and len(context.immediate_threats) > 0:
            utility = 0.6
            priority = DecisionPriority.HIGH
            reasoning = f"Outnumbered ({context.enemy_count} vs {context.ally_count + 1})"
        else:
            utility = 0.1
            priority = DecisionPriority.LOW
            reasoning = "No retreat needed"
        
        confidence = 0.9
        return ActionScore(CombatAction.RETREAT, utility, priority, confidence, reasoning)
    
    def _evaluate_special(self, context: DecisionContext) -> ActionScore:
        """Evaluate special ability action."""
        # Simple heuristic - use special abilities when in combat
        if context.immediate_threats:
            utility = 0.4 + (len(context.immediate_threats) * 0.1)
            priority = DecisionPriority.MEDIUM
            reasoning = f"Special ability vs {len(context.immediate_threats)} threats"
        else:
            utility = 0.1
            priority = DecisionPriority.LOW
            reasoning = "No immediate need for special ability"
        
        confidence = 0.5  # Lower confidence as special abilities are complex
        return ActionScore(CombatAction.USE_SPECIAL, utility, priority, confidence, reasoning)
    
    def _evaluate_cooperate(self, context: DecisionContext) -> ActionScore:
        """Evaluate cooperation action."""
        if not context.visible_allies:
            utility = 0.0
            priority = DecisionPriority.MINIMAL
            reasoning = "No allies to cooperate with"
        elif context.has_tactical_advantage and context.immediate_threats:
            utility = 0.5
            priority = DecisionPriority.MEDIUM
            reasoning = "Coordinate attack with allies"
        else:
            utility = 0.2
            priority = DecisionPriority.LOW
            reasoning = "General cooperation opportunity"
        
        confidence = 0.4  # Lower confidence as cooperation is complex
        return ActionScore(CombatAction.COOPERATE, utility, priority, confidence, reasoning)


class ActionValidator:
    """
    Validates whether actions are legal/possible in the current context.
    
    This class checks constraints like cooldowns, resources, range, etc.
    to ensure that only valid actions are considered.
    """
    
    def __init__(self, agent: 'BaseAgent'):
        self.agent = agent
        self.logger = get_logger(f"ActionValidator_{agent.agent_id}")
    
    def is_action_valid(self, action: CombatAction, context: DecisionContext) -> Tuple[bool, str]:
        """
        Check if an action is valid in the current context.
        
        Args:
            action: Action to validate
            context: Current battlefield context
            
        Returns:
            Tuple of (is_valid, reason)
        """
        
        if action == CombatAction.ATTACK_MELEE:
            return self._validate_melee_attack(context)
        elif action == CombatAction.ATTACK_RANGED:
            return self._validate_ranged_attack(context)
        elif action == CombatAction.DODGE:
            return self._validate_dodge(context)
        elif action == CombatAction.DEFEND:
            return self._validate_defend(context)
        elif action == CombatAction.MOVE:
            return self._validate_move(context)
        elif action == CombatAction.RETREAT:
            return self._validate_retreat(context)
        elif action == CombatAction.USE_SPECIAL:
            return self._validate_special(context)
        elif action == CombatAction.COOPERATE:
            return self._validate_cooperate(context)
        else:
            return False, "Unknown action type"
    
    def _validate_melee_attack(self, context: DecisionContext) -> Tuple[bool, str]:
        """Validate melee attack."""
        if not self.agent.can_attack:
            return False, "Attack on cooldown"
        
        if not context.nearest_enemy:
            return False, "No enemy targets"
        
        distance = self.agent.position.distance_to(context.nearest_enemy.position)
        if distance > self.agent.stats.attack_range:
            return False, f"Target out of range ({distance:.1f} > {self.agent.stats.attack_range})"
        
        return True, "Valid melee attack"
    
    def _validate_ranged_attack(self, context: DecisionContext) -> Tuple[bool, str]:
        """Validate ranged attack."""
        if not self.agent.can_attack:
            return False, "Attack on cooldown"
        
        if not context.nearest_enemy:
            return False, "No enemy targets"
        
        distance = self.agent.position.distance_to(context.nearest_enemy.position)
        if distance > self.agent.stats.attack_range:
            return False, f"Target out of range ({distance:.1f} > {self.agent.stats.attack_range})"
        
        return True, "Valid ranged attack"
    
    def _validate_dodge(self, context: DecisionContext) -> Tuple[bool, str]:
        """Validate dodge action."""
        # Dodge is almost always valid if agent is alive
        if self.agent.is_alive:
            return True, "Valid dodge"
        return False, "Agent is dead"
    
    def _validate_defend(self, context: DecisionContext) -> Tuple[bool, str]:
        """Validate defend action."""
        if self.agent.is_alive:
            return True, "Valid defend"
        return False, "Agent is dead"
    
    def _validate_move(self, context: DecisionContext) -> Tuple[bool, str]:
        """Validate move action."""
        if self.agent.is_alive:
            return True, "Valid move"
        return False, "Agent is dead"
    
    def _validate_retreat(self, context: DecisionContext) -> Tuple[bool, str]:
        """Validate retreat action."""
        if self.agent.is_alive:
            return True, "Valid retreat"
        return False, "Agent is dead"
    
    def _validate_special(self, context: DecisionContext) -> Tuple[bool, str]:
        """Validate special ability."""
        # For now, assume special abilities are always available
        # In future versions, this could check resources, cooldowns, etc.
        if self.agent.is_alive:
            return True, "Valid special ability"
        return False, "Agent is dead"
    
    def _validate_cooperate(self, context: DecisionContext) -> Tuple[bool, str]:
        """Validate cooperation action."""
        if not self.agent.is_alive:
            return False, "Agent is dead"
        
        if not context.visible_allies:
            return False, "No allies to cooperate with"
        
        return True, "Valid cooperation"
    
    def filter_valid_actions(self, scores: List[ActionScore], context: DecisionContext) -> List[ActionScore]:
        """Filter action scores to only include valid actions."""
        valid_scores = []
        
        for score in scores:
            is_valid, reason = self.is_action_valid(score.action, context)
            if is_valid:
                valid_scores.append(score)
            else:
                self.logger.debug(f"Filtered out {score.action}: {reason}")
        
        return valid_scores


class DecisionMaker:
    """
    Core decision-making framework that coordinates context analysis,
    action evaluation, validation, and final selection.
    
    This is the main interface that agents use to make decisions.
    """
    
    def __init__(self, agent: 'BaseAgent', evaluator: Optional[ActionEvaluator] = None):
        self.agent = agent
        self.evaluator = evaluator or DefaultActionEvaluator(agent)
        self.validator = ActionValidator(agent)
        self.logger = get_logger(f"DecisionMaker_{agent.agent_id}")
        
        # Decision history for learning/debugging
        self.decision_history: List[Tuple[DecisionContext, ActionScore]] = []
    
    def decide_action(self, visible_agents: Sequence['BaseAgent'], 
                     battlefield_info: Dict[str, Any], dt: float = 1.0) -> CombatAction:
        """
        Make a decision about what action to take.
        
        Args:
            visible_agents: All agents visible to this agent
            battlefield_info: Current battlefield state
            dt: Time step
            
        Returns:
            The selected action
        """
        # Create decision context
        context = self._create_context(visible_agents, battlefield_info, dt)
        
        # Evaluate all possible actions
        action_scores = self.evaluator.evaluate_all_actions(context)
        
        # Filter to only valid actions
        valid_scores = self.validator.filter_valid_actions(action_scores, context)
        
        # Select best action
        if valid_scores:
            selected_score = valid_scores[0]  # Already sorted by weighted score
            selected_action = selected_score.action
            
            # Log decision
            self.logger.debug(
                f"Selected {selected_action} (score: {selected_score.weighted_score:.2f}, "
                f"reasoning: {selected_score.reasoning})"
            )
            
            # Store decision history
            self.decision_history.append((context, selected_score))
            
            # Limit history size
            if len(self.decision_history) > 100:
                self.decision_history = self.decision_history[-50:]
        
        else:
            # Fallback to basic movement if no valid actions
            selected_action = CombatAction.MOVE
            self.logger.warning("No valid actions found, defaulting to MOVE")
        
        return selected_action
    
    def _create_context(self, visible_agents: Sequence['BaseAgent'], 
                       battlefield_info: Dict[str, Any], dt: float) -> DecisionContext:
        """Create decision context from current battlefield state."""
        
        # Separate enemies and allies
        enemies = []
        allies = []
        
        for agent in visible_agents:
            if agent.agent_id != self.agent.agent_id:
                # For now, assume all other agents are enemies
                # In future versions, this would check team affiliation
                if hasattr(agent, 'team_id') and hasattr(self.agent, 'team_id'):
                    if agent.team_id != self.agent.team_id:
                        enemies.append(agent)
                    else:
                        allies.append(agent)
                else:
                    enemies.append(agent)  # Default to enemy if no team info
        
        return DecisionContext(
            self_agent=self.agent,
            visible_agents=visible_agents,
            visible_enemies=enemies,
            visible_allies=allies,
            battlefield_info=battlefield_info,
            dt=dt
        )
    
    def get_decision_summary(self, last_n: int = 5) -> str:
        """Get a summary of recent decisions for debugging."""
        if not self.decision_history:
            return "No decision history available"
        
        recent_decisions = self.decision_history[-last_n:]
        summary_lines = [f"Recent decisions for agent {self.agent.agent_id}:"]
        
        for i, (context, score) in enumerate(recent_decisions):
            summary_lines.append(
                f"  {i+1}. {score.action} (score: {score.weighted_score:.2f}) - {score.reasoning}"
            )
        
        return "\n".join(summary_lines)


# Convenience function for agents to create decision makers
def create_decision_maker(agent: 'BaseAgent', 
                         evaluator_class: Optional[type] = None) -> DecisionMaker:
    """
    Create a decision maker for an agent.
    
    Args:
        agent: The agent that will use this decision maker
        evaluator_class: Optional custom evaluator class
        
    Returns:
        Configured DecisionMaker instance
    """
    if evaluator_class:
        evaluator = evaluator_class(agent)
    else:
        evaluator = DefaultActionEvaluator(agent)
    
    return DecisionMaker(agent, evaluator)

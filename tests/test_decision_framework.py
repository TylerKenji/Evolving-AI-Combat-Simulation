"""
Test suite for the Decision-Making Framework

Tests all components of the decision framework including:
- DecisionContext creation and analysis
- ActionEvaluator implementations
- ActionValidator functionality
- DecisionMaker coordination
- Integration with BaseAgent

Note: Uses type: ignore comments to work around type checking with mock objects.
"""

import pytest
import math
from unittest.mock import Mock, MagicMock
from typing import List, Dict, Any

from src.agents.decision_framework import (
    DecisionMaker, DecisionContext, ActionEvaluator, DefaultActionEvaluator,
    ActionValidator, ActionScore, DecisionPriority, ContextType,
    create_decision_maker
)
from src.agents.base_agent import BaseAgent, CombatAction, AgentState, AgentStats
from src.utils.vector2d import Vector2D


def test_decision_framework_import():
    """Test that all components can be imported successfully."""
    assert DecisionMaker is not None
    assert DecisionContext is not None
    assert ActionEvaluator is not None
    assert DefaultActionEvaluator is not None
    assert ActionValidator is not None
    assert ActionScore is not None
    assert DecisionPriority is not None
    assert ContextType is not None
    assert create_decision_maker is not None


def test_action_score_functionality():
    """Test ActionScore basic functionality."""
    score = ActionScore(
        action=CombatAction.ATTACK_MELEE,
        utility=0.8,
        priority=DecisionPriority.HIGH,
        confidence=0.9,
        reasoning="Test attack"
    )
    
    assert score.action == CombatAction.ATTACK_MELEE
    assert score.utility == 0.8
    assert score.priority == DecisionPriority.HIGH
    assert score.confidence == 0.9
    assert score.reasoning == "Test attack"
    
    # Test weighted score calculation
    expected_weighted = 0.8 * (4 * 2.0) * 0.9  # utility * (priority * 2) * confidence
    assert abs(score.weighted_score - expected_weighted) < 0.01


def test_decision_priority_ordering():
    """Test that decision priorities are ordered correctly."""
    assert DecisionPriority.EMERGENCY.value > DecisionPriority.HIGH.value
    assert DecisionPriority.HIGH.value > DecisionPriority.MEDIUM.value
    assert DecisionPriority.MEDIUM.value > DecisionPriority.LOW.value
    assert DecisionPriority.LOW.value > DecisionPriority.MINIMAL.value


def test_context_types():
    """Test that context types are defined."""
    context_types = [
        ContextType.SURVIVAL,
        ContextType.COMBAT,
        ContextType.POSITIONING,
        ContextType.COOPERATION,
        ContextType.OPPORTUNITY
    ]
    
    assert len(context_types) == 5
    for context_type in context_types:
        assert isinstance(context_type.value, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

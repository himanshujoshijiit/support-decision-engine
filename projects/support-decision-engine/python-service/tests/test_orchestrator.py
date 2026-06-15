"""Tests for the Decision Orchestrator — the policy trust boundary.

The orchestrator must guarantee that a model can never recommend an action outside the
policy-allowed set, and that refund amounts never exceed the policy ceiling.

Run from the python-service directory:  pytest
"""
from __future__ import annotations

from app.models import Decision, PolicyResult, RecommendedAction
from app.orchestrator import DecisionOrchestrator

ORCH = DecisionOrchestrator()


def _decision(action: str, amount: float | None = None, confidence: float = 0.95) -> Decision:
    return Decision(
        ticket_id="T-orch",
        customer_id="cus_x",
        recommended_action=RecommendedAction(action),
        confidence=confidence,
        reason="model rationale",
        amount_usd=amount,
        auto_executed=True,
    )


def test_clamps_disallowed_action_to_decisive():
    """Model tries to APPROVE_REFUND but policy only allows DENY/ESCALATE -> clamp."""
    policy = PolicyResult(
        decisive_action="DENY_REFUND",
        allowed_actions=["DENY_REFUND", "ESCALATE", "RESPOND", "ASK_CLARIFICATION"],
    )
    decision = ORCH.enforce(_decision("APPROVE_REFUND", amount=500), policy)

    assert decision.recommended_action == RecommendedAction.DENY_REFUND
    assert decision.policy_clamped is True
    assert "policy_clamped" in decision.flags
    assert decision.auto_executed is False
    assert decision.amount_usd is None  # cleared: not a refund approval
    assert decision.confidence <= 0.7


def test_allowed_action_passes_through_untouched():
    policy = PolicyResult(
        decisive_action="APPROVE_REFUND",
        allowed_actions=["APPROVE_REFUND", "ASK_CLARIFICATION", "ESCALATE"],
        max_refund_usd=200,
    )
    decision = ORCH.enforce(_decision("APPROVE_REFUND", amount=49), policy)

    assert decision.recommended_action == RecommendedAction.APPROVE_REFUND
    assert decision.policy_clamped is False
    assert decision.amount_usd == 49
    assert decision.allowed_actions == ["APPROVE_REFUND", "ASK_CLARIFICATION", "ESCALATE"]


def test_refund_amount_capped_to_ceiling():
    policy = PolicyResult(
        decisive_action="APPROVE_REFUND",
        allowed_actions=["APPROVE_REFUND", "ESCALATE"],
        max_refund_usd=200,
    )
    decision = ORCH.enforce(_decision("APPROVE_REFUND", amount=999), policy)

    assert decision.amount_usd == 200
    assert "amount_capped" in decision.flags


def test_falls_back_to_safe_action_when_decisive_not_allowed():
    """If even the decisive action isn't in allowed, pick the safest allowed action."""
    policy = PolicyResult(
        decisive_action="APPROVE_REFUND",  # not in allowed below
        allowed_actions=["ESCALATE", "RESPOND"],
    )
    decision = ORCH.enforce(_decision("APPROVE_REFUND"), policy)

    assert decision.recommended_action == RecommendedAction.ESCALATE
    assert decision.policy_clamped is True


def test_clarifying_question_only_kept_for_ask():
    policy = PolicyResult(
        decisive_action="RESPOND",
        allowed_actions=["RESPOND", "ASK_CLARIFICATION", "ESCALATE"],
    )
    d = _decision("RESPOND")
    d.clarifying_question = "leftover question"
    result = ORCH.enforce(d, policy)
    assert result.clarifying_question is None

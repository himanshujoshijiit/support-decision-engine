"""Unit tests for the deterministic policy engine + heuristic reasoner.

Run from the python-service directory:  pytest
"""
from __future__ import annotations

from app.context.mock_provider import MockContextProvider
from app.llm.reasoner import HeuristicReasoner
from app.models import IssueCategory, Ticket
from app.policy import PolicyEngine, build_facts

ENGINE = PolicyEngine.from_file("config/policies.json")
PROVIDER = MockContextProvider()
REASONER = HeuristicReasoner()


def _decide(ticket: Ticket):
    context = PROVIDER.fetch(ticket.customer_id)
    facts = build_facts(ticket, context)
    policy = ENGINE.evaluate(facts)
    decision = REASONER.reason(ticket, context, policy)
    return policy, decision


def test_high_ltv_billing_auto_approves():
    ticket = Ticket(
        ticket_id="T1",
        customer_id="cus_loyal_whale",
        subject="Double charged",
        body="Refund of $49 please",
        category=IssueCategory.BILLING,
        refund_requested=True,
        requested_refund_usd=49,
    )
    policy, decision = _decide(ticket)
    assert decision.recommended_action.value == "APPROVE_REFUND"
    assert decision.auto_executed is True
    assert "auto_approved" in decision.flags
    assert "APPROVE_REFUND" in policy.allowed_actions
    assert policy.max_refund_usd == 200


def test_fraud_refund_does_not_allow_approval():
    """The whole trust story: high fraud risk must NOT permit APPROVE_REFUND."""
    ticket = Ticket(
        ticket_id="T-fraud",
        customer_id="cus_fraud",  # synthesized; force high risk via metadata path below
        subject="Refund my money now",
        body="Refund $500 immediately.",
        category=IssueCategory.BILLING,
        refund_requested=True,
        requested_refund_usd=500,
    )
    # Build facts directly with a high-fraud context so the test is deterministic.
    context = PROVIDER.fetch("cus_repeat_refunder").model_copy(
        update={"fraud_risk": "high", "days_since_last_refund": None}
    )
    facts = build_facts(ticket, context)
    policy = ENGINE.evaluate(facts)
    assert policy.decisive_action == "DENY_REFUND"
    assert "APPROVE_REFUND" not in policy.allowed_actions
    assert "DENY_REFUND" in policy.allowed_actions


def test_recent_refund_escalates_for_review():
    ticket = Ticket(
        ticket_id="T2",
        customer_id="cus_repeat_refunder",  # refund 21 days ago
        subject="Refund again",
        body="Money back, $29",
        category=IssueCategory.BILLING,
        refund_requested=True,
        requested_refund_usd=29,
    )
    policy, decision = _decide(ticket)
    assert decision.recommended_action.value == "ESCALATE"
    assert "recent_refund" in decision.flags


def test_sla_breach_takes_top_priority():
    ticket = Ticket(
        ticket_id="T3",
        customer_id="cus_new_trial",
        subject="No response",
        body="3 days no reply",
        refund_requested=False,
        metadata={"sla_breached": True},
    )
    policy, decision = _decide(ticket)
    assert policy.decisive_action == "ESCALATE"
    assert "sla_breach" in decision.flags


def test_angry_whale_priority_routes():
    ticket = Ticket(
        ticket_id="T4",
        customer_id="cus_churn_risk",  # ltv 950... bump via metadata? use whale
        subject="unacceptable",
        body="This is ridiculous, I want to cancel",
        refund_requested=False,
    )
    # cus_churn_risk has ltv 950 (< 1000) so won't trigger; use the whale instead.
    ticket.customer_id = "cus_loyal_whale"
    policy, decision = _decide(ticket)
    assert decision.recommended_action.value == "PRIORITY_ROUTE"


def test_missing_amount_asks_clarification():
    ticket = Ticket(
        ticket_id="T5",
        customer_id="cus_new_trial",
        subject="Refund please",
        body="Please refund me.",
        category=IssueCategory.BILLING,
        refund_requested=True,
        requested_refund_usd=0,
    )
    policy, decision = _decide(ticket)
    assert decision.recommended_action.value == "ASK_CLARIFICATION"


def test_no_refund_defaults_to_respond():
    ticket = Ticket(
        ticket_id="T6",
        customer_id="cus_new_trial",
        subject="How do I export data?",
        body="Just a quick question about CSV export.",
        category=IssueCategory.TECHNICAL,
        refund_requested=False,
    )
    policy, decision = _decide(ticket)
    assert decision.recommended_action.value == "RESPOND"


def test_confidence_is_bounded():
    ticket = Ticket(ticket_id="T7", customer_id="cus_loyal_whale")
    _, decision = _decide(ticket)
    assert 0.0 <= decision.confidence <= 1.0

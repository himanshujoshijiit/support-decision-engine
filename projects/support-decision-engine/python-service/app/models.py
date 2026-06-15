"""Domain models shared across the pipeline.

These are the contracts between the stages: intake -> context -> policy -> llm -> audit.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


class IssueCategory(str, Enum):
    BILLING = "billing"
    TECHNICAL = "technical"
    ACCOUNT = "account"
    SHIPPING = "shipping"
    OTHER = "other"


class RecommendedAction(str, Enum):
    APPROVE_REFUND = "APPROVE_REFUND"
    DENY_REFUND = "DENY_REFUND"
    ESCALATE = "ESCALATE"
    ASK_CLARIFICATION = "ASK_CLARIFICATION"
    RESPOND = "RESPOND"
    PRIORITY_ROUTE = "PRIORITY_ROUTE"


class Ticket(BaseModel):
    """A normalized support ticket, independent of the source helpdesk."""

    ticket_id: str
    customer_id: str
    requester_email: str = ""
    subject: str = ""
    body: str = ""
    source: str = "manual"  # zendesk | intercom | freshdesk | manual
    category: IssueCategory = IssueCategory.OTHER
    refund_requested: bool = False
    requested_refund_usd: float = 0.0
    created_at: datetime = Field(default_factory=_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CustomerContext(BaseModel):
    """Everything we know about the customer, pulled from billing + helpdesk."""

    customer_id: str
    name: str = ""
    email: str = ""
    ltv_usd: float = 0.0
    tenure_months: int = 0
    subscription_status: str = "unknown"  # active | past_due | canceled | trialing
    mrr_usd: float = 0.0
    past_ticket_count: int = 0
    refunds_given_count: int = 0
    days_since_last_refund: int | None = None
    open_disputes: int = 0
    fraud_risk: str = "low"  # low | medium | high


class PolicyMatch(BaseModel):
    rule_id: str
    description: str
    action: str
    priority: int
    effects: dict[str, Any] = Field(default_factory=dict)


class PolicyResult(BaseModel):
    """Output of the deterministic rules engine.

    `allowed_actions` is the trust boundary: the LLM may ONLY recommend an action
    from this set. The orchestrator enforces it. `max_refund_usd`, when set, is the
    hard ceiling the policy permits a refund to be auto/recommended for.
    """

    matches: list[PolicyMatch] = Field(default_factory=list)
    decisive_action: str | None = None
    allowed_actions: list[str] = Field(default_factory=list)
    max_refund_usd: float | None = None
    flags: list[str] = Field(default_factory=list)
    facts: dict[str, Any] = Field(default_factory=dict)


class Decision(BaseModel):
    """The final, auditable recommendation produced by the engine."""

    ticket_id: str
    customer_id: str
    recommended_action: RecommendedAction
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    amount_usd: float | None = None
    clarifying_question: str | None = None
    policy_matches: list[str] = Field(default_factory=list)
    allowed_actions: list[str] = Field(default_factory=list)
    flags: list[str] = Field(default_factory=list)
    source: str = "engine"  # engine = LLM, policy = rules-only fallback
    auto_executed: bool = False
    # True when the orchestrator overrode the model because it tried to recommend
    # an action outside the policy-allowed set. This is the legal/compliance cover.
    policy_clamped: bool = False
    context_snapshot: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_now)

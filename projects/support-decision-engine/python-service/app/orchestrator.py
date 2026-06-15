"""The Decision Orchestrator — the trust boundary of the engine.

    policy (hard rules)  ->  LLM (soft reasoning)  ->  ORCHESTRATOR  ->  Decision

The architectural principle the whole product rests on:

    *Never let the LLM invent an action outside what policy allows.*

The policy engine runs first and emits `allowed_actions`. The LLM/heuristic then
reasons and proposes an action. This module is the gate that enforces the contract:

  1. If the model proposes an action that policy does NOT allow, it is **clamped** back
     to the policy's decisive action (or the safest allowed fallback) and the decision
     is flagged `policy_clamped`. This is the legal/compliance cover.
  2. A recommended refund amount is **capped** at the policy's `max_refund_usd` ceiling.

The orchestrator never widens what the model is allowed to do — it can only narrow it.
"""
from __future__ import annotations

import logging

from app.models import Decision, PolicyResult, RecommendedAction

logger = logging.getLogger("sde.orchestrator")

# Order of preference when we must pick a safe fallback action that policy allows.
_FALLBACK_PREFERENCE = [
    "ESCALATE",
    "ASK_CLARIFICATION",
    "DENY_REFUND",
    "PRIORITY_ROUTE",
    "RESPOND",
]


class DecisionOrchestrator:
    """Enforces policy constraints on a model-produced decision."""

    def enforce(self, decision: Decision, policy: PolicyResult) -> Decision:
        allowed = policy.allowed_actions or [RecommendedAction.RESPOND.value]
        decision.allowed_actions = allowed

        proposed = decision.recommended_action.value
        if proposed not in allowed:
            fallback = self._fallback_action(policy, allowed)
            logger.warning(
                "ticket=%s policy_clamp proposed=%s allowed=%s -> %s",
                decision.ticket_id,
                proposed,
                allowed,
                fallback,
            )
            decision.policy_clamped = True
            if "policy_clamped" not in decision.flags:
                decision.flags = [*decision.flags, "policy_clamped"]
            decision.reason = (
                f"[Policy override] The model recommended {proposed}, which the active "
                f"policy does not permit for this ticket; clamped to {fallback}. "
                f"Original rationale: {decision.reason}"
            )
            decision.recommended_action = RecommendedAction(fallback)
            # A clamped recommendation should never silently auto-execute, and the
            # confidence in the *clamped* action is, by definition, the policy's.
            decision.auto_executed = False
            decision.confidence = min(decision.confidence, 0.7)

        self._cap_amount(decision, policy)
        self._normalize_amount(decision)
        return decision

    @staticmethod
    def _fallback_action(policy: PolicyResult, allowed: list[str]) -> str:
        """Pick the action to clamp to: the policy's decisive action if it is allowed,
        otherwise the safest allowed action by preference order."""
        if policy.decisive_action and policy.decisive_action in allowed:
            return policy.decisive_action
        for candidate in _FALLBACK_PREFERENCE:
            if candidate in allowed:
                return candidate
        return allowed[0]

    @staticmethod
    def _cap_amount(decision: Decision, policy: PolicyResult) -> None:
        if (
            decision.recommended_action == RecommendedAction.APPROVE_REFUND
            and policy.max_refund_usd is not None
            and decision.amount_usd is not None
            and decision.amount_usd > policy.max_refund_usd
        ):
            logger.info(
                "ticket=%s refund_capped %.2f -> %.2f",
                decision.ticket_id,
                decision.amount_usd,
                policy.max_refund_usd,
            )
            decision.amount_usd = policy.max_refund_usd
            if "amount_capped" not in decision.flags:
                decision.flags = [*decision.flags, "amount_capped"]

    @staticmethod
    def _normalize_amount(decision: Decision) -> None:
        """Only a refund approval carries a dollar amount; clear it otherwise."""
        if decision.recommended_action != RecommendedAction.APPROVE_REFUND:
            decision.amount_usd = None
        if decision.recommended_action != RecommendedAction.ASK_CLARIFICATION:
            decision.clarifying_question = None


_orchestrator: DecisionOrchestrator | None = None


def get_orchestrator() -> DecisionOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = DecisionOrchestrator()
    return _orchestrator

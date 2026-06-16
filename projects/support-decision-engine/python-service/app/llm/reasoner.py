"""The reasoning layer: turn (ticket + context + policy) into a final Decision.

Three implementations behind one interface:
  - HeuristicReasoner  (default; no API key, deterministic, demo-safe)
  - OpenAIReasoner     (LLM_PROVIDER=openai + OPENAI_API_KEY)
  - AnthropicReasoner  (LLM_PROVIDER=anthropic + ANTHROPIC_API_KEY)

The heuristic is intentionally good enough to demo offline: it leans on the policy
engine for the action and synthesizes a plain-English reason from the real numbers.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod

from app.config import Settings, get_settings
from app.llm.prompts import SYSTEM_PROMPT, build_user_prompt
from app.models import (
    CustomerContext,
    Decision,
    PolicyResult,
    RecommendedAction,
    Ticket,
)
from app.retry import with_retry

_VALID_ACTIONS = {a.value for a in RecommendedAction}


class Reasoner(ABC):
    @abstractmethod
    def reason(
        self, ticket: Ticket, context: CustomerContext, policy: PolicyResult
    ) -> Decision:
        raise NotImplementedError

    @staticmethod
    def _auto_executed(policy: PolicyResult, action: str) -> bool:
        for m in policy.matches:
            if m.action == action and m.effects.get("auto_execute"):
                return True
        return False


class HeuristicReasoner(Reasoner):
    """Deterministic fallback. Action follows policy; reason is generated."""

    def reason(
        self, ticket: Ticket, context: CustomerContext, policy: PolicyResult
    ) -> Decision:
        action = policy.decisive_action or RecommendedAction.RESPOND.value
        confidence = _heuristic_confidence(policy, context)
        reason = _heuristic_reason(action, ticket, context, policy)
        amount = (
            ticket.requested_refund_usd or None
            if action == RecommendedAction.APPROVE_REFUND.value
            else None
        )
        clarifying = (
            "Could you confirm the exact amount and the charge you'd like refunded?"
            if action == RecommendedAction.ASK_CLARIFICATION.value
            else None
        )
        return Decision(
            ticket_id=ticket.ticket_id,
            customer_id=ticket.customer_id,
            recommended_action=RecommendedAction(action),
            confidence=confidence,
            reason=reason,
            amount_usd=amount,
            clarifying_question=clarifying,
            policy_matches=[m.rule_id for m in policy.matches],
            flags=policy.flags,
            source="heuristic",
            auto_executed=self._auto_executed(policy, action),
            context_snapshot=context.model_dump(),
            ticket_snapshot=ticket.model_dump(mode="json"),
        )


class _LLMReasoner(Reasoner):
    """Shared logic for live LLM providers: prompt -> JSON -> Decision, with a
    safe fallback to the heuristic on any error or malformed output."""

    def __init__(self, settings: Settings):
        self._settings = settings
        self._fallback = HeuristicReasoner()

    def reason(
        self, ticket: Ticket, context: CustomerContext, policy: PolicyResult
    ) -> Decision:
        try:
            raw = with_retry(
                lambda: self._complete(SYSTEM_PROMPT, build_user_prompt(ticket, context, policy)),
                attempts=2,
                base_delay=0.75,
                exceptions=(Exception,),
                label=f"llm.{self._settings.llm_provider}",
            )
            data = _extract_json(raw)
            action = data.get("recommended_action")
            if action not in _VALID_ACTIONS:
                raise ValueError(f"invalid action from LLM: {action!r}")
            confidence = float(data.get("confidence", 0.7))
            confidence = min(max(confidence, 0.0), 1.0)
            amount = data.get("amount_usd")
            clarifying = data.get("clarifying_question")
            return Decision(
                ticket_id=ticket.ticket_id,
                customer_id=ticket.customer_id,
                recommended_action=RecommendedAction(action),
                confidence=confidence,
                reason=str(data.get("reason", "")).strip()
                or "No reason provided by model.",
                amount_usd=float(amount) if amount is not None else None,
                clarifying_question=str(clarifying).strip() if clarifying else None,
                policy_matches=[m.rule_id for m in policy.matches],
                flags=policy.flags,
                source=f"llm:{self._settings.llm_provider}",
                auto_executed=self._auto_executed(policy, action),
                context_snapshot=context.model_dump(),
                ticket_snapshot=ticket.model_dump(mode="json"),
            )
        except Exception:
            # Never let a model failure break the pipeline.
            return self._fallback.reason(ticket, context, policy)

    @abstractmethod
    def _complete(self, system: str, user: str) -> str:
        raise NotImplementedError


class OpenAIReasoner(_LLMReasoner):
    def _complete(self, system: str, user: str) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=self._settings.openai_api_key)
        resp = client.chat.completions.create(
            model=self._settings.llm_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        return resp.choices[0].message.content or ""


class AnthropicReasoner(_LLMReasoner):
    def _complete(self, system: str, user: str) -> str:
        import anthropic

        client = anthropic.Anthropic(api_key=self._settings.anthropic_api_key)
        resp = client.messages.create(
            model=self._settings.llm_model,
            max_tokens=512,
            temperature=0.2,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(
            block.text for block in resp.content if getattr(block, "type", "") == "text"
        )


def get_reasoner() -> Reasoner:
    settings = get_settings()
    if settings.llm_provider == "openai" and settings.openai_api_key:
        return OpenAIReasoner(settings)
    if settings.llm_provider == "anthropic" and settings.anthropic_api_key:
        return AnthropicReasoner(settings)
    return HeuristicReasoner()


# --- heuristic helpers --------------------------------------------------------


def _heuristic_confidence(policy: PolicyResult, context: CustomerContext) -> float:
    if not policy.matches:
        return 0.5
    top = policy.matches[0]
    base = {
        "APPROVE_REFUND": 0.9,
        "DENY_REFUND": 0.82,
        "ESCALATE": 0.88,
        "PRIORITY_ROUTE": 0.85,
        "ASK_CLARIFICATION": 0.8,
        "RESPOND": 0.65,
    }.get(top.action, 0.7)
    if context.fraud_risk == "high":
        base -= 0.1
    if context.subscription_status == "unknown":
        base -= 0.05
    return round(min(max(base, 0.4), 0.98), 2)


def _heuristic_reason(
    action: str, ticket: Ticket, context: CustomerContext, policy: PolicyResult
) -> str:
    ltv = f"${context.ltv_usd:,.0f}"
    tenure = f"{context.tenure_months} mo"
    refunds = context.refunds_given_count
    rule = policy.matches[0].description if policy.matches else ""

    profile = (
        f"{context.name or context.customer_id} has spent {ltv} over {tenure}, "
        f"{refunds} prior refund(s), {context.fraud_risk} fraud risk"
    )

    if action == "APPROVE_REFUND":
        return (
            f"{profile} — first/clean refund history and high value. "
            f"Policy '{policy.matches[0].rule_id}' auto-approves. Low risk to approve."
        )
    if action == "DENY_REFUND":
        return f"{profile}. {rule} Recommend denying and routing to fraud review."
    if action == "ESCALATE":
        return f"{profile}. {rule} Escalating to a human for a judgment call."
    if action == "PRIORITY_ROUTE":
        return (
            f"{profile}. High-value customer expressing strong frustration — "
            f"priority-route to a senior agent before this churns."
        )
    if action == "ASK_CLARIFICATION":
        return (
            f"{profile}. Refund requested but the amount/details are unclear — "
            f"ask one clarifying question before deciding."
        )
    return f"{profile}. No special policy applies; draft a standard response."


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if "\n" in text:
            text = text.split("\n", 1)[1]
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1:
        text = text[start : end + 1]
    return json.loads(text)

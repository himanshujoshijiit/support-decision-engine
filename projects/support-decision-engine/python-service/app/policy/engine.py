"""A small, explainable JSON-driven rules engine.

This is deliberately *not* ML. It is pure, fast, deterministic logic that a buyer can
read and trust. Rules live in `config/policies.json` and are hot-loadable, so an ops
team can tune their own policies without a deploy.

Rule shape (see config/policies.json):

    {
      "id": "auto_approve_high_ltv_billing",
      "description": "...",
      "priority": 100,
      "when": { "all": [ {"fact": "customer.ltv_usd", "op": "gte", "value": 1000}, ... ] },
      "then": { "action": "APPROVE_REFUND", "flags": ["trusted"], "auto_execute": true }
    }

`when` supports nested `all` / `any` groups and leaf conditions
`{fact, op, value}`. Supported ops: eq, ne, gt, gte, lt, lte, in, not_in, contains.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.models import CustomerContext, PolicyMatch, PolicyResult, Ticket

# Actions a human/agent can always safely fall back to, regardless of policy: asking
# the customer a question, escalating to a person, or sending a normal reply can never
# violate a refund/compliance rule. These are always added to `allowed_actions` so the
# LLM and the agent are never boxed into a single option.
_ALWAYS_SAFE_ACTIONS = ["RESPOND", "ASK_CLARIFICATION", "ESCALATE"]

# Canonical ordering so `allowed_actions` is stable/deterministic for tests + UI.
_ACTION_ORDER = [
    "APPROVE_REFUND",
    "DENY_REFUND",
    "PRIORITY_ROUTE",
    "ESCALATE",
    "ASK_CLARIFICATION",
    "RESPOND",
]


def build_facts(ticket: Ticket, context: CustomerContext) -> dict[str, Any]:
    """Flatten ticket + context (+ a few derived signals) into a fact dictionary.

    Derived signals are where domain knowledge lives, e.g. "refund_in_last_90d".
    """
    sentiment = _estimate_sentiment(f"{ticket.subject}\n{ticket.body}")
    refund_in_last_90d = (
        context.days_since_last_refund is not None
        and context.days_since_last_refund <= 90
    )
    return {
        "ticket.category": ticket.category.value,
        "ticket.refund_requested": ticket.refund_requested,
        "ticket.requested_refund_usd": ticket.requested_refund_usd,
        "ticket.source": ticket.source,
        "ticket.sentiment": sentiment,
        "customer.ltv_usd": context.ltv_usd,
        "customer.tenure_months": context.tenure_months,
        "customer.subscription_status": context.subscription_status,
        "customer.mrr_usd": context.mrr_usd,
        "customer.refunds_given_count": context.refunds_given_count,
        "customer.days_since_last_refund": context.days_since_last_refund,
        "customer.open_disputes": context.open_disputes,
        "customer.fraud_risk": context.fraud_risk,
        "derived.refund_in_last_90d": refund_in_last_90d,
        "derived.sla_breached": bool(ticket.metadata.get("sla_breached", False)),
        "derived.high_anger": sentiment == "angry",
    }


_OPS = {
    "eq": lambda a, b: a == b,
    "ne": lambda a, b: a != b,
    "gt": lambda a, b: a is not None and a > b,
    "gte": lambda a, b: a is not None and a >= b,
    "lt": lambda a, b: a is not None and a < b,
    "lte": lambda a, b: a is not None and a <= b,
    "in": lambda a, b: a in b,
    "not_in": lambda a, b: a not in b,
    "contains": lambda a, b: b in (a or []),
}


class PolicyEngine:
    def __init__(self, rules: list[dict[str, Any]]):
        # Highest priority first; ties keep config order.
        self._rules = sorted(rules, key=lambda r: r.get("priority", 0), reverse=True)

    @classmethod
    def from_file(cls, path: str | Path) -> "PolicyEngine":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(data.get("rules", []))

    def evaluate(self, facts: dict[str, Any]) -> PolicyResult:
        matches: list[PolicyMatch] = []
        flags: list[str] = []

        for rule in self._rules:
            if self._matches(rule.get("when", {}), facts):
                then = rule.get("then", {})
                matches.append(
                    PolicyMatch(
                        rule_id=rule["id"],
                        description=rule.get("description", ""),
                        action=then.get("action", "RESPOND"),
                        priority=rule.get("priority", 0),
                        effects=then,
                    )
                )
                flags.extend(then.get("flags", []))

        # The decisive action is the highest-priority match's action (rules are
        # pre-sorted). Flags from all matches accumulate.
        decisive = matches[0].action if matches else None
        return PolicyResult(
            matches=matches,
            decisive_action=decisive,
            allowed_actions=self._allowed_actions(matches),
            max_refund_usd=self._max_refund(matches),
            flags=_dedupe(flags),
            facts=facts,
        )

    @staticmethod
    def _allowed_actions(matches: list[PolicyMatch]) -> list[str]:
        """The set of actions the LLM is permitted to recommend.

        For each matched rule we take its explicit `allow` list if present, otherwise
        the rule's own action. The always-safe actions are unioned in so an agent can
        always ask, escalate, or reply. Result is returned in canonical order.
        """
        allowed: set[str] = set(_ALWAYS_SAFE_ACTIONS)
        for m in matches:
            explicit = m.effects.get("allow")
            if explicit:
                allowed.update(explicit)
            else:
                allowed.add(m.action)
        ordered = [a for a in _ACTION_ORDER if a in allowed]
        # Preserve any custom actions not in the canonical order, appended at the end.
        ordered += [a for a in allowed if a not in _ACTION_ORDER]
        return ordered

    @staticmethod
    def _max_refund(matches: list[PolicyMatch]) -> float | None:
        """Highest-priority refund ceiling among matched rules (rules are pre-sorted)."""
        for m in matches:
            cap = m.effects.get("max_refund_usd")
            if cap is not None:
                return float(cap)
        return None

    # --- condition evaluation -------------------------------------------------

    def _matches(self, condition: dict[str, Any], facts: dict[str, Any]) -> bool:
        if not condition:
            return False
        if "all" in condition:
            return all(self._matches(c, facts) for c in condition["all"])
        if "any" in condition:
            return any(self._matches(c, facts) for c in condition["any"])
        if "not" in condition:
            return not self._matches(condition["not"], facts)
        return self._eval_leaf(condition, facts)

    def _eval_leaf(self, leaf: dict[str, Any], facts: dict[str, Any]) -> bool:
        fact_name = leaf.get("fact")
        op = leaf.get("op")
        expected = leaf.get("value")
        if fact_name is None or op not in _OPS:
            return False
        actual = facts.get(fact_name)
        try:
            return bool(_OPS[op](actual, expected))
        except TypeError:
            return False


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _estimate_sentiment(text: str) -> str:
    """Tiny keyword sentiment heuristic. Good enough for routing; the LLM layer
    does the nuanced read. Returns one of: angry | unhappy | neutral | happy."""
    t = text.lower()
    angry = ["furious", "ridiculous", "unacceptable", "scam", "lawyer", "cancel",
             "worst", "terrible", "outrageous", "fraud", "!!!"]
    unhappy = ["disappointed", "frustrated", "annoyed", "not happy", "broken",
               "doesn't work", "still waiting", "no response"]
    happy = ["thank", "great", "love", "awesome", "appreciate"]
    if any(w in t for w in angry):
        return "angry"
    if any(w in t for w in unhappy):
        return "unhappy"
    if any(w in t for w in happy):
        return "happy"
    return "neutral"

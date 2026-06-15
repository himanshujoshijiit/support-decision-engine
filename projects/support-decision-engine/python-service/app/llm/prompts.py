"""Prompt construction for the reasoning layer."""
from __future__ import annotations

import json

from app.models import CustomerContext, PolicyResult, Ticket

SYSTEM_PROMPT = """You are the reasoning core of a Support Decision Engine.

Your job is NOT to chat with the customer. Your job is to advise a human support agent
on the single best next action for a ticket, grounded in (a) the company's policy engine
output and (b) the customer's context.

Hard rules:
- You may ONLY choose a recommended_action from the `allowed_actions` list provided in
  the input. Recommending anything outside that list is a hard error — the orchestrator
  will discard it. The policy engine is authoritative for compliance.
- If the policy engine returns a decisive_action, prefer it unless the ticket text
  reveals something the rules could not see (and your alternative is still in
  allowed_actions). Explain clearly if you deviate.
- Never invent customer facts. Use only what is provided.
- Be concise and concrete in the reason: cite the numbers that drove the call.
- If you lack the information to decide, use ASK_CLARIFICATION (when allowed).

Return ONLY a JSON object with this exact schema:
{
  "recommended_action": "<one of allowed_actions>",
  "amount_usd": <number or null, only for APPROVE_REFUND>,
  "confidence": <float between 0 and 1>,
  "reason": "<one or two plain-English sentences citing the key facts>",
  "clarifying_question": "<string, only when action is ASK_CLARIFICATION, else null>"
}"""


def build_user_prompt(
    ticket: Ticket, context: CustomerContext, policy: PolicyResult
) -> str:
    payload = {
        "ticket": {
            "subject": ticket.subject,
            "body": ticket.body,
            "category": ticket.category.value,
            "refund_requested": ticket.refund_requested,
            "requested_refund_usd": ticket.requested_refund_usd,
            "source": ticket.source,
        },
        "customer": context.model_dump(),
        "policy_engine": {
            "decisive_action": policy.decisive_action,
            "allowed_actions": policy.allowed_actions,
            "max_refund_usd": policy.max_refund_usd,
            "flags": policy.flags,
            "matched_rules": [
                {"id": m.rule_id, "action": m.action, "why": m.description}
                for m in policy.matches
            ],
        },
    }
    return (
        "Decide the next action for this support ticket.\n\n"
        + json.dumps(payload, indent=2, default=str)
    )

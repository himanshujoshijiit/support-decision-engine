"""The decision pipeline: the heart of the engine.

    ticket -> fetch context -> run policy engine -> LLM reasoning -> persist to audit

Each stage is swappable (see the provider factories). This module just wires them in
order and returns the final Decision.
"""
from __future__ import annotations

import logging

from app.audit_client import AuditClient
from app.config import get_settings
from app.context import get_context_provider
from app.llm import get_reasoner
from app.models import Decision, Ticket
from app.orchestrator import get_orchestrator
from app.policy import PolicyEngine, build_facts

logger = logging.getLogger("sde.pipeline")


class DecisionPipeline:
    def __init__(self) -> None:
        settings = get_settings()
        self._context_provider = get_context_provider()
        self._policy_engine = PolicyEngine.from_file(settings.policies_path)
        self._reasoner = get_reasoner()
        self._orchestrator = get_orchestrator()
        self._audit = AuditClient()

    def reload_policies(self) -> int:
        """Hot-reload policy rules from disk. Returns the rule count."""
        settings = get_settings()
        self._policy_engine = PolicyEngine.from_file(settings.policies_path)
        return len(self._policy_engine._rules)  # noqa: SLF001 - intentional introspection

    def run(self, ticket: Ticket, persist: bool = True) -> Decision:
        context = self._context_provider.fetch(ticket.customer_id)

        facts = build_facts(ticket, context)
        policy_result = self._policy_engine.evaluate(facts)
        logger.info(
            "ticket=%s policy_action=%s allowed=%s flags=%s",
            ticket.ticket_id,
            policy_result.decisive_action,
            policy_result.allowed_actions,
            policy_result.flags,
        )

        # Soft reasoning proposes; the orchestrator enforces the policy boundary.
        decision = self._reasoner.reason(ticket, context, policy_result)
        decision = self._orchestrator.enforce(decision, policy_result)

        if persist:
            self._audit.record(decision)

        return decision


# A single shared pipeline instance for the app process.
_pipeline: DecisionPipeline | None = None


def get_pipeline() -> DecisionPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = DecisionPipeline()
    return _pipeline

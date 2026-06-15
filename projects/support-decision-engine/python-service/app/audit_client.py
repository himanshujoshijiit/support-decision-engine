"""Client for shipping decisions to the Java audit/decision store.

Resilient by design: if the audit service is unreachable, we log a warning and keep
going. The decision is still returned to the caller; persistence is best-effort here so
a dashboard outage never blocks a support agent.
"""
from __future__ import annotations

import logging

import httpx

from app.config import get_settings
from app.models import Decision

logger = logging.getLogger("sde.audit")


class AuditClient:
    def __init__(self, base_url: str | None = None) -> None:
        settings = get_settings()
        self._base_url = (base_url or settings.audit_base_url).rstrip("/")
        self._enabled = settings.audit_enabled

    def record(self, decision: Decision) -> bool:
        """Persist a decision. Returns True on success, False otherwise."""
        if not self._enabled:
            logger.info("Audit disabled; skipping persistence for %s", decision.ticket_id)
            return False
        url = f"{self._base_url}/api/decisions"
        try:
            payload = decision.model_dump(mode="json")
            resp = httpx.post(url, json=payload, timeout=5.0)
            resp.raise_for_status()
            return True
        except Exception as exc:  # network / 5xx / timeout
            logger.warning("Could not record decision to audit store (%s): %s", url, exc)
            return False

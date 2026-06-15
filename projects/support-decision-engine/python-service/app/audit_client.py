"""Client for shipping decisions to the Java audit/decision store.

Retries with exponential backoff. If the audit service is still unreachable after
retries, logs a warning and returns False — the decision is still returned to the
caller so a dashboard outage never blocks ticket processing.
"""
from __future__ import annotations

import logging

import httpx

from app.config import get_settings
from app.models import Decision
from app.retry import with_retry

logger = logging.getLogger("sde.audit")


class AuditClient:
    def __init__(self, base_url: str | None = None) -> None:
        settings = get_settings()
        self._base_url = (base_url or settings.audit_base_url).rstrip("/")
        self._enabled = settings.audit_enabled
        self._api_key = settings.sde_api_key
        self._attempts = settings.retry_attempts
        self._base_delay = settings.retry_base_delay

    def record(self, decision: Decision) -> bool:
        """Persist a decision. Returns True on success, False otherwise."""
        if not self._enabled:
            logger.info("Audit disabled; skipping persistence for %s", decision.ticket_id)
            return False
        url = f"{self._base_url}/api/decisions"
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["X-API-Key"] = self._api_key

        payload = decision.model_dump(mode="json")

        def _post() -> bool:
            resp = httpx.post(url, json=payload, headers=headers, timeout=10.0)
            resp.raise_for_status()
            return True

        try:
            return with_retry(
                _post,
                attempts=self._attempts,
                base_delay=self._base_delay,
                exceptions=(httpx.HTTPError, httpx.TimeoutException),
                label=f"audit.record({decision.ticket_id})",
            )
        except Exception as exc:
            logger.warning("Could not record decision to audit store (%s): %s", url, exc)
            return False

    def health_check(self) -> dict:
        """Probe the Java audit service health endpoint."""
        url = f"{self._base_url}/api/health"
        try:
            resp = httpx.get(url, timeout=5.0)
            resp.raise_for_status()
            return resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {"status": resp.text}
        except Exception as exc:
            return {"status": "down", "error": str(exc)}

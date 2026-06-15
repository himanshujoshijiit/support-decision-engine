"""FastAPI app: webhook intake + a direct decision endpoint for demos/testing."""
from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from app import __version__, webhooks
from app.audit_client import AuditClient
from app.config import get_settings
from app.models import Decision, Ticket
from app.pipeline import get_pipeline
from app.security import ApiKeyMiddleware, verify_zendesk_signature

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Support Decision Engine",
    version=__version__,
    description="The AI judgment layer: intake -> context -> policy -> LLM -> decision.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ApiKeyMiddleware)


@app.get("/health")
def health() -> dict[str, Any]:
    s = get_settings()
    audit = AuditClient().health_check() if s.audit_enabled else {"status": "disabled"}
    return {
        "status": "ok",
        "version": __version__,
        "llm_provider": s.llm_provider,
        "llm_live": s.llm_is_live,
        "context_provider": s.context_provider,
        "audit_url": s.audit_base_url,
        "audit_enabled": s.audit_enabled,
        "audit_status": audit.get("status", "unknown"),
        "auth_enabled": bool(s.engine_api_key),
        "zendesk_signature_required": bool(s.zendesk_webhook_secret),
    }


@app.post("/decide", response_model=Decision)
def decide(ticket: Ticket, persist: bool = True) -> Decision:
    """Score a normalized ticket directly. Handy for demos, tests, and manual entry."""
    return get_pipeline().run(ticket, persist=persist)


@app.post("/webhooks/zendesk", response_model=Decision)
async def zendesk_webhook(request: Request) -> Decision:
    body = await request.body()
    settings = get_settings()
    verify_zendesk_signature(request.headers, body, settings.zendesk_webhook_secret or "")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc
    ticket = webhooks.from_zendesk(payload)
    return get_pipeline().run(ticket)


@app.post("/webhooks/intercom", response_model=Decision)
async def intercom_webhook(request: Request) -> Decision:
    payload = await request.json()
    ticket = webhooks.from_intercom(payload)
    return get_pipeline().run(ticket)


@app.post("/admin/reload-policies")
def reload_policies() -> dict[str, Any]:
    """Hot-reload the JSON policy rules from disk (no redeploy needed)."""
    count = get_pipeline().reload_policies()
    return {"status": "reloaded", "rule_count": count}

"""FastAPI app: webhook intake + a direct decision endpoint for demos/testing."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app import __version__, webhooks
from app.config import get_settings
from app.models import Decision, Ticket
from app.pipeline import get_pipeline

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


@app.get("/health")
def health() -> dict[str, Any]:
    s = get_settings()
    return {
        "status": "ok",
        "version": __version__,
        "llm_provider": s.llm_provider,
        "llm_live": s.llm_is_live,
        "context_provider": s.context_provider,
        "audit_url": s.audit_base_url,
        "audit_enabled": s.audit_enabled,
    }


@app.post("/decide", response_model=Decision)
def decide(ticket: Ticket, persist: bool = True) -> Decision:
    """Score a normalized ticket directly. Handy for demos, tests, and manual entry."""
    return get_pipeline().run(ticket, persist=persist)


@app.post("/webhooks/zendesk", response_model=Decision)
async def zendesk_webhook(request: Request) -> Decision:
    payload = await request.json()
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

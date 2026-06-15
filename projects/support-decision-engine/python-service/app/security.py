"""Authentication and webhook signature verification."""
from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import time
from typing import Mapping

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import get_settings

logger = logging.getLogger("sde.security")

PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """Require X-API-Key on protected routes when ENGINE_API_KEY is configured."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path.rstrip("/") or "/"
        if path in PUBLIC_PATHS or path.startswith("/docs"):
            return await call_next(request)

        settings = get_settings()
        if not settings.engine_api_key:
            return await call_next(request)

        provided = request.headers.get("X-API-Key")
        if not provided or not hmac.compare_digest(provided, settings.engine_api_key):
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing X-API-Key header"},
            )
        return await call_next(request)


def verify_zendesk_signature(headers: Mapping[str, str], body: bytes, secret: str) -> None:
    """Validate Zendesk webhook HMAC (X-Zendesk-Webhook-Signature)."""
    if not secret:
        logger.debug("ZENDESK_WEBHOOK_SECRET not set — skipping signature check (dev mode)")
        return

    sig = _header(headers, "x-zendesk-webhook-signature")
    ts = _header(headers, "x-zendesk-webhook-signature-timestamp")
    if not sig or not ts:
        raise HTTPException(status_code=401, detail="Missing Zendesk webhook signature headers")

    try:
        ts_int = int(ts)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid Zendesk timestamp") from exc

    if abs(time.time() - ts_int) > 300:
        raise HTTPException(status_code=401, detail="Stale Zendesk webhook timestamp")

    signed_payload = f"{ts}.{body.decode('utf-8')}"
    expected = base64.b64encode(
        hmac.new(secret.encode("utf-8"), signed_payload.encode("utf-8"), hashlib.sha256).digest()
    ).decode("utf-8")

    if not hmac.compare_digest(expected, sig):
        raise HTTPException(status_code=401, detail="Invalid Zendesk webhook signature")


def _header(headers: Mapping[str, str], name: str) -> str | None:
    for key, value in headers.items():
        if key.lower() == name:
            return value
    return None

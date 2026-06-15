"""Tests for Zendesk webhook HMAC verification."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time

import pytest
from fastapi import HTTPException

from app.security import verify_zendesk_signature


def _sign(body: bytes, secret: str, ts: int | None = None) -> tuple[str, str]:
    ts = ts or int(time.time())
    signed = f"{ts}.{body.decode()}"
    sig = base64.b64encode(
        hmac.new(secret.encode(), signed.encode(), hashlib.sha256).digest()
    ).decode()
    return sig, str(ts)


def test_valid_zendesk_signature():
    body = json.dumps({"ticket": {"id": 1, "subject": "refund"}}).encode()
    secret = "test-secret"
    sig, ts = _sign(body, secret)
    headers = {"x-zendesk-webhook-signature": sig, "x-zendesk-webhook-signature-timestamp": ts}
    verify_zendesk_signature(headers, body, secret)  # no raise


def test_invalid_zendesk_signature():
    body = b'{"ticket":{"id":1}}'
    with pytest.raises(HTTPException) as exc:
        verify_zendesk_signature(
            {"x-zendesk-webhook-signature": "bad", "x-zendesk-webhook-signature-timestamp": str(int(time.time()))},
            body,
            "secret",
        )
    assert exc.value.status_code == 401


def test_skips_when_secret_not_configured():
    verify_zendesk_signature({}, b"{}", "")

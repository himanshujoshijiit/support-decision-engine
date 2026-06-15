"""Adapters that normalize incoming helpdesk webhooks into our `Ticket` model.

Each helpdesk has its own payload shape; this is the only place that knows about them.
We keep the parsing tolerant (lots of `.get`) because webhook payloads vary by plan and
API version.
"""
from __future__ import annotations

import re
from typing import Any

from app.models import IssueCategory, Ticket

_REFUND_WORDS = ["refund", "money back", "reimburse", "charge back", "chargeback"]
_AMOUNT_RE = re.compile(r"[$₹]\s?(\d{1,3}(?:[,\d]*)(?:\.\d+)?)")

_CATEGORY_HINTS = {
    IssueCategory.BILLING: ["refund", "charge", "invoice", "payment", "billing", "subscription", "price"],
    IssueCategory.TECHNICAL: ["error", "bug", "crash", "not working", "broken", "login", "500"],
    IssueCategory.ACCOUNT: ["account", "password", "access", "login", "seat", "user"],
    IssueCategory.SHIPPING: ["shipping", "delivery", "package", "tracking", "arrive"],
}


def detect_category(text: str) -> IssueCategory:
    t = text.lower()
    best, best_score = IssueCategory.OTHER, 0
    for category, words in _CATEGORY_HINTS.items():
        score = sum(1 for w in words if w in t)
        if score > best_score:
            best, best_score = category, score
    return best


def detect_refund(text: str) -> tuple[bool, float]:
    t = text.lower()
    requested = any(w in t for w in _REFUND_WORDS)
    amount = 0.0
    if requested:
        m = _AMOUNT_RE.search(text)
        if m:
            try:
                amount = float(m.group(1).replace(",", ""))
            except ValueError:
                amount = 0.0
    return requested, amount


def from_zendesk(payload: dict[str, Any]) -> Ticket:
    """Zendesk ticket webhook (flattened or nested under `ticket`)."""
    t = payload.get("ticket", payload)
    subject = t.get("subject") or t.get("title") or ""
    body = (
        t.get("description")
        or t.get("body")
        or (t.get("comment") or {}).get("body", "")
        or ""
    )
    text = f"{subject}\n{body}"
    refund_requested, amount = detect_refund(text)
    requester = t.get("requester") or {}
    requester_email = (requester.get("email") or t.get("requester_email") or "").strip()
    customer_id = str(
        t.get("requester_id")
        or requester.get("id")
        or requester_email
        or "unknown"
    )
    return Ticket(
        ticket_id=str(t.get("id") or payload.get("id") or "unknown"),
        customer_id=customer_id,
        requester_email=requester_email,
        subject=subject,
        body=body,
        source="zendesk",
        category=detect_category(text),
        refund_requested=refund_requested,
        requested_refund_usd=amount,
        metadata={
            "priority": t.get("priority"),
            "tags": t.get("tags", []),
            "requester_email": requester_email,
            "zendesk_status": t.get("status"),
        },
    )


def from_intercom(payload: dict[str, Any]) -> Ticket:
    """Intercom conversation.* webhook."""
    item = (payload.get("data") or {}).get("item", payload)
    source = item.get("source") or {}
    subject = source.get("subject") or ""
    body = _strip_html(source.get("body") or "")
    text = f"{subject}\n{body}"
    refund_requested, amount = detect_refund(text)
    contacts = (item.get("contacts") or {}).get("contacts") or []
    customer_id = contacts[0].get("id") if contacts else (source.get("author") or {}).get("id")
    return Ticket(
        ticket_id=str(item.get("id") or "unknown"),
        customer_id=str(customer_id or "unknown"),
        subject=subject,
        body=body,
        source="intercom",
        category=detect_category(text),
        refund_requested=refund_requested,
        requested_refund_usd=amount,
        metadata={"state": item.get("state")},
    )


def _strip_html(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html).strip()

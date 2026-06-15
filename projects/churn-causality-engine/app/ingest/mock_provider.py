"""Mock product analytics + billing data (Mixpanel/Amplitude/Stripe shape)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.models import JourneyEvent

_NOW = datetime.now(timezone.utc)

_PROFILES: dict[str, dict] = {
    "cus_at_risk_01": {
        "plan": "pro",
        "mrr_usd": 99.0,
        "tenure_days": 45,
        "payment_failed": True,
        "support_tickets_30d": 4,
        "events": [
            ("signup", 40),
            ("verify_email", 39),
            ("connect_integration", 38),
            # stalled — never reached first_value_event
        ],
        "cohort_drop_offs": {
            "connect_integration": 0.62,
            "first_value_event": 0.48,
        },
    },
    "cus_healthy_02": {
        "plan": "business",
        "mrr_usd": 299.0,
        "tenure_days": 320,
        "payment_failed": False,
        "support_tickets_30d": 0,
        "events": [
            ("signup", 300),
            ("verify_email", 300),
            ("connect_integration", 299),
            ("first_value_event", 298),
            ("invite_team", 290),
            ("upgrade", 120),
        ],
        "cohort_drop_offs": {"connect_integration": 0.12, "first_value_event": 0.08},
    },
    "cus_slipping_03": {
        "plan": "starter",
        "mrr_usd": 29.0,
        "tenure_days": 90,
        "payment_failed": False,
        "support_tickets_30d": 2,
        "events": [
            ("signup", 85),
            ("verify_email", 85),
            ("connect_integration", 84),
            ("first_value_event", 80),
            # login decline — no events in 21 days
        ],
        "last_active_days_ago": 21,
        "cohort_drop_offs": {"first_value_event": 0.35},
    },
}


def fetch_customer_profile(customer_id: str) -> dict:
    if customer_id in _PROFILES:
        return _deep_copy(_PROFILES[customer_id], customer_id)
    return _synthetic(customer_id)


def _deep_copy(profile: dict, customer_id: str) -> dict:
    events = [
        JourneyEvent(
            name=name,
            timestamp=_NOW - timedelta(days=days_ago),
        )
        for name, days_ago in profile["events"]
    ]
    return {
        "customer_id": customer_id,
        "plan": profile["plan"],
        "mrr_usd": profile["mrr_usd"],
        "tenure_days": profile["tenure_days"],
        "payment_failed": profile.get("payment_failed", False),
        "support_tickets_30d": profile.get("support_tickets_30d", 0),
        "last_active_days_ago": profile.get("last_active_days_ago", 2),
        "events": events,
        "cohort_drop_offs": profile.get("cohort_drop_offs", {}),
    }


def _synthetic(customer_id: str) -> dict:
    h = sum(ord(c) for c in customer_id)
    return {
        "customer_id": customer_id,
        "plan": "pro" if h % 2 else "starter",
        "mrr_usd": float(h % 500),
        "tenure_days": h % 400,
        "payment_failed": h % 7 == 0,
        "support_tickets_30d": h % 5,
        "last_active_days_ago": h % 30,
        "events": [
            JourneyEvent(name="signup", timestamp=_NOW - timedelta(days=30)),
            JourneyEvent(name="verify_email", timestamp=_NOW - timedelta(days=29)),
        ],
        "cohort_drop_offs": {"connect_integration": 0.4},
    }

"""Deterministic mock context provider.

Lets the whole system run end-to-end with zero external accounts. Customer profiles
are generated deterministically from the customer_id so demos are reproducible, with a
handful of hand-crafted "named" customers that produce interesting, distinct decisions.
"""
from __future__ import annotations

import hashlib

from app.context.base import ContextProvider
from app.models import CustomerContext

# Hand-crafted profiles that map cleanly to the demo narrative.
_SEEDED: dict[str, CustomerContext] = {
    "cus_loyal_whale": CustomerContext(
        customer_id="cus_loyal_whale",
        name="Acme Corp (Dana Reed)",
        email="dana@acme.io",
        ltv_usd=2400.0,
        tenure_months=8,
        subscription_status="active",
        mrr_usd=300.0,
        past_ticket_count=3,
        refunds_given_count=0,
        days_since_last_refund=None,
        open_disputes=0,
        fraud_risk="low",
    ),
    "cus_repeat_refunder": CustomerContext(
        customer_id="cus_repeat_refunder",
        name="Jordan Blake",
        email="jordan@example.com",
        ltv_usd=180.0,
        tenure_months=4,
        subscription_status="active",
        mrr_usd=29.0,
        past_ticket_count=9,
        refunds_given_count=2,
        days_since_last_refund=21,  # within 90 days -> review flag
        open_disputes=0,
        fraud_risk="medium",
    ),
    "cus_churn_risk": CustomerContext(
        customer_id="cus_churn_risk",
        name="Sam Rivera",
        email="sam@startup.dev",
        ltv_usd=950.0,
        tenure_months=14,
        subscription_status="past_due",
        mrr_usd=99.0,
        past_ticket_count=6,
        refunds_given_count=1,
        days_since_last_refund=210,
        open_disputes=1,
        fraud_risk="low",
    ),
    "cus_new_trial": CustomerContext(
        customer_id="cus_new_trial",
        name="Priya Nair",
        email="priya@trial.co",
        ltv_usd=0.0,
        tenure_months=0,
        subscription_status="trialing",
        mrr_usd=0.0,
        past_ticket_count=1,
        refunds_given_count=0,
        days_since_last_refund=None,
        open_disputes=0,
        fraud_risk="low",
    ),
}


class MockContextProvider(ContextProvider):
    def fetch(self, customer_id: str, email: str | None = None) -> CustomerContext:
        if customer_id in _SEEDED:
            return _SEEDED[customer_id].model_copy(deep=True)
        if email:
            for ctx in _SEEDED.values():
                if ctx.email.lower() == email.lower():
                    return ctx.model_copy(deep=True)
        return _synthesize(customer_id)


def _synthesize(customer_id: str) -> CustomerContext:
    """Deterministically derive a plausible profile from the id hash."""
    h = int(hashlib.sha256(customer_id.encode()).hexdigest(), 16)
    ltv = float(h % 5000)
    tenure = h % 36
    refunds = h % 3
    statuses = ["active", "active", "active", "past_due", "trialing", "canceled"]
    risks = ["low", "low", "low", "medium", "high"]
    return CustomerContext(
        customer_id=customer_id,
        name=f"Customer {customer_id[-4:]}",
        email=f"{customer_id}@example.com",
        ltv_usd=ltv,
        tenure_months=tenure,
        subscription_status=statuses[h % len(statuses)],
        mrr_usd=round(ltv / max(tenure, 1), 2),
        past_ticket_count=h % 12,
        refunds_given_count=refunds,
        days_since_last_refund=(h % 200) if refunds else None,
        open_disputes=h % 2,
        fraud_risk=risks[h % len(risks)],
    )

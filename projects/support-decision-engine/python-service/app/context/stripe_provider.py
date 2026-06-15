"""Stripe-backed context provider (skeleton for a real pilot).

This intentionally ships as a thin, well-documented skeleton. The point of the MVP is
to prove the *decision* value with mocks; when a pilot customer connects their real
billing data, fill in the marked calls. The rest of the pipeline does not change.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.context.base import ContextProvider
from app.models import CustomerContext


class StripeContextProvider(ContextProvider):
    def __init__(self, api_key: str | None) -> None:
        if not api_key:
            raise ValueError(
                "CONTEXT_PROVIDER=stripe requires STRIPE_API_KEY to be set."
            )
        # Imported lazily; `stripe` is an optional dependency.
        import stripe

        stripe.api_key = api_key
        self._stripe = stripe

    def fetch(self, customer_id: str) -> CustomerContext:
        try:
            customer = self._stripe.Customer.retrieve(customer_id)
            charges = self._stripe.Charge.list(customer=customer_id, limit=100)
            refunds = self._stripe.Refund.list(limit=100)
            subscriptions = self._stripe.Subscription.list(
                customer=customer_id, status="all", limit=10
            )
        except Exception:
            # Resilient by design: degrade to an empty-but-valid context.
            return CustomerContext(customer_id=customer_id)

        ltv = sum(c["amount"] for c in charges.get("data", [])) / 100.0
        customer_refunds = [
            r for r in refunds.get("data", []) if r.get("customer") == customer_id
        ]
        days_since_last_refund = _days_since_latest(
            [r.get("created") for r in customer_refunds]
        )
        sub = (subscriptions.get("data") or [{}])[0]
        mrr = _monthly_amount(sub)

        return CustomerContext(
            customer_id=customer_id,
            name=customer.get("name") or "",
            email=customer.get("email") or "",
            ltv_usd=round(ltv, 2),
            tenure_months=_months_since(customer.get("created")),
            subscription_status=sub.get("status", "unknown"),
            mrr_usd=mrr,
            refunds_given_count=len(customer_refunds),
            days_since_last_refund=days_since_last_refund,
            # past_ticket_count / open_disputes / fraud_risk would come from the
            # helpdesk + a risk signal; left at defaults until wired up.
        )


def _months_since(unix_ts: int | None) -> int:
    if not unix_ts:
        return 0
    created = datetime.fromtimestamp(unix_ts, tz=timezone.utc)
    delta = datetime.now(timezone.utc) - created
    return int(delta.days / 30)


def _days_since_latest(unix_timestamps: list[int | None]) -> int | None:
    valid = [t for t in unix_timestamps if t]
    if not valid:
        return None
    latest = datetime.fromtimestamp(max(valid), tz=timezone.utc)
    return (datetime.now(timezone.utc) - latest).days


def _monthly_amount(subscription: dict) -> float:
    items = (subscription.get("items") or {}).get("data") or []
    if not items:
        return 0.0
    price = items[0].get("price") or {}
    amount = (price.get("unit_amount") or 0) / 100.0
    interval = (price.get("recurring") or {}).get("interval", "month")
    return round(amount / 12.0 if interval == "year" else amount, 2)

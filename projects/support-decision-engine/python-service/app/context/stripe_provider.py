"""Stripe-backed customer context — production-ready with email lookup and retries."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.context.base import ContextProvider
from app.models import CustomerContext
from app.retry import with_retry

logger = logging.getLogger("sde.stripe")


class StripeContextProvider(ContextProvider):
    def __init__(self, api_key: str | None) -> None:
        if not api_key:
            raise ValueError(
                "CONTEXT_PROVIDER=stripe requires STRIPE_API_KEY to be set."
            )
        import stripe

        stripe.api_key = api_key
        self._stripe = stripe

    def fetch(self, customer_id: str, email: str | None = None) -> CustomerContext:
        stripe_id = self._resolve_customer_id(customer_id, email)
        if not stripe_id:
            return CustomerContext(
                customer_id=customer_id,
                email=email or "",
            )
        try:
            return with_retry(
                lambda: self._build_context(stripe_id, customer_id, email),
                attempts=3,
                exceptions=(Exception,),
                label=f"stripe.fetch({stripe_id})",
            )
        except Exception as exc:
            logger.warning("Stripe lookup failed for %s: %s", stripe_id, exc)
            return CustomerContext(customer_id=customer_id, email=email or "")

    def _resolve_customer_id(self, customer_id: str, email: str | None) -> str | None:
        if customer_id.startswith("cus_"):
            return customer_id
        lookup_email = email or ("@" in customer_id and customer_id or None)
        if not lookup_email:
            return None
        try:
            customers = self._stripe.Customer.list(email=lookup_email, limit=1)
            data = customers.get("data") or []
            if data:
                return data[0]["id"]
        except Exception as exc:
            logger.warning("Stripe email lookup failed for %s: %s", lookup_email, exc)
        return None

    def _build_context(
        self, stripe_id: str, original_id: str, email: str | None
    ) -> CustomerContext:
        customer = self._stripe.Customer.retrieve(stripe_id)
        charges = self._stripe.Charge.list(customer=stripe_id, limit=100)
        refunds = self._stripe.Refund.list(limit=100)
        subscriptions = self._stripe.Subscription.list(
            customer=stripe_id, status="all", limit=10
        )
        disputes = self._stripe.Dispute.list(limit=50)

        charge_data = charges.get("data", [])
        ltv = sum(c.get("amount", 0) for c in charge_data if c.get("paid")) / 100.0

        customer_refunds = [
            r
            for r in refunds.get("data", [])
            if r.get("charge") in {c.get("id") for c in charge_data}
        ]
        days_since_last_refund = _days_since_latest(
            [r.get("created") for r in customer_refunds]
        )
        sub = (subscriptions.get("data") or [{}])[0]
        mrr = _monthly_amount(sub)

        open_disputes = sum(
            1
            for d in disputes.get("data", [])
            if d.get("status") in {"needs_response", "under_review", "warning_needs_response"}
            and d.get("charge") in {c.get("id") for c in charge_data}
        )

        fraud_risk = "low"
        if open_disputes >= 2:
            fraud_risk = "high"
        elif open_disputes == 1 or len(customer_refunds) >= 3:
            fraud_risk = "medium"

        return CustomerContext(
            customer_id=stripe_id,
            name=customer.get("name") or "",
            email=customer.get("email") or email or "",
            ltv_usd=round(ltv, 2),
            tenure_months=_months_since(customer.get("created")),
            subscription_status=sub.get("status", "unknown"),
            mrr_usd=mrr,
            refunds_given_count=len(customer_refunds),
            days_since_last_refund=days_since_last_refund,
            open_disputes=open_disputes,
            fraud_risk=fraud_risk,
        )


def _months_since(unix_ts: int | None) -> int:
    if not unix_ts:
        return 0
    created = datetime.fromtimestamp(unix_ts, tz=timezone.utc)
    delta = datetime.now(timezone.utc) - created
    return max(int(delta.days / 30), 0)


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

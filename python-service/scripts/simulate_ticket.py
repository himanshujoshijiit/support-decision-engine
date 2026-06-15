"""Fire sample tickets at the running decision engine — the demo driver.

Usage:
    python scripts/simulate_ticket.py            # send the full demo set
    python scripts/simulate_ticket.py --one      # send a single random-ish ticket
    python scripts/simulate_ticket.py --url http://localhost:8000

Each scenario maps to a seeded customer so the decisions are reproducible and tell a
clear story in the dashboard.
"""
from __future__ import annotations

import argparse
import json

import httpx

SCENARIOS = [
    {
        "label": "High-LTV billing refund (should AUTO-APPROVE)",
        "ticket": {
            "ticket_id": "T-1001",
            "customer_id": "cus_loyal_whale",
            "subject": "Double charged this month",
            "body": "Hi, I was charged twice for my $49 plan. Could I get a refund of $49? Thanks!",
            "source": "zendesk",
            "category": "billing",
            "refund_requested": True,
            "requested_refund_usd": 49,
        },
    },
    {
        "label": "Repeat refunder within 90 days (should ESCALATE for review)",
        "ticket": {
            "ticket_id": "T-1002",
            "customer_id": "cus_repeat_refunder",
            "subject": "Want a refund again",
            "body": "I'd like my money back for this month, $29. The feature still doesn't work.",
            "source": "intercom",
            "category": "billing",
            "refund_requested": True,
            "requested_refund_usd": 29,
        },
    },
    {
        "label": "Angry high-value customer (should PRIORITY_ROUTE)",
        "ticket": {
            "ticket_id": "T-1003",
            "customer_id": "cus_churn_risk",
            "subject": "This is unacceptable",
            "body": "Your outage cost us a demo. This is ridiculous and I'm ready to cancel and talk to a lawyer.",
            "source": "zendesk",
            "category": "technical",
            "refund_requested": False,
        },
    },
    {
        "label": "SLA breach (should ESCALATE immediately)",
        "ticket": {
            "ticket_id": "T-1004",
            "customer_id": "cus_new_trial",
            "subject": "Still no response after 3 days",
            "body": "I opened a ticket 3 days ago and nobody replied. What's going on?",
            "source": "zendesk",
            "category": "account",
            "refund_requested": False,
            "metadata": {"sla_breached": True},
        },
    },
    {
        "label": "Refund with no amount (should ASK_CLARIFICATION)",
        "ticket": {
            "ticket_id": "T-1005",
            "customer_id": "cus_loyal_whale",
            "subject": "Refund please",
            "body": "Please refund me.",
            "source": "intercom",
            "category": "billing",
            "refund_requested": True,
            "requested_refund_usd": 0,
        },
    },
]


def send(url: str, ticket: dict) -> dict:
    resp = httpx.post(f"{url.rstrip('/')}/decide", json=ticket, timeout=30.0)
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--one", action="store_true", help="send only the first scenario")
    args = parser.parse_args()

    scenarios = SCENARIOS[:1] if args.one else SCENARIOS
    for s in scenarios:
        print(f"\n=== {s['label']} ===")
        try:
            decision = send(args.url, s["ticket"])
        except Exception as exc:
            print(f"  ! request failed: {exc}")
            continue
        print(f"  action     : {decision['recommended_action']}")
        if decision.get("amount_usd") is not None:
            print(f"  amount     : ${decision['amount_usd']:.0f}")
        print(f"  confidence : {decision['confidence']}")
        print(f"  reason     : {decision['reason']}")
        print(f"  allowed    : {', '.join(decision.get('allowed_actions') or []) or '-'}")
        print(f"  policies   : {', '.join(decision['policy_matches']) or '-'}")
        print(f"  flags      : {', '.join(decision['flags']) or '-'}")
        print(f"  auto_exec  : {decision['auto_executed']}")
        if decision.get("policy_clamped"):
            print("  ! policy_clamped: model action was outside policy and was overridden")

    print("\nDone. Open the dashboard at http://localhost:8080/ to action these tickets.")


if __name__ == "__main__":
    main()

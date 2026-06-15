# Security & Data-Flow One-Pager

A page you can send to ops/finance before a pilot. Keep it honest — if you're
pre-compliance, say so with a timeline.

---

## What data we touch

| Source | Scope | Examples |
|--------|-------|----------|
| Helpdesk (Zendesk) | **Read-only** ticket + requester | subject, body, requester id, tags, priority |
| Billing (Stripe) | **Read-only** customer + charges | LTV, subscription status, recent charges, refund history |
| Optional write-back | Ticket tag / internal note only | "auto-approved by SDE", decision id |

We do **not** request payment-method, card, or PII beyond what's needed to decide a
ticket. No write access to issue refunds unless a customer explicitly enables it.

---

## How a decision flows

```
ticket → normalize → fetch context (read-only) → policy rules → LLM reason
   → orchestrator (policy caps the action) → store decision → agent acts → audit log
```

The LLM only ever sees the **context snapshot** for the ticket being decided, and can
only recommend an action the policy engine already permitted.

---

## Controls

- **Read-only scopes** — Zendesk ticket read, Stripe customer/charges read.
- **No model training on your data** without written opt-in.
- **Policy-before-LLM** — deterministic rules run first; the AI cannot choose an action
  outside the allowed set, and refund amounts are capped in code. Out-of-policy attempts
  are logged (`policy_clamped`).
- **Immutable audit trail** — every decision + human action is appended, attributed by
  agent id, with timestamps; exportable for finance review.
- **Encryption** — TLS in transit; encryption at rest (Postgres) for pilots.
- **Data retention** — 90 days default, configurable delete.
- **Tenant isolation** — one policy file + datastore per customer.

---

## Compliance posture (be honest)

- **SOC 2:** roadmap — Type I targeted [Qx], Type II [Qx+2]. Pre-compliance today.
- **GDPR/data deletion:** retention is configurable; deletion on request is supported.
- **Subprocessors:** LLM provider (OpenAI/Anthropic) only when enabled; otherwise the
  engine runs fully offline on the deterministic heuristic.

---

## Pilot defaults

- Run on a **sandbox or a single tagged queue** first.
- Read-only by default — no refunds executed automatically during the pilot.
- All recommendations reviewed by a human; we measure agreement vs. override rate.

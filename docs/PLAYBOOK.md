# Support Decision Engine — Founder Playbook

> The product is not the hard part. **Getting the first 3 paying customers is.**

This repo is the technical MVP. This doc is the go-to-market that goes with it.

> **Companion docs:** [Architecture & pipelines](ARCHITECTURE.md) ·
> [Outreach templates](OUTREACH.md) · [Demo script](DEMO_SCRIPT.md) ·
> [Security one-pager](SECURITY.md) · [Pilot agreement](PILOT_AGREEMENT.md) ·
> [Integration checklist](INTEGRATION_CHECKLIST.md)

---

## The one architectural principle (locked in)

```
Hard rules (policy)  →  Soft reasoning (LLM)  →  Human decision  →  Audit
```

**Never let the LLM invent an action outside what policy allows.** This is now enforced
in code by the Decision Orchestrator (`python-service/app/orchestrator.py`): the policy
engine emits `allowed_actions`, and any out-of-policy model recommendation is clamped and
logged (`policy_clamped`). Refund amounts are capped to the policy ceiling. That is the
trust story and the legal cover — not a prompt instruction, an enforced boundary.

---

## Gaps closed before build

| Gap | Fix |
|-----|-----|
| ICP too broad | Wedge: subscription SaaS, **$50–500 ARPU, refund-heavy** (devtools, education, fitness) |
| No success metrics | Defined below: time-to-action, override rate, refund $ saved, audit coverage |
| Security/compliance | [SECURITY.md](SECURITY.md): read-only scopes, retention, SOC2 timeline |
| Failure modes | Policy runs first; LLM reasons **only within allowed actions** (enforced) |
| Integration reality | **One helpdesk for MVP — Zendesk.** See [INTEGRATION_CHECKLIST.md](INTEGRATION_CHECKLIST.md) |
| Human workflow | Sidebar/queue console, not a separate product |
| Policy ownership | "We encode your playbook in week 1" = the onboarding fee |

---

## What you're building

A **judgment layer** between an incoming support ticket and the human/action that
resolves it. It reads context, applies policy, and either acts or tells the agent exactly
what to do and why.

**One-liner:** *"Your support team will never give a wrong refund, miss an SLA, or make
an inconsistent call again."*

Not a chatbot. Not another helpdesk. A decision + audit system.

---

## How the repo maps to the 6-week plan

| Week | Plan | Where it lives |
|---|---|---|
| 1–2 | Data in (webhook + context) | `python-service/app/webhooks.py`, `app/context/` |
| 3 | Policy engine (core IP) | `python-service/app/policy/`, `config/policies.json` |
| 4 | LLM reasoning layer | `python-service/app/llm/` |
| 5 | Agent UI + audit log | `java-service/.../static/index.html`, `java-service/.../model/Decision.java` |
| 6 | Feedback loop | override capture in `DecisionService` + `/api/stats` |

**Not in MVP:** mobile app, complex settings UI, multi-language, self-serve signup.
Integrations are mocked behind interfaces so it runs with zero accounts.

---

## The 15-minute demo

1. **(1–3) The pain.** Ask: *"How do your agents decide whether to give a refund?"* The
   answer will be vague. *"That's exactly the problem."*
2. **(3–10) The demo.** Run `python scripts/simulate_ticket.py`. Walk the dashboard:
   ticket in → customer history pulled → policy flags it → plain-English recommendation
   with a confidence score → agent clicks approve → done in 20s, logged forever. Then show
   an **override** and how the reason is captured.
3. **(10–13) The ROI.** *"How many tickets/day? How many are judgment calls? What's the
   cost of one wrong refund or one missed SLA?"* Let the numbers sell.
4. **(13–15) The ask.** *"We're working with 3 pilot companies at a reduced rate. Let me
   set this up on your actual tickets for 2 weeks, no commitment. Want to try?"*

---

## First 3 customers

1. **Warm network** — one founder/ops head you know. Free for 30 days for honest feedback
   + a testimonial. Social proof unlocks customers 2 and 3.
2. **Targeted cold outreach** — SaaS, 50–200 employees, has a support team, uses
   Intercom/Zendesk. Message the Head of Support or COO:
   > *"Hey [Name] — I'm building a tool that gives support agents an instant recommendation
   > (refund / escalate / deny) on every ticket, with the reasoning shown. Takes 2 weeks to
   > plug into Zendesk. Would a 15-min demo be worth your time?"*
3. **Referral** — after feedback, ask *"Who else do you know running a support team that
   would find this useful?"* One warm referral beats 100 cold emails.

---

## Pricing

| Package | Price | Includes |
|---|---|---|
| Pilot | Free / 30 days | Full setup, your involvement, feedback expected |
| Starter | $499/mo | Up to 500 tickets/mo, 1 integration |
| Growth | $1,200/mo | Unlimited tickets, 3 integrations, audit log |
| Custom | $2,500+/mo | Custom policy engine, dedicated support |

**Onboarding fee:** one-time setup fee (e.g. ₹75,000–₹1,50,000). Covers your time and
filters out non-serious buyers.

---

## The moat

The feedback loop. Every override + reason (captured in the Java audit store and surfaced
in `/api/stats`) is raw material for tuning that customer's `policies.json`. The longer
they use it, the better it fits their policies — and the harder it is to rip out.

---

## 30-day action plan (with deliverables)

| Week | Build | GTM | Deliverable |
|------|-------|-----|-------------|
| 1 | Zendesk webhook + Stripe context | 5 warm messages | One real ticket flowing into the audit store |
| 2 | Policy engine + LLM JSON + orchestrator | 5 cold LinkedIn | API prints a clamped, policy-safe recommendation |
| 3 | Agent console + audit log | 3 demo calls | Recordable 10-min demo |
| 4 | Override capture + policy export | Close 1 pilot | Signed pilot + sandbox checklist |

## Pilot success criteria (put in the pilot agreement)

- ≥ 80% of recommendations in the "acceptable" set per ops lead
- ≥ 30% reduction in time-to-first-action on judgment tickets
- 100% audit coverage
- Override reasons captured on ≥ 90% of overrides

These map to `GET /api/stats` (agreement/override rate) and the per-decision audit trail.
See [PILOT_AGREEMENT.md](PILOT_AGREEMENT.md).

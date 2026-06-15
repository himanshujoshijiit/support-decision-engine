# 15-Minute Demo Script (word for word)

**Setup:** a real or realistic ticket pre-loaded. Screen: the agent console
(`http://localhost:8080/`) with the recommendation panel visible. Have
`python scripts/simulate_ticket.py` ready to fire the demo set.

---

### [0:00–1:00] Open

> "Before I show anything — quick question: when your agents get a refund request, how do
> they decide yes or no?"

*[Let them talk. Don't interrupt.]*

> "That's exactly what we built for. Not replacing agents — giving them a consistent
> judgment layer so finance and ops can trust every call."

---

### [1:00–2:00] Frame the flow

> "I'll walk one ticket end to end. Ticket comes in from Zendesk, we pull customer and
> billing context, run your policies, then the system recommends an action with a
> plain-English reason. Agent approves or overrides in one click. Everything is logged."

---

### [2:00–4:00] Ticket arrives

*[Click the "Double charged" ticket.]*

> "Here's a billing ticket — customer says they were double-charged. Watch the right panel."

*[Context loads: LTV $2,400, 8-month customer, 0 refunds in 90 days, duplicate charge.]*

> "In about two seconds we've pulled tenure, lifetime value, refund history, and billing
> status. This is what agents usually tab-hop for."

---

### [4:00–6:00] Policy engine (runs FIRST)

*[Point at the policy chips and the "Policy allowed" row.]*

> "Policy layer ran first — not the AI. Your rules: high-LTV billing issues with no recent
> refund are eligible for refund up to your cap. This ticket hit that rule. That's your
> playbook, encoded. And notice this row — these are the *only* actions the AI is even
> allowed to recommend on this ticket. It physically cannot invent a different one."

---

### [6:00–9:00] LLM recommendation

*[Show: Action APPROVE REFUND ($49), confidence, reason block.]*

> "Recommendation: approve refund of $49. Reason: eight-month customer, $2,400 LTV, first
> refund request, duplicate charge confirmed — low fraud risk, aligns with policy."

> "The model doesn't invent policy. It explains the call inside the boundaries your rules
> allow. If it ever tried to step outside them, the system overrides it and logs that it
> tried — that's the compliance story."

---

### [9:00–11:00] Agent action + audit

*[Click Approve.]*

> "Agent clicks approve — done. The helpdesk updates; the refund triggers or queues per
> your workflow."

*[Open the audit trail on the card.]*

> "This is what your CFO cares about: ticket ID, context snapshot, rules fired,
> recommendation, the human action, and a timestamp. If someone overrides, we capture
> *why* — and that reason feeds policy tuning later."

---

### [11:00–13:00] ROI (let them do the math)

> "Rough numbers — how many tickets a day need a judgment call: refund, credit,
> escalation? … And how long does an agent spend researching the account and billing
> before deciding? … What's the fully loaded cost per agent hour?"

*[Pause. Let them multiply.]*

> "Even at 50 judgment tickets a day and five minutes saved each, that's four-plus hours
> back daily — before counting wrong refunds or missed SLAs."

---

### [13:00–15:00] Close

> "We're running three pilots at reduced setup — plug into your Zendesk and Stripe, encode
> your refund and escalation rules in week one, run on a real queue or sandbox for two
> weeks, no commitment."

> "If it's useful, we move to Starter at $499/month; setup is a one-time onboarding fee
> because we're encoding your policies with you."

> "Want to pick a pilot kickoff date, or should I send the security one-pager and sandbox
> checklist first?"

---

## Objection handlers (keep in pocket)

| They say | You say |
|----------|---------|
| "We already use AI in Zendesk" | "That's usually deflection or macros. We're focused on **judgment calls** — refund, deny, escalate — with audit and a hard policy boundary." |
| "Agents won't trust AI" | "They don't have to. Policy runs first; the AI can only suggest actions policy allows; agents override with one click and a reason." |
| "Security?" | "Read-only APIs, no training on your data without opt-in, configurable retention, audit export for compliance. One-pager attached." |
| "What if the AI gives a wrong refund?" | "It structurally can't exceed your policy — the engine clamps any out-of-policy action and logs the attempt. The refund ceiling is enforced in code." |
| "Build in-house?" | "You can — most teams underestimate policy maintenance and audit. We're live in two weeks; you own the rules, we run the layer." |

---

## The live demo set

`python scripts/simulate_ticket.py` fires five scenarios that each tell a clear story:

1. High-LTV billing refund → **AUTO-APPROVE** (capped at policy ceiling)
2. Repeat refunder within 90 days → **ESCALATE for review**
3. Angry high-value customer → **PRIORITY_ROUTE**
4. SLA breach → **ESCALATE immediately**
5. Refund with no amount → **ASK_CLARIFICATION**

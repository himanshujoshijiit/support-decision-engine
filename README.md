# Support Decision Engine

A **judgment layer** that sits between an incoming support ticket and the human/action
that resolves it. It reads context, applies policy, and either acts or tells the agent
*exactly what to do and why*.

> *"Your support team will never give a wrong refund, miss an SLA, or make an inconsistent call again."*

This is **not** a chatbot and **not** another helpdesk. It is a decision + audit system.

---

## Architecture

Two services, split by responsibility:

| Service | Language | Responsibility |
|---|---|---|
| `python-service` | Python (FastAPI) | The **AI judgment layer**: webhook intake → customer-context fetch → policy rules engine → LLM reasoning → **orchestrator (policy caps the LLM action)** → emit a `Decision` |
| `java-service` | Java (Spring Boot) | The **enterprise audit + decision store**: persists every decision, serves the agent dashboard, records human actions (approve / override / escalate) and override reasons (the feedback loop) |

### The principle this rests on

```
Hard rules (policy) → Soft reasoning (LLM) → Human decision → Audit
```

The policy engine runs **first** and emits the set of `allowed_actions`. The LLM may only
recommend an action from that set — the **Decision Orchestrator**
(`python-service/app/orchestrator.py`) clamps anything out of policy and caps refund
amounts in code. A hallucinating or jailbroken model cannot issue a refund your policy
forbids. That's the trust story; see [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

```
                    ┌──────────────────────────────────────────────┐
 Zendesk / Intercom │                PYTHON SERVICE                  │
 webhook ──────────►│  intake → context → policy engine → LLM layer  │
                    │            produces a Decision                 │
                    └───────────────────────┬────────────────────────┘
                                             │ POST /api/decisions
                                             ▼
                    ┌──────────────────────────────────────────────┐
                    │                 JAVA SERVICE                   │
   Agent dashboard ◄┤  stores decisions • audit log • agent actions  │
   (approve/        │  approve / override (+reason) / escalate        │
    override)       └────────────────────────────────────────────────┘
```

Why this split? The Python side is where the AI "wow moment" lives and where Python's
LLM/ML ecosystem shines. The Java side is the durable, traceable system of record that
CFOs and ops heads trust — full audit trail of *what was recommended, what the human did,
and why*.

---

## Quick start

You need **two terminals**.

### 1. Java audit + dashboard service

```bash
cd java-service
mvn spring-boot:run
```

- Dashboard: http://localhost:8080/
- API:       http://localhost:8080/api/decisions

### 2. Python decision engine (requires Python 3.10+)

```bash
cd python-service
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- API + docs: http://localhost:8000/docs

### 3. Send a sample ticket (the demo)

```bash
cd python-service
python scripts/simulate_ticket.py
```

Watch it appear in the dashboard at http://localhost:8080/ with an AI recommendation,
a confidence score, and a plain-English reason. Click **Approve** / **Override** / **Escalate**
and see it logged in the audit trail.

---

## What's intentionally NOT built (per the MVP plan)

Mobile app, complex settings UI, multi-language, self-serve signup. None of that belongs
in the MVP. Integrations (Stripe, Zendesk) are **mocked** behind clean interfaces so the
whole thing runs end-to-end with zero external accounts or API keys — swap in the real
provider when a pilot customer is ready.

## Documentation

| Doc | What's in it |
|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | System + sequence diagrams, the full pipeline, data model, policy config, prompt skeleton, stack |
| [`docs/PLAYBOOK.md`](docs/PLAYBOOK.md) | Founder GTM: positioning, pricing, the moat, 30-day plan, success metrics |
| [`docs/OUTREACH.md`](docs/OUTREACH.md) | Warm / cold / post-demo / referral / CFO message templates |
| [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) | Word-for-word 15-minute demo + objection handlers |
| [`docs/SECURITY.md`](docs/SECURITY.md) | Data-flow + compliance one-pager for ops/finance |
| [`docs/PILOT_AGREEMENT.md`](docs/PILOT_AGREEMENT.md) | 1-page pilot/LOI skeleton + success criteria |
| [`docs/INTEGRATION_CHECKLIST.md`](docs/INTEGRATION_CHECKLIST.md) | Zendesk + Stripe scopes, webhooks, test tickets, go-live gate |

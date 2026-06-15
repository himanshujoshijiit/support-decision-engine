# Python Service — The AI Judgment Layer

FastAPI app that turns an incoming support ticket into an auditable **Decision**.

```
ticket ─► fetch context ─► policy engine ─► LLM reasoning ─► orchestrator ─► Decision
                              (allowed_actions)              (caps the LLM)     │
                                                                                ▼
                                                              POST to Java audit store
```

The **orchestrator** is the trust gate: the policy engine emits `allowed_actions`, and
the orchestrator clamps any model recommendation outside that set (`policy_clamped`) and
caps refund amounts to the policy ceiling. See [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md).

## Run

Requires **Python 3.10+**.

```bash
python -m venv .venv
# Windows:      .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Open the interactive API docs at http://localhost:8000/docs.

> **No API keys needed.** The LLM layer falls back to a deterministic heuristic and the
> customer context is mocked. Everything runs offline. Add a `.env` (see `.env.example`)
> to switch on OpenAI/Anthropic or Stripe.

## Try it

```bash
python scripts/simulate_ticket.py
```

Or score a single ticket directly:

```bash
curl -X POST http://localhost:8000/decide \
  -H "Content-Type: application/json" \
  -d '{"ticket_id":"T-1","customer_id":"cus_loyal_whale","subject":"Double charged","body":"Refund of $49 please","category":"billing","refund_requested":true,"requested_refund_usd":49}'
```

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET  | `/health` | Service + provider status |
| POST | `/decide` | Score a normalized ticket (demo/manual) |
| POST | `/webhooks/zendesk` | Zendesk ticket webhook |
| POST | `/webhooks/intercom` | Intercom conversation webhook |
| POST | `/admin/reload-policies` | Hot-reload `config/policies.json` |

## Layout

```
app/
  main.py          FastAPI routes (intake)
  pipeline.py      wires the stages in order
  orchestrator.py  the trust gate: policy caps the LLM action + refund amount
  models.py        Ticket / CustomerContext / PolicyResult / Decision
  webhooks.py      Zendesk/Intercom -> Ticket adapters
  audit_client.py  ships decisions to the Java store
  config.py        env-driven settings
  context/         customer-context providers (mock + stripe skeleton)
  policy/          the JSON-driven rules engine  (core IP, emits allowed_actions)
  llm/             reasoning layer (heuristic + OpenAI + Anthropic)
config/policies.json   editable policy rules
scripts/simulate_ticket.py   demo driver
tests/                 policy-engine unit tests
```

## Test

```bash
pytest
```

## Tuning policies

Edit `config/policies.json` (rules are sorted by `priority`, highest wins) and call
`POST /admin/reload-policies` — no redeploy. This is the file an ops team owns.

## Production setup

Copy `.env.example` to `.env` and configure:

| Variable | Purpose |
|---|---|
| `SDE_API_KEY` | Shared key for Java audit API + dashboard (header: `X-API-Key`) |
| `ENGINE_API_KEY` | Protects Python `/decide`, webhooks, `/admin/*` |
| `ZENDESK_WEBHOOK_SECRET` | HMAC verification on `/webhooks/zendesk` |
| `STRIPE_API_KEY` + `CONTEXT_PROVIDER=stripe` | Real billing context (email → Stripe customer lookup) |
| `RETRY_ATTEMPTS` / `RETRY_BASE_DELAY` | Exponential backoff for audit + Stripe calls |

**Docker (both services):**

```bash
# from repo root
docker compose up --build
```

Dashboard: http://localhost:8080/ · Engine: http://localhost:8000/docs

When `SDE_API_KEY` is set, the dashboard prompts for the key on first load (stored in session).

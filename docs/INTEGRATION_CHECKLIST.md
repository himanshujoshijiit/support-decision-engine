# Zendesk + Stripe Integration Checklist

For MVP we pick **one** helpdesk (Zendesk — usually easiest for B2B SaaS) and **one**
billing source (Stripe). Both are mocked behind clean interfaces, so you flip from mock
to real by setting env vars and dropping in credentials — no code changes to the pipeline.

---

## 0. Local first (no accounts)

The engine runs fully offline with the mock context provider and heuristic reasoner:

```bash
# Java audit store
cd java-service && mvn spring-boot:run        # http://localhost:8080/

# Python engine
cd python-service && uvicorn app.main:app --reload --port 8000
python scripts/simulate_ticket.py             # fire the demo set
```

Confirm decisions appear in the dashboard before wiring anything real.

---

## 1. Zendesk (read-only)

**API scopes / auth**
- [ ] Create an API token (Admin Center → Apps and integrations → APIs → Zendesk API).
- [ ] Use a dedicated read-only agent/service account.
- [ ] Required read: **Tickets read**, **Users read** (requester context).
- [ ] (Optional write-back) **Tickets write** only if you want tags / internal notes.

**Webhook**
- [ ] Create a webhook → target URL `https://<your-host>/webhooks/zendesk`.
- [ ] Trigger on `ticket.created` (and optionally `ticket.updated`).
- [ ] Add a signing secret; verify the signature at the receiver (TODO before prod).
- [ ] Payload: ensure subject/description/requester are included.

**Test tickets**
- [ ] Create a sandbox or use a **tagged queue** (e.g. tag `sde-pilot`).
- [ ] Fire: a billing/refund ticket, a no-response/SLA ticket, an angry message.
- [ ] Confirm each becomes a `Decision` in the dashboard with the expected action.

> The normalizer (`app/webhooks.py::from_zendesk`) already tolerates flattened or nested
> payloads and auto-detects category + refund intent + amount.

---

## 2. Stripe (read-only)

**API key / scopes**
- [ ] Create a **restricted key** (Developers → API keys → Restricted).
- [ ] Grant **read** on: Customers, Charges, Subscriptions, Refunds, Disputes.
- [ ] Grant **no write** permissions.
- [ ] Store as `STRIPE_API_KEY`; never commit it.

**Wire it up**
- [ ] Set in `python-service/.env`:
  ```
  CONTEXT_PROVIDER=stripe
  STRIPE_API_KEY=rk_live_or_test_xxx
  ```
- [ ] Map your Zendesk requester → Stripe customer (email match or external id).
- [ ] Implement the field mapping in `app/context/stripe_provider.py`
      (LTV, tenure, refunds_last_90d, subscription_status, fraud_risk).

**Test**
- [ ] Use Stripe **test mode** customers with known LTV / refund history.
- [ ] Confirm the `context_snapshot` on a decision reflects real Stripe data.

---

## 3. LLM provider (optional — heuristic works without it)

- [ ] Set in `.env`:
  ```
  LLM_PROVIDER=openai        # or anthropic
  OPENAI_API_KEY=sk-xxx      # or ANTHROPIC_API_KEY
  LLM_MODEL=gpt-4o-mini
  ```
- [ ] Confirm `GET /health` shows `"llm_live": true`.
- [ ] Run the demo set and confirm reasons are model-generated, actions still respect
      `allowed_actions` (the orchestrator clamps anything out of policy).

---

## 4. Audit store → Postgres (for the pilot)

H2 (in-memory) is the default. For a pilot, point Spring at Postgres in
`java-service/src/main/resources/application.properties`:

```properties
spring.datasource.url=jdbc:postgresql://localhost:5432/sde
spring.datasource.username=sde
spring.datasource.password=...
spring.jpa.hibernate.ddl-auto=update
```

- [ ] Confirm decisions persist across restarts.
- [ ] Set `AUDIT_BASE_URL` in the Python `.env` if the Java service isn't on localhost:8080.

---

## 5. Policies (week-1 onboarding work)

- [ ] Encode the customer's refund/SLA/escalation rules in `config/policies.json`.
- [ ] Set `then.allow` per rule (the action whitelist) and `max_refund_usd` ceilings.
- [ ] Hot-reload with `POST /admin/reload-policies` — no redeploy.
- [ ] Walk the ops owner through each rule and the `allowed_actions` it produces.

---

## 6. Go-live gate

- [ ] Read-only verified end to end (no accidental writes).
- [ ] Webhook signature verification enabled.
- [ ] Secrets in a vault / env, not in git.
- [ ] Audit export tested (hand it to the finance contact).
- [ ] Success metrics dashboard (`GET /api/stats`) reviewed with the ops lead.

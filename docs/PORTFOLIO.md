# Decision Intelligence Suite — Portfolio

You're building a **suite of decision intelligence tools** for mid-size SaaS companies.
Same buyer, same trust, increasing ACV over time.

---

## Products

### 1. Support Decision Engine (live)

**Problem:** Agents decide refunds/escalations from gut feel — inconsistent, unaudited.

**Solution:** Policy runs first → LLM explains → human approves → full audit trail.

**Stack:** Python (FastAPI) + Java (Spring Boot) · Zendesk + Stripe (mocked)

**Path:** `projects/support-decision-engine/` + `java-service/`

---

### 2. Churn Causality Engine (MVP)

**Problem:** "Why are customers leaving?" — product and ops guess from dashboards.

**Solution:** Mixpanel/Amplitude + billing → journey friction → churn score → plain-English root causes.

**Stack:** Python (FastAPI) · mock analytics · port **8001**

**Natural upsell:** Every support-engine customer eventually asks about churn.

---

### 3. Internal Knowledge Search (MVP)

**Problem:** "Where is that doc?" — tribal knowledge in Notion, Slack, Drive.

**Solution:** Connect sources → ask a question → answer with citations.

**Stack:** Python (FastAPI) · mock corpus · port **8002**

**Wow factor:** Instant demo — no integrations required for pilot.

---

### 4. Cost Drift Detector (MVP)

**Problem:** AWS/cloud costs creep silently; finance finds out at month-end.

**Solution:** Baseline vs current scan → severity-ranked findings → likely cause + fix.

**Stack:** Python (FastAPI) · mock CUR data · port **8003**

**Buyer:** CFO — you're already in the room via support audit story.

---

## Revenue model (per customer)

| Product | Monthly |
|---------|---------|
| Support Decision Engine | $500–1,500 |
| Churn Causality Engine | $800–3,000 |
| Knowledge Search | $300–800 per team |
| Cost Drift | $500–2,000 |
| **Suite (all three core)** | **$2,000–5,000** |

---

## Build order (honest)

1. Pilot customer on **Support** — nothing else matters until this
2. LinkedIn demo video
3. **Churn** hardening from real feedback
4. **Knowledge Search** as expansion play
5. **Cost Drift** when finance is in the loop
6. Package as **Decision Suite** with shared auth + billing

---

## Shared architecture pattern

Each product follows the same MVP shape:

```
Sources (mocked)  →  deterministic rules / scoring  →  plain-English output  →  simple UI
```

Support adds: orchestrator trust boundary + Java audit store (enterprise requirement).

Future: shared `platform/` package for auth, tenant config, audit export.

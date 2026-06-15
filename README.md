# Decision Intelligence Suite

Four **decision intelligence** products for mid-size SaaS — same buyer (ops/product/finance), increasing ACV.

| # | Product | Folder | Port | Status | ACV |
|---|---------|--------|------|--------|-----|
| 1 | **Support Decision Engine** | [`projects/support-decision-engine/`](projects/support-decision-engine/) + [`java-service/`](java-service/) | 8000 + 8080 | Live MVP | $500–1,500/mo |
| 2 | **Churn Causality Engine** | [`projects/churn-causality-engine/`](projects/churn-causality-engine/) | 8001 | MVP | $800–3,000/mo |
| 3 | **Internal Knowledge Search** | [`projects/knowledge-search/`](projects/knowledge-search/) | 8002 | MVP | $300–800/mo per team |
| 4 | **Cost Drift Detector** | [`projects/cost-drift-detector/`](projects/cost-drift-detector/) | 8003 | MVP | CFO-led |

**One customer on all three upsells ≈ $2,000–5,000/month.** Close 10 companies → ₹1–3 Cr/year.

---

## Honest priority order

1. **Get 1 pilot** on Support Decision Engine ← do this before building anything new
2. Record a demo video and post on LinkedIn
3. **Churn Causality Engine** once you have customer feedback (natural upsell)
4. Package as **Decision Suite** for mid-size SaaS

---

## Run everything (requires Python 3.10+)

**Terminal 1 — Support (Java dashboard)**

```powershell
cd java-service
mvn spring-boot:run
```

**Terminal 2 — Support (Python engine)**

```powershell
cd projects/support-decision-engine/python-service
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
python scripts/simulate_ticket.py
```

Dashboard: http://localhost:8080/

**Terminal 3+ — New products (each in its own venv or shared)**

```powershell
# Churn
cd projects/churn-causality-engine
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# Knowledge Search
cd projects/knowledge-search
uvicorn app.main:app --reload --port 8002

# Cost Drift
cd projects/cost-drift-detector
uvicorn app.main:app --reload --port 8003
```

| Product | URL |
|---------|-----|
| Support dashboard | http://localhost:8080/ |
| Churn dashboard | http://localhost:8001/ |
| Knowledge Search | http://localhost:8002/ |
| Cost Drift | http://localhost:8003/ |

---

## Portfolio strategy

```
Support Decision Engine  →  first entry point   ($500–1,500/mo)
         +
Churn Causality Engine   →  upsell              ($800–3,000/mo)
         +
Knowledge Search         →  expansion           ($300–800/mo)
         +
Cost Drift Detector      →  finance expansion   (custom)
```

---

## Documentation

Open **[docs/index.html](docs/index.html)** in a browser for the full HTML docs (architecture, outreach, demo script, security, integration, **getting started**).

Markdown docs: [`docs/PORTFOLIO.md`](docs/PORTFOLIO.md) · [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) · [`docs/PLAYBOOK.md`](docs/PLAYBOOK.md)

---

## Repo layout

```
decision-intelligence-suite/   (this repo)
├── java-service/              Support audit store + agent dashboard
├── projects/
│   ├── support-decision-engine/python-service/
│   ├── churn-causality-engine/
│   ├── knowledge-search/
│   └── cost-drift-detector/
└── docs/                      Shared GTM + architecture docs
```

# Churn Causality Engine

Connects **Mixpanel/Amplitude + Stripe** (mocked for MVP) → detects journey friction →
scores churn risk → outputs **plain-English root causes** with recommended actions.

Natural upsell after Support Decision Engine — same buyer, same data sources.

## Run

```powershell
cd projects/churn-causality-engine
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

- Dashboard: http://localhost:8001/
- API docs: http://localhost:8001/docs

## Demo

```powershell
python scripts/simulate_churn.py
```

## Pipeline

```
analytics events + billing  →  friction detection  →  churn score  →  root cause narrative
```

## Pricing target

$800–3,000/month — maps directly to retained MRR.

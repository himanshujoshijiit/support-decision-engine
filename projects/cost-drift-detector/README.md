# Cost Drift Detector

Detects **AWS/cloud cost drift** vs baseline — the silent spend creep finance teams miss.

Natural expansion once you're already talking to ops/finance buyers through the Support Decision Engine.

## Run

```powershell
cd projects/cost-drift-detector
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8003
```

- Dashboard: http://localhost:8003/
- API: `GET /scan` or `POST /scan`

## What it flags (demo data)

- NAT Gateway traffic spike (+110%)
- CloudWatch log ingestion doubling
- Staging EC2 left running 24/7

## Pricing target

CFO-led — low competition, high pain. Custom pricing $500–2,000/mo.

# Internal Knowledge Search

Connect **Notion + Slack + Google Drive** (mocked for MVP) → search → answer with citations.

Every support buyer also says *"our team can't find anything."* Easiest second product to demo.

## Run

```powershell
cd projects/knowledge-search
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8002
```

- UI: http://localhost:8002/
- API: `POST /ask` with `{"question": "..."}`

## Example

```powershell
curl -X POST http://localhost:8002/ask -H "Content-Type: application/json" -d "{\"question\":\"refund policy for annual plans\"}"
```

## Pricing target

$300–800/month per team — per-seat SaaS, very sticky once embedded.

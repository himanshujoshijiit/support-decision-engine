# Support Decision Engine

First product in the Decision Intelligence Suite — a **judgment layer** for support tickets.

| Component | Path | Port |
|-----------|------|------|
| Python engine | `python-service/` | 8000 |
| Java audit + dashboard | `../../java-service/` *(moving here when not running)* | 8080 / 8090 |

See repo root [README.md](../../README.md) and [docs/](../../docs/).

```powershell
# Terminal 1 — Java
cd java-service
mvn spring-boot:run

# Terminal 2 — Python
cd projects/support-decision-engine/python-service
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Demo
python scripts/simulate_ticket.py
```

Dashboard: http://localhost:8080/

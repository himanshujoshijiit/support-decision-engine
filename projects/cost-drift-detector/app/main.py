"""Cost Drift Detector API."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app import __version__
from app.detect.drift_engine import scan
from app.models import ScanResult

app = FastAPI(title="Cost Drift Detector", version=__version__)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_STATIC = Path(__file__).resolve().parent.parent / "static"


@app.get("/health")
def health():
    return {"status": "ok", "version": __version__, "product": "cost-drift-detector"}


@app.post("/scan", response_model=ScanResult)
def run_scan() -> ScanResult:
    return scan()


@app.get("/scan", response_model=ScanResult)
def run_scan_get() -> ScanResult:
    return scan()


@app.get("/")
def ui():
    p = _STATIC / "index.html"
    return FileResponse(p) if p.exists() else {"docs": "/docs"}

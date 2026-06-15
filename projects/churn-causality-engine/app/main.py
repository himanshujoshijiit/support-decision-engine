"""Churn Causality Engine API."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path

from app import __version__
from app.models import AnalyzeRequest, ChurnAnalysis
from app.pipeline import get_pipeline

app = FastAPI(
    title="Churn Causality Engine",
    version=__version__,
    description="Connects product analytics + billing → friction → churn risk → plain-English root causes.",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_STATIC = Path(__file__).resolve().parent.parent / "static"


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": __version__, "product": "churn-causality-engine"}


@app.post("/analyze", response_model=ChurnAnalysis)
def analyze(req: AnalyzeRequest) -> ChurnAnalysis:
    return get_pipeline().analyze(req.customer_id)


@app.get("/analyze/{customer_id}", response_model=ChurnAnalysis)
def analyze_get(customer_id: str) -> ChurnAnalysis:
    return get_pipeline().analyze(customer_id)


@app.get("/")
def dashboard():
    index = _STATIC / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"message": "Churn Causality Engine API", "docs": "/docs"}

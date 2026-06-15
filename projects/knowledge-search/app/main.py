"""Knowledge Search API."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app import __version__
from app.ask.answerer import answer
from app.models import AskRequest, AskResponse, SearchHit
from app.search.engine import search

app = FastAPI(title="Internal Knowledge Search", version=__version__)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_STATIC = Path(__file__).resolve().parent.parent / "static"


@app.get("/health")
def health():
    return {"status": "ok", "version": __version__, "product": "knowledge-search"}


@app.get("/search")
def search_get(q: str, top_k: int = 5) -> list[SearchHit]:
    return search(q, top_k)


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    hits = search(req.question, req.top_k)
    return answer(req, hits)


@app.get("/")
def ui():
    p = _STATIC / "index.html"
    return FileResponse(p) if p.exists() else {"docs": "/docs"}

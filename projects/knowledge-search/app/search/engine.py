"""Simple keyword search over the mock corpus."""
from __future__ import annotations

import re

from app.models import Document, SearchHit
from app.sources.mock_index import all_documents


def search(query: str, top_k: int = 5) -> list[SearchHit]:
    tokens = _tokenize(query)
    hits: list[SearchHit] = []
    for doc in all_documents():
        text = f"{doc.title} {doc.body}".lower()
        score = sum(1 for t in tokens if t in text)
        if score == 0:
            continue
        snippet = _snippet(doc.body, tokens)
        hits.append(SearchHit(document=doc, score=float(score), snippet=snippet))
    hits.sort(key=lambda h: h.score, reverse=True)
    return hits[:top_k]


def _tokenize(q: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9]+", q.lower()) if len(w) > 2]


def _snippet(body: str, tokens: list[str], width: int = 160) -> str:
    lower = body.lower()
    for t in tokens:
        i = lower.find(t)
        if i >= 0:
            start = max(0, i - 40)
            return ("..." if start else "") + body[start : start + width] + "..."
    return body[:width] + "..."

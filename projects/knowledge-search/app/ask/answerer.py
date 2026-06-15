"""Synthesize an answer from search hits (heuristic; LLM later)."""
from __future__ import annotations

from app.models import AskRequest, AskResponse, Citation, SearchHit


def answer(req: AskRequest, hits: list[SearchHit]) -> AskResponse:
    if not hits:
        return AskResponse(
            question=req.question,
            answer="I couldn't find anything relevant in Notion, Slack, or Drive. Try rephrasing or check if the doc exists.",
            citations=[],
            confidence=0.2,
        )

    top = hits[0]
    citations = [
        Citation(
            source=h.document.source,
            title=h.document.title,
            url=h.document.url,
            snippet=h.snippet,
        )
        for h in hits[: req.top_k]
    ]

    # Plain-English synthesis from top snippets — good enough for demo.
    parts = [f"Based on **{top.document.title}** ({top.document.source}): {top.snippet}"]
    if len(hits) > 1:
        parts.append(
            f"Also see **{hits[1].document.title}** for related context."
        )
    answer_text = " ".join(parts)
    confidence = min(0.5 + 0.1 * len(hits), 0.92)

    return AskResponse(
        question=req.question,
        answer=answer_text,
        citations=citations,
        confidence=round(confidence, 2),
    )

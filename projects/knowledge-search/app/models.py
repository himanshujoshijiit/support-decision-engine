"""Models for knowledge search."""
from __future__ import annotations

from pydantic import BaseModel, Field


class Document(BaseModel):
    id: str
    source: str  # notion | slack | drive
    title: str
    body: str
    url: str = ""
    updated_at: str = ""


class SearchHit(BaseModel):
    document: Document
    score: float
    snippet: str


class AskRequest(BaseModel):
    question: str
    top_k: int = Field(default=3, ge=1, le=10)


class Citation(BaseModel):
    source: str
    title: str
    url: str
    snippet: str


class AskResponse(BaseModel):
    question: str
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)

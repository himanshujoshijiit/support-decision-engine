"""Domain models for churn analysis."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class JourneyEvent(BaseModel):
    name: str
    timestamp: datetime
    properties: dict = Field(default_factory=dict)


class FrictionPoint(BaseModel):
    step: str
    drop_off_rate: float = Field(ge=0.0, le=1.0)
    severity: str
    detail: str


class BehavioralSignal(BaseModel):
    signal_id: str
    label: str
    value: float | str
    weight: float = 1.0


class RootCause(BaseModel):
    title: str
    explanation: str
    confidence: float = Field(ge=0.0, le=1.0)
    recommended_action: str


class ChurnAnalysis(BaseModel):
    customer_id: str
    plan: str = "unknown"
    mrr_usd: float = 0.0
    tenure_days: int = 0
    churn_risk_score: float = Field(ge=0.0, le=1.0)
    risk_level: RiskLevel
    friction_points: list[FrictionPoint] = Field(default_factory=list)
    behavioral_signals: list[BehavioralSignal] = Field(default_factory=list)
    root_causes: list[RootCause] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_now)


class AnalyzeRequest(BaseModel):
    customer_id: str
    include_cohort_context: bool = False

"""Cost drift models."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class CostLineItem(BaseModel):
    service: str
    account: str = "production"
    environment: str = "prod"
    current_usd: float
    baseline_usd: float


class DriftFinding(BaseModel):
    service: str
    account: str
    environment: str
    baseline_usd: float
    current_usd: float
    delta_usd: float
    delta_pct: float
    severity: Severity
    likely_cause: str
    recommended_action: str


class ScanResult(BaseModel):
    scan_id: str
    period: str = "last_30d"
    total_baseline_usd: float
    total_current_usd: float
    total_delta_usd: float
    findings: list[DriftFinding] = Field(default_factory=list)
    scanned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

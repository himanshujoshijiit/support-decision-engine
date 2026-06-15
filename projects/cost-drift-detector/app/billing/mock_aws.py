"""Mock AWS Cost Explorer / CUR data."""
from __future__ import annotations

from app.models import CostLineItem

# Baseline = prior month; current = this month (with intentional drift)
CURRENT: list[CostLineItem] = [
    CostLineItem(service="EC2", account="prod", current_usd=4200, baseline_usd=3800),
    CostLineItem(service="RDS", account="prod", current_usd=890, baseline_usd=850),
    CostLineItem(service="S3", account="prod", current_usd=320, baseline_usd=280),
    CostLineItem(service="Lambda", account="prod", current_usd=45, baseline_usd=40),
    CostLineItem(service="CloudWatch", account="prod", current_usd=180, baseline_usd=95),
    CostLineItem(service="EC2", account="staging", current_usd=890, baseline_usd=420),
    CostLineItem(service="NAT Gateway", account="prod", current_usd=650, baseline_usd=310),
    CostLineItem(service="EKS", account="prod", current_usd=1100, baseline_usd=1050),
]


def fetch_current_costs() -> list[CostLineItem]:
    return list(CURRENT)

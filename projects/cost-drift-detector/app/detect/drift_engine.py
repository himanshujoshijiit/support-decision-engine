"""Detect cost drift vs baseline."""
from __future__ import annotations

import uuid

from app.billing.mock_aws import fetch_current_costs
from app.models import CostLineItem, DriftFinding, ScanResult, Severity

_CAUSES = {
    "EC2": "New m5.2xlarge instances in us-east-1 — check autoscaling group max size.",
    "RDS": "Storage autoscaling triggered; review retention and instance class.",
    "S3": "Increased PUT requests — likely log shipping or backup duplication.",
    "Lambda": "Invocation spike from new webhook handler — within normal variance.",
    "CloudWatch": "Log ingestion doubled — verbose debug logging left on in prod.",
    "NAT Gateway": "Cross-AZ traffic spike — review VPC endpoint usage for S3/Dynamo.",
    "EKS": "Minor node pool increase — within 5% tolerance.",
}


def scan(warning_pct: float = 0.15, critical_pct: float = 0.35) -> ScanResult:
    items = fetch_current_costs()
    findings: list[DriftFinding] = []

    for item in items:
        delta = item.current_usd - item.baseline_usd
        if item.baseline_usd <= 0:
            continue
        pct = delta / item.baseline_usd
        if pct < warning_pct:
            continue
        severity = Severity.CRITICAL if pct >= critical_pct else Severity.WARNING
        findings.append(
            DriftFinding(
                service=item.service,
                account=item.account,
                environment=item.environment,
                baseline_usd=item.baseline_usd,
                current_usd=item.current_usd,
                delta_usd=round(delta, 2),
                delta_pct=round(pct, 3),
                severity=severity,
                likely_cause=_CAUSES.get(item.service, "Review resource tags and usage in Cost Explorer."),
                recommended_action=_action(item, pct),
            )
        )

    findings.sort(key=lambda f: f.delta_usd, reverse=True)
    total_base = sum(i.baseline_usd for i in items)
    total_cur = sum(i.current_usd for i in items)

    return ScanResult(
        scan_id=str(uuid.uuid4())[:8],
        total_baseline_usd=round(total_base, 2),
        total_current_usd=round(total_cur, 2),
        total_delta_usd=round(total_cur - total_base, 2),
        findings=findings,
    )


def _action(item: CostLineItem, pct: float) -> str:
    if item.service == "NAT Gateway":
        return "Add VPC endpoints for S3; review NAT-heavy workloads."
    if item.service == "CloudWatch":
        return "Drop debug log level in prod; set 30-day retention on noisy log groups."
    if item.account == "staging" and pct > 0.5:
        return "Schedule staging shutdown nights/weekends; right-size instances."
    return f"Set AWS Budget alert at ${item.baseline_usd * 1.2:.0f}/mo for {item.service}."

"""Drift detection finds material cost increases."""
from app.detect.drift_engine import scan


def test_scan_finds_nat_gateway_drift():
    result = scan()
    services = {f.service for f in result.findings}
    assert "NAT Gateway" in services
    assert result.total_delta_usd > 0

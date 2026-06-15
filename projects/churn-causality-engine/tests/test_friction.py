"""Friction detection tests."""
from app.analyze.friction import detect_friction, load_config
from app.ingest.mock_provider import fetch_customer_profile


def test_at_risk_has_critical_friction():
    profile = fetch_customer_profile("cus_at_risk_01")
    config = load_config("config/signals.json")
    points = detect_friction(profile, config)
    assert any(p.severity == "critical" for p in points)


def test_healthy_low_friction():
    profile = fetch_customer_profile("cus_healthy_02")
    config = load_config("config/signals.json")
    points = detect_friction(profile, config)
    assert len(points) == 0 or all(p.severity == "info" for p in points)

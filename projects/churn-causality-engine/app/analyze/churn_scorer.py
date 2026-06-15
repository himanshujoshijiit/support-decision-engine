"""Score churn risk and extract behavioral signals."""
from __future__ import annotations

from app.models import BehavioralSignal, FrictionPoint, RiskLevel


def score_churn(profile: dict, friction: list[FrictionPoint], weights: dict) -> tuple[float, RiskLevel, list[BehavioralSignal]]:
    signals: list[BehavioralSignal] = []
    score = 0.0

    if profile.get("payment_failed"):
        w = weights.get("payment_failed", 0.3)
        score += w
        signals.append(BehavioralSignal(signal_id="payment_failed", label="Failed payment", value=True, weight=w))

    tickets = profile.get("support_tickets_30d", 0)
    if tickets >= 2:
        w = weights.get("support_tickets_30d", 0.15) * min(tickets / 5, 1.0)
        score += w
        signals.append(BehavioralSignal(signal_id="support_spike", label="Support ticket spike", value=tickets, weight=w))

    inactive = profile.get("last_active_days_ago", 0)
    if inactive >= 14:
        w = weights.get("login_decline", 0.1) * min(inactive / 30, 1.0)
        score += w
        signals.append(BehavioralSignal(signal_id="login_decline", label="Days since last active", value=inactive, weight=w))

    stalled = any(f.severity == "critical" for f in friction)
    if stalled:
        w = weights.get("onboarding_incomplete", 0.25)
        score += w
        signals.append(BehavioralSignal(signal_id="onboarding_stall", label="Onboarding stall", value=True, weight=w))

    completed_steps = len({e.name for e in profile["events"]})
    if completed_steps <= 3 and profile.get("tenure_days", 0) > 30:
        w = weights.get("feature_adoption_low", 0.2)
        score += w
        signals.append(BehavioralSignal(signal_id="low_adoption", label="Low feature adoption", value=completed_steps, weight=w))

    score = min(round(score, 2), 1.0)
    level = _to_level(score)
    return score, level, signals


def _to_level(score: float) -> RiskLevel:
    if score >= 0.75:
        return RiskLevel.CRITICAL
    if score >= 0.5:
        return RiskLevel.HIGH
    if score >= 0.25:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW

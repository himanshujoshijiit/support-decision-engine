"""Plain-English root cause narratives (heuristic; LLM optional later)."""
from __future__ import annotations

from app.models import BehavioralSignal, FrictionPoint, RootCause, RiskLevel


def explain_root_causes(
    customer_id: str,
    plan: str,
    mrr_usd: float,
    risk_level: RiskLevel,
    friction: list[FrictionPoint],
    signals: list[BehavioralSignal],
) -> list[RootCause]:
    causes: list[RootCause] = []

    for fp in friction:
        if fp.severity in ("critical", "warning"):
            causes.append(
                RootCause(
                    title=f"Friction at '{fp.step}'",
                    explanation=fp.detail,
                    confidence=0.85 if fp.severity == "critical" else 0.72,
                    recommended_action=_action_for_step(fp.step),
                )
            )

    for sig in signals:
        if sig.signal_id == "payment_failed":
            causes.append(
                RootCause(
                    title="Billing failure",
                    explanation=f"Customer on {plan} (${mrr_usd:.0f}/mo) has a failed payment — "
                    "strongest single predictor of involuntary churn.",
                    confidence=0.92,
                    recommended_action="Trigger dunning email + in-app banner; offer billing support.",
                )
            )
        elif sig.signal_id == "login_decline":
            causes.append(
                RootCause(
                    title="Product disengagement",
                    explanation=f"No meaningful activity in {sig.value} days after initial setup. "
                    "They may not have reached first value.",
                    confidence=0.78,
                    recommended_action="Send re-activation campaign highlighting the one feature they started but didn't finish.",
                )
            )

    if not causes and risk_level == RiskLevel.LOW:
        causes.append(
            RootCause(
                title="Healthy engagement",
                explanation="Journey completion and activity signals look normal for this cohort.",
                confidence=0.8,
                recommended_action="No intervention needed; monitor monthly.",
            )
        )

    return causes[:5]


def _action_for_step(step: str) -> str:
    actions = {
        "connect_integration": "Offer a 15-min onboarding call or in-app wizard for integration setup.",
        "first_value_event": "Trigger guided tour to the single action that delivers first value.",
        "invite_team": "Email champion with team invite template + ROI one-pager.",
        "upgrade": "Surface usage limits with upgrade CTA before they hit a wall.",
        "engagement": "Re-activation sequence: case study + feature highlight for their use case.",
        "support_load": "Route to CSM; review recent tickets for recurring product pain.",
    }
    return actions.get(step, "Review with product team; add to weekly churn review.")

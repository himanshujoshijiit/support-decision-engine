"""Churn analysis pipeline: ingest -> friction -> score -> explain."""
from __future__ import annotations

from app.analyze.churn_scorer import score_churn
from app.analyze.friction import detect_friction, load_config
from app.config import get_settings
from app.explain.root_cause import explain_root_causes
from app.ingest.mock_provider import fetch_customer_profile
from app.models import ChurnAnalysis


class ChurnPipeline:
    def __init__(self) -> None:
        settings = get_settings()
        self._config = load_config(settings.signals_path)

    def analyze(self, customer_id: str) -> ChurnAnalysis:
        profile = fetch_customer_profile(customer_id)
        friction = detect_friction(profile, self._config)
        score, level, signals = score_churn(profile, friction, self._config["churn_weights"])
        causes = explain_root_causes(
            customer_id,
            profile["plan"],
            profile["mrr_usd"],
            level,
            friction,
            signals,
        )
        return ChurnAnalysis(
            customer_id=customer_id,
            plan=profile["plan"],
            mrr_usd=profile["mrr_usd"],
            tenure_days=profile["tenure_days"],
            churn_risk_score=score,
            risk_level=level,
            friction_points=friction,
            behavioral_signals=signals,
            root_causes=causes,
        )


_pipeline: ChurnPipeline | None = None


def get_pipeline() -> ChurnPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = ChurnPipeline()
    return _pipeline

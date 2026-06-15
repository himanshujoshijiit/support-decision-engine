"""Detect journey friction from events + cohort benchmarks."""
from __future__ import annotations

import json
from pathlib import Path

from app.models import FrictionPoint


def load_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def detect_friction(profile: dict, config: dict) -> list[FrictionPoint]:
    points: list[FrictionPoint] = []
    completed = {e.name for e in profile["events"]}
    steps = config.get("journey_steps", [])
    warn = config["friction_thresholds"]["drop_off_warning"]
    crit = config["friction_thresholds"]["drop_off_critical"]

    # Where did THIS customer stall?
    for i, step in enumerate(steps):
        if step not in completed:
            prev = steps[i - 1] if i > 0 else "signup"
            rate = profile["cohort_drop_offs"].get(step, 0.25)
            severity = "critical" if rate >= crit else "warning" if rate >= warn else "info"
            points.append(
                FrictionPoint(
                    step=step,
                    drop_off_rate=rate,
                    severity=severity,
                    detail=f"Customer completed '{prev}' but never reached '{step}'. "
                    f"Cohort drop-off at this step: {rate:.0%}.",
                )
            )
            break

    if profile.get("last_active_days_ago", 0) >= 14:
        points.append(
            FrictionPoint(
                step="engagement",
                drop_off_rate=min(profile["last_active_days_ago"] / 30, 1.0),
                severity="warning",
                detail=f"No product activity in {profile['last_active_days_ago']} days.",
            )
        )

    if profile.get("support_tickets_30d", 0) >= 3:
        points.append(
            FrictionPoint(
                step="support_load",
                drop_off_rate=0.4,
                severity="warning",
                detail=f"{profile['support_tickets_30d']} support tickets in 30 days — friction signal.",
            )
        )

    return points

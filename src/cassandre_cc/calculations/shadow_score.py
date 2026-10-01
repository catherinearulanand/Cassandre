"""Phase 8 scaffold ONLY — spec §9/§17's "predictive ML research" phase.

This is explicitly NOT a trained model. Spec §9 requires: a defined target
and horizon agreed before feature collection, transparent baselines before
RF/XGBoost, time/group-split validation on real labelled historical data,
and model governance sign-off. None of that exists — there is no labelled
outcome data, synthetic or otherwise, because outcomes (default, breach
cured vs not) take real time to observe and this pilot has none.

What this module *does* provide: the feature-snapshot shape spec §9 asks
for ("use only information available at prediction time... a post-event
waiver or future audit result cannot become an earlier feature"), and one
transparent, deterministic, hand-written heuristic — not fit to any data —
so the shadow-mode plumbing (capture → score → never act on it
automatically) exists and can be swapped for a real baseline once real
data exists. The score is never used to gate, block, or auto-decide
anything; the API only ever returns it alongside this same disclaimer.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class ShadowScoreResult:
    score: int  # 0-100, higher = more attention indicated. NOT a probability.
    basis: str
    disclaimer: str = (
        "Heuristic baseline only — not a trained model, not validated against "
        "real outcomes, and not used to gate any decision (spec §9)."
    )


_DISCLAIMER_FIELDS = ("utilisation_ratio", "covenant_headroom_ratio")


def compute_shadow_score(
    utilisation_ratio: Optional[Decimal],
    covenant_headroom_ratio: Optional[Decimal],
    evidence_delay_flag: bool,
    open_cure_task_count: int,
) -> ShadowScoreResult:
    if utilisation_ratio is None or covenant_headroom_ratio is None:
        return ShadowScoreResult(
            score=0,
            basis="insufficient data: one or more inputs indeterminate for this period",
        )

    # Purely additive, hand-written weights — not fit to any dataset.
    points = 0
    reasons: list[str] = []

    if utilisation_ratio >= Decimal("0.95"):
        points += 35
        reasons.append("utilisation >= 95% of usable cap")
    elif utilisation_ratio >= Decimal("0.85"):
        points += 15
        reasons.append("utilisation >= 85% of usable cap")

    if covenant_headroom_ratio < Decimal("0"):
        points += 35
        reasons.append("covenant headroom negative")
    elif covenant_headroom_ratio < Decimal("0.05"):
        points += 15
        reasons.append("covenant headroom below 5%")

    if evidence_delay_flag:
        points += 15
        reasons.append("required evidence overdue")

    points += min(open_cure_task_count, 3) * 5
    if open_cure_task_count:
        reasons.append(f"{open_cure_task_count} open cure task(s)")

    return ShadowScoreResult(score=min(points, 100), basis="; ".join(reasons) or "no attention signals")

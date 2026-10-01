"""Deterministic covenant test engine — spec §18/§8's finding states.

The specific threshold and near-threshold band used anywhere this module is
called are a **provisional placeholder** (mirrors the spec's own
`DEC-RSK-01`-style disclosure): this prototype does not know any bank's
actual approved covenant definition. A real deployment must source
`CovenantTest.threshold` from an approved `EligibilityRuleSet`/sanction
condition, never from a default in this file (spec §8: "Definitions
override generic ratios").
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Optional

from cassandre_cc.domain.states import FindingState


class Comparator(str, Enum):
    AT_LEAST = "at_least"  # value must be >= threshold to be compliant
    AT_MOST = "at_most"  # value must be <= threshold to be compliant


@dataclass(frozen=True)
class CovenantTest:
    test_id: str
    description: str
    comparator: Comparator
    threshold: Decimal
    near_threshold_band: Decimal = Decimal("0.05")  # 5% of threshold, provisional


def evaluate_covenant_with_waiver(
    value: Optional[Decimal], test: CovenantTest, has_active_waiver: bool
) -> FindingState:
    """Spec acceptance scenario #8: "Limited waiver: only named obligation/
    test period is waived; new cure is tracked." The caller resolves
    `has_active_waiver` by checking the store for a waiver scoped to this
    exact (facility, test_id, period) — this function stays a pure
    function of its three inputs, with no store access, so the waiver
    scoping logic lives in exactly one place (`MemoryStore.active_waiver`)
    rather than being re-derived here."""

    base_state = evaluate_covenant(value, test)
    if has_active_waiver and base_state in (
        FindingState.POTENTIAL_BREACH,
        FindingState.CONFIRMED_BREACH,
    ):
        return FindingState.WAIVED_FOR_SCOPE
    return base_state


def evaluate_covenant(value: Optional[Decimal], test: CovenantTest) -> FindingState:
    if value is None:
        return FindingState.INDETERMINATE

    band_width = abs(test.threshold) * test.near_threshold_band

    if test.comparator is Comparator.AT_LEAST:
        passes = value >= test.threshold
        distance = value - test.threshold
    else:
        passes = value <= test.threshold
        distance = test.threshold - value

    if abs(distance) <= band_width:
        return FindingState.NEAR_THRESHOLD
    return FindingState.COMPLIANT if passes else FindingState.POTENTIAL_BREACH

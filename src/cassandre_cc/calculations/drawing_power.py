"""Deterministic drawing-power calculation — spec §8's worked fixture,
implemented exactly, plus the "missing input -> indeterminate, never zero"
rule from spec §8 ("No universal DP formula... Missing inputs yield
indeterminate, never assumed zero") and acceptance scenario #4.

This is explicitly NOT a universal bank formula (spec §8, §17 Phase 4 exit
criteria: "approved golden calculations match"). The margins, exclusions,
and ageing cutoff are per-facility `EligibilityRuleSet` values that must
come from an approved, maker-checker-reviewed rule version — this module
only does the arithmetic once those inputs are supplied.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from cassandre_cc.domain.states import DPResultState
from cassandre_cc.money import Money, Unit


@dataclass(frozen=True)
class DPInputs:
    reported_stock: Optional[Money]
    stock_exclusions: Optional[Money]
    reported_receivables: Optional[Money]
    receivable_exclusions: Optional[Money]
    stock_margin: Optional[Decimal]  # e.g. Decimal("0.25")
    receivable_margin: Optional[Decimal]  # e.g. Decimal("0.30")
    sanctioned_cap: Optional[Money]
    outstanding: Optional[Money]


@dataclass(frozen=True)
class DPResult:
    state: DPResultState
    missing_fields: tuple[str, ...] = ()
    eligible_stock: Optional[Money] = None
    eligible_receivables: Optional[Money] = None
    proposed_dp: Optional[Money] = None
    usable_cap: Optional[Money] = None
    headroom: Optional[Money] = None


_REQUIRED_FIELDS = (
    "reported_stock",
    "stock_exclusions",
    "reported_receivables",
    "receivable_exclusions",
    "stock_margin",
    "receivable_margin",
    "sanctioned_cap",
    "outstanding",
)


def calculate_drawing_power(inputs: DPInputs) -> DPResult:
    missing = tuple(f for f in _REQUIRED_FIELDS if getattr(inputs, f) is None)
    if missing:
        return DPResult(state=DPResultState.INDETERMINATE, missing_fields=missing)

    # Bad evidence must never become an apparently valid negative borrowing base.
    money_fields = [f for f in _REQUIRED_FIELDS if f not in ("stock_margin", "receivable_margin")]
    for field in money_fields:
        value = getattr(inputs, field)
        if not isinstance(value, Money):
            raise TypeError(f"{field} must be Money")
        inputs.reported_stock._check_compatible(value)
        if value.amount < 0:
            raise ValueError(f"{field} cannot be negative; normalise ledger signs explicitly")
    for field in ("stock_margin", "receivable_margin"):
        value = getattr(inputs, field)
        if not isinstance(value, Decimal):
            raise TypeError(f"{field} must be Decimal")
        if not value.is_finite() or not Decimal("0") <= value <= Decimal("1"):
            raise ValueError(f"{field} must be finite and between zero and one")
    if inputs.stock_exclusions > inputs.reported_stock:
        raise ValueError("stock exclusions exceed reported stock; reconcile evidence")
    if inputs.receivable_exclusions > inputs.reported_receivables:
        raise ValueError("receivable exclusions exceed reported receivables; reconcile evidence")

    eligible_stock = inputs.reported_stock - inputs.stock_exclusions
    eligible_receivables = inputs.reported_receivables - inputs.receivable_exclusions

    stock_component = eligible_stock * (Decimal("1") - inputs.stock_margin)
    receivable_component = eligible_receivables * (Decimal("1") - inputs.receivable_margin)
    proposed_dp = stock_component + receivable_component

    usable_cap = proposed_dp.min(inputs.sanctioned_cap)
    headroom = usable_cap - inputs.outstanding

    return DPResult(
        state=DPResultState.CALCULATED,
        eligible_stock=eligible_stock,
        eligible_receivables=eligible_receivables,
        proposed_dp=proposed_dp,
        usable_cap=usable_cap,
        headroom=headroom,
    )


def _parse_money(value: Optional[str]) -> Optional[Money]:
    return Money(Decimal(value), Unit.CRORE) if value is not None else None


def _parse_decimal(value: Optional[str]) -> Optional[Decimal]:
    return Decimal(value) if value is not None else None


def inputs_from_records(financials, rule_set, sanctioned_limit_crore: str) -> DPInputs:
    """Assemble DPInputs from a facility's stored financials + its approved
    rule set. A field missing on either record propagates through as
    `None`, which `calculate_drawing_power` turns into INDETERMINATE
    rather than a silent zero."""

    return DPInputs(
        reported_stock=_parse_money(financials.reported_stock_crore),
        stock_exclusions=_parse_money(financials.stock_exclusions_crore),
        reported_receivables=_parse_money(financials.reported_receivables_crore),
        receivable_exclusions=_parse_money(financials.receivable_exclusions_crore),
        stock_margin=_parse_decimal(rule_set.stock_margin) if rule_set else None,
        receivable_margin=_parse_decimal(rule_set.receivable_margin) if rule_set else None,
        sanctioned_cap=_parse_money(sanctioned_limit_crore),
        outstanding=_parse_money(financials.outstanding_crore),
    )


def worked_fixture() -> DPInputs:
    """The exact synthetic worked example from spec §8 — used as the golden
    test case and as this prototype's seed data. Not a template for real
    bank margins/exclusions (spec §8: "This is not a universal bank formula
    or authorisation to draw")."""

    crore = Unit.CRORE
    return DPInputs(
        reported_stock=Money(Decimal("4.00"), crore),
        stock_exclusions=Money(Decimal("0.50"), crore),
        reported_receivables=Money(Decimal("3.00"), crore),
        receivable_exclusions=Money(Decimal("0.80"), crore),
        stock_margin=Decimal("0.25"),
        receivable_margin=Decimal("0.30"),
        sanctioned_cap=Money(Decimal("5.00"), crore),
        outstanding=Money(Decimal("3.60"), crore),
    )

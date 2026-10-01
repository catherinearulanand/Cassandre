"""Golden test: reproduces the spec §8 worked fixture exactly, plus
acceptance scenario #4 (missing input -> indeterminate, never zero) and
acceptance scenario #6 (creditors already excluded from stock: no second
deduction — verified by the single-subtraction exclusion path)."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

import pytest

from cassandre_cc.calculations.drawing_power import (
    DPInputs,
    calculate_drawing_power,
    worked_fixture,
)
from cassandre_cc.domain.states import DPResultState
from cassandre_cc.money import Money, Unit, UnitMismatchError


def test_worked_fixture_matches_spec_exactly():
    result = calculate_drawing_power(worked_fixture())

    assert result.state is DPResultState.CALCULATED
    assert result.eligible_stock.amount == Decimal("3.50")
    assert result.eligible_receivables.amount == Decimal("2.20")
    assert result.proposed_dp.amount == Decimal("4.165")
    assert result.usable_cap.amount == Decimal("4.165")  # below the 5.00 sanctioned cap
    assert result.headroom.amount == Decimal("0.565")


def test_usable_cap_is_bounded_by_sanctioned_limit():
    inputs = replace(worked_fixture(), sanctioned_cap=Money(Decimal("4.00"), Unit.CRORE))
    result = calculate_drawing_power(inputs)
    assert result.usable_cap.amount == Decimal("4.00")  # capped, not 4.165
    assert result.headroom.amount == Decimal("0.40")


@pytest.mark.parametrize(
    "field",
    [
        "reported_stock",
        "stock_exclusions",
        "reported_receivables",
        "receivable_exclusions",
        "stock_margin",
        "receivable_margin",
        "sanctioned_cap",
        "outstanding",
    ],
)
def test_missing_any_required_field_yields_indeterminate_not_zero(field):
    inputs = replace(worked_fixture(), **{field: None})
    result = calculate_drawing_power(inputs)

    assert result.state is DPResultState.INDETERMINATE
    assert field in result.missing_fields
    assert result.proposed_dp is None  # never silently zero


def test_rupee_and_crore_cannot_be_combined_without_explicit_conversion():
    stock_in_crore = Money(Decimal("4.00"), Unit.CRORE)
    stock_in_rupees = Money(Decimal("40000"), Unit.RUPEE)
    with pytest.raises(UnitMismatchError):
        stock_in_crore - stock_in_rupees


def test_explicit_unit_conversion_then_combines_correctly():
    one_crore = Money(Decimal("1"), Unit.CRORE)
    converted = one_crore.as_unit(Unit.LAKH)
    assert converted.amount == Decimal("100")
    assert (converted - Money(Decimal("40"), Unit.LAKH)).amount == Decimal("60")

@pytest.mark.parametrize("amount", ["NaN", "Infinity", "-Infinity"])
def test_nonfinite_money_rejected(amount):
    with pytest.raises(ValueError, match="finite"):
        Money(Decimal(amount))


@pytest.mark.parametrize("field", ["stock_margin", "receivable_margin"])
@pytest.mark.parametrize("value", ["-0.01", "1.01", "NaN", "Infinity"])
def test_invalid_margins_block_calculation(field, value):
    with pytest.raises(ValueError):
        calculate_drawing_power(replace(worked_fixture(), **{field: Decimal(value)}))


@pytest.mark.parametrize("field", ["reported_stock", "stock_exclusions", "reported_receivables", "receivable_exclusions", "sanctioned_cap", "outstanding"])
def test_negative_evidence_blocks_calculation(field):
    with pytest.raises(ValueError, match="negative"):
        calculate_drawing_power(replace(worked_fixture(), **{field: Money(Decimal("-1"))}))


def test_exclusions_above_assets_block_calculation():
    with pytest.raises(ValueError, match="exclusions exceed"):
        calculate_drawing_power(replace(worked_fixture(), stock_exclusions=Money(Decimal("4.01"))))


def test_overdrawn_headroom_remains_negative():
    result = calculate_drawing_power(replace(worked_fixture(), outstanding=Money(Decimal("5"))))
    assert result.headroom.amount == Decimal("-0.835")


def test_mixed_units_across_asset_classes_rejected():
    with pytest.raises(UnitMismatchError):
        calculate_drawing_power(replace(worked_fixture(), outstanding=Money(Decimal("360"), Unit.LAKH)))

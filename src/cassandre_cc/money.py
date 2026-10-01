"""Decimal-only monetary values with an explicit unit.

Spec mandatory constraint #4: "Arithmetic, date logic, eligibility and
monitoring rules use versioned deterministic code." No floats anywhere in
this module — Decimal throughout. Acceptance scenario #3 ("Rupees vs lakh
mismatch: validation stops computation") is enforced by `Money.__add__` and
`Money.__sub__` refusing to combine values of different units rather than
silently converting them.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class Unit(str, Enum):
    RUPEE = "rupee"
    LAKH = "lakh"
    CRORE = "crore"


_TO_RUPEES = {
    Unit.RUPEE: Decimal("1"),
    Unit.LAKH: Decimal("100000"),
    Unit.CRORE: Decimal("10000000"),
}


class UnitMismatchError(ValueError):
    """Raised when two Money values of different units are combined without
    an explicit conversion. Never silently resolved — the caller must
    convert first (spec acceptance scenario #3)."""


@dataclass(frozen=True)
class Money:
    amount: Decimal
    unit: Unit = Unit.CRORE
    currency: str = "INR"

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            raise TypeError(f"Money.amount must be Decimal, got {type(self.amount).__name__}")

        if not self.amount.is_finite():
            raise ValueError("Money.amount must be finite")
        if not isinstance(self.unit, Unit):
            raise TypeError("Money.unit must be an explicit Unit")
        if not isinstance(self.currency, str) or not self.currency.strip():
            raise ValueError("Money.currency must be specified")

    def to_rupees(self) -> Decimal:
        return self.amount * _TO_RUPEES[self.unit]

    def as_unit(self, unit: Unit) -> "Money":
        rupees = self.to_rupees()
        return Money(rupees / _TO_RUPEES[unit], unit=unit, currency=self.currency)

    def _check_compatible(self, other: "Money") -> None:
        if self.currency != other.currency:
            raise UnitMismatchError(f"currency mismatch: {self.currency} vs {other.currency}")
        if self.unit != other.unit:
            raise UnitMismatchError(
                f"unit mismatch: {self.unit.value} vs {other.unit.value} — "
                "convert explicitly with .as_unit() before combining"
            )

    def __add__(self, other: "Money") -> "Money":
        self._check_compatible(other)
        return Money(self.amount + other.amount, unit=self.unit, currency=self.currency)

    def __sub__(self, other: "Money") -> "Money":
        self._check_compatible(other)
        return Money(self.amount - other.amount, unit=self.unit, currency=self.currency)

    def __mul__(self, factor: Decimal) -> "Money":
        if not isinstance(factor, Decimal):
            raise TypeError(f"Money can only be multiplied by Decimal, got {type(factor).__name__}")
        return Money(self.amount * factor, unit=self.unit, currency=self.currency)

    def __lt__(self, other: "Money") -> bool:
        self._check_compatible(other)
        return self.amount < other.amount

    def __le__(self, other: "Money") -> bool:
        self._check_compatible(other)
        return self.amount <= other.amount

    def min(self, other: "Money") -> "Money":
        self._check_compatible(other)
        return self if self.amount <= other.amount else other

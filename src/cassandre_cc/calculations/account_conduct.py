"""Read-only RBI commercial-bank CC conduct checks; never classification writes."""
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Literal, Sequence

PROFILE = "rbi-commercial-bank-cc-2026-07-01"
SOURCE = "https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=13146"


@dataclass(frozen=True)
class DailyConduct:
    business_date: date
    outstanding_rupees: Decimal
    credits_rupees: Decimal
    interest_debited_rupees: Decimal
    sanctioned_limit_rupees: Decimal
    active_drawing_power_rupees: Decimal
    source_reference: str


@dataclass(frozen=True)
class ConductSignal:
    code: str
    status: Literal["potential_trigger", "not_triggered", "indeterminate"]
    explanation: str


@dataclass(frozen=True)
class ConductResult:
    profile: str
    as_of: date
    window_start: date
    signals: tuple[ConductSignal, ...]
    issues: tuple[str, ...]
    total_credits_rupees: Decimal | None = None
    total_interest_rupees: Decimal | None = None
    consecutive_excess_days: int | None = None
    source_references: tuple[str, ...] = ()
    advisory_only: bool = True


_CODES = ("continuous_excess_90_days", "no_credits_90_days", "credits_below_interest_90_days")


def evaluate_account_conduct(
    records: Sequence[DailyConduct], *, as_of: date,
    profile: str = PROFILE, complete_day_end_feed: bool = False,
) -> ConductResult:
    """Amounts must be INR rupees; all calendar days include bank-certified carry forwards.

    Feed attestation must come from the approved integration, not a borrower upload.
    A potential trigger requires bank review; no output asserts NPA/SMA status.
    """
    start = as_of - timedelta(days=89)
    issues: list[str] = []
    if profile != PROFILE:
        issues.append("unsupported_profile: commercial-bank CC only")
    if not complete_day_end_feed:
        issues.append("day_end_feed_not_attested_complete")
    by_day: dict[date, DailyConduct] = {}
    for row in records:
        if type(row.business_date) is not date:
            issues.append("invalid_business_date")
            continue
        if row.business_date > as_of:
            issues.append("future_business_date")
        if row.business_date in by_day:
            issues.append("duplicate_business_date")
        by_day[row.business_date] = row
        amounts = (row.outstanding_rupees, row.credits_rupees, row.interest_debited_rupees,
                   row.sanctioned_limit_rupees, row.active_drawing_power_rupees)
        if any(not isinstance(v, Decimal) or not v.is_finite() for v in amounts):
            issues.append("amounts_must_be_finite_decimal_INR_rupees")
        elif any(v < 0 for v in amounts[1:]):
            issues.append("negative_credit_interest_or_limit")
        if not row.source_reference or not row.source_reference.strip():
            issues.append("missing_source_reference")
    expected = [start + timedelta(days=i) for i in range(90)]
    missing = [day.isoformat() for day in expected if day not in by_day]
    if missing:
        issues.append("missing_calendar_days: " + ",".join(missing))
    if issues:
        return ConductResult(profile, as_of, start,
                             tuple(ConductSignal(c, "indeterminate", "Incomplete or invalid evidence")
                                   for c in _CODES), tuple(dict.fromkeys(issues)))
    window = [by_day[day] for day in expected]
    credits = sum((r.credits_rupees for r in window), Decimal(0))
    interest = sum((r.interest_debited_rupees for r in window), Decimal(0))
    def cap(row: DailyConduct) -> Decimal:
        return min(row.sanctioned_limit_rupees, row.active_drawing_power_rupees)
    streak = 0
    for row in reversed(window):
        if row.outstanding_rupees <= cap(row):
            break
        streak += 1
    current = window[-1]
    below = current.outstanding_rupees < cap(current)
    equal = current.outstanding_rupees == cap(current)
    def credit_signal(code: str, triggered: bool, explanation: str) -> ConductSignal:
        if equal:
            return ConductSignal(code, "indeterminate", "At-limit boundary requires bank-approved interpretation")
        return ConductSignal(code, "potential_trigger" if below and triggered else "not_triggered", explanation)
    signals = (
        ConductSignal(_CODES[0], "potential_trigger" if streak == 90 else "not_triggered",
                      f"{streak} consecutive observed day-end excess days (capped at 90)"),
        credit_signal(_CODES[1], credits == 0, f"90-day credits INR {credits}; current balance below cap: {below}"),
        credit_signal(_CODES[2], credits < interest,
                      f"Inclusive 90-day credits INR {credits}; interest debited INR {interest}; below cap: {below}"),
    )
    return ConductResult(profile, as_of, start, signals, (), credits, interest, streak,
                         tuple(dict.fromkeys(r.source_reference for r in window)))

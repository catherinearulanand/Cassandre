"""Minimum entities for the Phase 1 vertical slice (spec §13's entity list,
narrowed to what this slice's workflow actually touches). Every business
object carries `institution_id` (spec §11.3 — "validate institution... at
server level"); this prototype enforces that scope in `store/memory_store.py`
rather than at the database layer, since there is no database yet.

Identifiers use the `SIM-` prefix throughout — no real borrower, account, or
facility ID is ever synthesised to look authentic (spec §3, mandatory
constraint #1).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional

from cassandre_cc.domain.states import EvidenceState, FacilityState, ObligationState


@dataclass(frozen=True)
class Institution:
    institution_id: str
    name: str


@dataclass(frozen=True)
class Borrower:
    borrower_id: str
    institution_id: str
    legal_name: str
    external_borrower_ref: str  # preserves the lender's own borrower ID (mandatory constraint #2)


@dataclass(frozen=True)
class Facility:
    facility_id: str
    institution_id: str
    borrower_id: str
    external_facility_ref: str  # preserves the lender's own facility ID
    sanctioned_limit_crore: str  # Decimal serialised as str at the boundary; parsed by callers
    state: FacilityState = FacilityState.ACTIVE


@dataclass(frozen=True)
class DocumentRef:
    document_id: str
    institution_id: str
    facility_id: str
    document_type: str
    evidence_period: str  # e.g. "2026-08" — the reporting month this document is evidence for
    received_at: datetime
    source_hash: str  # content checksum; stands in for the spec's "original bytes" integrity check
    supersedes_document_id: Optional[str] = None  # non-None => this row is itself a replacement
    is_original: bool = True  # False iff supersedes_document_id is set; fixed at creation, never mutated


@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str
    facility_id: str
    document_id: Optional[str]
    field_name: str
    period: str
    state: EvidenceState
    reviewer: Optional[str] = None


@dataclass(frozen=True)
class EligibilityRuleSet:
    rule_set_id: str
    facility_id: str
    version: int
    state: ObligationState
    stock_margin: str  # Decimal as str, e.g. "0.25"
    receivable_margin: str  # e.g. "0.30"
    debtor_ageing_cutoff_days: int
    submitted_by: str
    approved_by: Optional[str] = None
    effective_from: Optional[date] = None


@dataclass(frozen=True)
class FacilityFinancials:
    """One period's reported stock/receivables figures for a facility — the
    raw inputs a DP calculation run is assembled from. Any field left
    `None` means that figure has not been received/verified for this
    period, which is what drives the "indeterminate, never zero" rule
    (spec §8, acceptance scenario #4)."""

    facility_id: str
    period: str
    reported_stock_crore: Optional[str] = None
    stock_exclusions_crore: Optional[str] = None
    reported_receivables_crore: Optional[str] = None
    receivable_exclusions_crore: Optional[str] = None
    outstanding_crore: Optional[str] = None


@dataclass(frozen=True)
class ImportBatch:
    """A read-only fixture import (spec §6 / §17 Phase 2). Keyed by
    `content_hash` in the store so re-submitting byte-identical content is a
    no-op — acceptance scenario #1 ("Import one facility twice: no
    duplicated facility/evidence/case")."""

    batch_id: str
    institution_id: str
    facility_id: str
    period: str
    content_hash: str
    record_count: int
    imported_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class Waiver:
    """Spec §21 / acceptance scenario #8: "Limited waiver: only named
    obligation/test period is waived; new cure is tracked." A waiver is
    scoped to exactly one (facility, test_id, period) triple — it never
    applies to a different period's evaluation of the same test, even for
    the same facility."""

    waiver_id: str
    facility_id: str
    test_id: str
    scoped_period: str
    reason: str
    submitted_by: str
    approved_by: Optional[str] = None
    state: ObligationState = ObligationState.DRAFT
    expires_after_period: Optional[str] = None  # inclusive; None = this period only


@dataclass(frozen=True)
class CureTask:
    cure_id: str
    facility_id: str
    test_id: str
    period: str
    opened_at: datetime
    status: str = "open"  # "open" | "closed"
    closed_at: Optional[datetime] = None


@dataclass(frozen=True)
class RenewalRecord:
    renewal_id: str
    facility_id: str
    review_cycle_period: str
    decision: str = "pending"  # "pending" | "renewed" | "declined"
    decided_by: Optional[str] = None
    decided_at: Optional[datetime] = None
    notes: str = ""


@dataclass(frozen=True)
class ClosureChecklist:
    """Spec §23 / acceptance scenario #15: "Zero balance with linked
    commitment/security: closure release remains pending." A facility may
    not transition to CLOSED unless every item here is True — enforced in
    the API layer, not just hidden in the UI."""

    facility_id: str
    dues_reconciled: bool = False
    security_released: bool = False
    linked_exposures_clear: bool = False
    originals_returned: bool = False


@dataclass(frozen=True)
class FeatureSnapshot:
    """Spec §9 / Phase 8 scaffold only — NOT a trained model. Captures only
    values available at prediction time (no post-event leakage), so that
    *if* a real labelled corpus and model-governance owner exist later, a
    baseline can be built on top of exactly this shape. No RF/XGBoost model
    is trained or claimed here (spec §9: "No synthetic pilot proves
    predictive credit accuracy")."""

    snapshot_id: str
    facility_id: str
    period: str
    utilisation_ratio: Optional[str]  # outstanding / usable_cap, as Decimal str
    covenant_headroom_ratio: Optional[str]
    evidence_delay_flag: bool
    open_cure_task_count: int
    captured_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    institution_id: str
    facility_id: Optional[str]
    actor: str
    action: str
    detail: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class CalculationRun:
    """Immutable replay record: exact inputs, selected terms and derived output.

    JSON values are canonical strings so later in-memory record replacements
    cannot alter this run. A local checksum is not an independent audit anchor.
    """
    run_id: str
    institution_id: str
    facility_id: str
    period: Optional[str]
    actor: str
    inputs_json: str
    rule_json: str
    result_json: str
    source_batch_ids: tuple[str, ...]
    payload_sha256: str
    engine_version: str = "cc-deterministic-0.3"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

"""In-memory synthetic store, now with an optional JSON snapshot persisted
to disk (see `store/persistence.py`) so state survives a process restart.

Flagged assumption (see docs/ASSUMPTIONS.md item 1): this still stands in
for the Postgres-backed, institution-scoped persistence layer spec §13
calls for — no migrations, no concurrent-writer safety, no query indexes.
It still enforces the one non-negotiable rule from spec §11.3 ("validate
institution... at server level; user-supplied institution IDs are never
trusted") by raising on any cross-institution access, since that boundary
must exist from day one even in a throwaway store.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from cassandre_cc.domain.entities import (
    AuditEvent,
    Borrower,
    ClosureChecklist,
    CalculationRun,
    CureTask,
    DocumentRef,
    EligibilityRuleSet,
    EvidenceItem,
    Facility,
    FacilityFinancials,
    FeatureSnapshot,
    ImportBatch,
    Institution,
    RenewalRecord,
    Waiver,
)
from cassandre_cc.domain.states import ObligationState
from cassandre_cc.workflow.maker_checker import ApprovalCase


class CrossInstitutionAccessError(PermissionError):
    """Raised when a caller's institution_id does not match the record's."""


class DuplicateImportError(Exception):
    """Not actually an error condition for the caller — raised internally
    to signal "this exact content was already imported" so the API layer
    can return the existing batch instead of creating a new one."""


def new_id(prefix: str) -> str:
    return f"SIM-{prefix}-{uuid.uuid4().hex[:10].upper()}"


def _financials_key(facility_id: str, period: str) -> str:
    return f"{facility_id}:{period}"


@dataclass
class MemoryStore:
    institutions: dict[str, Institution] = field(default_factory=dict)
    borrowers: dict[str, Borrower] = field(default_factory=dict)
    facilities: dict[str, Facility] = field(default_factory=dict)
    documents: dict[str, DocumentRef] = field(default_factory=dict)
    evidence_items: dict[str, EvidenceItem] = field(default_factory=dict)
    rule_sets: dict[str, EligibilityRuleSet] = field(default_factory=dict)  # keyed by rule_set_id
    financials: dict[str, FacilityFinancials] = field(default_factory=dict)  # keyed by facility_id:period
    financials_history: dict[str, FacilityFinancials] = field(default_factory=dict)  # immutable import revisions
    approval_cases: dict[str, ApprovalCase] = field(default_factory=dict)
    import_batches: dict[str, ImportBatch] = field(default_factory=dict)  # keyed by content_hash
    waivers: dict[str, Waiver] = field(default_factory=dict)
    cure_tasks: dict[str, CureTask] = field(default_factory=dict)
    renewals: dict[str, RenewalRecord] = field(default_factory=dict)
    closures: dict[str, ClosureChecklist] = field(default_factory=dict)  # keyed by facility_id
    feature_snapshots: dict[str, FeatureSnapshot] = field(default_factory=dict)
    calculation_runs: dict[str, CalculationRun] = field(default_factory=dict)
    audit_events: list[AuditEvent] = field(default_factory=list)

    # ---- facilities -----------------------------------------------------

    def get_facility(self, facility_id: str, institution_id: str) -> Facility:
        facility = self.facilities.get(facility_id)
        if facility is None:
            raise KeyError(facility_id)
        if facility.institution_id != institution_id:
            raise CrossInstitutionAccessError(
                f"facility {facility_id} does not belong to institution {institution_id}"
            )
        return facility

    def evidence_for_facility(self, facility_id: str) -> list[EvidenceItem]:
        return [e for e in self.evidence_items.values() if e.facility_id == facility_id]

    def documents_for_facility(self, facility_id: str) -> list[DocumentRef]:
        return [d for d in self.documents.values() if d.facility_id == facility_id]

    # ---- financials / periods -------------------------------------------

    def set_financials(self, financials: FacilityFinancials) -> None:
        self.financials[_financials_key(financials.facility_id, financials.period)] = financials

    def get_financials(self, facility_id: str, period: str) -> Optional[FacilityFinancials]:
        return self.financials.get(_financials_key(facility_id, period))

    def latest_period_for_facility(self, facility_id: str) -> Optional[str]:
        periods = [f.period for f in self.financials.values() if f.facility_id == facility_id]
        return max(periods) if periods else None

    # ---- rule versions ----------------------------------------------------

    def rule_versions_for_facility(self, facility_id: str) -> list[EligibilityRuleSet]:
        versions = [r for r in self.rule_sets.values() if r.facility_id == facility_id]
        return sorted(versions, key=lambda r: r.version)

    def effective_rule_on_date(self, facility_id: str, business_date) -> Optional[EligibilityRuleSet]:
        """Select approved terms on an exact business date; reject ambiguous ties.

        Superseded versions remain eligible for historical replay. Retirement
        cannot erase historical approval, so approved retired terms remain
        historical candidates until a replacement takes effect.
        """
        candidates = [
            r for r in self.rule_versions_for_facility(facility_id)
            if r.approved_by is not None
            and r.state in (ObligationState.ACTIVE, ObligationState.SUPERSEDED,
                            ObligationState.RETIRED)
            and r.effective_from is not None
            and r.effective_from <= business_date
        ]
        if not candidates:
            return None
        latest = max(r.effective_from for r in candidates)
        winners = [r for r in candidates if r.effective_from == latest]
        return winners[0] if len(winners) == 1 else None

    def effective_rule_version(self, facility_id: str, period: str) -> Optional[EligibilityRuleSet]:
        """Monthly inputs cannot resolve an intra-month amendment.

        Without an explicit calculation business date and agreed period basis,
        return unknown instead of applying a new mid-month rule retrospectively
        to the whole month. First-day cutovers retain the existing monthly path.
        """
        from datetime import date
        import re

        if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", period):
            return None
        start = date.fromisoformat(period + "-01")
        if any(
            r.approved_by is not None and r.effective_from is not None
            and r.effective_from.isoformat()[:7] == period
            and r.effective_from.day != 1
            for r in self.rule_versions_for_facility(facility_id)
        ):
            return None
        return self.effective_rule_on_date(facility_id, start)

    # ---- imports (Phase 2) ------------------------------------------------

    def record_import(
        self,
        institution_id: str,
        facility_id: str,
        period: str,
        content_hash: str,
        record_count: int,
    ) -> tuple[ImportBatch, bool]:
        """Returns (batch, was_new). Re-importing identical content (same
        hash) returns the original batch with was_new=False — acceptance
        scenario #1: "Import one facility twice: no duplicated facility/
        evidence/case." """
        existing = self.import_batches.get(content_hash)
        if existing is not None:
            return existing, False

        batch = ImportBatch(
            batch_id=new_id("IMP"),
            institution_id=institution_id,
            facility_id=facility_id,
            period=period,
            content_hash=content_hash,
            record_count=record_count,
        )
        self.import_batches[content_hash] = batch
        return batch, True

    # ---- waivers / cure tasks (Phase 5) ------------------------------------

    def active_waiver(self, facility_id: str, test_id: str, period: str) -> Optional[Waiver]:
        for w in self.waivers.values():
            if (
                w.facility_id == facility_id
                and w.test_id == test_id
                and w.state is ObligationState.ACTIVE
                and w.scoped_period <= period <= (w.expires_after_period or w.scoped_period)
            ):
                return w
        return None

    def open_cure_task(self, facility_id: str, test_id: str, period: str) -> CureTask:
        """Idempotent: returns the existing open cure task for this exact
        (facility, test, period) if one is already open, otherwise opens a
        new one."""
        for task in self.cure_tasks.values():
            if (
                task.facility_id == facility_id
                and task.test_id == test_id
                and task.period == period
                and task.status == "open"
            ):
                return task
        task = CureTask(
            cure_id=new_id("CURE"),
            facility_id=facility_id,
            test_id=test_id,
            period=period,
            opened_at=datetime.now(timezone.utc),
        )
        self.cure_tasks[task.cure_id] = task
        return task

    def cure_tasks_for_facility(self, facility_id: str) -> list[CureTask]:
        return [c for c in self.cure_tasks.values() if c.facility_id == facility_id]

    # ---- audit --------------------------------------------------------------

    def record_event(
        self,
        institution_id: str,
        actor: str,
        action: str,
        detail: str,
        facility_id: str | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            event_id=new_id("EVT"),
            institution_id=institution_id,
            facility_id=facility_id,
            actor=actor,
            action=action,
            detail=detail,
            occurred_at=datetime.now(timezone.utc),
        )
        self.audit_events.append(event)
        return event

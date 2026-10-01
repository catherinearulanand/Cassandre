"""Synthetic seed data — the only data this prototype ever shows. All IDs
use the `SIM-` namespace (spec §3, mandatory constraint #1: "No real
institution, agreement, or price ever enters the system").

Seeds two facilities:
  - SIM-FAC-A001: complete evidence, two periods, and a mid-period rule
    amendment — reproduces the spec §8 worked fixture for 2026-07 (under
    the original v1 margins) and demonstrates acceptance scenario #7 for
    2026-08 (the v2 amendment applies going forward, v1 stays correct for
    the earlier period). Also carries one waived covenant finding scoped to
    exactly one period (acceptance scenario #8) and a renewal record.
  - SIM-FAC-B002: missing this period's receivables figure, to demonstrate
    acceptance scenario #4 (indeterminate DP) live in the UI.
"""

from __future__ import annotations

from datetime import date

from cassandre_cc.domain.entities import (
    Borrower,
    ClosureChecklist,
    EligibilityRuleSet,
    EvidenceItem,
    Facility,
    FacilityFinancials,
    Institution,
    RenewalRecord,
    Waiver,
)
from cassandre_cc.domain.states import EvidenceState, FacilityState, ObligationState
from cassandre_cc.store.memory_store import MemoryStore
from cassandre_cc.workflow.maker_checker import (
    ApprovalCase,
    approve_rule_version,
    approve_waiver,
    submit_for_review,
    submit_rule_version,
    submit_waiver,
    supersede_rule_version,
)

INSTITUTION_ID = "SIM-BANK-001"


def seed(store: MemoryStore) -> MemoryStore:
    store.institutions[INSTITUTION_ID] = Institution(INSTITUTION_ID, "Simulated Reference Bank")

    borrower_a = Borrower(
        borrower_id="SIM-BOR-A001",
        institution_id=INSTITUTION_ID,
        legal_name="Aranya Textiles Private Limited",
        external_borrower_ref="CIF-88213004",
    )
    borrower_b = Borrower(
        borrower_id="SIM-BOR-B002",
        institution_id=INSTITUTION_ID,
        legal_name="Konark Distributors Private Limited",
        external_borrower_ref="CIF-88213091",
    )
    store.borrowers[borrower_a.borrower_id] = borrower_a
    store.borrowers[borrower_b.borrower_id] = borrower_b

    facility_a = Facility(
        facility_id="SIM-FAC-A001",
        institution_id=INSTITUTION_ID,
        borrower_id=borrower_a.borrower_id,
        external_facility_ref="LN-CC-440921",
        sanctioned_limit_crore="5.00",
        state=FacilityState.ACTIVE,
    )
    facility_b = Facility(
        facility_id="SIM-FAC-B002",
        institution_id=INSTITUTION_ID,
        borrower_id=borrower_b.borrower_id,
        external_facility_ref="LN-CC-440977",
        sanctioned_limit_crore="3.00",
        state=FacilityState.ACTIVE,
    )
    store.facilities[facility_a.facility_id] = facility_a
    store.facilities[facility_b.facility_id] = facility_b

    # --- Facility A: rule version history (acceptance scenario #7) --------
    # v1: original terms, in force from 2026-06.
    rule_a_v1 = approve_rule_version(
        submit_rule_version(
            EligibilityRuleSet(
                rule_set_id="SIM-RULE-A001-V1",
                facility_id=facility_a.facility_id,
                version=1,
                state=ObligationState.DRAFT,
                stock_margin="0.25",
                receivable_margin="0.30",
                debtor_ageing_cutoff_days=90,
                submitted_by="maker.priya",
            )
        ),
        approver="checker.arvind",
        effective_from=date(2026, 6, 1),
    )
    store.rule_sets[rule_a_v1.rule_set_id] = rule_a_v1

    # v2: amendment tightening receivable margin, in force from 2026-08 —
    # v1 must still govern any calculation for periods before 2026-08.
    rule_a_v2 = approve_rule_version(
        submit_rule_version(
            EligibilityRuleSet(
                rule_set_id="SIM-RULE-A001-V2",
                facility_id=facility_a.facility_id,
                version=2,
                state=ObligationState.DRAFT,
                stock_margin="0.25",
                receivable_margin="0.35",
                debtor_ageing_cutoff_days=90,
                submitted_by="maker.priya",
            )
        ),
        approver="checker.arvind",
        effective_from=date(2026, 8, 1),
    )
    rule_a_v1 = supersede_rule_version(rule_a_v1)
    store.rule_sets[rule_a_v1.rule_set_id] = rule_a_v1
    store.rule_sets[rule_a_v2.rule_set_id] = rule_a_v2

    rule_b_v1 = approve_rule_version(
        submit_rule_version(
            EligibilityRuleSet(
                rule_set_id="SIM-RULE-B002-V1",
                facility_id=facility_b.facility_id,
                version=1,
                state=ObligationState.DRAFT,
                stock_margin="0.30",
                receivable_margin="0.35",
                debtor_ageing_cutoff_days=75,
                submitted_by="maker.priya",
            )
        ),
        approver="checker.arvind",
        effective_from=date(2026, 5, 1),
    )
    store.rule_sets[rule_b_v1.rule_set_id] = rule_b_v1

    # --- Facility A: two periods of financials -----------------------------
    # 2026-07 under v1 terms — reproduces the spec §8 worked fixture exactly.
    store.set_financials(
        FacilityFinancials(
            facility_id=facility_a.facility_id,
            period="2026-07",
            reported_stock_crore="4.00",
            stock_exclusions_crore="0.50",
            reported_receivables_crore="3.00",
            receivable_exclusions_crore="0.80",
            outstanding_crore="3.60",
        )
    )
    # 2026-08 under v2 terms (tighter receivable margin) — same reported
    # figures, different eligible DP, because a different rule version now
    # governs this period.
    store.set_financials(
        FacilityFinancials(
            facility_id=facility_a.facility_id,
            period="2026-08",
            reported_stock_crore="4.00",
            stock_exclusions_crore="0.50",
            reported_receivables_crore="3.00",
            receivable_exclusions_crore="0.80",
            outstanding_crore="4.55",  # deliberately tight -> near/below headroom threshold
        )
    )

    # Facility B: receivables figure for this period has not been received
    # yet -> DP must come back indeterminate, not zero.
    store.set_financials(
        FacilityFinancials(
            facility_id=facility_b.facility_id,
            period="2026-08",
            reported_stock_crore="2.40",
            stock_exclusions_crore="0.20",
            reported_receivables_crore=None,
            receivable_exclusions_crore=None,
            outstanding_crore="1.10",
        )
    )

    evidence_items = [
        EvidenceItem(
            evidence_id="SIM-EVD-A001-STOCK-07",
            facility_id=facility_a.facility_id,
            document_id=None,
            field_name="stock_statement",
            period="2026-07",
            state=EvidenceState.VERIFIED,
            reviewer="checker.arvind",
        ),
        EvidenceItem(
            evidence_id="SIM-EVD-A001-RECV-07",
            facility_id=facility_a.facility_id,
            document_id=None,
            field_name="receivable_ageing",
            period="2026-07",
            state=EvidenceState.VERIFIED,
            reviewer="checker.arvind",
        ),
        EvidenceItem(
            evidence_id="SIM-EVD-A001-STOCK-08",
            facility_id=facility_a.facility_id,
            document_id=None,
            field_name="stock_statement",
            period="2026-08",
            state=EvidenceState.VERIFIED,
            reviewer="checker.arvind",
        ),
        EvidenceItem(
            evidence_id="SIM-EVD-A001-RECV-08",
            facility_id=facility_a.facility_id,
            document_id=None,
            field_name="receivable_ageing",
            period="2026-08",
            state=EvidenceState.VERIFIED,
            reviewer="checker.arvind",
        ),
        EvidenceItem(
            evidence_id="SIM-EVD-B002-STOCK",
            facility_id=facility_b.facility_id,
            document_id=None,
            field_name="stock_statement",
            period="2026-08",
            state=EvidenceState.RECEIVED,
            reviewer=None,
        ),
        EvidenceItem(
            evidence_id="SIM-EVD-B002-RECV",
            facility_id=facility_b.facility_id,
            document_id=None,
            field_name="receivable_ageing",
            period="2026-08",
            state=EvidenceState.DUE,
            reviewer=None,
        ),
        EvidenceItem(
            evidence_id="SIM-EVD-B002-INS",
            facility_id=facility_b.facility_id,
            document_id=None,
            field_name="insurance_certificate",
            period="2026-Q2",
            state=EvidenceState.INCOMPLETE,
            reviewer="rm.neha",
        ),
    ]
    for item in evidence_items:
        store.evidence_items[item.evidence_id] = item

    # --- Waiver scoped to exactly one period (acceptance scenario #8) ------
    waiver = approve_waiver(
        submit_waiver(
            Waiver(
                waiver_id="SIM-WAIVER-A001-01",
                facility_id=facility_a.facility_id,
                test_id="SIM-COV-HEADROOM",
                scoped_period="2026-08",
                reason="Temporary drawdown for festive-season inventory build-up, approved by credit committee.",
                submitted_by="rm.neha",
            )
        ),
        approver="credit.suresh",
    )
    store.waivers[waiver.waiver_id] = waiver

    # --- Renewal record (Phase 5) ------------------------------------------
    store.renewals["SIM-RENEWAL-A001-01"] = RenewalRecord(
        renewal_id="SIM-RENEWAL-A001-01",
        facility_id=facility_a.facility_id,
        review_cycle_period="2026-Q3",
        decision="pending",
    )

    # --- Closure checklists (Phase 5 / acceptance scenario #15) ------------
    store.closures[facility_a.facility_id] = ClosureChecklist(facility_id=facility_a.facility_id)
    store.closures[facility_b.facility_id] = ClosureChecklist(facility_id=facility_b.facility_id)

    # A pending maker-checker case: a proposed margin change for facility A,
    # submitted but not yet approved — lets the UI demonstrate both a
    # successful checker approval and a rejected self-approval attempt.
    pending_case = submit_for_review(
        ApprovalCase(
            case_id="SIM-CASE-A001-RULEV3",
            subject_type="rule_version",
            subject_id="SIM-RULE-A001-V2",
            submitted_by="maker.priya",
        )
    )
    store.approval_cases[pending_case.case_id] = pending_case

    store.record_event(
        institution_id=INSTITUTION_ID,
        actor="system.seed",
        action="SEED_LOADED",
        detail="Synthetic reference dataset loaded (SIM-BANK-001, 2 facilities).",
    )

    return store

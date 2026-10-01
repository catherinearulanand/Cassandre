"""Cassandre CC — monitoring, import, rule-version, waiver, renewal, and
closure API, plus a Phase 8 shadow-score scaffold.

Spec mandatory constraint #1: "Start with synthetic records and read-only
imports. No real bank credentials, live limit changes, payments, borrower
communications or external-model data transmission by default." Nothing
here writes a sanction, changes a live bank limit, or contacts any external
system. The only mutations are: importing synthetic fixture data,
maker-checker actions on rule versions/waivers/cases, renewal decisions,
and closure-checklist updates — all against the local synthetic store.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, replace
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from cassandre_cc.evidence.storage import EvidenceStore, EvidenceIntegrityError
from pydantic import BaseModel, Field, field_validator, ConfigDict
from cassandre_cc.api.security import actor as authenticated_actor, visible, require_facility, install_security, current_principal

from cassandre_cc.calculations.covenant import Comparator, CovenantTest, evaluate_covenant_with_waiver
from cassandre_cc.calculations.drawing_power import calculate_drawing_power, inputs_from_records
from cassandre_cc.calculations.shadow_score import compute_shadow_score
from cassandre_cc.calculations.replay import preserve_run
from cassandre_cc.domain.entities import (
    ClosureChecklist,
    DocumentRef,
    EligibilityRuleSet,
    FacilityFinancials,
    RenewalRecord,
    Waiver,
)
from cassandre_cc.domain.states import DPResultState, FacilityState, FindingState, ObligationState
from cassandre_cc.fixtures.synthetic_seed import INSTITUTION_ID, seed
from cassandre_cc.store import persistence
from cassandre_cc.store.transactions import SnapshotTransactions, WriterLease
from cassandre_cc.store.memory_store import CrossInstitutionAccessError, MemoryStore, new_id
from cassandre_cc.workflow.maker_checker import (
    InvalidTransitionError,
    SelfApprovalError,
    approve as approve_case,
    approve_rule_version,
    approve_waiver,
    submit_for_review,
    submit_rule_version,
    submit_waiver,
    supersede_rule_version,
)

app = FastAPI(title="Cassandre CC", version="0.2.0", docs_url=None, redoc_url=None, openapi_url=None)

_DEFAULT_SNAPSHOT_PATH = Path(__file__).resolve().parents[3] / "data" / "store_snapshot.json"
# Overridable so the test suite runs against an isolated, always-fresh
# snapshot instead of whatever a dev server run may have left on disk (see
# tests/conftest.py) — without this, a second `pytest` run would load the
# first run's mutated state instead of the synthetic seed.
_SNAPSHOT_PATH = Path(os.environ.get("CASSANDRE_CC_STORE_PATH", str(_DEFAULT_SNAPSHOT_PATH)))
_writer_lease = WriterLease(_SNAPSHOT_PATH)
_store = persistence.load(_SNAPSHOT_PATH) or seed(MemoryStore())
_evidence_store = EvidenceStore(_SNAPSHOT_PATH.parent / "evidence")


app.add_middleware(SnapshotTransactions, store_getter=lambda: _store, path=_SNAPSHOT_PATH)
install_security(app, lambda: _store)

@app.exception_handler(RequestValidationError)
async def safe_validation_error(request, exc):
    return JSONResponse(status_code=422, content={"detail": [{"loc": list(e["loc"]), "type": e["type"], "msg": "Invalid input"} for e in exc.errors()]})

def _persist() -> None:
    persistence.save(_store, _SNAPSHOT_PATH)


@app.get("/healthz")
def healthz():
    return {"status": "ok", "mode": "synthetic"}

# Provisional covenant test — see calculations/covenant.py module docstring:
# this threshold is a placeholder, not an approved bank definition.
_HEADROOM_COVENANT = CovenantTest(
    test_id="SIM-COV-HEADROOM",
    description="Indicative DP headroom must stay at or above 5% of the sanctioned limit",
    comparator=Comparator.AT_LEAST,
    threshold=Decimal("0.05"),
)


def _money_out(money) -> Optional[dict[str, str]]:
    if money is None:
        return None
    display_amount = money.amount.normalize()
    if display_amount == display_amount.to_integral_value():
        display_amount = display_amount.quantize(Decimal("1"))
    return {"amount": str(display_amount), "unit": money.unit.value, "currency": money.currency}


def _facility_summary(facility_id: str) -> dict[str, Any]:
    facility = _store.facilities[facility_id]
    borrower = _store.borrowers[facility.borrower_id]
    return {
        "facility_id": facility.facility_id,
        "external_facility_ref": facility.external_facility_ref,
        "borrower_name": borrower.legal_name,
        "external_borrower_ref": borrower.external_borrower_ref,
        "sanctioned_limit_crore": facility.sanctioned_limit_crore,
        "state": facility.state.value,
    }


def _calculation_for(facility_id: str, period: Optional[str] = None) -> dict[str, Any]:
    if period is not None:
        import re
        if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", period):
            raise HTTPException(422, "Reporting period must be YYYY-MM")
    facility = _store.facilities[facility_id]
    period = period or _store.latest_period_for_facility(facility_id)
    financials = _store.get_financials(facility_id, period) if period else None
    rule_set = _store.effective_rule_version(facility_id, period) if period else None

    if financials is None:
        return {
            "period": period,
            "result_state": DPResultState.INDETERMINATE.value,
            "missing_fields": ["no financials received for this period"],
            "eligible_stock": None,
            "eligible_receivables": None,
            "proposed_dp": None,
            "usable_cap": None,
            "headroom": None,
            "covenant_test": _HEADROOM_COVENANT.description,
            "covenant_finding": None,
            "rule_set_version": rule_set.version if rule_set else None,
            "rule_set_state": rule_set.state.value if rule_set else None,
            "waiver_applied": False,
        }

    inputs = inputs_from_records(financials, rule_set, facility.sanctioned_limit_crore)
    result = calculate_drawing_power(inputs)

    finding = None
    waiver_applied = False
    if result.state is DPResultState.CALCULATED:
        sanctioned = Decimal(facility.sanctioned_limit_crore)
        headroom_ratio = result.headroom.amount / sanctioned if sanctioned else None
        active_waiver = _store.active_waiver(facility_id, _HEADROOM_COVENANT.test_id, period)
        waiver_applied = active_waiver is not None
        finding = evaluate_covenant_with_waiver(headroom_ratio, _HEADROOM_COVENANT, waiver_applied).value

    return {
        "period": period,
        "result_state": result.state.value,
        "missing_fields": list(result.missing_fields),
        "eligible_stock": _money_out(result.eligible_stock),
        "eligible_receivables": _money_out(result.eligible_receivables),
        "proposed_dp": _money_out(result.proposed_dp),
        "usable_cap": _money_out(result.usable_cap),
        "headroom": _money_out(result.headroom),
        "covenant_test": _HEADROOM_COVENANT.description,
        "covenant_finding": finding,
        "rule_set_version": rule_set.version if rule_set else None,
        "rule_set_state": rule_set.state.value if rule_set else None,
        "waiver_applied": waiver_applied,
    }


# =========================================================================
# Facilities / calculations (Phase 1 + 4)
# =========================================================================


@app.get("/v1/session")
def authenticated_session():
    p = current_principal.get()
    return {"actor":p.actor, "institution_id":p.institution_id, "roles":sorted(p.roles)}

@app.get("/v1/facilities/{facility_id}/calculation-runs")
def calculation_runs(facility_id: str):
    return [asdict(run) for run in _store.calculation_runs.values() if run.facility_id == facility_id]

@app.get("/v1/facilities")
def list_facilities() -> list[dict[str, Any]]:
    return [_facility_summary(fid) for fid in _store.facilities if visible(_store, fid)]


@app.get("/v1/facilities/{facility_id}")
def get_facility(facility_id: str, period: Optional[str] = None) -> dict[str, Any]:
    try:
        _store.get_facility(facility_id, current_principal.get().institution_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="no facility for this id")
    except CrossInstitutionAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc))

    evidence = [asdict(e) for e in _store.evidence_for_facility(facility_id)]
    for item in evidence:
        item["state"] = item["state"].value if hasattr(item["state"], "value") else item["state"]

    periods = sorted({f.period for f in _store.financials.values() if f.facility_id == facility_id})
    rule_versions = [
        {**asdict(r), "state": r.state.value, "effective_from": r.effective_from.isoformat() if r.effective_from else None}
        for r in _store.rule_versions_for_facility(facility_id)
    ]
    cure_tasks = [
        {**asdict(c), "opened_at": c.opened_at.isoformat(), "closed_at": c.closed_at.isoformat() if c.closed_at else None}
        for c in _store.cure_tasks_for_facility(facility_id)
    ]
    closure = _store.closures.get(facility_id)

    return {
        **_facility_summary(facility_id),
        "calculation": _calculation_for(facility_id, period),
        "evidence": evidence,
        "periods": periods,
        "rule_versions": rule_versions,
        "cure_tasks": cure_tasks,
        "closure_checklist": asdict(closure) if closure else None,
        "closure_ready": all(
            [closure.dues_reconciled, closure.security_released, closure.linked_exposures_clear, closure.originals_returned]
        )
        if closure
        else False,
    }


@app.post("/v1/facilities/{facility_id}/calculations:recompute")
def recompute_calculation(facility_id: str, period: Optional[str] = None) -> dict[str, Any]:
    """Re-runs the deterministic DP/covenant calculation from currently
    stored evidence. Never writes a new sanction or limit — read-only
    derived output only, recorded to the audit log. If the result is a
    (non-waived) breach, opens a cure task — idempotent per (facility,
    test, period)."""
    try:
        _store.get_facility(facility_id, current_principal.get().institution_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="no facility for this id")

    calc = _calculation_for(facility_id, period)
    resolved_period = calc["period"]
    if calc["covenant_finding"] in (FindingState.POTENTIAL_BREACH.value, FindingState.CONFIRMED_BREACH.value):
        _store.open_cure_task(facility_id, _HEADROOM_COVENANT.test_id, resolved_period)

    run = preserve_run(_store, facility_id, calc, authenticated_actor())
    _store.record_event(
        institution_id=current_principal.get().institution_id,
        actor=authenticated_actor(),
        action="DP_CALCULATION_RUN",
        detail=f"run={run.run_id} period={resolved_period} result={calc['result_state']} finding={calc['covenant_finding']}",
        facility_id=facility_id,
    )
    _persist()
    return {**calc, "run_id": run.run_id}


# =========================================================================
# Imports (Phase 2) — read-only, idempotent by content hash
# =========================================================================


class BoundaryModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_max_length=4096)

    @field_validator("period", "evidence_period", "scoped_period", "expires_after_period", check_fields=False)
    @classmethod
    def valid_period(cls, value):
        if value is not None:
            import re
            if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", value):
                raise ValueError("Reporting period must be YYYY-MM")
        return value

class FinancialsImport(BoundaryModel):
    facility_id: str
    period: str
    reported_stock_crore: Optional[str] = None
    stock_exclusions_crore: Optional[str] = None
    reported_receivables_crore: Optional[str] = None
    receivable_exclusions_crore: Optional[str] = None
    outstanding_crore: Optional[str] = None


def _validate_decimal_fields(payload: FinancialsImport) -> None:
    """Acceptance scenario #3: a malformed figure (e.g. a stray unit suffix
    from a rupees/lakh mismatch upstream) must stop the import, not silently
    become zero or NaN."""
    for field_name in (
        "reported_stock_crore",
        "stock_exclusions_crore",
        "reported_receivables_crore",
        "receivable_exclusions_crore",
        "outstanding_crore",
    ):
        value = getattr(payload, field_name)
        if value is None:
            continue
        try:
            number = Decimal(value)
            if not number.is_finite() or number < 0 or number > Decimal("1000000000") or len(value) > 64:
                raise InvalidOperation
        except InvalidOperation:
            raise HTTPException(
                status_code=422,
                detail={"failure": "INVALID_DECIMAL_VALUE", "field": field_name},
            )


@app.post("/v1/imports:financials")
def import_financials(payload: FinancialsImport) -> dict[str, Any]:
    require_facility(_store, payload.facility_id)
    try:
        _store.get_facility(payload.facility_id, current_principal.get().institution_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="no facility for this id")

    _validate_decimal_fields(payload)

    content_hash = hashlib.sha256(
        json.dumps(payload.model_dump(), sort_keys=True).encode("utf-8")
    ).hexdigest()
    batch, was_new = _store.record_import(
        institution_id=current_principal.get().institution_id,
        facility_id=payload.facility_id,
        period=payload.period,
        content_hash=content_hash,
        record_count=1,
    )

    if was_new:
        prior = _store.get_financials(payload.facility_id, payload.period)
        if prior is not None:
            _store.financials_history.setdefault(f"seed:{payload.facility_id}:{payload.period}", prior)
        _store.set_financials(
            FacilityFinancials(
                facility_id=payload.facility_id,
                period=payload.period,
                reported_stock_crore=payload.reported_stock_crore,
                stock_exclusions_crore=payload.stock_exclusions_crore,
                reported_receivables_crore=payload.reported_receivables_crore,
                receivable_exclusions_crore=payload.receivable_exclusions_crore,
                outstanding_crore=payload.outstanding_crore,
            )
        )
        _store.financials_history[batch.batch_id] = _store.get_financials(payload.facility_id, payload.period)
        _store.record_event(
            institution_id=current_principal.get().institution_id,
            actor=authenticated_actor(),
            action="FINANCIALS_IMPORTED",
            detail=f"batch={batch.batch_id} period={payload.period}",
            facility_id=payload.facility_id,
        )
        _persist()

    return {
        "batch_id": batch.batch_id,
        "was_new": was_new,
        "content_hash": content_hash,
        "message": "imported" if was_new else "duplicate content — no new batch created",
    }


@app.get("/v1/imports")
def list_imports() -> list[dict[str, Any]]:
    return [{**asdict(b), "imported_at": b.imported_at.isoformat()} for b in _store.import_batches.values() if visible(_store, b.facility_id)]


# =========================================================================
# Document versioning (spec §6 / acceptance scenario #13)
# =========================================================================
# This registers bounded synthetic plain text and its content hash.
# PDFs, malware inspection, OCR and clause extraction remain later work.
# A replacement never
# overwrites the original row, so a past calculation that cited the
# original document stays reproducible (spec §11.6: "reviewer-confirmed
# replacements... previous result reproducible").


class DocumentRegister(BoundaryModel):
    document_type: str
    evidence_period: str
    content: str = Field(max_length=200000)  # bounded synthetic plain text; preserved exactly
    supersedes_document_id: Optional[str] = None


@app.post("/v1/facilities/{facility_id}/documents")
def register_document(facility_id: str, body: DocumentRegister) -> dict[str, Any]:
    try:
        _store.get_facility(facility_id, current_principal.get().institution_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="no facility for this id")

    if body.supersedes_document_id is not None and body.supersedes_document_id not in _store.documents:
        raise HTTPException(status_code=404, detail="supersedes_document_id does not exist")

    if body.supersedes_document_id and _store.documents[body.supersedes_document_id].facility_id != facility_id:
        raise HTTPException(422, "Replacement must belong to the same facility")

    try:
        content_digest = _evidence_store.put_text(body.content)
    except ValueError:
        raise HTTPException(422, "Invalid synthetic plain-text evidence")
    except OSError:
        raise HTTPException(503, "Evidence storage unavailable")
    doc = DocumentRef(
        document_id=new_id("DOC"),
        institution_id=current_principal.get().institution_id,
        facility_id=facility_id,
        document_type=body.document_type,
        evidence_period=body.evidence_period,
        received_at=datetime.now(timezone.utc),
        source_hash=content_digest,
        supersedes_document_id=body.supersedes_document_id,
        is_original=body.supersedes_document_id is None,
    )
    _store.documents[doc.document_id] = doc
    _store.record_event(
        institution_id=current_principal.get().institution_id,
        actor=authenticated_actor(),
        action="DOCUMENT_REGISTERED",
        detail=f"document={doc.document_id} type={doc.document_type}"
        + (f" supersedes={doc.supersedes_document_id}" if doc.supersedes_document_id else ""),
        facility_id=facility_id,
    )
    _persist()
    return {**asdict(doc), "received_at": doc.received_at.isoformat()}


@app.get("/v1/facilities/{facility_id}/documents/{document_id}/content")
def original_document(facility_id: str, document_id: str):
    doc = _store.documents.get(document_id)
    if doc is None or doc.facility_id != facility_id or doc.institution_id != current_principal.get().institution_id:
        raise HTTPException(404, "No accessible document")
    try:
        content = _evidence_store.get_bytes(doc.source_hash)
    except FileNotFoundError:
        raise HTTPException(409, "Original evidence missing; verification required")
    except EvidenceIntegrityError:
        raise HTTPException(409, "Evidence integrity verification failed")
    except OSError:
        raise HTTPException(503, "Evidence storage unavailable")
    return Response(content, media_type="application/octet-stream", headers={"Content-Disposition": "attachment; filename=synthetic-evidence.txt"})

@app.get("/v1/facilities/{facility_id}/documents")
def list_documents(facility_id: str) -> list[dict[str, Any]]:
    superseded_ids = {d.supersedes_document_id for d in _store.documents.values() if d.supersedes_document_id}
    out = []
    for doc in _store.documents_for_facility(facility_id):
        out.append(
            {
                **asdict(doc),
                "received_at": doc.received_at.isoformat(),
                "is_current": doc.document_id not in superseded_ids,
            }
        )
    return out


# =========================================================================
# Rule versions (Phase 3)
# =========================================================================


class RuleVersionPropose(BoundaryModel):
    stock_margin: str
    receivable_margin: str
    debtor_ageing_cutoff_days: int
    submitted_by: str = ""


@app.post("/v1/facilities/{facility_id}/rule-versions")
def propose_rule_version(facility_id: str, body: RuleVersionPropose) -> dict[str, Any]:
    try:
        _store.get_facility(facility_id, current_principal.get().institution_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="no facility for this id")

    for margin in (body.stock_margin, body.receivable_margin):
        try:
            number = Decimal(margin)
            if not number.is_finite() or not 0 <= number <= 1:
                raise InvalidOperation
        except InvalidOperation:
            raise HTTPException(422, "Margins must be finite fractions between zero and one")
    if not 0 <= body.debtor_ageing_cutoff_days <= 3650:
        raise HTTPException(422, "Invalid ageing cutoff")
    existing = _store.rule_versions_for_facility(facility_id)
    next_version = (max((r.version for r in existing), default=0)) + 1

    rule = EligibilityRuleSet(
        rule_set_id=new_id("RULE"),
        facility_id=facility_id,
        version=next_version,
        state=ObligationState.DRAFT,
        stock_margin=body.stock_margin,
        receivable_margin=body.receivable_margin,
        debtor_ageing_cutoff_days=body.debtor_ageing_cutoff_days,
        submitted_by=authenticated_actor(),
    )
    rule = submit_rule_version(rule)
    _store.rule_sets[rule.rule_set_id] = rule
    _store.record_event(
        institution_id=current_principal.get().institution_id,
        actor=authenticated_actor(),
        action="RULE_VERSION_PROPOSED",
        detail=f"rule_set={rule.rule_set_id} v{rule.version}",
        facility_id=facility_id,
    )
    _persist()
    return {**asdict(rule), "state": rule.state.value}


class RuleVersionApprove(BoundaryModel):
    approver: str = ""
    effective_from: date


@app.post("/v1/rule-versions/{rule_set_id}:approve")
def approve_rule_version_endpoint(rule_set_id: str, body: RuleVersionApprove) -> dict[str, Any]:
    rule = _store.rule_sets.get(rule_set_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="no rule version for this id")

    try:
        approved = approve_rule_version(rule, authenticated_actor(), body.effective_from)
    except SelfApprovalError as exc:
        raise HTTPException(status_code=409, detail={"failure": "SELF_APPROVAL_DENIED", "message": str(exc)})
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=422, detail={"failure": "INVALID_TRANSITION", "message": str(exc)})

    # Supersede whatever was previously ACTIVE for this facility — it
    # remains correct for periods before the new effective_from (spec
    # acceptance scenario #7), so it is superseded, never deleted.
    for other in _store.rule_versions_for_facility(rule.facility_id):
        if other.rule_set_id != rule_set_id and other.state is ObligationState.ACTIVE:
            _store.rule_sets[other.rule_set_id] = supersede_rule_version(other)

    _store.rule_sets[rule_set_id] = approved
    _store.record_event(
        institution_id=current_principal.get().institution_id,
        actor=authenticated_actor(),
        action="RULE_VERSION_APPROVED",
        detail=f"rule_set={rule_set_id} effective_from={body.effective_from.isoformat()}",
        facility_id=rule.facility_id,
    )
    _persist()
    return {**asdict(approved), "state": approved.state.value}


# =========================================================================
# Waivers (Phase 5)
# =========================================================================


class WaiverPropose(BoundaryModel):
    facility_id: str
    test_id: str
    scoped_period: str
    reason: str
    submitted_by: str = ""
    expires_after_period: Optional[str] = None


@app.post("/v1/waivers")
def propose_waiver(body: WaiverPropose) -> dict[str, Any]:
    require_facility(_store, body.facility_id)
    try:
        _store.get_facility(body.facility_id, current_principal.get().institution_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="no facility for this id")

    waiver = Waiver(
        waiver_id=new_id("WAIVER"),
        facility_id=body.facility_id,
        test_id=body.test_id,
        scoped_period=body.scoped_period,
        reason=body.reason,
        submitted_by=authenticated_actor(),
        expires_after_period=body.expires_after_period,
    )
    waiver = submit_waiver(waiver)
    _store.waivers[waiver.waiver_id] = waiver
    _store.record_event(
        institution_id=current_principal.get().institution_id,
        actor=authenticated_actor(),
        action="WAIVER_PROPOSED",
        detail=f"waiver={waiver.waiver_id} test={body.test_id} period={body.scoped_period}",
        facility_id=body.facility_id,
    )
    _persist()
    return {**asdict(waiver), "state": waiver.state.value}


class WaiverApprove(BoundaryModel):
    approver: str = ""


@app.post("/v1/waivers/{waiver_id}:approve")
def approve_waiver_endpoint(waiver_id: str, body: WaiverApprove) -> dict[str, Any]:
    waiver = _store.waivers.get(waiver_id)
    if waiver is None:
        raise HTTPException(status_code=404, detail="no waiver for this id")

    try:
        approved = approve_waiver(waiver, authenticated_actor())
    except SelfApprovalError as exc:
        raise HTTPException(status_code=409, detail={"failure": "SELF_APPROVAL_DENIED", "message": str(exc)})
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=422, detail={"failure": "INVALID_TRANSITION", "message": str(exc)})

    _store.waivers[waiver_id] = approved
    _store.record_event(
        institution_id=current_principal.get().institution_id,
        actor=authenticated_actor(),
        action="WAIVER_APPROVED",
        detail=f"waiver={waiver_id}",
        facility_id=waiver.facility_id,
    )
    _persist()
    return {**asdict(approved), "state": approved.state.value}


@app.get("/v1/waivers")
def list_waivers(facility_id: Optional[str] = None) -> list[dict[str, Any]]:
    waivers = [w for w in _store.waivers.values() if visible(_store, w.facility_id)]
    if facility_id:
        waivers = [w for w in waivers if w.facility_id == facility_id]
    return [{**asdict(w), "state": w.state.value} for w in waivers]


# =========================================================================
# Renewal + closure (Phase 5 / spec §20, §23)
# =========================================================================


class RenewalDecide(BoundaryModel):
    decision: str  # "renewed" | "declined"
    decided_by: str = ""
    notes: str = ""


@app.post("/v1/renewals/{renewal_id}:decide")
def decide_renewal(renewal_id: str, body: RenewalDecide) -> dict[str, Any]:
    renewal = _store.renewals.get(renewal_id)
    if renewal is None:
        raise HTTPException(status_code=404, detail="no renewal for this id")
    if body.decision not in ("renewed", "declined"):
        raise HTTPException(status_code=422, detail={"failure": "INVALID_DECISION", "value": body.decision})

    if renewal.decision != "pending":
        raise HTTPException(409, "Renewal decision already recorded")
    updated = replace(
        renewal,
        decision=body.decision,
        decided_by=authenticated_actor(),
        decided_at=datetime.now(timezone.utc),
        notes=body.notes,
    )
    _store.renewals[renewal_id] = updated
    _store.record_event(
        institution_id=current_principal.get().institution_id,
        actor=authenticated_actor(),
        action="RENEWAL_DECIDED",
        detail=f"renewal={renewal_id} decision={body.decision}",
        facility_id=renewal.facility_id,
    )
    _persist()
    return {**asdict(updated), "decided_at": updated.decided_at.isoformat()}


@app.get("/v1/renewals")
def list_renewals() -> list[dict[str, Any]]:
    return [
        {**asdict(r), "decided_at": r.decided_at.isoformat() if r.decided_at else None}
        for r in _store.renewals.values() if visible(_store, r.facility_id)
    ]


class ClosureUpdate(BoundaryModel):
    dues_reconciled: Optional[bool] = None
    security_released: Optional[bool] = None
    linked_exposures_clear: Optional[bool] = None
    originals_returned: Optional[bool] = None
    actor: str = "ops.unknown"


@app.post("/v1/facilities/{facility_id}/closure")
def update_closure_checklist(facility_id: str, body: ClosureUpdate) -> dict[str, Any]:
    checklist = _store.closures.get(facility_id)
    if checklist is None:
        raise HTTPException(status_code=404, detail="no closure checklist for this facility")

    updates = {
        k: v
        for k, v in body.model_dump(exclude={"actor"}).items()
        if v is not None
    }
    updated = replace(checklist, **updates)
    _store.closures[facility_id] = updated
    _store.record_event(
        institution_id=current_principal.get().institution_id,
        actor=authenticated_actor(),
        action="CLOSURE_CHECKLIST_UPDATED",
        detail=f"{updates}",
        facility_id=facility_id,
    )
    _persist()
    ready = all(
        [updated.dues_reconciled, updated.security_released, updated.linked_exposures_clear, updated.originals_returned]
    )
    return {**asdict(updated), "closure_ready": ready}


class CloseFacility(BoundaryModel):
    actor: str = ""


@app.post("/v1/facilities/{facility_id}:close")
def close_facility(facility_id: str, body: CloseFacility) -> dict[str, Any]:
    """Acceptance scenario #15: a facility cannot close while any closure
    checklist item is outstanding — enforced here, not only in the UI."""
    facility = _store.facilities.get(facility_id)
    if facility is None:
        raise HTTPException(status_code=404, detail="no facility for this id")
    checklist = _store.closures.get(facility_id)
    ready = bool(checklist) and all(
        [checklist.dues_reconciled, checklist.security_released, checklist.linked_exposures_clear, checklist.originals_returned]
    )
    if not ready:
        raise HTTPException(
            status_code=409,
            detail={
                "failure": "CLOSURE_CHECKLIST_INCOMPLETE",
                "message": "closure release remains pending until every checklist item is complete",
                "checklist": asdict(checklist) if checklist else None,
            },
        )

    period = _store.latest_period_for_facility(facility_id)
    financials = _store.get_financials(facility_id, period) if period else None
    if financials is None or financials.outstanding_crore is None or Decimal(financials.outstanding_crore) != 0:
        raise HTTPException(409, {"failure": "OUTSTANDING_NOT_ZERO", "message": "Latest recorded outstanding must be present and zero; synthetic data only"})
    checklist_events = [e for e in _store.audit_events if e.facility_id == facility_id and e.action == "CLOSURE_CHECKLIST_UPDATED"]
    if any(e.actor == authenticated_actor() for e in checklist_events):
        raise HTTPException(409, {"failure":"SELF_APPROVAL_DENIED", "message":"Closure checker must differ from checklist maker"})
    _store.facilities[facility_id] = replace(facility, state=FacilityState.CLOSED)
    _store.record_event(
        institution_id=current_principal.get().institution_id,
        actor=authenticated_actor(),
        action="FACILITY_CLOSED",
        detail="all closure checklist items complete",
        facility_id=facility_id,
    )
    _persist()
    return _facility_summary(facility_id)


# =========================================================================
# Cases (generic maker-checker), audit, shadow score
# =========================================================================


@app.get("/v1/cases")
def list_cases() -> list[dict[str, Any]]:
    return [{**asdict(c), "state": c.state.value} for c in _store.approval_cases.values()
            if visible(_store, getattr(_store.rule_sets.get(c.subject_id) or _store.waivers.get(c.subject_id), "facility_id", None))]


class ApproveRequest(BoundaryModel):
    approver: str = ""


@app.post("/v1/cases/{case_id}:approve")
def approve_case_endpoint(case_id: str, body: ApproveRequest) -> dict[str, Any]:
    case = _store.approval_cases.get(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="no case for this id")

    try:
        updated = approve_case(case, authenticated_actor())
    except SelfApprovalError as exc:
        raise HTTPException(status_code=409, detail={"failure": "SELF_APPROVAL_DENIED", "message": str(exc)})
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=422, detail={"failure": "INVALID_TRANSITION", "message": str(exc)})

    _store.approval_cases[case_id] = updated
    _store.record_event(
        institution_id=current_principal.get().institution_id,
        actor=authenticated_actor(),
        action="CASE_APPROVED",
        detail=f"case={case_id} subject={case.subject_id}",
    )
    _persist()
    return {**asdict(updated), "state": updated.state.value}


@app.get("/v1/audit-events")
def list_audit_events(facility_id: Optional[str] = None) -> list[dict[str, Any]]:
    events = [e for e in _store.audit_events if e.institution_id == current_principal.get().institution_id]
    if facility_id:
        events = [e for e in events if e.facility_id == facility_id]
    return [
        {**asdict(e), "occurred_at": e.occurred_at.isoformat()}
        for e in sorted(events, key=lambda e: e.occurred_at, reverse=True)
    ]


@app.get("/v1/facilities/{facility_id}/shadow-score")
def get_shadow_score(facility_id: str, period: Optional[str] = None) -> dict[str, Any]:
    """Phase 8 scaffold. See calculations/shadow_score.py — not a trained
    model, never used to gate anything, returned only with its disclaimer."""
    try:
        _store.get_facility(facility_id, current_principal.get().institution_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="no facility for this id")

    calc = _calculation_for(facility_id, period)
    facility = _store.facilities[facility_id]
    sanctioned = Decimal(facility.sanctioned_limit_crore)

    utilisation = None
    headroom_ratio = None
    if calc["usable_cap"] and calc["proposed_dp"] is not None:
        financials = _store.get_financials(facility_id, calc["period"])
        if financials and financials.outstanding_crore and Decimal(calc["usable_cap"]["amount"]) != 0:
            utilisation = Decimal(financials.outstanding_crore) / Decimal(calc["usable_cap"]["amount"])
    if calc["headroom"]:
        headroom_ratio = Decimal(calc["headroom"]["amount"]) / sanctioned

    evidence_delay_flag = any(
        e.state.value in ("due", "incomplete")
        for e in _store.evidence_for_facility(facility_id)
        if e.period == calc["period"]
    )
    open_cures = len([c for c in _store.cure_tasks_for_facility(facility_id) if c.status == "open"])

    result = compute_shadow_score(utilisation, headroom_ratio, evidence_delay_flag, open_cures)
    return {"score": result.score, "basis": result.basis, "disclaimer": result.disclaimer, "period": calc["period"]}


_STATIC_DIR = Path(__file__).resolve().parents[1] / "web" / "static"
if _STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=_STATIC_DIR, html=True), name="web-ui")

"""Generic maker-checker gate — spec §8: "No state may jump to
confirmed/waived/closed solely because a model suggests it... The submitter
cannot approve their own material change." Enforces acceptance scenario
#12 ("Maker attempts self-approval: denied").

Used for rule-version activation here; the same gate is meant to cover
waiver approval and release sign-off as those are built out (spec §8's
Obligation states: draft -> reviewed -> active -> superseded/retired).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from typing import Optional

from cassandre_cc.domain.entities import EligibilityRuleSet, Waiver
from cassandre_cc.domain.states import ObligationState


class SelfApprovalError(PermissionError):
    """Raised when the approver is the same identity as the submitter."""


class InvalidTransitionError(ValueError):
    """Raised for any state transition outside draft -> reviewed -> active
    (or -> superseded/retired), e.g. approving something never submitted."""


@dataclass(frozen=True)
class ApprovalCase:
    case_id: str
    subject_type: str  # "rule_version" | "waiver" | ...
    subject_id: str
    submitted_by: str
    state: ObligationState = ObligationState.DRAFT
    approved_by: Optional[str] = None


def submit_for_review(case: ApprovalCase) -> ApprovalCase:
    if case.state is not ObligationState.DRAFT:
        raise InvalidTransitionError(f"cannot submit case in state {case.state.value}")
    return replace(case, state=ObligationState.REVIEWED)


def approve(case: ApprovalCase, approver: str) -> ApprovalCase:
    if case.state is not ObligationState.REVIEWED:
        raise InvalidTransitionError(f"cannot approve case in state {case.state.value}")
    if approver == case.submitted_by:
        raise SelfApprovalError(
            f"{approver!r} submitted this case and cannot also approve it"
        )
    return replace(case, state=ObligationState.ACTIVE, approved_by=approver)


def retire(case: ApprovalCase) -> ApprovalCase:
    if case.state not in (ObligationState.ACTIVE, ObligationState.REVIEWED):
        raise InvalidTransitionError(f"cannot retire case in state {case.state.value}")
    return replace(case, state=ObligationState.RETIRED)


# ---- the same gate, applied directly to an EligibilityRuleSet -------------
# (EligibilityRuleSet carries its own state/submitted_by/approved_by rather
# than going through a generic ApprovalCase, since a rule version also
# needs an `effective_from` date set at approval time and — on approval —
# the facility's previously-active version superseded. Same rules, same
# exceptions, so callers get one consistent failure vocabulary.)


def submit_rule_version(rule: EligibilityRuleSet) -> EligibilityRuleSet:
    if rule.state is not ObligationState.DRAFT:
        raise InvalidTransitionError(f"cannot submit rule version in state {rule.state.value}")
    return replace(rule, state=ObligationState.REVIEWED)


def approve_rule_version(
    rule: EligibilityRuleSet, approver: str, effective_from: date
) -> EligibilityRuleSet:
    if rule.state is not ObligationState.REVIEWED:
        raise InvalidTransitionError(f"cannot approve rule version in state {rule.state.value}")
    if approver == rule.submitted_by:
        raise SelfApprovalError(f"{approver!r} submitted this rule version and cannot also approve it")
    return replace(rule, state=ObligationState.ACTIVE, approved_by=approver, effective_from=effective_from)


def supersede_rule_version(rule: EligibilityRuleSet) -> EligibilityRuleSet:
    if rule.state is not ObligationState.ACTIVE:
        raise InvalidTransitionError(f"cannot supersede rule version in state {rule.state.value}")
    return replace(rule, state=ObligationState.SUPERSEDED)


# ---- the same gate, applied to a Waiver (spec §21) -------------------------


def submit_waiver(waiver: Waiver) -> Waiver:
    if waiver.state is not ObligationState.DRAFT:
        raise InvalidTransitionError(f"cannot submit waiver in state {waiver.state.value}")
    return replace(waiver, state=ObligationState.REVIEWED)


def approve_waiver(waiver: Waiver, approver: str) -> Waiver:
    if waiver.state is not ObligationState.REVIEWED:
        raise InvalidTransitionError(f"cannot approve waiver in state {waiver.state.value}")
    if approver == waiver.submitted_by:
        raise SelfApprovalError(f"{approver!r} submitted this waiver and cannot also approve it")
    return replace(waiver, state=ObligationState.ACTIVE, approved_by=approver)

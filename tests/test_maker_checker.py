"""Acceptance scenario #12: "Maker attempts self-approval: denied."""

import pytest

from cassandre_cc.domain.states import ObligationState
from cassandre_cc.workflow.maker_checker import (
    ApprovalCase,
    InvalidTransitionError,
    SelfApprovalError,
    approve,
    retire,
    submit_for_review,
)


def _draft_case() -> ApprovalCase:
    return ApprovalCase(
        case_id="C1",
        subject_type="rule_version",
        subject_id="RULE-V2",
        submitted_by="maker.priya",
    )


def test_submitter_cannot_approve_own_case():
    case = submit_for_review(_draft_case())
    with pytest.raises(SelfApprovalError):
        approve(case, "maker.priya")


def test_independent_checker_can_approve():
    case = submit_for_review(_draft_case())
    approved = approve(case, "checker.arvind")
    assert approved.state is ObligationState.ACTIVE
    assert approved.approved_by == "checker.arvind"


def test_cannot_approve_before_submission():
    with pytest.raises(InvalidTransitionError):
        approve(_draft_case(), "checker.arvind")


def test_cannot_submit_twice():
    case = submit_for_review(_draft_case())
    with pytest.raises(InvalidTransitionError):
        submit_for_review(case)


def test_retire_only_from_active_or_reviewed():
    case = submit_for_review(_draft_case())
    approved = approve(case, "checker.arvind")
    retired = retire(approved)
    assert retired.state is ObligationState.RETIRED

    with pytest.raises(InvalidTransitionError):
        retire(retired)

"""State enums exactly as enumerated in the build specification §8.

No state may jump to a terminal value solely because a model suggests it
(mandatory constraint #5 / spec §8's own rule) — these enums exist so the
workflow layer has a closed set of valid transitions to check against,
rather than a free-text status field.
"""

from __future__ import annotations

from enum import Enum


class ObligationState(str, Enum):
    DRAFT = "draft"
    REVIEWED = "reviewed"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    RETIRED = "retired"


class EvidenceState(str, Enum):
    NOT_DUE = "not_due"
    DUE = "due"
    RECEIVED = "received"
    INCOMPLETE = "incomplete"
    VERIFIED = "verified"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class FindingState(str, Enum):
    COMPLIANT = "compliant"
    NEAR_THRESHOLD = "near_threshold"
    INDETERMINATE = "indeterminate"
    POTENTIAL_BREACH = "potential_breach"
    CONFIRMED_BREACH = "confirmed_breach"
    WAIVED_FOR_SCOPE = "waived_for_scope"
    CURE_PENDING = "cure_pending"
    REMEDIATED = "remediated"


class FacilityState(str, Enum):
    APPLICATION = "application"
    APPRAISAL = "appraisal"
    APPROVED = "approved"
    DOCUMENTATION = "documentation"
    READY = "ready"
    ACTIVE = "active"
    REVIEW_DUE = "review_due"
    RESTRICTED_BY_AUTHORISED_DECISION = "restricted_by_authorised_decision"
    CLOSED = "closed"


class DPResultState(str, Enum):
    """Not in the spec's core state table verbatim, but required by
    acceptance scenario #4 ("missing statement pages or unresolved margin:
    indeterminate DP") — a calculation run must be able to report that it
    could not reach a number, distinctly from reporting zero."""

    CALCULATED = "calculated"
    INDETERMINATE = "indeterminate"


class Role(str, Enum):
    RM = "rm"
    MAKER = "maker"
    CHECKER = "checker"
    APPROVER = "approver"
    LEGAL = "legal"
    AUDITOR = "auditor"
    ADMIN = "admin"

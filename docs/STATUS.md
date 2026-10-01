# Build status — 1 October 2026

This is a synthetic, single-server on-premises evaluation prototype, not the complete application-to-closure product or production bank deployment. The original claim that six phases were complete has been corrected. See REPOSITORY_AUDIT.md for every lifecycle step.

## Implemented

- Decimal DP arithmetic with finite/nonnegative input, margin, exclusion, currency and unit checks. Missing inputs are indeterminate; negative headroom is preserved.
- Fail-closed hashed bearer credentials, server-attributed actors, reader/maker/checker roles, tenant access checks and bounded request inputs. Independent approval cannot be bypassed by submitting another actor's name.
- Reviewed rule versions, historical replay, explicit ambiguous effective-date blocking. Monthly inputs cannot silently resolve a mid-month amendment.
- Idempotent aggregate imports, retained input revisions, immutable calculation receipts containing exact selected terms/inputs/results.
- Immutable local synthetic UTF-8 text originals with authorised attachment retrieval and checksum verification; full snapshot/evidence backup bundles.
- Scoped local waivers and cure tasks, local renewal records, closure blocks for incomplete checklist, missing/nonzero latest balance and non-independent checklist approval.
- Pure commercial-bank CC daily conduct engine: continuous excess, no credits and credit/interest comparison over complete inclusive 90-day evidence. Incomplete/unattested data and unsupported profiles return indeterminate. No NPA/SMA writes.
- Atomic versioned/checksummed snapshots, one-writer lease, serialized request commit/rollback and fail-closed persistence failure. Backup/restore tests.
- On-premises Docker/Compose configuration, exact hashed Python dependency lock, non-root/read-only image settings, persistent volume and deployment/recovery guide. Container execution remains unverified.

## Partial or deferred

- JSON remains the runtime store: one worker, local disk, no HA/throughput claim. PostgreSQL target DDL is design-only, not a tested runtime migration.
- Local bearer authentication is not bank SSO/MFA. No branch/portfolio authority matrix or independently protected audit store.
- Aggregate DP inputs do not implement line-level ageing, creditor/exclusion ordering, sublimits, actual bank DP reconciliation or feed freshness.
- One synthetic covenant only; no full financial/nonfinancial obligations, legal source/clause extraction, insurance or physical-custody workflow.
- Two synthetic active facilities; pre-sanction steps are not implemented. Document intake capabilities are described in SECURITY_REVIEW.md; no PDF/OCR/AI review pipeline.
- The daily conduct module is not connected to a real bank ledger feed. The heuristic shadow score is not a trained/predictively validated model.
- Checksums are corruption checks, not proof against an administrator rewriting data. Storage/backups require host encryption and separate protected audit controls before real data.

## Four external gates

1. **Phase 0 — discovery:** actual BOB/Union account walkthrough, data owners, approved rules, authority and source mapping. Preparation is buildable; validation requires bank staff.
2. **Phase 6 — approved integration/pilot:** API, scheduled bank export or another approved interface; permissions, operational support and actual reporting-cycle comparison. An API is not mandatory. No endpoint has been invented.
3. **Phase 7 — assurance:** independent security testing, legal/privacy applicability, bank process/IT/risk/vendor approvals, target-host recovery and support. This change prepares controls; it cannot self-grant external sign-off.
4. **Phase 9 — optional multi-party ledger:** demonstrated shared-trust problem and participating institutions. Not a prerequisite for a single-bank prototype; compare a central signed registry first.

Do not claim all scenarios or all ambiguities are covered. Tests and remaining limits are recorded in the pull request and review documentation.

## Verification evidence

132 tests passed in the final shared-tree run, including an actual Uvicorn socket/process restart that retained an import and calculation receipt. JavaScript syntax and git whitespace checks passed. Docker/container and PostgreSQL execution were not performed. One upstream Starlette/httpx deprecation warning remains. Tests do not establish independent penetration-test or regulatory sign-off.

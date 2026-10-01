# Build status

Tracks implemented vs mocked vs deferred, per the build specification's own
requirement ("Report implemented, mocked, blocked and deferred capabilities
separately," spec §17) and the user's instruction to distinguish these
explicitly. This file reflects the state after completing every phase of
spec §17 that a coding session can actually complete — see "Phases that
cannot be completed in code" below for why four of the ten phases are not,
and never will be, checkable off by writing more code.

## Implemented (real, tested code)

**Phase 1 — foundation**
- Decimal-only `Money` type with unit-mismatch protection.
- Institution-scoped access control (`CrossInstitutionAccessError`).
- Append-only audit log on every mutation.
- Dashboard UI, driven entirely by the real API.

**Phase 2 — imports and evidence linking**
- `POST /v1/imports:financials` — idempotent by content hash (acceptance
  scenario #1: re-importing identical content creates no duplicate).
- Malformed figures are rejected before anything is written (acceptance
  scenario #3).
- Document versioning: `POST /v1/facilities/{id}/documents` — a replacement
  never overwrites the original row; both remain queryable, `is_current`
  is derived, not mutated (acceptance scenario #13).

**Phase 3 — reviewed rule register**
- Full rule-version lifecycle: propose (draft) → submit (reviewed) →
  approve (active), maker-checker enforced, self-approval denied.
- Approving a new version supersedes the old one without deleting it.
- Effective-dated selection: a calculation for a historical period still
  uses the rule version that was in force *then*, even after a newer
  version has since superseded it for current periods (acceptance
  scenario #7 — verified live: facility A's 2026-07 calculation keeps
  using v1 after v2 and v3 were approved for later periods).

**Phase 4 — DP and evidence monitoring**
- Deterministic DP engine reproducing the spec §8 worked fixture exactly.
- "Missing input → indeterminate, never zero" (acceptance scenario #4).
- Multi-period support with a period selector in the UI.

**Phase 5 — covenants, exceptions, renewal, closure**
- Covenant engine with the spec's full finding-state set.
- Waivers: maker-checker approved, scoped to exactly one
  (facility, test, period) triple — a waiver never silently covers a
  different period's breach of the same test (acceptance scenario #8,
  verified live: December's breach was not suppressed by November's
  waiver).
- Cure tasks: opened automatically on an unwaived breach, idempotent per
  (facility, test, period) — recomputing twice does not open a duplicate.
- Renewal decisions (renewed/declined) with actor and timestamp.
- Closure checklist: a facility cannot close while any item is
  outstanding — enforced server-side, not just hidden in the UI
  (acceptance scenario #15, verified live: the close button stayed
  blocked with 3/4 items checked, then succeeded at 4/4).

**Persistence**
- State now survives a process restart (JSON snapshot, verified by
  restarting the real dev server mid-session and confirming an approval
  was still there). Still not Postgres — see docs/ASSUMPTIONS.md.

**Phase 8 — predictive ML, scoped down to what's honest**
- A feature-snapshot shape and one transparent, hand-written heuristic
  (`calculations/shadow_score.py`) — explicitly NOT a trained model, every
  API response carries the disclaimer. This is the full extent of what
  spec §9 permits without real labelled outcome data, which does not
  exist for a synthetic pilot (spec §9: "No synthetic pilot proves
  predictive credit accuracy").

**Tests:** 55 passed, 0 failed (`uv run pytest -q`), covering every
acceptance scenario above at the HTTP layer, not just unit-level.

## Mocked / stubbed (present but not real)

- Persistence: JSON file, not a relational database — no migrations, no
  concurrent-writer safety, no indexes.
- Auth: a static "Viewing as: RM" label; the API's maker-checker check is
  real, but the UI does not yet hide either role's action based on a real
  logged-in identity.
- Shadow score: heuristic, not a trained model (see Phase 8 above).
- Document registration: hashes and versions a reference; does not store,
  OCR, or parse actual files.

## Phases that cannot be completed in code

Spec §17 defines ten phases. Six are done (above). Four are not attempted,
and building more code cannot complete them — they require things that
only exist outside this session:

- **Phase 0 (bank discovery):** requires an actual walkthrough of a real
  sanctioned CC account with BOB/Union staff. Nothing here can substitute
  for that without inventing bank process details, which the spec's
  mandatory constraints explicitly forbid.
- **Phase 6 (bank-approved interfaces, shadow pilot):** requires a bank to
  hand over a documented, approved integration interface (mandatory
  constraint #8: "No invented bank APIs"). `adapters/bob` and
  `adapters/union` remain empty, flagged stubs — this is correct, not
  incomplete.
- **Phase 7 (production assurance):** requires independent security
  testing, legal/compliance sign-off, and a real support/DR posture — none
  of which a coding session can grant itself.
- **Phase 9 (multi-party evidence network / blockchain):** requires
  multiple real participating institutions and a demonstrated shared-trust
  problem (spec §10: "Do not put blockchain in the MVP"). Not started, on
  purpose.

## Known limitations of this slice

- The UI's role label does not gate actions — the *server* correctly
  rejects a self-approval, but nothing yet hides the option client-side.
- One covenant test is wired up, not the full obligation register spec
  §18 describes.
- No real document storage/OCR — only reference registration and
  versioning.
- Single synthetic institution, two facilities — spec §17's fuller
  corpus (`SIM-002..009`) is explicitly out of scope, same pacing the spec
  itself recommends.

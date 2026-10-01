# Architecture (this slice)

Modular monolith per spec §13, one FastAPI process:

```
src/cassandre_cc/
  money.py            Decimal-only Money/Unit value type
  domain/
    entities.py       Institution, Borrower, Facility, EvidenceItem, EligibilityRuleSet, ...
    states.py         The spec §8 closed state enums (Obligation/Evidence/Finding/Facility)
  calculations/
    drawing_power.py  Deterministic DP engine + the spec's worked fixture
    covenant.py        Deterministic covenant threshold engine
  workflow/
    maker_checker.py  Generic submit/approve gate, self-approval denial
  store/
    memory_store.py   Synthetic, institution-scoped store (Postgres stand-in)
  fixtures/
    synthetic_seed.py The only data this prototype ever shows
  api/
    main.py           FastAPI app: read-only monitoring + maker-checker actions
  web/static/          Dashboard UI (vanilla HTML/CSS/JS, calls only this API)
adapters/
  bob/, union/         Empty, flagged — no bank API is invented (mandatory constraint #8)
docs/
  ASSUMPTIONS.md        What's stood in for what, and why
  STATUS.md              Implemented / mocked / deferred
```

No product boundary enforcement script exists yet (unlike the sibling
derivatives-platform repo's `check_import_graph.py`) — this is a single
package, not yet a multi-product workspace, because spec §13 itself
recommends starting as a modular monolith and splitting later only if scale
justifies it.

## Data flow for the one connected workflow this slice demonstrates

1. `fixtures/synthetic_seed.py` loads two facilities into the store at
   process start (one with complete evidence, one missing a field).
2. `GET /v1/facilities/{id}` assembles `DPInputs` from stored
   `FacilityFinancials` + the facility's approved `EligibilityRuleSet`, runs
   `calculate_drawing_power`, then feeds the resulting headroom ratio into
   `evaluate_covenant`.
3. The UI renders that result as a "control record" card — calculated or
   indeterminate, never a silent zero — plus the evidence queue and any
   open maker-checker case.
4. Approving a case calls the real `workflow.maker_checker.approve` gate;
   a self-approval attempt is rejected with the exact failure reason
   (`SELF_APPROVAL_DENIED`), not a generic error, echoing the spec's own
   evidence-labelling discipline about never collapsing distinct failures
   into one message.
5. Every calculation run and case approval writes an `AuditEvent`.

## Why a modular monolith instead of the sibling repo's multi-package workspace

The existing `D:\Cassandre-Platform` derivatives platform demonstrates the
heavier pattern (per-product `src/` packages, `uv` workspace, import-graph
CI check) for a mature, multi-product system. This is a first vertical
slice of a single, new product — adding that ceremony now would slow down
exactly the kind of fast, connected-workflow iteration the user asked for.
If/when this splits into genuinely independent products (per spec §13's own
module list), the same package-per-module structure is already in place to
promote into that pattern.

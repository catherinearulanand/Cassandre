# Assumption register

Required by the build specification's starter prompt (§20: "Create an
implementation plan and assumption register") and by the user's own
instruction to distinguish implemented features, mocks, and items requiring
bank confirmation. Nothing below is a claim that the underlying gap is
closed — each item names what stands in for it today and what would replace
it.

| # | Assumption | Why | What replaces it later |
|---|---|---|---|
| 1 | Persistence is a JSON file snapshot of the in-memory store, not Postgres | Spec §13 recommends Postgres; this got state-survives-restart without the schema/migration overhead of a full RDBMS on day one — verified by actually restarting the dev server mid-session | SQLAlchemy + Alembic migrations, same entity shapes already defined in `domain/entities.py` |
| 2 | Auth is a single dev-mode "viewing as" label, not Keycloak/OIDC | Spec §11.2 calls for bank SSO + MFA; wiring a realm for a single-session prototype was deferred, same gap the sibling derivatives-platform repo recorded for the identical reason | Phase 6: OIDC provider + real role-based session, before any non-synthetic data is ever considered |
| 3 | One synthetic institution, bank-CC profile only, no NBFC path | Spec §3: "Banks and NBFCs are separate product/regulatory profiles" | Explicit NBFC profile validation (spec §3) before that path is enabled at all |
| 4 | Margins, ageing cutoffs, and the covenant headroom threshold are placeholders | Spec §8/§18: "No universal DP formula... Definitions override generic ratios." These numbers exist only so the worked fixture (and its mid-period amendment) has something concrete to compute against | Real values must come from an approved `EligibilityRuleSet` per facility, sourced from the actual sanction terms — never a default in code |
| 5 | No BOB/Union adapters implemented — `adapters/bob`, `adapters/union` are empty, flagged `README-discovery-required.md` | Spec mandatory constraint #8: "No invented bank APIs" | Phase 0 bank discovery walkthrough, then Phase 6 adapter build against a documented, bank-approved interface — genuinely cannot happen inside a coding session, see docs/STATUS.md |
| 6 | No Docker/Compose | Prototype speed; nothing here depends on containerisation yet | Phase 6/7, alongside the real database |
| 7 | Covenant engine implements one generic threshold test (`evaluate_covenant_with_waiver`), not the full financial/non-financial test library from spec §18 | Scope control — demonstrating the *mechanism* (compliant / near-threshold / indeterminate / breach / waived-for-scope) mattered more than test coverage breadth | Registering more `CovenantTest` instances per facility is mechanical once real definitions exist — the engine and waiver-scoping logic already support it |
| 8 | All identifiers use the `SIM-` prefix; two synthetic borrowers/facilities, one institution | Spec §3, mandatory constraint #1 | Corpus expansion (spec §17 `SIM-002..009`) is explicitly out of scope, same pacing the spec itself recommends |
| 9 | Phase 8's shadow score is a hand-written heuristic, not a trained model | Spec §9 requires labelled historical outcome data and model governance before any RF/XGBoost model — neither exists for a synthetic pilot; a fabricated "trained model" would be a false claim the spec explicitly prohibits | A real baseline, per spec §9's own sequencing, only after real labelled data and a model-governance owner exist |
| 10 | Document registration hashes and versions a reference, not real files | OCR/clause extraction (spec §6, §9) is explicitly later-phase work requiring a real document pipeline | Real file storage + OCR once a document source (scan/DMS export) is actually connected |

## Items that require bank confirmation before any production step

These are not assumptions this codebase can resolve by itself — spec §6 and
§19 call them out as founder/bank actions, not engineering ones:

- Actual BOB/Union CBS/LOS/DMS export mechanism, refresh frequency, and
  access permissions for one real (or bank-approved synthetic) CC account.
- The bank's actual approved DP formula, covenant definitions, and ageing
  rules for the facility type being piloted — this prototype's numbers are
  illustrative only, taken directly from the spec's own worked example.
- Authority matrix / role mapping for maker, checker, approver, legal,
  auditor in the pilot bank unit.
- Legal/compliance sign-off on data handling before anything beyond
  synthetic data is processed (spec §12).

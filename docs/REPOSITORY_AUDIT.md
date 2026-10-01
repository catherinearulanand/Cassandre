# Cassandre repository audit and phased delivery

Reviewed 1 October 2026 against the supplied 24-step Cassandre CC specification and the complete initial source/test inventory. Findings below distinguish code from external sign-off. No actual bank environment, borrower file or proprietary JPMC/Goldman system was accessed.

## Verdict

The original repository did **not** implement the full specification. It was a two-facility synthetic monitoring slice. Its assertion that six phases were complete overstated coverage: no authenticated identity, relational database, original document storage, extraction/review, full lifecycle or continuous ledger feed existed. The reported 55 tests did not establish bank compliance, production security or complete acceptance-scenario coverage.

This change hardens that slice into a bounded single-server, synthetic on-premises prototype. It does not turn demonstration records into sanctioned bank records. JSON remains the active store; PostgreSQL is a separately documented migration target. Do not present the prototype as production-approved or fully scalable.

## Position in a bank

| Bank component | Authoritative responsibility | Cassandre responsibility |
|---|---|---|
| Origination/loan appraisal system | application, assessment, approval, sanction | consume approved terms and pre-sanction context; flag conflicts |
| Core banking / ledger (e.g. installed Finacle) | account, live limit/DP, debits, credits, interest, bank classification | read approved extracts; calculate recommendations and conduct signals |
| Document management / paper custody | official documents and originals | retain version references, bounded synthetic text copies now; approved PDF/page evidence later; track missing evidence |
| Credit administration / risk workflow | authorised decision and execution | reviewed exceptions, rule changes, waivers, reproducible monitoring |
| Bank identity, security, audit infrastructure | identity/MFA, encryption/key management, independent audit and operational controls | integrate with those controls before real-data deployment |

Finacle is an Infosys/EdgeVerve product. TCS BaNCS is a separate product. Vendor product availability does not establish that a particular module is installed at BOB or Union. A customer-facing bank API does not grant access to internal credit records.

## Full lifecycle coverage

| Step | Current code coverage | Required next implementation / bank validation |
|---|---|---|
| 01 Enquiry and product fit | absent | reference originating system/product profile, avoid duplicate application |
| 02 Application/completeness | absent | application ID and source checklist |
| 03 KYC/ownership/authority | absent | approved KYC status/ownership references, restricted permissions |
| 04 Existing debt/history | absent | permitted bureau/debt evidence and coverage limitations |
| 05 Business/site verification | absent | inspection evidence and reviewer |
| 06 Financial spreading | aggregate synthetic import only | source pages, reviewed mapping, reconciliation |
| 07 Working-capital assessment | absent | bank-approved assessment basis; proposed vs sanctioned distinction |
| 08 Security/legal valuation | absent | asset/charge/custody/legal evidence and independent decisions |
| 09 Appraisal/internal rating | absent | consume approved rating and appraisal, not shadow heuristic |
| 10 Sanction | static fixture limit | immutable approved sanction versions and authority evidence |
| 11 Acceptance | absent | signed/accepted terms and conflict review |
| 12 Documentation/perfection | absent | legal/security conditions and custody status |
| 13 Pre-release/account setup | absent | independently checked prerequisites and CBS reconciliation |
| 14 Activation/drawdown | fixture active state only | bank activation feed; no Cassandre limit writes |
| 15 End use/account conduct | new pure daily advisory engine | approved complete day-end ledger adapter and bank interpretations |
| 16 Stock/receivables receipt | aggregate import + bounded original text metadata | PDF/page evidence, reviewer status, due/freshness monitoring |
| 17 Eligibility/proposed DP | simplified aggregate Decimal engine | line ageing, creditors, exclusions, sublimits, bank DP comparison |
| 18 Continuing covenants | one synthetic headroom test | approved financial/nonfinancial obligation register, due evidence |
| 19 Inspection/security maintenance | absent | inspection/insurance dates, valuation and charge conditions |
| 20 Renewal/enhancement | local decision record only | review schedules, independent authority, source-approved terms |
| 21 Waiver/amendment | local maker-checker versions/scopes | legal source and contractual scope; no regulatory-rule waiver |
| 22 Stress/recovery | advisory conduct module only | separate bank-owned classification and recovery process |
| 23 Closure/releases | checklist strengthened with zero-balance/independence | authoritative current balance, commitments, charge release/custody evidence |
| 24 Retention/audit/corrections | version references, run receipts, recovery tooling | retention policy, independent protected audit archive and lawful correction |

A zero value or an uploaded reference is not evidence of verification. The synthetic headroom covenant is explicitly illustrative, not a BOB/Union covenant. The proposed DP is not the bank's live drawing power.

## Review personas and research boundaries

These are simulated review lenses, not employees or certifications.

* **BOB credit administration reviewer:** approved scheme/sanction terms, working-capital evidence, proposed versus live DP, renewal/custody. Public bank material establishes some digital channels, not exact internal access permissions. See BANK_REVIEW.md.
* **Union credit operations reviewer:** facility identifiers, appraisal/document/core-system reconciliation and bank-authorised exports. Public tender/app evidence suggests document digitisation; paper originals and complete scanning require discovery.
* **JPMC enterprise control reviewer:** independently attributable approvals, machine-readable control evidence, software inventory, recovery and third-party assurance. Public JPMC discussion supports these general patterns; its market-risk platform is not proof of an Indian CC covenant-monitoring design.
* **Goldman Sachs data/platform reviewer:** consistent data definitions, versioned provenance, governed platform boundaries and repeatable calculations. Public Legend/data-engineering material informs design principles; Cassandre does not reproduce proprietary GS credit systems.
* **Finacle/Newgen/Nucleus product reviewer:** use existing origination, document workflow and limit/covenant capabilities as integration/competitive boundaries. Do not claim an unconfirmed module or copy proprietary code.

Public primary references (retrieved 1 October 2026):
- RBI commercial-bank IRACP, updated 1 July 2026: https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=13146
- JPMC control evidence/third-party risk discussion: https://www.jpmorganchase.com/newsroom/from-the-desk-of/modernizing-third-party-risk-management
- Goldman Sachs governed data-engineering/Legend example: https://developer.gs.com/blog/posts/sustainability-in-action-diving-into-esg-data-engineering
- Finacle limit/collateral/covenant suite: https://www.finacle.com/solution/limits-collaterals-and-covenants-management-suite/
- Newgen commercial loan management: https://newgensoft.com/in/solutions/industries/financial-institutions/commercial-banking/loan-management-system/
- Nucleus corporate lending: https://www.nucleussoftware.com/corporate-lending/

## Phases and next gates

| Phase | Current disposition | What can be built now | External gate |
|---|---|---|---|
| 0 Discovery | blocked for real bank evidence | input inventory, walkthrough/checklist templates | BOB/Union staff validate actual account, systems, authority and policy |
| 1 Foundation | improved, partial | authenticated local roles, isolation, secure packaging | bank SSO/MFA, database migration, document storage and all lifecycle screens |
| 2 Intake | partial | validated idempotent aggregate imports/history | approved source schema, original files, reviewed linkage, completeness/freshness |
| 3 Rule register | partial | independent activation, dates, conflicting-date blocking | source-backed reviewed clauses and approved interpretations |
| 4 Monitoring | partial | robust aggregate DP, preserved run receipts, advisory conduct | approved golden fixtures, line eligibility, feed reconciliation/freshness |
| 5 Workflow | partial | scoped waiver, cure/renewal records, stronger closure | full obligation set, authority matrix and bank execution reconciliation |
| 6 Bank pilot | blocked for real feeds | generic read-only import contracts and feed tests | approved API **or** export/SFTP/interface; actual reporting-cycle comparison |
| 7 Assurance | preparation possible, approval blocked | recovery tests, inventory, threat tests, deployment guide | independent penetration test, legal/privacy assessment, bank IT/risk sign-off and DR/support |
| 8 ML | deferred research | explainable synthetic heuristic only | lawful labelled data, temporal validation, independent model review |
| 9 Multi-party ledger | deferred optional | requirements/central-registry comparison | multiple institutions and demonstrated shared-trust benefit |

The four external phases are not reasons to omit all preparatory engineering. Phase 6 does not require an API specifically. Phase 7 includes buildable controls and tests, followed by independent assurance. Phase 9 is not a prerequisite for an on-premises demo.

## On-premises readiness and honest limits

Run the locked tests and recovery checks described in ON_PREM.md. Container execution must be tested on a Docker-capable host; Docker is unavailable in the review environment. The runtime is deliberately one process and one local filesystem writer. It has no throughput or HA claim. PostgreSQL, protected original-file storage, workers/outbox, SSO, independently protected logs, key management and approved data feeds remain necessary before institutional-scale or real-data deployment.

No software can detect every hidden liability, forged plausible statement, missing amendment or collusion. Missing/unavailable evidence must remain visible and indeterminate. AI/OCR extraction must produce proposals with source pages; staff confirm facts and rules. RF/XGBoost are deferred until labelled outcomes and model governance exist. Blockchain is unnecessary for this single-bank prototype.

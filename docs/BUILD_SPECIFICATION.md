# Cassandre: India Cash-Credit Lifecycle and Monitoring Build Specification

Version: 1.0 | Research cut-off: 1 October 2026 IST
Audience: Founder, bank design partner, engineering team and Claude coding assistant
Status: researched implementation specification; bank-specific discovery and production approvals remain required.

## 1. Instructions to Claude — read before implementing

Build one connected borrower-to-closure workflow for inventory/receivables-backed cash-credit facilities. The primary commercial value is continuous post-sanction monitoring. Pre-sanction functions provide provenance and handover, and must coexist with the lender's existing origination system rather than require duplicate applications.

Finacle is an Infosys/EdgeVerve product, not TCS. TCS BaNCS is a different product. Never label an integration “TCS Finacle.”

Do not claim this specification is an actual Bank of Baroda or Union Bank internal procedure manual. Public evidence confirms selected systems and product features, not every branch practice. Implement the common workflow and separate bank adapters. Mark unverified integration details as discovery required.

Mandatory engineering constraints:

1. Start with synthetic records and read-only imports. No real bank credentials, live limit changes, payments, borrower communications or external-model data transmission by default.
2. Preserve the lender's borrower ID, account ID and facility ID; do not join records by company name alone.
3. Every material extracted field must retain source document, page/table location, evidence period, receipt time and reviewer status.
4. Arithmetic, date logic, eligibility and monitoring rules use versioned deterministic code. Generative AI must not perform authoritative financial calculations.
5. No automatic sanction, waiver, fraud classification, restructuring, recall or enforcement decision. Systems may execute approved deterministic controls only within authorised permissions.
6. Proposed findings are not confirmed findings. Missing evidence is not evidence of compliance or financial breach.
7. No universal DP formula, review frequency, debtor-age rule or financial threshold. Each comes from approved facility terms and lender policy.
8. No invented bank APIs. Build adapters against mocks until the bank supplies a documented approved interface and test data.
9. No claim of detecting all ambiguities, fraud or losses. Track observable contradictions and explicitly show unobservable or missing information.
10. Keep real records out of Claude coding prompts, source control, developer laptops and consumer chat products unless an independently approved data-handling arrangement permits the exact processing.

Build in the sequence in section 17. An end-to-end product does not require every advanced capability to launch together.

## 2. Evidence policy and limits

Evidence labels used in this file:

- **Confirmed:** supported by an identified primary source, within that source's date and scope.
- **Product-specific:** confirmed for a named scheme, not all commercial CC accounts.
- **Historical:** official evidence describes an earlier implementation; current configuration must be checked.
- **Proposed:** Cassandre design decision, not a requirement imposed by RBI.
- **Unknown:** must be demonstrated by the bank or verified by legal/compliance before production.

The CRISIL article is a 2024 global analysis. Its European regulatory discussion is not binding Indian law. It identifies fragmented monitoring, weak amendment capture and future ML possibilities; it does not validate Cassandre or establish prevalence in BOB/Union CC portfolios [S01].

The supplied Grok share URL could not be retrieved through the research tool. Its contents have NOT been evaluated or used as evidence [S02]. Obtain an export or pasted text for a later source-by-source review.

The founder reports a discussion with an IFSCA ED about a multi-entity blockchain project. This is an interview lead, not verified evidence of a deployed system, approval, required architecture or endorsement. Ask for the project's name, participants, legal perimeter, data model, evaluation and production status.

The institutional personas in section 16 are simulated review lenses, not employees or endorsements. American-bank perspectives are design critiques, not Indian regulatory requirements.

## 3. Product boundary and borrower selection

Primary facility: bank CC supported by eligible inventory and receivables, for established trading/distribution businesses initially. Add manufacturing after work-in-progress, production and valuation complexities are supported. Choose borrowers with accessible reporting history and straightforward ownership/security arrangements.

Initial portfolio: one bank unit, 20–50 synthetic or appropriately authorised historical accounts, single-lender, performing accounts, a small defined obligation set. These quantities are proposed pilot scope, not market or regulatory thresholds.

Banks and NBFCs are separate product/regulatory profiles. A bank CC operating account is not identical to an NBFC revolving working-capital facility. NBFCs do not become banks through Cassandre, and a bank's CC “out of order” logic must not be copied indiscriminately into an NBFC product. Validate actual NBFC contract, ledger mechanics, entity category, applicable prudential directions and banking arrangements before enabling that profile.

Core outputs:

- a current facility record linking application, sanction, agreement, amendments, ledger and evidence;
- a reviewed obligation register;
- evidence due/overdue/uncertain queues;
- proposed DP assessment with exclusions and source trace;
- financial/non-financial covenant findings;
- investigation and approval packs;
- an authorised decision and follow-up history;
- closure reconciliation and release tracking.

Continuous means responding to new records, scheduled checks and changes, with visible freshness. Monthly borrower evidence cannot support claims of live inventory truth.

## 4. What is known about BOB and Union systems

| Area | Bank of Baroda | Union Bank of India | Implication |
|---|---|---|---|
| Core account processing | Finacle-related in-house customisation appears in official tenders [S03]. Exact version/modules not established here. | FY2024–25 annual report describes a Finacle upgrade [S04]. Version statement is date-specific. | Import authorised records; do not infer the full current stack from CBS name. |
| Origination | Named digital MSME schemes provide online journeys and data-based appraisal [S05,S06]. | Public LAS references and named digital MSME journeys [S07,S08]. | A digital product does not prove all larger secured CC cases are paperless. |
| Documents | Historical official report records customer-document digitisation [S09]; current commercial-loan coverage unknown. | Official 2022 scanner RFP identifies Newgen document software; official staff scanning app confirms scanning capability [S10,S11]. | Existing scans can be reused, but completeness and account links require verification. |
| External connectivity | bob Open Banking confirms API services [S12]. | Historical procurement lists API gateway/DMS/Finacle and approved integration methods [S13]. | Neither establishes an API returning every agreement or covenant. |
| Working-capital submissions | Internet banking advertises stock-statement update [S14]. | Verify actual CC statement entry/submission screens with the bank. | Avoid inventing exact branch workflow or universal statement storage. |

Public data does not establish: complete document coverage, all middleware, APIs, schema, responsible unit, actual refresh rate, permissions, staff workarounds or integration cost. Those are discovery requirements.

## 5. Sequential lifecycle — bank process, digital state and improvements

Employee roles below are generic functions. Banks can centralise or combine them. Digital reach is a qualitative design assessment, not a measured adoption percentage. “BOB/Union” references are evidence anchors, not assertions that every stage uses the named product at every branch.

### Step 01 — Borrower enquiry and product fit
**Process:** establish business activity, working-capital cycle, requested amount, existing borrowings and whether CC fits.
**People:** RM/business officer originates; branch manager screens; credit officer advises facility structure.
**Documents:** business profile, initial request, turnover and debt summary.
**Today/digital reach:** moderate; assisted discussions and digital leads coexist. BOB/Union named digital journeys establish selective online entry [S05–S08]. CRM brand/coverage unknown.
**Pros/cons:** online capture improves tracking but fixed forms can conceal complex needs.
**Improve:** reuse existing lead/application ID; optional bank-approved intake screen only where no existing channel exists. AI may summarise the request with sources; no unsupervised product or eligibility decision.

### Step 02 — Formal application and completeness
**Process:** register application, obtain scheme-specific checklist, acknowledge receipt and identify missing evidence.
**People:** RM collects; processing officer checks; credit supervisor allocates.
**Documents:** application, entity records, financials, statements, funding assessment and security details.
**Today/digital reach:** moderate; uploaded files, scans and assisted submissions. BOB product pages specify data inputs [S05,S06]; Union coverage must be shown for the actual selected scheme.
**Pros/cons:** checklist tracking prevents lost requests, but “received” is not “valid.”
**Improve:** import existing files once, classify them, identify missing pages and reporting periods; preserve originals. Staff resolve gaps rather than re-enter entire applications.

### Step 03 — KYC, ownership and authority
**Process:** establish legal borrower, beneficial ownership, authorised signatories and applicable compliance checks.
**People:** onboarding/KYC maker; checker; compliance escalation; RM clarification.
**Documents:** entity constitution, PAN, relevant identity/address evidence, ownership declaration and resolutions.
**Today/digital reach:** moderate–high for routine checking; ownership complexity remains assisted. Union historical integration records include CKYC/eKYC [S13]. Exact access unknown.
**Pros/cons:** reusable identification reduces work, but verified identity is not verified credit quality.
**Improve:** import verified status and references; avoid unnecessary duplicate identity documents. Expired/unresolved status remains visible. AI can extract ownership evidence; compliance interpretation stays authorised.

### Step 04 — Existing debt and credit-history checks
**Process:** reconcile declared borrowings with permitted bureau information and lender records, including group relationships.
**People:** credit analyst examines; RM clarifies; risk reviews adverse cases.
**Documents:** commercial bureau report, borrowing schedules, sanction letters, relevant guarantor reports.
**Today/digital reach:** high retrieval where integrated, moderate interpretation. Actual bureau connections and reuse rights must be verified.
**Pros/cons:** external reports reveal conduct, but reporting delay and identity errors limit completeness.
**Improve:** join by verified identifiers; mark report date; show mismatches for investigation. No unauthorised onward redistribution of licensed reports.

### Step 05 — Business and site verification
**Process:** confirm premises, operations, inventory handling, suppliers/customers and licences.
**People:** RM/credit officer; technical specialist where needed; external verification agency if appointed.
**Documents:** visit report, licences, invoices, operational evidence and photographs.
**Today/digital reach:** low–moderate; digital forms organise evidence but cannot replace physical inspection.
**Pros/cons:** dated checklists support consistency; images alone cannot prove inventory quantity or authenticity.
**Improve:** bank-approved mobile capture, assigned findings and independent sample checks. Geolocation/device evidence is corroboration, not proof. AI flags inconsistent observations.

### Step 06 — Financial spreading and reconciliation
**Process:** map accounts into approved financial categories; compare audited/provisional accounts, tax information and bank flows.
**People:** analyst prepares; checker validates; RM obtains explanations.
**Documents:** audited accounts/notes, provisional accounts, GST/ITR where relevant, bank statements, ageing and related-party schedules.
**Today/digital reach:** moderate; LOS tools, PDF extraction and spreadsheets. BOB digital products use financial footprints [S05,S06].
**Pros/cons:** repeatable calculations help; extraction and one-off adjustments can distort the result.
**Improve:** source-linked spreading with materiality checks, explicit adjustments and “cannot conclude” state. AI proposes mapping, deterministic code calculates.

### Step 07 — Working-capital assessment
**Process:** assess inventory/collection/payable cycles, seasonality, projected need, borrower contribution and downside scenarios.
**People:** appraisal officer; credit reviewer; technical support for complex businesses.
**Documents:** CMA/working-capital assessment where required, projections, cash-flow forecast and order book.
**Today/digital reach:** moderate; model/LOS assistance, assumptions require judgment.
**Pros/cons:** templates aid comparisons; mechanically applying turnover methods can misstate needs.
**Improve:** preserve assumptions and sensitivities; compare forecasts with later actuals. Do not prescribe one method or threshold across lenders.

### Step 08 — Security, valuation and legal examination
**Process:** identify primary security/collateral, ownership, value, encumbrances and priority.
**People:** credit/legal/collateral officers; external panel advocate and valuer.
**Documents:** title/search/valuation reports, asset lists, ownership and existing-charge records.
**Today/digital reach:** low–moderate verification; moderate digital tracking. Current BOB/Union collateral software configuration unknown.
**Pros/cons:** digital inventories reduce omissions; flawed valuation/title evidence remains flawed.
**Improve:** asset identifiers, independent report status, expiry dates and open defects. AI compares records; no AI legal-title certification.

### Step 09 — Credit appraisal and internal rating
**Process:** combine financial, business, management, industry and conduct risks; prepare recommendation and deviations.
**People:** credit analyst; RM business case; independent risk reviewer.
**Documents:** appraisal memo, rating, sensitivities, proposed controls and deviations.
**Today/digital reach:** moderate–high workflow, judgment remains. Union LAS is an evidence anchor; scheme-specific ratings must not become universal rules [S07,S08].
**Pros/cons:** structured review improves consistency; weak assumptions can survive a polished memo.
**Improve:** evidence-backed memo, source references and override history. AI drafts; approved rating engine remains authoritative.

### Step 10 — Sanction decision
**Process:** authorised officer/committee approves, declines or requests more information under delegated powers.
**People:** sanctioning authority; credit secretariat; risk reviewer.
**Documents:** approved proposal, committee decision, deviations and sanction conditions.
**Today/digital reach:** moderate–high routing; exact platforms/authority matrices unknown.
**Pros/cons:** electronic approval records decisions; free-text conditions may not enter monitoring.
**Improve:** permission checks, separate maker/approver, current authority matrix and approved-terms handover. Cassandre cannot sanction independently.

### Step 11 — Sanction communication and acceptance
**Process:** communicate limit, pricing, reporting, eligibility, security, renewal and other conditions; record acceptance and approved negotiations.
**People:** RM; credit officer; operations/legal; sanction authority for changes.
**Documents:** final sanction, acceptance, disclosures and approved revisions.
**Today/digital reach:** moderate; digital letters and assisted execution can coexist.
**Pros/cons:** templates help; accepted wording may diverge from proposal.
**Improve:** compare proposal, decision and final terms; resolve conflicts before making any rule active. Source precedence is an approved legal mapping, not a blind “newest file wins.”

### Step 12 — Execution and security perfection
**Process:** execute loan/security documents, fulfil stamping/registration/filing requirements and arrange custody.
**People:** legal/documentation officers; operations checker; custodian; external professionals.
**Documents:** agreement, applicable notes/guarantees, hypothecation/mortgage, resolutions and relevant ROC/CERSAI records.
**Today/digital reach:** moderate; supported digital execution exists [S15]. Physical originals and some registration remain separate requirements.
**Pros/cons:** e-execution reduces handling; does not correct invalid authority or defective security.
**Improve:** execution/perfection tracked separately; connect scanned copies to physical custody register. No blockchain substitute for legally required filings or originals.

### Step 13 — Pre-release conditions and account setup
**Process:** verify documentation, insurance, contribution, security and approved exceptions; configure account and facility correctly.
**People:** credit administration maker; checker; operations; authorised exception approver.
**Documents:** condition checklist, evidence, exceptions, account-setup record and release approval.
**Today/digital reach:** high posting, moderate condition interpretation; CBS plus origination/operations records.
**Pros/cons:** system gates reduce omissions; a wrong checkbox or rate/limit setup propagates.
**Improve:** compare approved terms with account configuration; unresolved required evidence blocks “ready,” without altering CBS unless separately authorised.

### Step 14 — Activation and drawdown
**Process:** activate CC availability; borrower draws/repays within approved constraints. Sanction is not automatic full disbursement.
**People:** operations maker/checker; RM coordination; credit administration.
**Documents/data:** activation approval, limit/DP records and account transactions.
**Today/digital reach:** high transaction processing in CBS; precise integration unknown.
**Pros/cons:** strong ledger controls; stale DP or incorrect setup can undermine them.
**Improve:** read-only availability reconciliation; timestamp every imported snapshot. No duplicate loan ledger.

### Step 15 — End-use and account-conduct review
**Process:** examine approved use, sales routing, unusual transfers, interest servicing, excesses and credits.
**People:** RM; credit-monitoring officer; operations; risk investigation for material concerns.
**Documents/data:** transactions, invoices, delivery records, visit reports and approved account conditions.
**Today/digital reach:** high transaction collection, moderate investigation.
**Pros/cons:** analytics surface changes; other-bank flows and cash activity can remain invisible.
**Improve:** explainable rule alerts and linked investigation. Transactions are indicators, not automatic fraud conclusions.

### Step 16 — Periodic stock and receivable receipt
**Process:** receive required statements and confirm period, completeness and responsible attestation.
**People:** borrower finance team submits; RM follows up; monitoring officer validates.
**Documents:** stock schedule, receivable ageing, creditors, invoices/ERP extracts where agreed.
**Today/digital reach:** moderate; BOB advertises stock-statement updates [S14]. Union selected channel/storage must be demonstrated.
**Pros/cons:** portals reduce chasing; uploaded statements remain self-reported evidence.
**Improve:** reuse existing submission channel, version replaced statements, track due dates from contract and minimise duplicate requests.

### Step 17 — Eligibility and proposed drawing power
**Process:** apply approved stock/receivable exclusions, margins, creditor treatment, sublimits and caps to eligible security values.
**People:** DP maker; checker; operations implements authorised result; RM clarifies exceptions.
**Documents:** current statements, approved eligibility rules, audits and prior DP decision.
**Today/digital reach:** moderate, using bank applications/CBS fields or assisted worksheets; exact BOB/Union formula unknown.
**Pros/cons:** calculation automation helps; fabricated or misclassified inputs survive perfect arithmetic.
**Improve:** deterministic line-by-line assessment with source/period checks and mismatch investigation. Missing inputs yield indeterminate, never assumed zero. Keep proposed DP distinct from active CBS DP.

### Step 18 — Covenant and continuing-condition checks
**Process:** test approved financial definitions and non-financial obligations using valid evidence; distinguish headroom, missing evidence and confirmed failure.
**People:** monitoring maker/checker; RM; legal for ambiguous definitions; credit authority for decisions.
**Documents:** final terms, current accounts, certificates, insurance, amendments and waivers.
**Today/digital reach:** variable/moderate; incumbent capability exists [S16–S18], deployment extent unknown.
**Pros/cons:** reminders/formulas help; wrong period/definition or unrecorded waiver creates false findings.
**Improve:** reviewed obligation register, effective dates, evidence lineage and linked follow-up. Definitions override generic ratios.

### Step 19 — Inspection, audit and security maintenance
**Process:** verify stock/business/security; assess audit findings, insurance and valuations.
**People:** RM/monitoring/collateral team; external stock auditor/valuer.
**Documents:** inspection, stock audit, insurance and valuation reports; cure evidence.
**Today/digital reach:** low–moderate physical checks, moderate tracking.
**Pros/cons:** dashboards expose overdue work; completed reports are not guaranteed truthful.
**Improve:** track independent checks, findings and verified closure; use discrepancies to prioritise visits rather than replace them.

### Step 20 — Periodic review, renewal or enhancement
**Process:** reassess need, performance, conduct, rating, covenants and security; approve changed or continued limits.
**People:** RM; credit analyst; independent risk; sanction authority; operations.
**Documents:** updated financials/projections, monitoring history, revised appraisal and sanction.
**Today/digital reach:** moderate–high workflow. Scheme annual review is not a universal blanket rule; use policy/terms and current prudential constraints [S05,S19].
**Pros/cons:** reminders help; repeated extensions can disguise incomplete review.
**Improve:** feed verified monitoring history into renewal automatically, preserve temporary-extension expiry and next actions.

### Step 21 — Exception, waiver and amendment
**Process:** investigate, collect explanation, review alternatives, obtain authorised decision and implement follow-up.
**People:** RM; monitoring; credit/risk; legal; designated authority.
**Documents:** finding, source evidence, exception memo, approval and formal waiver/amendment.
**Today/digital reach:** moderate; exact case/approval applications unknown.
**Pros/cons:** tracked cases help; email-only decisions can be missed next cycle.
**Improve:** scoped waiver period, approval power, cure obligation and retest date. Amendment prospectively creates new rule version; old runs remain reproducible.

### Step 22 — Stress, prudential treatment and recovery (conditional)
**Process:** apply relevant reporting/classification rules and consider authorised resolution/recovery options.
**People:** risk/operations/finance; stressed-assets unit; recovery/legal; authorised committee.
**Documents:** overdue/conduct records, viability assessment, resolution approvals and legal records.
**Today/digital reach:** high approved accounting rules, moderate discretionary strategy.
**Pros/cons:** deterministic classifications improve consistency; bad data and inappropriate overrides cause harm.
**Improve:** explain rule-derived candidates; lender's authorised system remains the classification/reporting source. Watchlist, covenant breach, SMA/NPA, fraud and wilful default are separate states.

### Step 23 — Closure and releases
**Process:** reconcile dues/commitments, cancel availability, verify linked security, release eligible charges/guarantees and return originals.
**People:** operations; credit administration; legal/collateral; custodian; RM.
**Documents:** final ledger, closure approval, no-dues/release documents, applicable satisfaction filings and return receipt.
**Today/digital reach:** high ledger closure, moderate release/custody coordination.
**Pros/cons:** zero balance is easy to observe; another facility may still require shared security.
**Improve:** closure checklist includes linked exposures, final obligations, custody and registry actions. Archive monitoring without deleting history.

### Step 24 — Retention, audit and corrections
**Process:** retain evidence under approved schedule, correct reporting and support disputes/audit.
**People:** records/operations; reporting; compliance/legal; internal audit.
**Documents:** complete decision/evidence history and release/retention records.
**Today/digital reach:** moderate–high archives, integration varies.
**Pros/cons:** retrieval improves; retention without deletion/purpose controls accumulates sensitive data.
**Improve:** exportable audit pack, legal holds, scheduled deletion where permitted and proof of access/revisions.

## 6. Ingestion — no duplicate data-entry portal

Order of preference: (1) approved existing system interface; (2) scheduled bank-generated secure export; (3) existing document-store export; (4) controlled bulk upload; (5) scan only required paper pages. Manual typing is an exception for unavailable/uncertain information.

No assumption that customer-facing APIs expose internal credit files. Account Aggregator can support permitted financial-data sharing; it is not a universal route to internal appraisal memos, agreements, committee decisions or paper files.

| Source | Required content | Checks | Failure action |
|---|---|---|---|
| CBS/ledger export | borrower/facility IDs, sanction/active limit, DP, balance, credits, interest, review/setup dates as available | schema/version, totals, business date, duplicates, reconciliation | mark stale/incomplete; block affected conclusions |
| LOS/LAS | application, assessment, sanction approval and conditions | approved vs proposed, facility link, authority/version | hold proposed terms inactive |
| DMS/file store | sanction, agreement, security evidence, amendments | file hash, pages, document type, period, account link | quarantine unsupported/unsafe file or route gaps |
| Borrower evidence channel | statements, accounts, insurance | sender/attestation, period, duplicates, replacements, completeness | request specific correction through approved channel |
| Physical custody | original reference, location, status and scan if available | original/copy distinction, completeness, custody chain | show paper-only; authorised scanning task |

Technical reader: structured files are mapped directly; selectable PDF text is parsed; scanned images use OCR; extracted obligations use a schema-constrained model followed by review. Preserve source copies and page coordinates. Never collect borrower internet-banking, tax-portal or GST passwords in Cassandre. Use bank-approved consent/data-sharing arrangements. Do not assert a signature/image proves authenticity. Automated forgery flags require independent confirmation.

Bank-specific discovery deliverable must list each required input, owner, actual application, export method, permissions, refresh frequency, retrospective coverage and missing-data cost. End-to-end demos must not substitute for this discovery.

## 7. Ambiguity and discrepancy register

| Observable issue | Detection | Required disposition |
|---|---|---|
| Proposal differs from sanction | compare mapped fields and conditions | authorised final term confirmed |
| Agreement differs from sanction | clause comparison | legal/credit reconciliation, no guessed precedence |
| Amendment lacks facility link/effective date | required fields/relationship checks | obtain valid mapping and date |
| Same document has revised figures | hashes + period/type comparison | preserve both; reviewer selects controlling evidence |
| Statement period is stale or missing | period/freshness checks | indeterminate assessment and follow-up |
| Certificate says compliant but figures disagree | approved computation comparison | potential breach review |
| Stock/receivables inconsistent with other evidence | reconciliations and agreed tolerance | investigation, not fraud label |
| Debtor ageing exceeds eligibility | deterministic rule | excluded amount with reason |
| Creditor deduction or margin unclear | rule completeness check | no authoritative DP until resolved |
| Shared asset/security or double counting | asset identifiers and charge records | review priority/coverage; incomplete external visibility disclosed |
| Insurance period/cover inadequate | dates and approved requirements | correction task, not merely “policy uploaded” |
| Waiver expires or cure is unverified | effective-date and evidence test | follow-up/retest; no permanent suppression |
| Ledger and approved terms differ | configuration comparison | operations correction through existing process |
| Cross-bank conduct unavailable | coverage flag | cannot conclude; no inference of clean conduct |

Cannot guarantee discovery of collusion, hidden liabilities, off-book inventory, forged but plausible evidence, missing amendments or events not in accessible sources. Show data coverage and investigation limits next to each result.

## 8. Deterministic calculation and state engines

Use Decimal amounts, explicit currency/unit, agreed rounding and business-date/timezone logic. Store reported figures separately from normalised and adjusted figures. Validate GST inclusive/exclusive, rupees/lakh/crore, debit/credit sign and period boundaries.

DP implementation uses approved configurable components: inventory categories, unpaid-stock/creditor treatment, receivable eligibility, ageing boundary, related-party/disputed exclusions, approved margins, sublimits and caps. Exclusion ordering must avoid double deductions. Related-party exclusion is conditional on approved rules, not universal.

Synthetic worked fixture ONLY:

- reported stock ₹4.00 crore; approved exclusions ₹0.50 crore; eligible stock ₹3.50 crore;
- reported receivables ₹3.00 crore; approved exclusions ₹0.80 crore; eligible receivables ₹2.20 crore;
- approved stock margin 25%, receivable margin 30%; creditor treatment already included once in exclusions;
- proposed DP = ₹3.50×0.75 + ₹2.20×0.70 = ₹4.165 crore;
- sanctioned cap ₹5.00 crore; proposed usable cap ₹4.165 crore;
- outstanding ₹3.60 crore; indicative headroom ₹0.565 crore before other blocks/sublimits;
- compare with active bank DP separately. This is not a universal bank formula or authorisation to draw.

Out-of-order bank CC rule profile must distinguish continuous excess against applicable limits/DP, no-credit period and insufficient credits to service interest. Use current lender-approved interpretation of [S19], including day-end/boundary tests; do not assume a covenant breach itself makes an NPA. Stale-stock and delayed-renewal consequences require separate rule paths, not an invented generic “90 days for everything.”

Obligation states: draft → reviewed → active → superseded/retired.
Evidence states: not due, due, received, incomplete, verified, rejected, superseded.
Finding states: compliant, near-threshold, indeterminate, potential breach, confirmed breach, waived-for-scope, cure pending, remediated.
Facility states: application, appraisal, approved, documentation, ready, active, review due, restricted-by-authorised-decision, closed. Stress/watchlist/classification remain separate attributes.

No state may jump to confirmed/waived/closed solely because a model suggests it. Capture role, permission, decision reason and evidence. The submitter cannot approve their own material change.

## 9. AI and ML allocation

| Capability | Use | Safeguards | Initial status |
|---|---|---|---|
| OCR/layout recognition | scan-to-text and tables | quality thresholds, page evidence, human review | build |
| Document classification | identify type/period | uncertainty, duplicate checks | build |
| Clause extraction | propose obligations and fields | schema, source locations, no invented defaults | build |
| Financial spreading | propose mappings | deterministic totals and checker | limited build |
| Evidence-backed memo | explain reviewed findings | citations, no added facts | build after rules |
| Anomaly prioritisation | suspicious changes/behaviour | explain signal; no fraud conclusion | rules first |
| RF/XGBoost risk ranking | predict defined future event | lender-approved labels, temporal testing and model governance | later research |
| Covenant/threshold suggestion | assist renewal/origination | policy boundaries, credit approval, bias review | later research |

Random Forest (RF) and XGBoost plan: define target and horizon before collecting features; begin with transparent rule/logistic baselines; compare RF and gradient boosting only on adequately sized real labelled datasets. Candidate features include utilisation, credit/interest conduct, eligible receivable changes, evidence delays, approved covenant headroom and historic waivers. Use only information available at prediction time. A post-event waiver or future audit result cannot become an earlier feature.

Split by time and borrower/group to avoid leakage. Address missingness and imbalanced events. Assess precision at analyst capacity, recall, calibration, PR-AUC, subgroup error, stability and incremental value versus baseline. Feature-attribution tools explain model contributions, not causality. Register features/model/training data versions; independent validation; approved release; drift monitoring; rollback; kill switch. No synthetic pilot proves predictive credit accuracy.

CRISIL's future-tech ideas inform the roadmap but do not establish model accuracy or regulatory permission [S01]. Its summary is limited to section 2 and this roadmap; product requirements elsewhere are independent proposed design.

## 10. Blockchain assessment

Do not put blockchain in the MVP. First establish whether independent organisations actually need a shared record and cannot accept a trusted operator. Within one bank, signed append-only audit events and restricted storage are usually a simpler starting architecture.

Possible later use: permissioned evidence receipts among borrower, lender, auditor and security custodian, recording attestation time, status and version reference. Each participant sees only authorised information. Store sensitive documents and personal data off-chain; even hashes/identifiers can reveal or link information, so minimise, scope and assess them.

Blockchain does not prove a stock statement is true, remove legal title requirements, grant permissions, fix wrong borrower IDs or make private data safe. It adds governance, key management, participant onboarding, revocation, correction, retention and availability complexity.

Evaluate: who writes; who validates; who can view; how keys are revoked; how disputes/corrections work; how data is deleted/retained; legal admissibility; operator liability; who pays. Benchmark against a centrally operated signed evidence registry. Adopt only if multi-party incremental benefit exceeds costs and all affected institutions approve. No token, public chain, smart-contract sanction or automatic security enforcement.

## 11. Security architecture — resistant to manipulation and leakage

This is a proposed control baseline, not a promise of zero vulnerability or formal bank certification.

1. **Deployment:** separate synthetic demo from real-data environment. Offer bank-controlled isolated deployment/private approved environment; no default external network access. Maintain a subprocessor list and approved processing locations.
2. **Identity:** bank single sign-on, strong MFA, short sessions, least privilege. Separate borrower, RM, maker, checker, credit approver, legal, auditor, integration operator and platform administrator.
3. **Authorisation:** validate institution, portfolio, branch, facility, document and action at server level. User-supplied institution IDs are never trusted. Search, retrieval, exports and AI context enforce the same permissions.
4. **Separation:** one bank's records must never enter another's response, embeddings, cache, logs or model context. Prefer separate databases/buckets/keys for early production institutions; shared architecture requires demonstrated isolation.
5. **Cryptography:** TLS with approved modern settings, mutual authentication for service links where required, encrypted storage/backups, keys managed separately with rotation/revocation and bank-approved KMS/HSM. No home-made cryptography.
6. **Evidence integrity:** immutable original bytes and version IDs; cryptographic file checksums; reviewer-confirmed replacements. Signed append-only event records anchored in independently protected storage; hash chains alone cannot stop an administrator rewriting the entire chain.
7. **Four-eyes controls:** material mappings, rule versions, evidence overrides, waiver activation and limit recommendations require independent approval. Emergency access is time-limited and reviewed.
8. **Ingestion:** validate file types/content/size, scan malware, reject decompression bombs, isolate parsers, remove active content, block external-resource fetching and unsafe links.
9. **AI containment:** documents are untrusted input. Embedded instructions cannot trigger tools, alter rules, export data or override access. Read-only model context, structured output validation and separate approval boundary.
10. **Data minimisation:** mask unnecessary identity/account details; no secrets or full sensitive records in logs. No customer-data training by default; no cross-bank fine-tuning without lawful, explicit approved arrangements.
11. **Exports:** limited role permissions, field-level redaction, approval for bulk export, expiry and protected delivery. Watermarks support traceability but cannot prevent screenshots; endpoint/user controls remain needed.
12. **Operations:** independent audit logs, security monitoring, dependency inventories/SBOM, patch process, penetration testing, backup/restore drills, incident response, vendor exit and deletion verification. Bank-approved recovery time/data-loss targets, timed support access and defined incident-notification responsibilities are required; the bank owns applicable regulatory reporting decisions.
13. **Availability:** queue retries, safe failure, circuit breakers, stale-data labels and replay after restoration. Missing feed means unknown, never compliant.
14. **Residual risk:** insiders, authorised screenshots, bad source attestations and unknown vulnerabilities remain possible. Record likelihood, controls, owner and accepted residual risk.

Threat tests: cross-tenant ID substitution, privilege escalation, forged document substitution, unreviewed rule edits, prompt-injected PDF, export abuse, malicious upload, compromised integration credentials, stale feed, log tampering and failed recovery. Test actual enforcement, not the presence of a security checkbox.

Post-quantum migration can be a later cryptographic-agility requirement where a buyer requests it. Do not add unvalidated hybrid algorithms or claim “quantum-proof” protection in the first build.

## 12. Regulatory mapping and approval boundary

Research cut-off matters: 2025 institution-specific consolidated RBI directions and 2026 updates must be considered; do not rely only on old 2023 IT outsourcing or April 2025 master circulars. Maintain rule effective dates and institution applicability. Current exact regulatory text and commencement must be verified before production.

| Area | Source/status | Build consequence |
|---|---|---|
| Bank CC prudential controls | Commercial Banks IRACP Directions 2025, official page updated July 2026 [S19], binding within scope | approved deterministic freshness/conduct/review profiles; current classification source retained |
| Bank lending framework | Commercial Banks Credit Facilities Directions 2025, updated official listing [S20] | validate activity-specific conditions; no universal covenant policy |
| Outsourcing | Commercial Banks Managing Risks in Outsourcing Directions 2025 [S21] | customer bank retains responsibility; vendor due diligence, confidentiality, audit, resilience and exit arrangements |
| Technology/cyber | 2026 Commercial Banks cybersecurity/technology framework identified [S22]; effective/transitional details need legal verification | use current institution-specific security review; no claim all provisions already apply |
| KYC | Commercial Banks KYC Directions 2025 [S23] | import verified status and controls; do not replace legal/compliance review |
| NBFC | separate NBFC directions/profile [S24] | assess category/layer/activity; do not copy bank CC prudential definitions |
| AI governance | FREE-AI committee report [S25], recommendations; model-risk guidance identified as draft [S26] | governance design inputs, not blanket approval or final legal mandate |
| Personal data | DPDP Act/Rules and commencement notifications [S27] | identify applicable commenced provisions and transition; purpose/minimisation/access/retention controls now as design requirements |
| Digital lending | assess whether Cassandre's role/activity triggers relevant lender/LSP/digital-lending provisions | contract scope and actual processing determine applicability, not product name |
| IFSCA | applies where entity/activity falls within IFSC regime | Indian domestic bank CC pilot does not become IFSCA-regulated because of an interview |

DPDP has staged commencement; do not label every future duty as already effective on the research date. Legal mapping must include Act sections as well as Rules. Corporate financial information can contain personal data; banking confidentiality and contractual controls also matter.

“Regulated manner” is achieved through specific lawful data access, institution-approved controls and applicable obligations. There is no universal RBI approval for AI covenant software established by this research. Human oversight alone does not make a design compliant.

Outsourcing classification is activity-specific: a software licence is not automatically a material IT outsourcing arrangement. Hosted or managed processing requires separate assessment. NBFC IT-outsourcing scope differs by layer; verify the current NBFC outsourcing directions [S30].

Production gate: legal/compliance determines applicability; risk approves calculations/models; business approves process/authority matrix; IT validates interfaces and support; information security approves deployment/testing; procurement/vendor risk approves arrangements; operations signs off on reconciliation and fallback. Formal regulator approval, if any, depends on actual activity and applicable law, not a generic requirement added by Cassandre.

## 13. Architecture and data model

Proposed first implementation: modular monolith, relational database, protected object storage, job queue/workers and web application. Avoid microservice complexity until scale/isolation needs justify it. Suggested stack: Python/FastAPI for APIs and deterministic rules, PostgreSQL for structured records, TypeScript/React for UI, bank-compatible object storage and approved identity provider. Versions/licences/provider security must be checked at implementation. No cloud or AI vendor is pre-approved by this specification.

Modules: Intake/import; document/evidence; financial spreading; rule registry; DP/covenant calculation; workflow/approvals; conduct/EWS signals; renewal/closure; audit/export; security/administration. Adapter packages separate BOB, Union and NBFC profiles. Bank brand changes must not alter calculation code secretly.

Minimum entities:

- Institution, InstitutionProfile, Branch, UserRole, AuthorityGrant;
- Borrower, LegalEntityRelationship, Facility, Application, SanctionVersion;
- Document, DocumentVersion, SourceReference, PhysicalCustodyReference;
- ExtractedField, VerifiedField, EvidencePeriod, Reconciliation;
- Obligation, ObligationVersion, EligibilityRuleSet, CalculationRun, CalculationInput;
- LedgerSnapshot, StockLine, ReceivableLine, CreditorAdjustment;
- Finding, Case, Decision, Approval, Waiver, Amendment, CureTask;
- ReviewCycle, SecurityAsset, InsuranceEvidence, ClosureChecklist;
- ModelRegistry, ModelPrediction, FeedRun, AuditEvent, RetentionPolicy.

Every business object carries institution scope; records needing branch/facility scope carry it explicitly. Monetary fields use Decimal, dates have effective/observed/received distinctions. Documents maintain original hash; decisions link the exact rule/data versions used.

Internal API example (Cassandre API, NOT a bank API): POST /imports; GET /facilities/{id}/evidence; POST /extractions/{id}/review; POST /rule-versions/{id}/submit; POST /rule-versions/{id}/approve; POST /facilities/{id}/calculations; GET /cases/{id}; POST /cases/{id}/decisions; GET /audit-packs/{id}. Implement role/scope/approval checks and idempotency on relevant mutations.

Background events: evidence received, verified, rule approved, feed completed, reporting date reached, amendment approved, waiver expired, cure overdue, review due, closure approved. Use reliable transaction/outbox patterns; retried events must not create duplicate cases or double-count evidence. Recalculate affected facilities only, preserve previous run and clearly display changed result.

## 14. User experience

Borrower: use existing bank channel first; optional portal only if approved and it replaces a channel. Clear requested document, period, reason and upload status. No internal risk memo exposure.
RM: one facility page with due evidence, conduct changes, borrower interactions and unresolved cases.
Maker: source and extracted value side by side; incomplete inputs; proposed calculations.
Checker: changed fields/rules, evidence and comparison with bank result.
Approver: authority-aware decision pack with alternatives, exposure, exact finding and follow-up.
Legal: contract conflicts and proposed interpretation for approval.
Audit: reproducible decision trail and scoped export.
Operations: feed reconciliation, stale data and approved downstream update requests.

Each result shows evidence period, last import, verification state, rule version and whether the bank implemented the recommendation. Avoid unexplained “AI risk score” as the main screen. Give missing evidence and confirmed failure different labels and colours.

## 15. Incumbent comparison — patterns to implement independently

| Vendor | Public scope | Pattern Cassandre should adopt | Caveat |
|---|---|---|---|
| Finacle [S16] | enterprise limits/collateral/covenant management | connected borrower/facility/security records, limits hierarchy and versioned conditions | module capability is not proof of BOB/Union installation or configuration |
| Newgen [S17] | commercial origination, document/workflow, post-disbursement monitoring | structured evidence lifecycle, task routing, inspection/renewal cases | do not claim vendor marketing outcomes are independently achieved |
| Nucleus [S18] | corporate origination/servicing, exposures and covenant functionality | robust servicing integration, corporate account view and communication history | proprietary implementations cannot simply be copied |

Do not attempt to reproduce the entire CBS, document repository and collections stack. Build independent interfaces/patterns, respect IP/licensing, and measure incremental benefit versus configuring incumbents. Their mature offerings make integration and evidence resolution a more credible differentiation than another reminder dashboard.

## 16. Simulated institutional persona review

These perspectives were requested by the founder and evaluated as simulated reviews. They make no statement about each institution's private practices.

| Persona | Principal challenge | Mandatory design response |
|---|---|---|
| BOB credit-monitoring officer | Will this add uploads/manual work to an existing CC process? | reuse portal/system records; compare proposed DP with bank result; selected scheme controls only |
| Union credit/operations officer | Can scans, LAS records and Finacle entries be linked reliably? | account identifiers, document index, import reconciliation and explicit unscanned gaps |
| JPMC risk/control reviewer | Can every material finding and override be reproduced? | immutable inputs, rule/model versions, separate approval, independent validation |
| Morgan Stanley security/resilience reviewer | What happens after compromise or interrupted feeds? | isolation, restricted exports, independently protected audit, tested restore, stale-state handling |
| Goldman Sachs model reviewer | Is the score genuinely predictive or leaking future data? | time/group splits, baselines, calibration, cost-sensitive measures and out-of-time testing |
| Finacle integration architect | Are you duplicating account truth or inventing interfaces? | CBS remains account source; bank-approved adapters and reconciliation |
| Newgen workflow architect | Are documents and decisions connected to tasks? | evidence-to-case links, due-date ownership, controlled state transitions and amendments |
| Nucleus servicing architect | Do facility changes propagate consistently? | effective-dated terms, sublimits, schedule/event handling and clear downstream acknowledgements |

Consensus: full lifecycle context is appropriate, but first value should be a complete CC monitoring cycle with dependable ingestion. Forecast models and multi-party blockchain come after validated records, rules and workflow.

## 17. Sequential build backlog and exit criteria

### Phase 0 — Bank discovery and source mapping
Deliver actual screen/document walkthrough for one CC account, system/data inventory, permissions, scheme/contract rules, authority matrix and confirmed baseline. No production adapter without this input. If bank access is unavailable, use an explicitly synthetic reference profile and label it.

### Phase 1 — Secure foundation and synthetic end-to-end shell
Deliver identity/roles, institution isolation, database migrations, object storage, audit, lifecycle screens and synthetic accounts. Exit: cross-tenant/role tests fail closed; secrets absent; full synthetic application-to-closure navigation works.

### Phase 2 — Read-only imports and evidence linking
Deliver CSV/JSON fixture imports, document bulk intake, identifier matching, reconciliation, safe parsers, versioning and source view. Exit: duplicate import is idempotent; stale/missing rows visible; originals retained; unsafe upload blocked.

### Phase 3 — Reviewed rule register
Deliver extraction proposals, field review, final-term reconciliation, rule authoring and independent activation. Exit: unapproved rules cannot run authoritatively; amendment/waiver effective-date tests pass.

### Phase 4 — DP and evidence monitoring
Deliver contract-specific eligibility, Decimal calculations, statement checks, due queues and bank-result comparison. Exit: approved golden calculations match; missing input is indeterminate; changed evidence creates traceable new run; no live limit write.

### Phase 5 — Covenants, exceptions and renewal feedback
Deliver reviewed financial/non-financial tests, case/waiver/cure workflow, draft decision packs, renewal record and closure checklist. Exit: authorised end-to-end historic replay, expired waiver does not suppress later breach, self-approval blocked.

### Phase 6 — Bank-approved interfaces and shadow pilot
Deliver approved bank adapter, access controls, operational support and feed monitoring. Exit: 2–3 actual reporting cycles (proposed) compared with current workflow; correction/false-positive workload measured; institution-approved go/no-go.

### Phase 7 — Production assurance
Deliver current legal mapping, security assessment, independent testing, DR/exit drills, support SLA and approved rollout. Exit: all production gates signed; no unaddressed critical security issue; rollback proven; audit pack reproducible.

### Phase 8 — Predictive ML research
Requires labelled historical data and model-governance owner. Compare RF/XGBoost with baselines; shadow predictions only before approved use. Reject if no incremental value or unmanageable false alerts.

### Phase 9 — Optional multi-party evidence network
Requires several participating institutions and a demonstrated shared-trust problem. Benchmark signed central registry vs permissioned ledger; implement only the chosen justified option after privacy/legal review.

Suggested repository layout:

```text
apps/web/
services/api/
services/workers/
domain/facilities/
domain/evidence/
domain/rules/
domain/calculations/
domain/workflow/
adapters/mock/
adapters/bob/README-discovery-required.md
adapters/union/README-discovery-required.md
profiles/bank-cc/
profiles/nbfc-working-capital/README-validation-required.md
security/
tests/golden/
tests/permissions/
tests/integration/
docs/decisions/
docs/source-register/
fixtures/synthetic/
```

Claude must finish and test each phase before expanding scope. Report implemented, mocked, blocked and deferred capabilities separately. Production bank integration is not “done” because a mock endpoint works.

## 18. Meaningful acceptance scenarios

1. Import one facility twice: no duplicated facility/evidence/case.
2. Wrong borrower ID on a scan: not silently linked by name.
3. Rupees vs lakh mismatch: validation stops computation.
4. Missing statement pages or unresolved margin: indeterminate DP.
5. Eligibility boundary at approved debtor-age cut-off: correct inclusive/exclusive result.
6. Creditors already excluded from stock: no second deduction.
7. Mid-period amendment: historical test uses old terms, future test uses approved effective version.
8. Limited waiver: only named obligation/test period is waived; new cure is tracked.
9. Feed outage: stale warning; no clean-compliance assertion.
10. Prompt injection in agreement: no external request, tool action or rule edit.
11. Borrower/other-bank user requests internal credit memo: denied server-side, including search/AI retrieval.
12. Maker attempts self-approval: denied.
13. Document replacement: original and replacement preserved; previous result reproducible.
14. Admin changes logs/storage: independently protected event integrity check detects divergence within tested limits.
15. Zero balance with linked commitment/security: closure release remains pending.
16. Restore to isolated environment: evidence, versions and decisions reconcile.
17. Nbfc profile receives bank CC rule: explicit rejection until profile validation.
18. Model uses post-event features: training pipeline detects prohibited temporal leakage.

Pilot metrics: active staff minutes per account, one-time preparation cost, missing-evidence rate, import reconciliation failures, extraction precision/recall on reviewed material fields, calculation discrepancies, false-alert rate, time-to-disposition and audit-pack completeness. Establish actual baselines. Do not claim NPA reduction from a small short pilot. Zero silent material calculation errors is a release expectation on approved fixtures, not a guarantee against every future error.

## 19. Immediate founder actions

1. Ask both banks for a walkthrough of one recently sanctioned CC and one recent exception, including actual storage/retrieval screens.
2. Obtain approved anonymised/synthetic examples: application, final sanction, agreement, amendment, stock/receivable schedule, DP worksheet, ledger snapshot, insurance and decision record.
3. Confirm whether existing APIs/exports can supply those exact records; quantify scan-only gaps.
4. Identify business owner, credit checker, IT integration owner and security/vendor-risk contact.
5. Choose one institution/profile for first implementation, with comparison adapter for the other; avoid two-bank production rollout simultaneously.
6. Give Claude this file and authorise Phase 1 synthetic implementation after Phase 0 assumptions are labelled.

## 20. Starter prompt for Claude

> Read this specification in full. Create an implementation plan and assumption register. Build Phases 1–5 as a synthetic, read-only reference implementation with one connected application-to-closure workflow. Do not invent BOB or Union APIs or label mocks as bank integration. Implement roles, institution isolation, source-linked evidence, reviewed rule versions, deterministic DP/covenant calculations, exception/waiver/cure workflow and audit replay before adding predictive models. Start with the worked fixture and acceptance scenarios. Use feature flags for external models, communications, production connectors and writes; keep them disabled. Identify bank discovery and regulatory gates explicitly. After each phase, show tests, limitations and the next concrete deliverable. Do not put real customer data into prompts or source control.

## 21. Source register

Links are primary sources except the inaccessible user-supplied Grok share. Access/freshness and applicability limitations are stated above. Marketing establishes offered capability, not independent performance. Tender specifications establish stated architecture/requirements at their date, not completed deployment.

- **S01:** [CRISIL, Raising your covenant monitoring nous, 26 April 2024](https://www.crisil.com/en/home/our-analysis/crisil-blogs/2024/04/raising-your-covenant-monitoring-nous.html). Read; global analysis; future RF/XGBoost suggestions.
- **S02:** [User-supplied Grok share](https://grok.com/share/c2hhcmQtMw_8d72f144-04b3-450d-8cdf-553443e86a26). Retrieval failed; excluded from substantive evidence.
- **S03:** [BOB archived corporate tenders](https://bankofbaroda.bank.in/tenders/corporate-office-archived). Finacle customisation evidence, not complete module inventory.
- **S04:** [Union FY2024–25 annual report](https://www.unionbankofindia.bank.in/pdf/union-bank-ar-2024-25-eng-final.pdf). Official indexed text identifies Finacle upgrade; date-specific; some full fetches timed out.
- **S05:** [BOB Digital MSME Loan](https://bankofbaroda.bank.in/business-banking/msme-banking/loans-and-advances/digital-msme-loan). Read; scheme-specific. The page displays older MSME classification thresholds, so do not copy those as current legal definitions. Current product limits/rules must be refreshed before use.
- **S06:** [BOB Digi Udyam](https://bankofbaroda.bank.in/business-banking/msme-banking/loans-and-advances/cash-flow-based-digital-mse-micro-and-small-enterprise-scheme). Read; digital evidence inputs/product-specific.
- **S07:** [Union RTI disclosures](https://www.unionbankofindia.bank.in/en/common/rti). LAS reference; not the internal CC manual.
- **S08:** [Union MSME Superfast](https://www.unionbankofindia.bank.in/en/details/union-msme-superfast). Named scheme; do not generalise its sole-banking/rating/turnover requirements.
- **S09:** [BOB FY2017–18 directors report](https://bankofbaroda.bank.in/hi-in/shareholders-corner/financial-reports/financial-report-2017-18/directors-report). Historical customer-document digitisation only.
- **S10:** [Union 2022–23 scanner/printer RFP](https://www.unionbankofindia.bank.in/tenderfiles/rfp%20for%20rate%20contract%20for%20printers%20and%20scanners%20final3.pdf). Read; Newgen document software evidence, historical.
- **S11:** [Union official Ubi Scanner listing](https://play.google.com/store/apps/details?id=com.newgen.nemf.client.ao). Read; staff scanning/uploading, not proof every loan is scanned.
- **S12:** [bob Open Banking](https://bankofbaroda.bank.in/digital-products/instant-banking/bob-open-banking). Official API offering; loan-file access unverified.
- **S13:** [Union 2022 integration procurement clarification](https://www.unionbankofindia.bank.in/tenderfiles/corrigendum%20final%20upload%2001.11.2022.pdf). Official indexed Finacle/API gateway/DMS/interface evidence; historical.
- **S14:** [BOB internet banking](https://bobibanking.bankofbaroda.bank.in/). Stock-statement update feature; completeness/integration unknown.
- **S15:** [NeSL Digital Document Execution](https://www.nesl.co.in/digital-document-execution-dde/). Supported digital execution; not universal replacement of originals/registration.
- **S16:** [Finacle limits, collateral and covenants suite](https://www.finacle.com/solution/limits-collaterals-and-covenants-management-suite/). Read; vendor offering.
- **S17:** [Newgen commercial loan management](https://newgensoft.com/in/solutions/industries/financial-institutions/commercial-banking/loan-management-system/). Read; vendor offering.
- **S18:** [Nucleus corporate lending](https://www.nucleussoftware.com/corporate-lending/). Read; vendor offering.
- **S19:** [RBI Commercial Banks IRACP Directions 2025](https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=13146). Official retrieved earlier in research; July 2026 update shown; refresh at implementation.
- **S20:** [RBI Commercial Banks Credit Facilities Directions 2025](https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=13156). Official reference; latest full-page retrieval timed out. Verify current clauses before activation.
- **S21:** [RBI Commercial Banks Managing Risks in Outsourcing Directions 2025](https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=13139). Read; current institution-specific basis.
- **S22:** [RBI Commercial Banks cybersecurity framework reference, 2026](https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=13643). Identified in research; exact commencement/transitional clauses require verification.
- **S23:** [RBI Commercial Banks KYC Directions 2025](https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=13141). Official retrieved; validate customer-specific application.
- **S24:** [RBI NBFC Credit Facilities Directions 2025](https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=12957). Verify full current NBFC prudential/outsourcing profile in addition to credit facilities.
- **S25:** [RBI FREE-AI committee report](https://rbidocs.rbi.org.in/rdocs/content/pdfs/FREEAIR13082025_ANVI.pdf). Committee recommendations, not blanket binding authorisation.
- **S26:** [RBI draft model-risk guidance release](https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx?prid=63006). Draft identified June 2026; final status must be checked before production.
- **S27:** [MeitY DPDP Rules and associated notifications](https://www.meity.gov.in/documents/act-and-policies/digital-personal-data-protection-rules-2025-gDOxUjMtQWa?pageTitle=Digit). Staged commencement; use gazette/corrigenda and Act commencement, not old draft explanatory notes.
- **S28:** [SBI FY2023–24 annual report](https://sbi.bank.in/documents/17836/39646794/Annual_Report_2024.pdf). Digi Vault integration example; not evidence of BOB/Union implementation.
- **S30:** [RBI NBFC Managing Risks in Outsourcing Directions 2025](https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=12941). Current institution-specific source; IT-specific scope differs by layer.
- **S31:** [MeitY final DPDP Rules Gazette](https://www.meity.gov.in/static/uploads/2025/11/53450e6e5dc0bfa85ebd78686cadad39.pdf). Rule commencement is staged; separately verify Act sections and corrigenda.
- **S32:** [RBI FREE-AI official report page](https://rbi.org.in/Scripts/PublicationReportDetails.aspx?ID=1306). Committee report; no blanket algorithm approval.
- **S29:** [NIST blockchain overview, IR 8202](https://csrc.nist.gov/pubs/ir/8202/final). Architecture/trust tradeoffs; not legal approval.

Final readiness statement: this document is sufficient to initiate a synthetic build and structured bank discovery. It is not sufficient to claim production connectivity, all-ambiguity detection, validated predictive scoring or regulatory certification.

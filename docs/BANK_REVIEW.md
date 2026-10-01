# Simulated Bank of Baroda / Union Bank credit-administration review

Research and code review: 1 October 2026. These analytical personas do not represent either bank or imply access to private procedures.

## Implemented correctness fixes

- Monetary inputs reject NaN/infinity and require explicit supported units. DP validates nonnegative reported inputs and caps, consistent currency/unit across all inputs, finite margins in [0,1], and exclusions no larger than the corresponding reported assets. Invalid evidence raises a validation error, rather than manufacturing a negative borrowing base. Missing evidence remains indeterminate.
- Negative headroom remains valid: outstanding can exceed calculated availability and must not be clipped to zero.
- Covenant warning bands apply only to passing values. A failing value within a warning band remains POTENTIAL_BREACH, enabling properly scoped waiver handling; no automatic confirmed breach.
- Decimal-only arithmetic and the specification's golden fixture remain unchanged. No generic rounding rule or universal lender margin is introduced.

## Material unresolved domain gaps

1. DP currently aggregates exclusions. It cannot verify creditor deductions were applied only once, debtor ageing, disputed/related-party receivables, category eligibility or sublimits from its inputs. The prior claim of double-deduction coverage from a single subtraction is insufficient; line-level evidence and approved rule ordering are required.
2. Calculation inputs have no source period, completeness, verified status or current approved rule-version proof. Arithmetic alone must not be presented as a validated operational DP decision. The application layer must block stale/incomplete/unapproved inputs.
3. No bank-CC IRACP conduct engine is implemented here. It requires complete daily balances, effective limits/DP, credits and interest history; incomplete feeds must be indeterminate. Distinguish 90-day continuous excess, no-credit and insufficient-credit tests, including the inclusive day-end window. Do not apply bank-specific rules to NBFCs automatically.
4. Contract ratio definitions, reporting period and waiver authority must be sourced and reviewed; the sample covenant is synthetic. No live CBS write or authority to draw is implied.
5. Physical documents, unscanned records and unsupported bank interfaces cannot be solved by arithmetic. There must be explicit evidence-gap and reconciliation workflows.

## Current official regulatory source

[RBI Commercial Banks IRACP Directions 2025, updated 1 July 2026](https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=13146), retrieved 1 October 2026:
- Paragraph 5(7): distinct out-of-order conditions and inclusive 90-day interest window.
- Paragraphs 15–21: current stock statement, three-month age boundary, review/renewal controls and CBS/MIS capture. Calendar months must not be silently converted into 90 days.
- Bank policy and approved facility conditions remain necessary for implementation. Covenant breach is not an NPA classification rule.

## Official bank architecture and workflow evidence

- [BOB Digital MSME Loan](https://bankofbaroda.bank.in/business-banking/msme-banking/loans-and-advances/digital-msme-loan): selected digital working-capital journey; product-specific inputs and annual review. Its displayed older MSME classifications must not be used as current legal thresholds.
- [BOB Digi Udyam](https://bankofbaroda.bank.in/business-banking/msme-banking/loans-and-advances/cash-flow-based-digital-mse-micro-and-small-enterprise-scheme): digital footprint-based lending including CC. This does not prove universal secured-CC automation.
- [BOB Open Banking](https://bankofbaroda.bank.in/digital-products/instant-banking/bob-open-banking) and [DigiNext](https://bankofbaroda.bank.in/digital-products/merchant-payment-solutions/baroda-diginext): API/host-to-host capabilities; not a confirmed internal loan-document interface.
- [Union scanner procurement, 2022–23](https://www.unionbankofindia.bank.in/tenderfiles/rfp%20for%20rate%20contract%20for%20printers%20and%20scanners%20final3.pdf): explicitly identifies Newgen OmniDocs/OmniScan. Historical evidence, not proof all files are digitised.
- [Official Union Ubi Scanner](https://play.google.com/store/apps/details?hl=en&id=com.newgen.nemf.client.ao): scanning/uploading by branch employees, October 2025 update. Coverage and extraction access remain unverified.
- [Union architecture procurement clarification, 2022](https://www.unionbankofindia.bank.in/tenderfiles/corrigendum%20final%20upload%2001.11.2022.pdf): existing Finacle/API Gateway/DMS mentioned; no Cassandre access promised.
- [Union MSME Superfast](https://www.unionbankofindia.bank.in/en/details/union-msme-superfast): selected digital GST-linked scheme; scheme controls must not be universalised.
- [Union delegated powers disclosure](https://www.unionbankofindia.bank.in/en/common/rti): approval authority and credit committees; actual lender delegation configuration required.

Finacle is an Infosys product; TCS BaNCS is separate. Neither institution's complete private CC SOP was established through public sources.

## Validation

Focused calculation regression suite: `uv run pytest tests/test_drawing_power.py tests/test_covenant.py -q` — 40 passed. Tests cover the approved synthetic fixture, invalid numerical evidence, cross-unit inputs, negative headroom, contractual boundary precedence and waiver behavior. This is not validation against actual bank DP worksheets.

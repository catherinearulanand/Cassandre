# Cash-credit account conduct: advisory prototype

This module is a simulated Indian commercial-bank credit-risk review perspective. It does not represent Union Bank or Bank of Baroda, and their internal implementations have not been inspected.

## Public rule basis

Source: [RBI Commercial Banks IRACP Directions 2025, updated 1 July 2026](https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=13146), paragraph 5(7), retrieved 1 October 2026. The engine checks continuous excess for 90 days, absence of credits for 90 days, and credits insufficient to cover interest in the inclusive 90-day window. Stock-statement irregularity and renewal rules require separate checks. Covenant breaches do not themselves establish these conditions. This module does not produce an NPA or SMA classification.

## Evidence contract and integration location

The existing bank system supplies certified day-end balances, credits, interest and effective sanctioned limits and active drawing power. Cassandre consumes an approved read-only extract after reconciliation. A proposed drawing-power calculation is not an active bank limit. Currency is INR and every amount is explicitly in rupees using Decimal; convert and reconcile upstream. Every calendar day needs a certified record, including non-working-day carry forwards where the bank approves them. Borrower-uploaded transaction summaries cannot establish feed completeness.

`evaluate_account_conduct` takes `DailyConduct` records and an explicit `as_of` business date. Feed completeness defaults to false. Missing dates, duplicate dates, future records, nonfinite values, negative credit/interest/limits and absent source references make every test indeterminate. A negative outstanding balance is permitted because the account may have a credit balance.

The effective availability cap is the lesser of sanctioned limit and active drawing power, using the bank's effective values on each date. This interpretation requires bank sign-off before enabling a live adapter. Credit/interest checks use the current balance being strictly below the cap; exact equality is explicitly indeterminate pending bank-approved interpretation. Outputs include dates, arithmetic totals, capped consecutive excess count and source references. A 90-day observation window cannot state the actual length of an earlier uninterrupted streak.

## Deliberate limits

This is a pure function, not an API route or production feed connector. There is no outbound CBS write. `potential_trigger` routes to authorised review; `not_triggered` only means these three checks did not trigger with the supplied evidence. Bank-wide asset classification, cross-facility borrower linkage, SMA reporting, credit reversals, circular transactions, backdated adjustments, holiday processing, renewals and aged-stock irregularity need bank discovery and their own approved controls. No NBFC profile is accepted. A waiver of a contractual covenant must not suppress these conduct signals.

## Verification

Run `.venv/bin/python -m pytest tests/test_account_conduct.py -q`.

The tests cover day 89/90 boundaries, changing active DP, streak reset, inclusive interest date, exact interest coverage, independent zero-credit tests, malformed/missing/stale evidence, source absence, unsupported NBFC profile, and exact-limit ambiguity. Actual bank-certified golden examples and independent regulatory review remain required.

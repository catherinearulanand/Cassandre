# Cassandre CC

A synthetic, read-only-origin prototype of the India cash-credit lending
monitoring platform described in `Cassandre_CC_Claude_Build_Specification.md`.
All data is simulated — see `docs/ASSUMPTIONS.md` and `docs/STATUS.md` for
exactly what is real, what is mocked, and what four of the spec's ten
phases cannot be completed by a coding session at all (bank discovery,
bank-approved adapters, production security/legal sign-off, multi-party
blockchain — see `docs/STATUS.md`).

## Run it

```bash
uv sync
uv run uvicorn cassandre_cc.api.main:app --reload --port 8740
```

Open `http://127.0.0.1:8740`. State persists to `data/store_snapshot.json`
across restarts; delete that file to reset to the synthetic seed.

## Test it

```bash
uv run pytest -q
```

55 tests, covering every acceptance scenario in spec §18 that this slice
implements, at the real HTTP layer.

## What you'll see

Two synthetic facilities:

- **Aranya Textiles** — two periods and a mid-period rule amendment.
  2026-07 reproduces the build specification's own worked drawing-power
  example exactly (proposed DP ₹4.165cr, headroom ₹0.565cr, under rule
  v1). 2026-08 uses an amended rule v2 and would breach its covenant, but
  a waiver scoped to exactly that period is already approved — switch the
  period selector to see both.
- **Konark Distributors** — this period's receivables figure hasn't been
  received yet, so the drawing-power result is **indeterminate**, not zero.

From the dashboard you can: import a new period's financials (idempotent —
re-importing the same content is a no-op), propose and approve a new rule
version (watch the old one get superseded, not deleted), propose/approve a
covenant waiver, watch an unwaived breach open a cure task, decide a
renewal, and walk a facility through its closure checklist (closing is
blocked server-side until every item is checked). A pending maker-checker
case lets you try approving as the original submitter (denied, with the
exact reason) or as an independent checker (succeeds, audited).

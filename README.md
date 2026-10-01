# Cassandre CC

A synthetic on-premises cash-credit monitoring prototype for Indian commercial banks. Cassandre sits beside origination, document and core-banking systems; it produces reviewed monitoring records and does not write bank limits, payments or asset classifications.

**The complete pre-sanction-to-closure specification is not implemented.** See [repository audit](docs/REPOSITORY_AUDIT.md) for all 24 steps and phase-by-phase gaps, [status](docs/STATUS.md), [security review](docs/SECURITY_REVIEW.md), and [on-premises deployment](docs/ON_PREM.md). No real BOB/Union integration or institutional approval is claimed.

## Local evaluation

```bash
uv sync --locked
# Configure independently issued hashed bearer credentials first; see docs/ON_PREM.md.
export CASSANDRE_AUTH_FILE=/absolute/path/to/auth.json
uv run uvicorn cassandre_cc.api.main:app --host 127.0.0.1 --port 8740 --workers 1 --no-access-log
```

Open `http://127.0.0.1:8740` and enter your operator-issued token. Tokens remain in page memory. No credentials means protected APIs reject access. Use separate maker/checker identities. One process only, local POSIX filesystem; `--reload` and multiple workers are deliberately unsupported. State defaults to `data/store_snapshot.json`; do not delete it to repair business records.

For an isolated container evaluation, follow [ON_PREM.md](docs/ON_PREM.md). Docker packaging is provided but container execution was not tested in the review environment because Docker was unavailable. The active database is still a bounded JSON snapshot; proposed PostgreSQL DDL is not connected to the runtime.

## Verification

```bash
uv run pytest -q
```

Tests cover calculations, authenticated API boundaries, independent approvals, historical versions, import revisions, immutable calculation receipts, advisory 90-day account conduct, persistence failure and recovery. They do not certify production compliance, predictive model accuracy or every acceptance scenario in the full specification.

## Demonstration scope

Aranya Textiles reproduces the specification's synthetic ₹4.165 crore drawing-power calculation and ₹0.565 crore headroom. Konark Distributors demonstrates missing evidence returning indeterminate. Margins and the headroom covenant are illustrative; they are not bank policy. Proposed DP is separate from bank-authorised active DP.

The dashboard supports aggregate financial imports, versioned rule proposals and approvals, scoped waivers, cure tasks, local renewal decisions and independently controlled closure. Daily account conduct is a separate pure advisory engine requiring complete approved day-end data. Shadow score is a labelled heuristic, not trained ML. Bank adapters, production assurance and optional multi-party blockchain remain external-gated work.

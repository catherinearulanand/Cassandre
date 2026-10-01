# On-premises synthetic evaluation deployment

This is a local single-process prototype. It is not approved for bank production or real customer records. The JSON store is unencrypted, all request state is held in memory and requests serialize. Host encrypted storage, independently retained audit records, SSO, production database and bank approvals remain requirements. No bank APIs or outbound AI services are configured.

## Reviewed controls and limits

- POSIX advisory writer lock rejects a second cooperating process on the same snapshot. Exactly one worker; no reload process in deployment. Never use network/shared filesystems or multiple hosts with this store.
- Snapshot uses versioned checksum envelope, restrictive file permissions, file fsync, same-filesystem atomic replacement and directory fsync. Checksum detects accidental corruption, not deliberate forgery. Invalid snapshot stops startup instead of resetting records.
- Request state and response are buffered, successful mutations persist before success is returned, errors roll back. Disk failure returns 503 and fail-closes further requests until operator recovery. A failure after replacement can leave the new disk snapshot committed while memory rolled back; inspect/restore before restarting. This is not a transactional database or disaster-proof storage.
- Container runs UID/GID 10001 with read-only image, dropped capabilities, no new privileges, temporary scratch filesystem and persistent `/data` volume. Named volume should inherit image directory ownership; verify write access on the target host. A bind mount must be provisioned by an operator with matching owner/mode.
- Localhost-bound port; internal Docker network removes ordinary external routing. Host firewall/egress controls are still needed; Docker isolation is not proof of bank-grade network security. Runtime has no package installation or third-party network dependency.
- Python dependencies have exact versions and hashes exported from `uv.lock`. Base image version is pinned by tag only; production build must provide a reviewed digest through `PYTHON_IMAGE`. Docker is absent in the current development environment: container build, health and host network behaviour are not validated here.

## Prepare credentials

Create `secrets/auth.json` outside source control. It contains a JSON list of `{actor, token_sha256, institution_id, roles}` entries. Use independently generated high-entropy bearer tokens, store only their SHA256 digests in this file, and give maker/checker separate people and credentials. A reader entry must have only `reader`; never distribute admin/checker credentials to borrowers. See SECURITY_REVIEW.md for complete authentication behaviour. File must be readable by container UID 10001; don't embed tokens in images or compose environment strings. Compose local secrets are mounted files, not automatically encrypted secret storage.

## Build and start

On an approved connected build host, review the lockfile and image, build, scan and transfer the image to the isolated evaluation host. No real loan data is needed to build.

```bash
# Set PYTHON_IMAGE to the bank-approved python image reference including @sha256 digest.
docker compose build
docker compose up -d --no-build
curl --fail http://127.0.0.1:8000/healthz
```

Verify auth-free health contains no sensitive records; record image digest and git commit. Never expose plain HTTP to a bank network; add bank-controlled TLS termination, restricted host access and SSO integration before network use. Do not run `docker compose down -v`: that deletes the persistent volume.

## Backup and restore

Stop the service first. The tool refuses backup/restore while a cooperating writer holds the lock. Snapshot backup contains sensitive records when real data is later approved: encrypt backups and restrict operator access, and establish retention/deletion policies. This tool creates a checksummed ZIP bundle containing the snapshot and local `evidence/` originals. It does not back up credentials, external repositories or future object storage. ZIP is not encryption. Legacy raw snapshot restore remains supported but cannot restore originals. Conflicting existing originals fail restore; newer unreferenced files remain retained for operator reconciliation.

Local environment:

```bash
PYTHONPATH=src .venv/bin/python scripts/snapshot.py backup data/store_snapshot.json /approved-backups/snapshot-001.ccbackup
PYTHONPATH=src .venv/bin/python scripts/snapshot.py verify /approved-backups/snapshot-001.ccbackup
PYTHONPATH=src .venv/bin/python scripts/snapshot.py restore data/store_snapshot.json /approved-backups/snapshot-001.ccbackup
```

Container environment, after `docker compose stop cassandre`:

```bash
# /backups must be owned/readable by UID10001 and on encrypted operator-approved storage.
docker compose run --rm --no-deps -v /approved-backups:/backups cassandre python scripts/snapshot.py backup /data/store_snapshot.json /backups/snapshot-001.ccbackup
docker compose run --rm --no-deps -v /approved-backups:/backups cassandre python scripts/snapshot.py restore /data/store_snapshot.json /backups/snapshot-001.ccbackup
docker compose up -d --no-build
```

Use a unique backup filename. Never edit raw snapshots to repair business state. A legacy snapshot can be read and is upgraded on the next commit; unknown future schema is rejected. For downgrade rollback, retain the previous image AND its pre-upgrade verified backup. Restoring an older snapshot loses subsequent accepted decisions; reconcile them from independently retained evidence/audit logs. Current schema migrations do not support running old/new application versions concurrently.

Recovery drill: create a record, stop, backup, restart/mutate, stop, restore, restart, verify restored record/history and reconciliation. Tests cover successful copy/restore, checksum corruption, live-writer rejection, replace failure, rollback and 503 fail-closed. Container drill still requires target-host verification.

## Scaling path

`migrations/001_postgres_target.sql` is proposed evaluation DDL, **not wired to runtime and not executed/tested against PostgreSQL here**. It demonstrates tenant-composite references, decimal amounts, source documents, immutable input revisions/calculations, maker-checker decisions and audit/outbox boundaries. It is not a production migration.

Next: implement repository transactions against PostgreSQL, add migration tooling, schema tests, non-owner runtime roles and tested row-level security; persist business state, audit and outbox together. Add independently encrypted object storage and metadata reconciliation. Replace whole-store copying with row locks/version checks, idempotency keys and optimistic concurrency. Then add separate stateless API replicas and isolated OCR workers. Deliver outbox events at least once with deduplication, never promise exactly-once external effects. Size and load-test on actual authorised representative volumes before setting capacity claims. Bank adapters require documented bank-owned interfaces.

Primary references checked 1 October 2026: [Docker volumes](https://docs.docker.com/engine/storage/volumes/), [Docker networking](https://docs.docker.com/engine/network/drivers/bridge/), [pip hash-checked installs](https://pip.pypa.io/en/stable/topics/secure-installs/), [PostgreSQL constraints](https://www.postgresql.org/docs/current/ddl-constraints.html). These describe infrastructure mechanics, not regulatory approval.

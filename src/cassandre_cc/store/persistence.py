"""Atomic, checksummed local snapshot persistence. Single process only.

The checksum detects accidental corruption, not malicious authorised writes.
This is not an encrypted database or independent tamper-evident audit store.
"""

from __future__ import annotations

import json
import hashlib
import os
import tempfile
import contextvars
import typing
from dataclasses import asdict, fields
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from cassandre_cc.domain.entities import (
    AuditEvent,
    Borrower,
    ClosureChecklist,
    CalculationRun,
    CureTask,
    DocumentRef,
    EligibilityRuleSet,
    EvidenceItem,
    Facility,
    FacilityFinancials,
    FeatureSnapshot,
    ImportBatch,
    Institution,
    RenewalRecord,
    Waiver,
)
from cassandre_cc.store.memory_store import MemoryStore
from cassandre_cc.workflow.maker_checker import ApprovalCase

_COLLECTION_TYPES: dict[str, type] = {
    "institutions": Institution,
    "borrowers": Borrower,
    "facilities": Facility,
    "documents": DocumentRef,
    "evidence_items": EvidenceItem,
    "rule_sets": EligibilityRuleSet,
    "financials": FacilityFinancials,
    "financials_history": FacilityFinancials,
    "calculation_runs": CalculationRun,
    "approval_cases": ApprovalCase,
    "import_batches": ImportBatch,
    "waivers": Waiver,
    "cure_tasks": CureTask,
    "renewals": RenewalRecord,
    "closures": ClosureChecklist,
    "feature_snapshots": FeatureSnapshot,
}


def _encode(obj: Any) -> Any:
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"not JSON serialisable: {type(obj)!r}")


def _convert_value(value: Any, hint: Any) -> Any:
    if value is None:
        return None
    if typing.get_origin(hint) is tuple:
        return tuple(value)
    origin = typing.get_origin(hint)
    if origin is typing.Union:
        args = [a for a in typing.get_args(hint) if a is not type(None)]
        return _convert_value(value, args[0]) if args else value
    if isinstance(hint, type) and issubclass(hint, Enum):
        return hint(value)
    if hint is datetime:
        return datetime.fromisoformat(value)
    if hint is date:
        return date.fromisoformat(value)
    return value


def _dataclass_from_dict(cls: type, data: dict) -> Any:
    hints = typing.get_type_hints(cls)
    kwargs = {f.name: _convert_value(data[f.name], hints[f.name]) for f in fields(cls) if f.name in data}
    return cls(**kwargs)


# Saves inside a request are deferred until its response has been validated.
_deferred = contextvars.ContextVar("snapshot_deferred", default=False)


class PersistenceError(RuntimeError):
    """Snapshot is invalid or cannot be committed; never silently reseed."""


def payload_for(store: MemoryStore) -> dict[str, Any]:
    payload = {
        name: {key: asdict(value) for key, value in getattr(store, name).items()}
        for name in _COLLECTION_TYPES
    }
    payload["audit_events"] = [asdict(e) for e in store.audit_events]
    return json.loads(json.dumps(payload, default=_encode, allow_nan=False))


def _canonical(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def save(store: MemoryStore, path: Path, *, force: bool = False) -> None:
    if _deferred.get() and not force:
        return
    payload = payload_for(store)
    envelope = {"schema_version": 2, "sha256": hashlib.sha256(_canonical(payload)).hexdigest(),
                "payload": payload}
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temp_path = None
    try:
        # Same directory guarantees rename remains on one filesystem.
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".snapshot-", delete=False) as f:
            temp_path = Path(f.name)
            os.chmod(temp_path, 0o600)
            f.write(_canonical(envelope))
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_path, path)
        temp_path = None
        # Ensure rename is durable on local POSIX filesystems.
        fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except (OSError, ValueError, TypeError) as exc:
        raise PersistenceError("Snapshot commit failed") from exc
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def load(path: Path) -> Optional[MemoryStore]:
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if "schema_version" in raw:
            if raw["schema_version"] not in (1, 2):
                raise ValueError("Unsupported snapshot schema")
            payload = raw["payload"]
            if hashlib.sha256(_canonical(payload)).hexdigest() != raw["sha256"]:
                raise ValueError("Snapshot checksum mismatch")
            raw = payload
        # Legacy snapshots are read once; the next save upgrades the envelope.
        if not isinstance(raw, dict) or any(name not in raw for name in _COLLECTION_TYPES if name not in {"financials_history", "calculation_runs"}):
            raise ValueError("Incomplete snapshot")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise PersistenceError("Snapshot cannot be loaded; restore a verified backup") from exc
    store = MemoryStore()
    for name, cls in _COLLECTION_TYPES.items():
        setattr(
            store,
            name,
            {key: _dataclass_from_dict(cls, value) for key, value in raw.get(name, {}).items()},
        )
    store.audit_events = [_dataclass_from_dict(AuditEvent, e) for e in raw.get("audit_events", [])]
    return store

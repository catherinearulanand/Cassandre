"""JSON snapshot persistence for `MemoryStore`.

Not a real database — no migrations, no concurrent-writer safety, no
indexes, single file on local disk. It does close the most visible gap from
docs/ASSUMPTIONS.md item 1 ("resets on every restart"): state now survives
a process restart. A real Postgres-backed store is still the documented
next step, not this.
"""

from __future__ import annotations

import json
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


def save(store: MemoryStore, path: Path) -> None:
    payload: dict[str, Any] = {
        name: {key: asdict(value) for key, value in getattr(store, name).items()}
        for name in _COLLECTION_TYPES
    }
    payload["audit_events"] = [asdict(e) for e in store.audit_events]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, default=_encode, indent=2), encoding="utf-8")


def load(path: Path) -> Optional[MemoryStore]:
    if not path.is_file():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    store = MemoryStore()
    for name, cls in _COLLECTION_TYPES.items():
        setattr(
            store,
            name,
            {key: _dataclass_from_dict(cls, value) for key, value in raw.get(name, {}).items()},
        )
    store.audit_events = [_dataclass_from_dict(AuditEvent, e) for e in raw.get("audit_events", [])]
    return store

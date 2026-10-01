import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from cassandre_cc.fixtures.synthetic_seed import seed
from cassandre_cc.store import persistence
from cassandre_cc.store.memory_store import MemoryStore
from cassandre_cc.store.transactions import SnapshotTransactions, WriterLease


def test_atomic_save_preserves_old_snapshot_on_replace_failure(tmp_path, monkeypatch):
    path = tmp_path / "store.json"
    state = seed(MemoryStore())
    persistence.save(state, path)
    old = path.read_bytes()
    state.audit_events.clear()
    monkeypatch.setattr(os, "replace", lambda *a: (_ for _ in ()).throw(OSError("disk error")))
    with pytest.raises(persistence.PersistenceError):
        persistence.save(state, path)
    assert path.read_bytes() == old
    assert not list(tmp_path.glob(".snapshot-*"))


def test_checksum_and_incomplete_snapshots_fail_closed(tmp_path):
    path = tmp_path / "store.json"
    persistence.save(seed(MemoryStore()), path)
    raw = json.loads(path.read_text())
    raw["payload"]["audit_events"] = []
    raw["sha256"] = "0" * 64
    path.write_text(json.dumps(raw))
    with pytest.raises(persistence.PersistenceError):
        persistence.load(path)
    path.write_text("{}")
    with pytest.raises(persistence.PersistenceError):
        persistence.load(path)


def test_second_writer_is_rejected(tmp_path):
    path = tmp_path / "store.json"
    lease = WriterLease(path)
    try:
        result = subprocess.run([sys.executable, "-c", "from pathlib import Path; from cassandre_cc.store.transactions import WriterLease; WriterLease(Path(__import__('sys').argv[1]))", str(path)], capture_output=True)
        assert result.returncode != 0
    finally:
        lease.close()
    WriterLease(path).close()


def test_failed_response_rolls_back_memory_and_deferred_disk(tmp_path):
    from fastapi.responses import JSONResponse
    state = seed(MemoryStore())
    path = tmp_path / "store.json"
    persistence.save(state, path)
    old = path.read_bytes()
    app = FastAPI()
    @app.post("/change")
    def change():
        state.audit_events.clear()
        state.facilities.clear()
        persistence.save(state, path)
        return JSONResponse({"detail": "invalid"}, status_code=409)
    app.add_middleware(SnapshotTransactions, store_getter=lambda: state, path=path)
    with TestClient(app) as client:
        assert client.post("/change").status_code == 409
    assert state.facilities
    assert path.read_bytes() == old


def test_commit_failure_returns_503_and_disables_followup(tmp_path, monkeypatch):
    state = seed(MemoryStore())
    path = tmp_path / "store.json"
    app = FastAPI()
    @app.post("/change")
    def change():
        state.facilities.clear()
        return {"ok": True}
    app.add_middleware(SnapshotTransactions, store_getter=lambda: state, path=path)
    monkeypatch.setattr(persistence, "save", lambda *a, **k: (_ for _ in ()).throw(persistence.PersistenceError("failed")))
    with TestClient(app) as client:
        assert client.post("/change").status_code == 503
        assert state.facilities
        assert client.post("/change").status_code == 503


def test_backup_restore_roundtrip_and_live_writer_refusal(tmp_path):
    store = tmp_path / "store.json"
    backup = tmp_path / "backup.json"
    state = seed(MemoryStore())
    original = persistence.payload_for(state)
    persistence.save(state, store)
    script = Path(__file__).parents[1] / "scripts" / "snapshot.py"
    def run(action):
        return subprocess.run([sys.executable, str(script), action, str(store), str(backup)], capture_output=True)
    lease = WriterLease(store)
    assert run("backup").returncode != 0
    lease.close()
    assert run("backup").returncode == 0
    state.facilities.clear()
    persistence.save(state, store)
    assert run("restore").returncode == 0
    assert persistence.load(store).facilities
    assert persistence.payload_for(persistence.load(store)) == original


def test_bundle_preserves_originals_and_rejects_tampering(tmp_path):
    import hashlib
    import importlib.util
    import zipfile
    module_spec = importlib.util.spec_from_file_location("backup_tool", Path(__file__).parents[1] / "scripts" / "snapshot.py")
    tool = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(tool)
    store = tmp_path / "store.json"
    persistence.save(seed(MemoryStore()), store)
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    original = b"Synthetic immutable sanction text"
    digest = hashlib.sha256(original).hexdigest()
    (evidence / digest).write_bytes(original)
    bundle = tmp_path / "full.ccbackup"
    tool.backup(store, bundle)
    (evidence / digest).unlink()
    tool.restore(store, bundle)
    assert (evidence / digest).read_bytes() == original
    with zipfile.ZipFile(bundle) as source:
        members = {name: source.read(name) for name in source.namelist()}
    members[f"evidence/{digest}"] = b"modified"
    corrupt = tmp_path / "corrupt.ccbackup"
    with zipfile.ZipFile(corrupt, "w") as target:
        for name, data in members.items():
            target.writestr(name, data)
    with pytest.raises(ValueError):
        tool.restore(store, corrupt)

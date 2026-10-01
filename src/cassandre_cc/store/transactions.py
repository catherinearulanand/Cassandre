"""Single-writer request transactions for the synthetic local snapshot runtime."""
from __future__ import annotations

import copy
import fcntl
import threading
from pathlib import Path

import anyio
from starlette.responses import JSONResponse

from cassandre_cc.store import persistence


class WriterLease:
    """Advisory POSIX lock: cooperating processes only; use local disk."""
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.file = path.with_suffix(path.suffix + ".lock").open("a+")
        try:
            fcntl.flock(self.file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.file.close()
            raise RuntimeError("Snapshot already has a writer; use exactly one worker") from None

    def close(self):
        self.file.close()


class SnapshotTransactions:
    """Serialize HTTP requests; buffer responses until commit; rollback errors.

    Persistence failure enters fail-closed mode until restart and operator
    recovery. No streaming endpoints are supported by this small runtime.
    """
    def __init__(self, app, store_getter, path: Path):
        self.app = app
        self.store_getter = store_getter
        self.path = path
        self.guard = threading.Lock()
        self.failed = False

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        await anyio.to_thread.run_sync(self.guard.acquire)
        token = persistence._deferred.set(True)
        store = self.store_getter()
        before = copy.deepcopy(store.__dict__)
        messages = []
        async def capture(message):
            messages.append(message)
        try:
            if self.failed:
                return await JSONResponse({"detail": "STORAGE_UNAVAILABLE"}, status_code=503)(scope, receive, send)
            await self.app(scope, receive, capture)
            status = next((m["status"] for m in messages if m["type"] == "http.response.start"), 500)
            if status >= 400:
                store.__dict__.clear()
                store.__dict__.update(before)
            elif store.__dict__ != before:
                try:
                    persistence.save(store, self.path, force=True)
                except persistence.PersistenceError:
                    store.__dict__.clear()
                    store.__dict__.update(before)
                    self.failed = True
                    return await JSONResponse({"detail": "STORAGE_UNAVAILABLE"}, status_code=503)(scope, receive, send)
            for message in messages:
                await send(message)
        except BaseException:
            store.__dict__.clear()
            store.__dict__.update(before)
            raise
        finally:
            persistence._deferred.reset(token)
            self.guard.release()

#!/usr/bin/env python3
"""Stopped-service snapshot/evidence bundle backup, verification and recovery."""
import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import zipfile
from pathlib import Path

from cassandre_cc.store.persistence import load, save
from cassandre_cc.store.transactions import WriterLease


def read_bundle(path):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or len(names) > 100000:
            raise ValueError("Invalid bundle members")
        files = {}
        total = 0
        for member in archive.infolist():
            name = member.filename
            if name not in {"snapshot.json", "manifest.json"} and not (
                name.startswith("evidence/") and len(name.split("/")) == 2
                and name.split("/")[1] not in {"", ".", ".."}
            ):
                raise ValueError("Invalid bundle path")
            total += member.file_size
            if total > 512 * 1024 * 1024:
                raise ValueError("Bundle too large for evaluation recovery")
            files[name] = archive.read(name)
        for name, data in files.items():
            if name.startswith("evidence/"):
                digest = name.split("/")[1]
                if not re.fullmatch("[a-f0-9]{64}", digest) or len(data) > 262144 or hashlib.sha256(data).hexdigest() != digest:
                    raise ValueError("Evidence digest mismatch")
        manifest = json.loads(files.pop("manifest.json"))
        if set(files) != set(manifest):
            raise ValueError("Manifest does not match bundle")
        if any(hashlib.sha256(data).hexdigest() != manifest[name] for name, data in files.items()):
            raise ValueError("Bundle checksum mismatch")
        with tempfile.TemporaryDirectory() as temp:
            snapshot = Path(temp) / "snapshot.json"
            snapshot.write_bytes(files["snapshot.json"])
            state = load(snapshot)
        if state is None:
            raise ValueError("Missing snapshot")
        return state, files


def backup(store, target):
    if target.exists():
        raise ValueError("Choose a new backup filename")
    state = load(store)
    if state is None:
        raise ValueError("Source snapshot does not exist")
    files = {"snapshot.json": store.read_bytes()}
    evidence = store.parent / "evidence"
    if evidence.exists():
        for path in evidence.iterdir():
            if path.is_symlink() or not path.is_file():
                raise ValueError("Unexpected evidence directory entry")
            files[f"evidence/{path.name}"] = path.read_bytes()
    manifest = {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=target.parent, prefix=".backup-")
    try:
        with os.fdopen(fd, "wb") as handle:
            with zipfile.ZipFile(handle, "w", compression=zipfile.ZIP_STORED) as archive:
                for name, data in files.items():
                    archive.writestr(name, data)
                archive.writestr("manifest.json", json.dumps(manifest))
            handle.flush()
            os.fsync(handle.fileno())
        read_bundle(Path(tmp))
        os.replace(tmp, target)
    finally:
        Path(tmp).unlink(missing_ok=True)


def restore(store, source):
    if zipfile.is_zipfile(source):
        state, files = read_bundle(source)
        evidence = store.parent / "evidence"
        evidence.mkdir(mode=0o700, parents=True, exist_ok=True)
        # Content-addressed originals can safely be restored before metadata.
        # Extra newer originals remain retained; their metadata is not restored.
        for name, data in files.items():
            if name.startswith("evidence/"):
                destination = evidence / name.split("/")[1]
                if destination.exists():
                    if destination.read_bytes() != data:
                        raise ValueError("Existing evidence conflicts with backup")
                    continue
                fd, tmp = tempfile.mkstemp(dir=evidence, prefix=".restore-")
                try:
                    with os.fdopen(fd, "wb") as handle:
                        handle.write(data)
                        handle.flush()
                        os.fsync(handle.fileno())
                    os.replace(tmp, destination)
                finally:
                    Path(tmp).unlink(missing_ok=True)
    else:
        # Legacy raw snapshot recovery. Does NOT restore evidence originals.
        state = load(source)
    if state is None:
        raise ValueError("Source snapshot does not exist")
    if zipfile.is_zipfile(source):
        fd = os.open(evidence, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    save(state, store)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["backup", "restore", "verify"])
    parser.add_argument("store", type=Path)
    parser.add_argument("backup", nargs="?", type=Path)
    args = parser.parse_args()
    if args.action == "verify":
        if zipfile.is_zipfile(args.store):
            read_bundle(args.store)
        elif load(args.store) is None:
            parser.error("Snapshot does not exist")
        print("Backup verified")
        return
    if args.backup is None or args.backup.resolve() == args.store.resolve():
        parser.error("A distinct backup path is required")
    lease = WriterLease(args.store)
    try:
        if args.action == "backup":
            backup(args.store, args.backup)
        else:
            restore(args.store, args.backup)
        print(f"{args.action.capitalize()} verified")
    finally:
        lease.close()


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        print(f"Snapshot operation failed: {type(exc).__name__}", file=sys.stderr)
        sys.exit(1)

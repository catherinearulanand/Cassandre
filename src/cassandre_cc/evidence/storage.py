"""Local content-addressed originals for bounded synthetic UTF-8 text only.

Callers MUST authorise tenant/facility/document access before fetching. Digest
knowledge conveys no permission. This is not PDF support or malware scanning.
Application operations never overwrite originals; privileged filesystem owners
can still alter files, which verified reads detect (not prevent).
"""
from __future__ import annotations

import hashlib
import os
import re
import secrets
import stat
from contextlib import contextmanager
from pathlib import Path

MAX_TEXT_BYTES = 256 * 1024
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")


class EvidenceIntegrityError(ValueError):
    """The stored original is unsafe, damaged or differs from its digest."""


class EvidenceStore:
    def __init__(self, root: Path | str):
        self.root = Path(root).absolute()
        if self.root.is_symlink():
            raise EvidenceIntegrityError("Evidence root must not be a symlink")
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        if not self.root.is_dir():
            raise EvidenceIntegrityError("Evidence root must be a directory")

    @contextmanager
    def _directory(self):
        # Use a directory descriptor throughout an operation so changing the
        # path after opening cannot redirect its subsequent file operations.
        descriptor = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            yield descriptor
        finally:
            os.close(descriptor)

    @staticmethod
    def _validate_digest(digest: str) -> None:
        if not isinstance(digest, str) or not _DIGEST.fullmatch(digest):
            raise ValueError("Expected a lowercase SHA-256 digest")

    def _read(self, directory: int, digest: str) -> bytes:
        try:
            descriptor = os.open(digest, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        except FileNotFoundError:
            raise
        except OSError as exc:
            raise EvidenceIntegrityError("Unsafe evidence file") from exc
        try:
            info = os.fstat(descriptor)
            if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_TEXT_BYTES:
                raise EvidenceIntegrityError("Invalid evidence file type or size")
            with os.fdopen(descriptor, "rb", closefd=False) as stream:
                data = stream.read(MAX_TEXT_BYTES + 1)
            if len(data) > MAX_TEXT_BYTES or hashlib.sha256(data).hexdigest() != digest:
                raise EvidenceIntegrityError("Original evidence checksum mismatch")
            try:
                data.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise EvidenceIntegrityError("Original evidence is not UTF-8 text") from exc
            return data
        finally:
            os.close(descriptor)

    def put_text(self, content: str) -> str:
        if not isinstance(content, str):
            raise TypeError("Only synthetic text strings are supported")
        data = content.encode("utf-8")
        if not data or len(data) > MAX_TEXT_BYTES:
            raise ValueError("Text must contain between 1 and 262144 UTF-8 bytes")
        if any(ord(c) < 32 and c not in "\n\r\t" for c in content):
            raise ValueError("Unsupported binary/control characters in text")
        digest = hashlib.sha256(data).hexdigest()
        temporary = ".pending-" + secrets.token_hex(16)
        with self._directory() as directory:
            descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                                 0o600, dir_fd=directory)
            try:
                with os.fdopen(descriptor, "wb", closefd=False) as stream:
                    stream.write(data)
                    stream.flush()
                    os.fsync(descriptor)
                try:
                    # Atomic no-clobber publication. Existing content must
                    # verify, never be replaced, including damaged originals.
                    os.link(temporary, digest, src_dir_fd=directory, dst_dir_fd=directory,
                            follow_symlinks=False)
                    os.fsync(directory)
                except FileExistsError:
                    if self._read(directory, digest) != data:
                        raise EvidenceIntegrityError("Existing original differs")
            finally:
                os.close(descriptor)
                os.unlink(temporary, dir_fd=directory)
                os.fsync(directory)
        return digest

    def get_bytes(self, digest: str) -> bytes:
        self._validate_digest(digest)
        with self._directory() as directory:
            return self._read(directory, digest)

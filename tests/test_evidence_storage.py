import hashlib

import pytest

from cassandre_cc.evidence.storage import EvidenceIntegrityError, EvidenceStore, MAX_TEXT_BYTES


def test_preserves_exact_original_and_duplicate_is_no_overwrite(tmp_path):
    store = EvidenceStore(tmp_path / "evidence")
    content = "Synthetic sanction ₹5 crore\r\nRule: margin 25%\n"
    digest = store.put_text(content)
    original = store.root / digest
    before = original.stat()
    assert digest == hashlib.sha256(content.encode()).hexdigest()
    assert store.get_bytes(digest) == content.encode()
    assert store.put_text(content) == digest
    assert original.stat().st_ino == before.st_ino
    assert original.stat().st_mtime_ns == before.st_mtime_ns
    assert original.stat().st_mode & 0o777 == 0o600
    assert list(store.root.iterdir()) == [original]


@pytest.mark.parametrize("digest", ["../secret", "/etc/passwd", "a" * 63, "A" * 64, "a" * 64 + "/x"])
def test_path_or_invalid_hash_rejected(tmp_path, digest):
    with pytest.raises(ValueError):
        EvidenceStore(tmp_path).get_bytes(digest)


def test_tampered_original_detected_and_not_replaced(tmp_path):
    store = EvidenceStore(tmp_path)
    digest = store.put_text("synthetic original")
    (tmp_path / digest).write_bytes(b"tampered")
    with pytest.raises(EvidenceIntegrityError, match="checksum"):
        store.get_bytes(digest)
    with pytest.raises(EvidenceIntegrityError):
        store.put_text("synthetic original")
    assert (tmp_path / digest).read_bytes() == b"tampered"
    assert not list(tmp_path.glob(".pending-*"))


def test_byte_limit_not_character_limit(tmp_path):
    store = EvidenceStore(tmp_path)
    with pytest.raises(ValueError):
        store.put_text("₹" * (MAX_TEXT_BYTES // 3 + 1))
    assert not list(tmp_path.iterdir())
    digest = store.put_text("x" * MAX_TEXT_BYTES)
    assert len(store.get_bytes(digest)) == MAX_TEXT_BYTES


@pytest.mark.parametrize("content", ["", "text\x00data", "text\x1bdata"])
def test_empty_or_binary_control_text_rejected(tmp_path, content):
    with pytest.raises(ValueError):
        EvidenceStore(tmp_path).put_text(content)


def test_symlink_original_cannot_redirect_fetch_or_replace(tmp_path):
    store = EvidenceStore(tmp_path / "evidence")
    text = "synthetic text"
    digest = hashlib.sha256(text.encode()).hexdigest()
    target = tmp_path / "outside"
    target.write_text(text)
    (store.root / digest).symlink_to(target)
    with pytest.raises(EvidenceIntegrityError):
        store.get_bytes(digest)
    with pytest.raises(EvidenceIntegrityError):
        store.put_text(text)
    assert target.read_text() == text


def test_symlink_root_rejected(tmp_path):
    target = tmp_path / "actual"
    target.mkdir()
    root = tmp_path / "link"
    root.symlink_to(target, target_is_directory=True)
    with pytest.raises(EvidenceIntegrityError):
        EvidenceStore(root)


def test_missing_original_is_not_silently_recreated(tmp_path):
    with pytest.raises(FileNotFoundError):
        EvidenceStore(tmp_path).get_bytes("0" * 64)


def test_replacement_creates_new_original_preserves_prior_version(tmp_path):
    store = EvidenceStore(tmp_path)
    old = store.put_text("synthetic original terms")
    new = store.put_text("synthetic approved amended terms")
    assert old != new
    assert store.get_bytes(old) == b"synthetic original terms"
    assert store.get_bytes(new) == b"synthetic approved amended terms"

"""Acceptance scenario #13: "Document replacement: original and
replacement preserved; previous result reproducible." Registration only —
not real file storage or OCR (explicitly deferred, see docs/STATUS.md)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from cassandre_cc.api.main import app

client = TestClient(app)


def test_register_original_document():
    resp = client.post(
        "/v1/facilities/SIM-FAC-A001/documents",
        json={
            "document_type": "stock_statement",
            "evidence_period": "2026-07",
            "content": "synthetic stock statement contents v1",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_original"] is True
    assert body["supersedes_document_id"] is None


def test_replacement_preserves_the_original_row():
    original = client.post(
        "/v1/facilities/SIM-FAC-A001/documents",
        json={
            "document_type": "stock_statement",
            "evidence_period": "2026-09",
            "content": "synthetic stock statement — first submission",
        },
    ).json()

    replacement = client.post(
        "/v1/facilities/SIM-FAC-A001/documents",
        json={
            "document_type": "stock_statement",
            "evidence_period": "2026-09",
            "content": "synthetic stock statement — corrected figures",
            "supersedes_document_id": original["document_id"],
        },
    )
    assert replacement.status_code == 200
    assert replacement.json()["is_original"] is False

    listing = client.get("/v1/facilities/SIM-FAC-A001/documents").json()
    by_id = {d["document_id"]: d for d in listing}

    assert original["document_id"] in by_id  # never deleted
    assert by_id[original["document_id"]]["is_current"] is False
    assert by_id[replacement.json()["document_id"]]["is_current"] is True
    # Different content -> different hash, both preserved distinctly.
    assert by_id[original["document_id"]]["source_hash"] != by_id[replacement.json()["document_id"]]["source_hash"]


def test_superseding_a_nonexistent_document_is_404():
    resp = client.post(
        "/v1/facilities/SIM-FAC-A001/documents",
        json={
            "document_type": "stock_statement",
            "evidence_period": "2026-09",
            "content": "x",
            "supersedes_document_id": "SIM-DOC-GHOST",
        },
    )
    assert resp.status_code == 404

"""Phase 2: read-only fixture imports. Acceptance scenario #1: "Import one
facility twice: no duplicated facility/evidence/case." Acceptance scenario
#3: a malformed figure stops the import rather than silently becoming
zero/garbage."""

from __future__ import annotations

from fastapi.testclient import TestClient

from cassandre_cc.api.main import app

client = TestClient(app)

_PAYLOAD = {
    "facility_id": "SIM-FAC-B002",
    "period": "2026-09",
    "reported_stock_crore": "2.10",
    "stock_exclusions_crore": "0.15",
    "reported_receivables_crore": "1.90",
    "receivable_exclusions_crore": "0.40",
    "outstanding_crore": "1.30",
}


def test_import_creates_a_new_batch():
    before = len(client.get("/v1/imports").json())
    resp = client.post("/v1/imports:financials", json=_PAYLOAD)
    assert resp.status_code == 200
    body = resp.json()
    assert body["was_new"] is True
    after = len(client.get("/v1/imports").json())
    assert after == before + 1


def test_reimporting_identical_content_is_a_no_op():
    before = len(client.get("/v1/imports").json())
    resp = client.post("/v1/imports:financials", json=_PAYLOAD)
    assert resp.status_code == 200
    assert resp.json()["was_new"] is False
    after = len(client.get("/v1/imports").json())
    assert after == before  # no duplicate batch


def test_imported_period_is_then_visible_on_the_facility():
    resp = client.get("/v1/facilities/SIM-FAC-B002", params={"period": "2026-09"})
    assert resp.status_code == 200
    assert "2026-09" in resp.json()["periods"]


def test_malformed_decimal_stops_the_import():
    bad_payload = {**_PAYLOAD, "period": "2026-10", "reported_stock_crore": "4.00 lakh"}
    resp = client.post("/v1/imports:financials", json=bad_payload)
    assert resp.status_code == 422
    assert resp.json()["detail"]["failure"] == "INVALID_DECIMAL_VALUE"


def test_import_for_unknown_facility_is_404():
    resp = client.post("/v1/imports:financials", json={**_PAYLOAD, "facility_id": "SIM-FAC-GHOST"})
    assert resp.status_code == 404

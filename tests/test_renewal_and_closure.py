"""Phase 5: renewal decisions and closure. Acceptance scenario #15: "Zero
balance with linked commitment/security: closure release remains
pending" — a facility must not close while any closure checklist item is
outstanding, enforced server-side."""

from __future__ import annotations

from auth_client import TestClient

from cassandre_cc.api.main import app

client = TestClient(app)


def test_renewal_decision_is_recorded():
    resp = client.post(
        "/v1/renewals/SIM-RENEWAL-A001-01:decide",
        json={"decision": "renewed", "decided_by": "credit.suresh", "notes": "Conduct satisfactory."},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["decision"] == "renewed"
    assert body["decided_by"] == "credit.suresh"
    assert body["decided_at"] is not None


def test_invalid_renewal_decision_is_rejected():
    resp = client.post(
        "/v1/renewals/SIM-RENEWAL-A001-01:decide",
        json={"decision": "maybe", "decided_by": "credit.suresh"},
    )
    assert resp.status_code == 422


def test_closing_facility_is_blocked_until_checklist_complete():
    resp = client.post("/v1/facilities/SIM-FAC-A001:close", json={"actor": "ops.rahul"})
    assert resp.status_code == 409
    assert resp.json()["detail"]["failure"] == "CLOSURE_CHECKLIST_INCOMPLETE"


def test_closing_facility_succeeds_once_every_item_is_true():
    for field in ("dues_reconciled", "security_released", "linked_exposures_clear"):
        resp = client.post(f"/v1/facilities/SIM-FAC-A001/closure", json={field: True, "actor": "ops.rahul"})
        assert resp.status_code == 200
        assert resp.json()["closure_ready"] is False  # still missing at least one item

    still_blocked = client.post("/v1/facilities/SIM-FAC-A001:close", json={"actor": "ops.rahul"})
    assert still_blocked.status_code == 409

    final = client.post(
        "/v1/facilities/SIM-FAC-A001/closure",
        json={"originals_returned": True, "actor": "ops.rahul"},
    )
    assert final.status_code == 200
    assert final.json()["closure_ready"] is True

    blocked = client.post("/v1/facilities/SIM-FAC-A001:close", json={"actor": "checker.arvind"})
    assert blocked.status_code == 409  # checklist cannot override nonzero balance
    assert client.post("/v1/imports:financials", json={"facility_id":"SIM-FAC-A001", "period":"2027-01", "outstanding_crore":"0"}).status_code == 200
    closed = client.post("/v1/facilities/SIM-FAC-A001:close", json={"actor": "checker.arvind"})
    assert closed.status_code == 200
    assert closed.json()["state"] == "closed"

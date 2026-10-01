"""Phase 5: waivers and cure tasks. Acceptance scenario #8: "Limited
waiver: only named obligation/test period is waived; new cure is
tracked." Uses facility B, importing a period with outstanding deliberately
above the usable cap so the covenant genuinely breaches with no waiver in
scope, then checks a later period (same underlying condition, no waiver)
still breaches and opens its own cure task rather than being silently
suppressed by the earlier waiver."""

from __future__ import annotations

from auth_client import TestClient

from cassandre_cc.api.main import app

client = TestClient(app)

_TEST_ID = "SIM-COV-HEADROOM"


def _import_breaching_period(period: str) -> None:
    resp = client.post(
        "/v1/imports:financials",
        json={
            "facility_id": "SIM-FAC-B002",
            "period": period,
            "reported_stock_crore": "2.00",
            "stock_exclusions_crore": "0.20",
            "reported_receivables_crore": "1.50",
            "receivable_exclusions_crore": "0.30",
            "outstanding_crore": "5.00",  # deliberately far above usable cap
        },
    )
    assert resp.status_code == 200


def test_unwaived_breach_opens_a_cure_task():
    _import_breaching_period("2026-11")
    resp = client.post("/v1/facilities/SIM-FAC-B002/calculations:recompute", params={"period": "2026-11"})
    assert resp.status_code == 200
    assert resp.json()["covenant_finding"] == "potential_breach"

    cures = client.get("/v1/facilities/SIM-FAC-B002").json()["cure_tasks"]
    matching = [c for c in cures if c["period"] == "2026-11" and c["test_id"] == _TEST_ID]
    assert len(matching) == 1
    assert matching[0]["status"] == "open"


def test_recompute_does_not_open_a_duplicate_cure_task():
    client.post("/v1/facilities/SIM-FAC-B002/calculations:recompute", params={"period": "2026-11"})
    client.post("/v1/facilities/SIM-FAC-B002/calculations:recompute", params={"period": "2026-11"})
    cures = client.get("/v1/facilities/SIM-FAC-B002").json()["cure_tasks"]
    matching = [c for c in cures if c["period"] == "2026-11" and c["test_id"] == _TEST_ID]
    assert len(matching) == 1


def test_waiver_scoped_to_one_period_does_not_cover_a_different_period():
    _import_breaching_period("2026-12")

    waiver = client.post(
        "/v1/waivers",
        json={
            "facility_id": "SIM-FAC-B002",
            "test_id": _TEST_ID,
            "scoped_period": "2026-11",
            "reason": "One-off seasonal drawdown, credit-committee approved.",
            "submitted_by": "rm.neha",
        },
    ).json()
    approved = client.post(
        f"/v1/waivers/{waiver['waiver_id']}:approve",
        json={"approver": "credit.suresh"},
    )
    assert approved.status_code == 200
    assert approved.json()["state"] == "active"

    # The waived period now reads as waived...
    nov_calc = client.get("/v1/facilities/SIM-FAC-B002", params={"period": "2026-11"}).json()["calculation"]
    assert nov_calc["covenant_finding"] == "waived_for_scope"

    # ...but December, same underlying condition, was never waived.
    dec_calc = client.get("/v1/facilities/SIM-FAC-B002", params={"period": "2026-12"}).json()["calculation"]
    assert dec_calc["covenant_finding"] == "potential_breach"
    assert dec_calc["waiver_applied"] is False


def test_self_approval_of_a_waiver_is_denied():
    waiver = client.post(
        "/v1/waivers",
        json={
            "facility_id": "SIM-FAC-B002",
            "test_id": _TEST_ID,
            "scoped_period": "2026-12",
            "reason": "test",
            "submitted_by": "rm.neha",
        },
    ).json()
    resp = client.post(f"/v1/waivers/{waiver['waiver_id']}:approve", json={"approver": "rm.neha"})
    assert resp.status_code == 409
    assert resp.json()["detail"]["failure"] == "SELF_APPROVAL_DENIED"

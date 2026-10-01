"""End-to-end smoke test over the real FastAPI app + synthetic seed data."""

from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient

from cassandre_cc.api.main import app

client = TestClient(app)


def test_index_html_served():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_lists_seeded_facilities():
    resp = client.get("/v1/facilities")
    assert resp.status_code == 200
    ids = {f["facility_id"] for f in resp.json()}
    assert ids == {"SIM-FAC-A001", "SIM-FAC-B002"}


def test_facility_a_2026_07_reproduces_the_worked_fixture_under_v1_terms():
    resp = client.get("/v1/facilities/SIM-FAC-A001", params={"period": "2026-07"})
    assert resp.status_code == 200
    calc = resp.json()["calculation"]
    assert calc["result_state"] == "calculated"
    assert calc["rule_set_version"] == 1
    assert Decimal(calc["proposed_dp"]["amount"]) == Decimal("4.165")
    assert Decimal(calc["headroom"]["amount"]) == Decimal("0.565")
    assert calc["covenant_finding"] == "compliant"


def test_facility_a_2026_08_uses_amended_v2_terms_and_is_waived():
    """Acceptance scenario #7 (mid-period amendment) + #8 (limited waiver):
    the later period picks up the v2 margins and a covenant breach that
    would otherwise fire is waived, because a waiver scoped to exactly this
    (facility, test, period) was approved."""
    resp = client.get("/v1/facilities/SIM-FAC-A001", params={"period": "2026-08"})
    assert resp.status_code == 200
    calc = resp.json()["calculation"]
    assert calc["result_state"] == "calculated"
    assert calc["rule_set_version"] == 2
    assert Decimal(calc["proposed_dp"]["amount"]) == Decimal("4.055")
    assert Decimal(calc["headroom"]["amount"]) == Decimal("-0.495")
    assert calc["covenant_finding"] == "waived_for_scope"
    assert calc["waiver_applied"] is True


def test_default_period_is_the_latest_one():
    resp = client.get("/v1/facilities/SIM-FAC-A001")
    assert resp.status_code == 200
    assert resp.json()["calculation"]["period"] == "2026-08"


def test_facility_b_is_indeterminate_because_receivables_are_missing():
    resp = client.get("/v1/facilities/SIM-FAC-B002")
    assert resp.status_code == 200
    calc = resp.json()["calculation"]
    assert calc["result_state"] == "indeterminate"
    assert "reported_receivables" in calc["missing_fields"]
    assert calc["proposed_dp"] is None


def test_unknown_facility_is_404_not_500():
    resp = client.get("/v1/facilities/SIM-FAC-DOES-NOT-EXIST")
    assert resp.status_code == 404


def test_self_approval_is_denied_with_exact_failure_reason():
    resp = client.post(
        "/v1/cases/SIM-CASE-A001-RULEV3:approve",
        json={"approver": "maker.priya"},
    )
    assert resp.status_code == 409
    assert resp.json()["detail"]["failure"] == "SELF_APPROVAL_DENIED"


def test_independent_checker_approval_succeeds_and_is_audited():
    resp = client.post(
        "/v1/cases/SIM-CASE-A001-RULEV3:approve",
        json={"approver": "checker.arvind"},
    )
    assert resp.status_code == 200
    assert resp.json()["state"] == "active"

    audit = client.get("/v1/audit-events").json()
    assert any(e["action"] == "CASE_APPROVED" for e in audit)


def test_recompute_is_audited():
    before = len(client.get("/v1/audit-events").json())
    resp = client.post("/v1/facilities/SIM-FAC-A001/calculations:recompute", params={"period": "2026-07"})
    assert resp.status_code == 200
    after = len(client.get("/v1/audit-events").json())
    assert after == before + 1

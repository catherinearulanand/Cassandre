"""Phase 3: reviewed rule register. Exercises proposing a new rule version,
maker-checker approval (including self-approval denial), and that
approving a new version supersedes the previously-active one without
deleting it."""

from __future__ import annotations

from auth_client import TestClient

from cassandre_cc.api.main import app

client = TestClient(app)


def test_propose_rule_version_starts_in_reviewed_state():
    resp = client.post(
        "/v1/facilities/SIM-FAC-B002/rule-versions",
        json={
            "stock_margin": "0.28",
            "receivable_margin": "0.32",
            "debtor_ageing_cutoff_days": 75,
            "submitted_by": "maker.priya",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["state"] == "reviewed"
    assert body["version"] == 2  # facility B already has v1 seeded


def test_self_approval_of_a_rule_version_is_denied():
    proposed = client.post(
        "/v1/facilities/SIM-FAC-B002/rule-versions",
        json={
            "stock_margin": "0.28",
            "receivable_margin": "0.32",
            "debtor_ageing_cutoff_days": 75,
            "submitted_by": "maker.priya",
        },
    ).json()

    resp = client.post(
        f"/v1/rule-versions/{proposed['rule_set_id']}:approve",
        json={"approver": "maker.priya", "effective_from": "2026-09-01"},
    )
    assert resp.status_code == 409
    assert resp.json()["detail"]["failure"] == "SELF_APPROVAL_DENIED"


def test_approving_a_new_version_supersedes_the_old_one_not_deletes_it():
    before = client.get("/v1/facilities/SIM-FAC-B002").json()
    active_before = [r for r in before["rule_versions"] if r["state"] == "active"]
    assert len(active_before) == 1
    old_active_id = active_before[0]["rule_set_id"]

    proposed = client.post(
        "/v1/facilities/SIM-FAC-B002/rule-versions",
        json={
            "stock_margin": "0.28",
            "receivable_margin": "0.32",
            "debtor_ageing_cutoff_days": 75,
            "submitted_by": "maker.priya",
        },
    ).json()
    approved = client.post(
        f"/v1/rule-versions/{proposed['rule_set_id']}:approve",
        json={"approver": "checker.arvind", "effective_from": "2026-09-01"},
    )
    assert approved.status_code == 200
    assert approved.json()["state"] == "active"

    after = client.get("/v1/facilities/SIM-FAC-B002").json()
    by_id = {r["rule_set_id"]: r for r in after["rule_versions"]}
    assert by_id[old_active_id]["state"] == "superseded"  # still present, not deleted
    assert by_id[proposed["rule_set_id"]]["state"] == "active"


def test_approving_rule_version_for_unknown_id_is_404():
    resp = client.post(
        "/v1/rule-versions/SIM-RULE-GHOST:approve",
        json={"approver": "checker.arvind", "effective_from": "2026-09-01"},
    )
    assert resp.status_code == 404

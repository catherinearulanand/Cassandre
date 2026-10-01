"""Phase 8 scaffold — calculations/shadow_score.py. Confirms the endpoint
always carries its disclaimer, never claims a score when inputs are
indeterminate, and reacts to worse inputs with a higher score (sanity check
on the heuristic, not a claim of predictive validity)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from cassandre_cc.api.main import app

client = TestClient(app)


def test_shadow_score_always_carries_the_disclaimer():
    resp = client.get("/v1/facilities/SIM-FAC-A001/shadow-score", params={"period": "2026-07"})
    assert resp.status_code == 200
    body = resp.json()
    assert "not a trained model" in body["disclaimer"]


def test_shadow_score_is_zero_with_explanation_when_data_is_indeterminate():
    resp = client.get("/v1/facilities/SIM-FAC-B002/shadow-score", params={"period": "2026-08"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["score"] == 0
    assert "insufficient data" in body["basis"]


def test_shadow_score_is_higher_for_the_waived_breach_period_than_the_clean_one():
    clean = client.get("/v1/facilities/SIM-FAC-A001/shadow-score", params={"period": "2026-07"}).json()
    stressed = client.get("/v1/facilities/SIM-FAC-A001/shadow-score", params={"period": "2026-08"}).json()
    assert stressed["score"] > clean["score"]


def test_shadow_score_for_unknown_facility_is_404():
    resp = client.get("/v1/facilities/SIM-FAC-GHOST/shadow-score")
    assert resp.status_code == 404

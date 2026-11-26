"""Contract: live HTTP shapes Daniel's client expects (v0.1.0)."""

import pytest

from tests.conftest import baseline_body, verify_body

pytestmark = [pytest.mark.contract]


def test_health_shape(client):
    r = client.get("/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["service"] == "ivs"
    assert body["contract_version"] == "0.1.0"


def test_baseline_response_fields(client, sha_a):
    r = client.post("/v1/baselines", json=baseline_body(sha=sha_a))
    assert r.status_code == 200
    body = r.json()
    for key in ("contract_version", "baseline_id", "status", "algorithm", "registered_at"):
        assert key in body
    assert body["status"] == "registered"
    assert body["baseline_id"].startswith("bl_")
    assert body["algorithm"] == "sha256"


def test_verification_response_fields(client, sha_a):
    bl = client.post("/v1/baselines", json=baseline_body(sha=sha_a)).json()
    r = client.post(
        "/v1/verifications",
        json=verify_body(sha=sha_a, baseline_id=bl["baseline_id"]),
    )
    assert r.status_code == 200
    body = r.json()
    for key in (
        "contract_version",
        "verification_id",
        "baseline_id",
        "verdict",
        "detail",
        "checked_at",
    ):
        assert key in body
    assert body["verdict"] == "intact"
    assert body["verification_id"].startswith("vr_")


def test_report_exists_after_verification(client, sha_a):
    bl = client.post("/v1/baselines", json=baseline_body(sha=sha_a)).json()
    vr = client.post(
        "/v1/verifications",
        json=verify_body(sha=sha_a, baseline_id=bl["baseline_id"]),
    ).json()
    r = client.get(f"/v1/reports/{vr['verification_id']}")
    assert r.status_code == 200
    doc = r.json()
    assert doc["verification_id"] == vr["verification_id"]
    assert doc["verdict"] == "intact"
    assert "summary" in doc


def test_rejects_wrong_contract_version(client, sha_a):
    body = baseline_body(sha=sha_a)
    body["contract_version"] = "9.9.9"
    assert client.post("/v1/baselines", json=body).status_code == 400

"""M1 acceptance: sha256 baselines and verifications (must stay green)."""

import pytest

from tests.conftest import baseline_body, verify_body

pytestmark = [pytest.mark.acceptance]


def test_register_then_intact(client, sha_a):
    bl = client.post("/v1/baselines", json=baseline_body(sha=sha_a)).json()
    vr = client.post(
        "/v1/verifications",
        json=verify_body(sha=sha_a, baseline_id=bl["baseline_id"]),
    ).json()
    assert vr["verdict"] == "intact"
    assert vr["detail"]["hash_match"] is True


def test_register_then_altered_when_hash_changes(client, sha_a, sha_b):
    bl = client.post("/v1/baselines", json=baseline_body(sha=sha_a)).json()
    vr = client.post(
        "/v1/verifications",
        json=verify_body(sha=sha_b, baseline_id=bl["baseline_id"]),
    ).json()
    assert vr["verdict"] == "altered"
    assert vr["detail"]["hash_match"] is False


def test_verify_without_baseline_id_looks_up_by_hash(client, sha_a):
    client.post("/v1/baselines", json=baseline_body(sha=sha_a))
    vr = client.post("/v1/verifications", json=verify_body(sha=sha_a)).json()
    assert vr["verdict"] == "intact"
    assert vr["baseline_id"]


def test_verify_unknown_without_any_baseline(client, sha_a):
    vr = client.post("/v1/verifications", json=verify_body(sha=sha_a)).json()
    assert vr["verdict"] == "unknown"


def test_missing_sha256_is_400(client):
    body = baseline_body()
    del body["object"]["sha256"]
    assert client.post("/v1/baselines", json=body).status_code == 400


def test_bad_sha256_is_400(client):
    assert client.post("/v1/baselines", json=baseline_body(sha="nope")).status_code == 400


def test_unknown_baseline_id_is_404(client, sha_a):
    r = client.post(
        "/v1/verifications",
        json=verify_body(sha=sha_a, baseline_id="bl_does_not_exist"),
    )
    assert r.status_code == 404


def test_tenant_cannot_use_another_tenants_baseline(client, sha_a):
    bl = client.post("/v1/baselines", json=baseline_body(tenant="tenant_a", sha=sha_a)).json()
    r = client.post(
        "/v1/verifications",
        json=verify_body(tenant="tenant_b", sha=sha_a, baseline_id=bl["baseline_id"]),
    )
    assert r.status_code == 403


def test_report_404_for_unknown_id(client):
    assert client.get("/v1/reports/vr_missing").status_code == 404


def test_report_for_altered_mentions_mismatch(client, sha_a, sha_b):
    bl = client.post("/v1/baselines", json=baseline_body(sha=sha_a)).json()
    vr = client.post(
        "/v1/verifications",
        json=verify_body(sha=sha_b, baseline_id=bl["baseline_id"]),
    ).json()
    doc = client.get(f"/v1/reports/{vr['verification_id']}").json()
    assert doc["verdict"] == "altered"
    assert "differ" in doc["summary"].lower() or "alter" in doc["summary"].lower()


def test_health_not_stub_label(client):
    assert client.get("/v1/health").json()["service"] == "ivs"

"""M2 — cryptographic signatures (Ed25519 or similar).

TODO(m2): implement signing on baseline register and signature checks on verify.
Remove every TODO(m2) and xfail when green.
"""

import pytest

from tests.conftest import baseline_body, verify_body

pytestmark = [pytest.mark.acceptance]


@pytest.mark.xfail(reason="TODO(m2): algorithm should become sha256+ed25519 (or documented equivalent)")
def test_baseline_algorithm_includes_signature_scheme(client, sha_a):
    body = client.post("/v1/baselines", json=baseline_body(sha=sha_a)).json()
    assert "ed25519" in body["algorithm"].lower() or "signature" in body["algorithm"].lower()


@pytest.mark.xfail(reason="TODO(m2): baseline response / store must expose a signature field")
def test_baseline_persists_signature_material(client, sha_a):
    bl = client.post("/v1/baselines", json=baseline_body(sha=sha_a)).json()
    # Expect either response field or reportable public metadata
    assert "signature" in bl or "public_key_id" in bl


@pytest.mark.xfail(reason="TODO(m2): tampered signature must yield altered or signature_valid=false")
def test_verify_detects_invalid_signature(client, sha_a):
    bl = client.post("/v1/baselines", json=baseline_body(sha=sha_a)).json()
    vr = client.post(
        "/v1/verifications",
        json=verify_body(sha=sha_a, baseline_id=bl["baseline_id"]),
    ).json()
    # Until signing exists this cannot pass; placeholder assertion for the milestone
    assert vr["detail"].get("signature_valid") is True


@pytest.mark.xfail(reason="TODO(m2): key rotation / key id documented and enforced")
def test_verify_rejects_unknown_key_id(client, sha_a):
    body = baseline_body(sha=sha_a)
    body["context"] = {"key_id": "unknown-key"}
    r = client.post("/v1/baselines", json=body)
    assert r.status_code in (400, 422) or r.json().get("status") == "registered"
    assert False, "TODO(m2): define key_id behaviour and assert it"

"""Checks for optional shared-token gate (no module reload)."""

import pytest

import app.main as main
from tests.conftest import baseline_body

pytestmark = [pytest.mark.unit]


def test_token_required_rejects_missing_header(client, monkeypatch, sha_a):
    monkeypatch.setattr(main, "REQUIRE_TOKEN", True)
    monkeypatch.setattr(main, "SHARED_TOKEN", "secret-token")
    r = client.post("/v1/baselines", json=baseline_body(sha=sha_a))
    assert r.status_code == 401


def test_token_required_accepts_matching_header(client, monkeypatch, sha_a):
    monkeypatch.setattr(main, "REQUIRE_TOKEN", True)
    monkeypatch.setattr(main, "SHARED_TOKEN", "secret-token")
    r = client.post(
        "/v1/baselines",
        headers={"X-Integrity-Token": "secret-token"},
        json=baseline_body(sha=sha_a),
    )
    assert r.status_code == 200


def test_token_required_rejects_wrong_header(client, monkeypatch, sha_a):
    monkeypatch.setattr(main, "REQUIRE_TOKEN", True)
    monkeypatch.setattr(main, "SHARED_TOKEN", "secret-token")
    r = client.post(
        "/v1/baselines",
        headers={"X-Integrity-Token": "wrong"},
        json=baseline_body(sha=sha_a),
    )
    assert r.status_code == 401

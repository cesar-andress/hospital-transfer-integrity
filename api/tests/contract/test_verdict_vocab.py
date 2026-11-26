"""Contract: verdict vocabulary stays aligned with Daniel's client."""

import pytest

from app.models import Verdict
from tests.conftest import baseline_body, verify_body

pytestmark = [pytest.mark.contract]

ALLOWED = {"intact", "altered", "encrypted_or_unreadable", "unknown", "passthrough"}


def test_verdict_literal_matches_allowed_set():
    # Typing Literal args are stored differently across Python versions; compare set.
    assert set(Verdict.__args__) == ALLOWED  # type: ignore[attr-defined]


def test_live_verdicts_are_from_vocab(client, sha_a, sha_b):
    bl = client.post("/v1/baselines", json=baseline_body(sha=sha_a)).json()
    intact = client.post(
        "/v1/verifications",
        json=verify_body(sha=sha_a, baseline_id=bl["baseline_id"]),
    ).json()["verdict"]
    altered = client.post(
        "/v1/verifications",
        json=verify_body(sha=sha_b, baseline_id=bl["baseline_id"]),
    ).json()["verdict"]
    unknown = client.post(
        "/v1/verifications",
        json=verify_body(sha="c" * 64),
    ).json()["verdict"]
    for v in (intact, altered, unknown):
        assert v in ALLOWED
        assert v != "passthrough"  # real IVS must not echo stub passthrough

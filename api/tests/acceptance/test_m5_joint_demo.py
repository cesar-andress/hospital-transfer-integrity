"""M5 — joint demo with Daniel (URL swap, no code merge).

TODO(m5): document and automate the dual-stack demo checklist.
Remove every TODO(m5) and xfail when green.
"""

from pathlib import Path

import pytest

from tests.conftest import baseline_body, verify_body

pytestmark = [pytest.mark.acceptance]

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.xfail(reason="TODO(m5): docs/JOINT_DEMO.md with URL-swap steps for Daniel")
def test_joint_demo_runbook_exists():
    path = ROOT / "docs" / "JOINT_DEMO.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8").lower()
    assert "integrity_api_base_url" in text or "url" in text
    assert "daniel" in text


@pytest.mark.xfail(reason="TODO(m5): health must expose deploy identity usable in the joint demo")
def test_health_exposes_demo_identity(client):
    body = client.get("/v1/health").json()
    assert "deploy" in body or "build" in body or "instance" in body


@pytest.mark.xfail(
    reason="TODO(m5): end-to-end fixture mirroring Daniel transfer_id → baseline → verify → report"
)
def test_joint_flow_preserves_transfer_id(client, sha_a):
    transfer_id = "550e8400-e29b-41d4-a716-446655440000"
    bl = client.post(
        "/v1/baselines",
        json=baseline_body(sha=sha_a),
    ).json()
    vr = client.post(
        "/v1/verifications",
        json=verify_body(sha=sha_a, baseline_id=bl["baseline_id"]),
    ).json()
    doc = client.get(f"/v1/reports/{vr['verification_id']}").json()
    # Milestone: transfer_id must appear in report/detail for the joint narrative
    blob = str(doc)
    assert transfer_id in blob
    assert doc.get("caller") == "mvp-saas" or "transfer_id" in doc.get("detail", {})


@pytest.mark.xfail(reason="TODO(m5): optional docker-compose.demo.yml wiring IVS alone for Daniel")
def test_demo_compose_file_exists():
    candidates = [
        ROOT / "docker-compose.demo.yml",
        ROOT / "compose.demo.yml",
        ROOT / "deploy" / "docker-compose.demo.yml",
    ]
    assert any(p.is_file() for p in candidates)

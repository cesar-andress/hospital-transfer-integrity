"""M4: metrics table, SIEM-shaped export, regulatory note.

TODO(m4): implement metrics aggregation and SIEM event payloads.
Remove every TODO(m4) and xfail when green.
"""

from pathlib import Path

import pytest

from tests.conftest import baseline_body, verify_body

pytestmark = [pytest.mark.acceptance]

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.xfail(reason="TODO(m4): GET /v1/metrics (or equivalent) returning corpus summary")
def test_metrics_endpoint_exists(client):
    r = client.get("/v1/metrics")
    assert r.status_code == 200
    body = r.json()
    assert "total_verifications" in body
    assert "by_verdict" in body


@pytest.mark.xfail(reason="TODO(m4): metrics must break down by object.kind (file/ehr/dicom)")
def test_metrics_by_kind(client, sha_a, sha_b):
    client.post("/v1/baselines", json=baseline_body(sha=sha_a, kind="file"))
    client.post("/v1/verifications", json=verify_body(sha=sha_a))
    body = client.get("/v1/metrics").json()
    assert "by_kind" in body
    assert "file" in body["by_kind"]


@pytest.mark.xfail(reason="TODO(m4): report.siem_event populated when verdict != intact")
def test_report_includes_siem_event_on_altered(client, sha_a, sha_b):
    bl = client.post("/v1/baselines", json=baseline_body(sha=sha_a)).json()
    vr = client.post(
        "/v1/verifications",
        json=verify_body(sha=sha_b, baseline_id=bl["baseline_id"]),
    ).json()
    doc = client.get(f"/v1/reports/{vr['verification_id']}").json()
    assert doc["verdict"] == "altered"
    assert isinstance(doc.get("siem_event"), dict)
    assert doc["siem_event"].get("event_type") in {
        "integrity.altered",
        "ivs.verdict.altered",
        "integrity_verification",
    }


@pytest.mark.xfail(reason="TODO(m4): SIEM event must carry tenant_id, verification_id, severity")
def test_siem_event_required_fields(client, sha_a, sha_b):
    bl = client.post("/v1/baselines", json=baseline_body(sha=sha_a)).json()
    vr = client.post(
        "/v1/verifications",
        json=verify_body(sha=sha_b, baseline_id=bl["baseline_id"]),
    ).json()
    event = client.get(f"/v1/reports/{vr['verification_id']}").json()["siem_event"]
    for key in ("tenant_id", "verification_id", "severity", "timestamp"):
        assert key in event


@pytest.mark.xfail(reason="TODO(m4): docs/regulatory.md (or section) with NIS2/GDPR/health-data note")
def test_regulatory_doc_exists():
    candidates = [
        ROOT / "docs" / "regulatory.md",
        ROOT / "docs" / "REGULATORY.md",
        ROOT / "docs" / "compliance.md",
    ]
    assert any(p.is_file() and p.stat().st_size > 200 for p in candidates)


@pytest.mark.xfail(reason="TODO(m4): metrics table exported as CSV/JSON artifact for the memoir")
def test_metrics_export_artifact(client):
    r = client.get("/v1/metrics/export")
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith(("application/json", "text/csv"))

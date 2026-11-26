"""M3 — synthetic EHR/DICOM corpus and attack harness.

TODO(m3): load clinical fixtures, mutate them (flip / encrypt / insider edit),
and assert veredicts. Remove every TODO(m3) and xfail when green.
"""

from pathlib import Path

import pytest

from tests.conftest import baseline_body, verify_body

pytestmark = [pytest.mark.acceptance]

FIXTURES = Path(__file__).resolve().parents[2] / "tests" / "fixtures"


@pytest.mark.xfail(reason="TODO(m3): synthetic EHR fixture corpus under tests/fixtures/ehr/")
def test_ehr_fixture_corpus_exists():
    ehr_dir = FIXTURES / "ehr"
    assert ehr_dir.is_dir()
    assert any(ehr_dir.glob("*.json")) or any(ehr_dir.glob("*.xml"))


@pytest.mark.xfail(reason="TODO(m3): synthetic DICOM (or imaging stand-in) under tests/fixtures/dicom/")
def test_dicom_fixture_corpus_exists():
    dicom_dir = FIXTURES / "dicom"
    assert dicom_dir.is_dir()
    assert any(dicom_dir.iterdir())


@pytest.mark.xfail(reason="TODO(m3): register baseline for kind=ehr_record with clinical metadata")
def test_baseline_accepts_ehr_record_kind(client, sha_a):
    body = baseline_body(sha=sha_a, kind="ehr_record")
    body["object"]["clinical"] = {"patient_id_hash": "ph_demo", "record_type": "discharge_summary"}
    r = client.post("/v1/baselines", json=body)
    assert r.status_code == 200
    assert r.json()["status"] == "registered"
    # Milestone expectation: clinical metadata round-trips into report/detail
    vr = client.post(
        "/v1/verifications",
        json=verify_body(sha=sha_a, baseline_id=r.json()["baseline_id"]),
    ).json()
    assert "clinical" in vr.get("detail", {}) or vr["verdict"] == "intact"
    assert False, "TODO(m3): assert clinical metadata is retained end-to-end"


@pytest.mark.xfail(reason="TODO(m3): register baseline for kind=dicom_study")
def test_baseline_accepts_dicom_study_kind(client, sha_a):
    body = baseline_body(sha=sha_a, kind="dicom_study")
    body["object"]["clinical"] = {"modality": "CT", "study_uid": "1.2.3.demo"}
    body["object"]["media_type"] = "application/dicom"
    r = client.post("/v1/baselines", json=body)
    assert r.status_code == 200
    assert "dicom" in str(r.json()).lower() or r.json()["status"] == "registered"
    assert False, "TODO(m3): assert DICOM-specific handling beyond opaque hash"


@pytest.mark.xfail(reason="TODO(m3): bit-flip attack must yield verdict=altered")
def test_attack_bit_flip_marks_altered(client, sha_a, sha_b):
    # sha_b stands in for a flipped payload hash until real fixtures land
    bl = client.post("/v1/baselines", json=baseline_body(sha=sha_a, kind="ehr_record")).json()
    vr = client.post(
        "/v1/verifications",
        json=verify_body(sha=sha_b, baseline_id=bl["baseline_id"]),
    ).json()
    assert vr["verdict"] == "altered"
    assert vr["detail"].get("attack_class") == "bit_flip"


@pytest.mark.xfail(reason="TODO(m3): encryption/ransomware-like attack → encrypted_or_unreadable")
def test_attack_encryption_marks_encrypted_or_unreadable(client, sha_a):
    bl = client.post("/v1/baselines", json=baseline_body(sha=sha_a)).json()
    body = verify_body(sha=sha_a, baseline_id=bl["baseline_id"])
    body["context"] = {
        "reason": "post_incident_check",
        "incident_id": "sim-ransom-001",
        "attack_class": "encryption",
        "readable": False,
    }
    vr = client.post("/v1/verifications", json=body).json()
    assert vr["verdict"] == "encrypted_or_unreadable"


@pytest.mark.xfail(reason="TODO(m3): insider edit (content change, same id) → altered")
def test_attack_insider_edit_marks_altered(client, sha_a, sha_b):
    bl = client.post(
        "/v1/baselines",
        json=baseline_body(sha=sha_a, kind="ehr_record"),
    ).json()
    body = verify_body(sha=sha_b, baseline_id=bl["baseline_id"])
    body["context"] = {"reason": "insider_modification", "attack_class": "insider_edit"}
    vr = client.post("/v1/verifications", json=body).json()
    assert vr["verdict"] == "altered"
    assert vr["detail"].get("attack_class") == "insider_edit"


@pytest.mark.xfail(reason="TODO(m3): attack harness CLI/module under app/attacks or scripts/")
def test_attack_harness_module_importable():
    import importlib

    mod = importlib.import_module("app.attacks")
    assert hasattr(mod, "bit_flip") or hasattr(mod, "encrypt_blob") or hasattr(mod, "insider_edit")

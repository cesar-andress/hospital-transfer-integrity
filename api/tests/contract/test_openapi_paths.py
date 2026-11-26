"""Contract: OpenAPI documents the paths Daniel calls."""

from pathlib import Path

import pytest
import yaml

pytestmark = [pytest.mark.contract]

ROOT = Path(__file__).resolve().parents[2]
OPENAPI = ROOT / "docs" / "openapi-integrity.yaml"


@pytest.fixture(scope="module")
def spec():
    assert OPENAPI.is_file()
    return yaml.safe_load(OPENAPI.read_text())


def test_contract_version_is_010(spec):
    assert spec["info"]["x-contract-version"] == "0.1.0"
    assert spec["info"]["version"] == "0.1.0"


@pytest.mark.parametrize(
    "path",
    ["/v1/health", "/v1/baselines", "/v1/verifications", "/v1/reports/{verification_id}"],
)
def test_required_paths_exist(spec, path):
    assert path in spec["paths"]


def test_object_kind_includes_clinical_types(spec):
    kinds = spec["components"]["schemas"]["ObjectRef"]["properties"]["kind"]["enum"]
    assert set(kinds) >= {"file", "ehr_record", "dicom_study"}


def test_verdict_enum_matches_contract(spec):
    enum = spec["components"]["schemas"]["VerificationResponse"]["properties"]["verdict"]["enum"]
    assert set(enum) == {
        "intact",
        "altered",
        "encrypted_or_unreadable",
        "unknown",
        "passthrough",
    }


def test_baseline_request_requires_core_fields(spec):
    required = set(spec["components"]["schemas"]["BaselineRequest"]["required"])
    assert required >= {"contract_version", "tenant_id", "object"}

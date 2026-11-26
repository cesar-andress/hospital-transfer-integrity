"""Shared fixtures for IVS tests."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.store import store


@pytest.fixture(autouse=True)
def _clean_store():
    store.clear()
    yield
    store.clear()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sha_a():
    return "a" * 64


@pytest.fixture
def sha_b():
    return "b" * 64


def baseline_body(tenant="tenant_a", sha=None, kind="file", **extra):
    body = {
        "contract_version": "0.1.0",
        "tenant_id": tenant,
        "object": {
            "kind": kind,
            "transfer_id": "550e8400-e29b-41d4-a716-446655440000",
            "filename": "historia_sintetica.pdf",
            "media_type": "application/pdf",
            "size_bytes": 12345,
            "sha256": sha or ("a" * 64),
        },
        "context": {"source": "mvp-saas-upload", "case": "ehr_document"},
    }
    body.update(extra)
    return body


def verify_body(tenant="tenant_a", sha=None, baseline_id=None, **extra):
    body = {
        "contract_version": "0.1.0",
        "tenant_id": tenant,
        "object": {
            "kind": "file",
            "transfer_id": "550e8400-e29b-41d4-a716-446655440000",
            "sha256": sha or ("a" * 64),
        },
        "context": {"reason": "post_incident_check", "incident_id": "sim-ransom-001"},
    }
    if baseline_id:
        body["baseline_id"] = baseline_id
    body.update(extra)
    return body

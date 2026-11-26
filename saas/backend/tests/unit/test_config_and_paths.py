"""Pure-logic tests: settings and per-tenant storage path rules."""

import os
import re

import pytest

from app.config import Settings


def test_database_url_is_built_from_settings(monkeypatch):
    cfg = Settings()
    cfg.POSTGRES_USER, cfg.POSTGRES_PASSWORD = "u", "p"
    cfg.POSTGRES_SERVER, cfg.POSTGRES_PORT, cfg.POSTGRES_DB = "db", "5432", "saas_db"
    assert cfg.DATABASE_URL == "postgresql://u:p@db:5432/saas_db"


def test_storage_base_path_comes_from_environment(storage_root):
    from app.database import STORAGE_BASE_PATH

    assert os.path.abspath(STORAGE_BASE_PATH) == os.path.abspath(str(storage_root))


def _is_under(root, candidate):
    root, candidate = os.path.abspath(root), os.path.abspath(candidate)
    return candidate == root or candidate.startswith(root + os.sep)


def test_tenant_roots_are_siblings_never_nested(storage_root):
    """Prefix-similar ids (acme / acme_2) must not share or nest directories."""
    a = os.path.join(str(storage_root), "acme")
    b = os.path.join(str(storage_root), "acme_2")
    assert not _is_under(a, b)
    assert not _is_under(b, a)


@pytest.mark.parametrize("tenant_id", ["../evil", "a/b", "a\\b", "", " ", "x;y", "..", "a b"])
def test_tenant_id_pattern_rejects_unsafe_values(tenant_id):
    """Same pattern the admin router enforces on tenant creation."""
    assert re.match(r"^[a-zA-Z0-9_-]+$", tenant_id) is None


@pytest.mark.parametrize("tenant_id", ["tenant_a", "acme-2", "ORG_9"])
def test_tenant_id_pattern_accepts_safe_values(tenant_id):
    assert re.match(r"^[a-zA-Z0-9_-]+$", tenant_id)


def test_cif_extraction_from_woocommerce_payload():
    from app.routers.webhook_router import _extract_cif_from_payload

    assert _extract_cif_from_payload({}, {"cif_nif": " b123 "}) == "B123"
    meta = {"meta_data": [{"key": "_billing_cif_nif", "value": "x9"}]}
    assert _extract_cif_from_payload(meta, {}) == "X9"
    assert _extract_cif_from_payload({}, {}) == ""

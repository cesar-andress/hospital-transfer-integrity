"""Spec: shared front end, tenant resolved from the login / Host header.

Target flow: ``https://<tenant>.app.saas.local`` (nginx wildcard) -> the single
SPA -> login without typing a tenant id -> API issues a token bound to the
tenant resolved from the Host. Today the tenant id is typed in the login form.
"""

import re

import pytest
import yaml

from tests.conftest import BACKEND_DIR, REPO_ROOT

NGINX = (REPO_ROOT / "nginx.conf").read_text(encoding="utf-8")
APP_JSX = (REPO_ROOT / "frontend" / "src" / "App.jsx").read_text(encoding="utf-8")
COMPOSE = yaml.safe_load((REPO_ROOT / "docker-compose.yml").read_text(encoding="utf-8"))


# ---- Static: front end routes ----------------------------------------------- #
@pytest.mark.static
def test_public_download_route_precedes_the_catch_all():
    assert 'path="/download/:transferId"' in APP_JSX
    assert APP_JSX.index('path="/download/:transferId"') < APP_JSX.index('path="*"')


@pytest.mark.static
@pytest.mark.parametrize("route", ['path="/login"', 'path="/admin"', 'path="/admin/monitor"', 'path="/tenant"'])
def test_expected_spa_routes_exist(route):
    assert route in APP_JSX


@pytest.mark.static
def test_admin_and_tenant_routes_are_role_guarded():
    assert "auth?.role === 'admin'" in APP_JSX and "auth?.role === 'user'" in APP_JSX


# ---- Static: one shared front end ------------------------------------------- #
@pytest.mark.static
def test_compose_runs_a_single_shared_frontend_service():
    services = COMPOSE["services"]
    frontends = [name for name in services if name.startswith("frontend")]
    assert frontends == ["frontend"], "no per-tenant front end containers"


@pytest.mark.static
def test_nginx_proxies_the_spa_and_the_api_on_separate_hosts():
    names = re.findall(r"server_name\s+([^;]+);", NGINX)
    assert "app.saas.local" in names and "api.saas.local" in names


@pytest.mark.static
def test_backend_storage_is_a_mounted_volume():
    volumes = COMPOSE["services"]["backend"]["volumes"]
    assert any("/app/vm_storage" in v for v in volumes)


# ---- Current login behaviour (passing) -------------------------------------- #
def test_login_requires_tenant_id_today(api):
    resp = api.client.post("/api/v1/auth/login", json={"email": "user1@alfa.com", "password": "password123"})
    assert resp.status_code == 422


def test_login_unknown_tenant_is_404(api):
    assert api.login("ghost", "x@x.test", "pw").status_code == 404


def test_token_carries_the_tenant_it_was_issued_for(api):
    resp = api.login("tenant_b", "user1@beta.com", "password123").json()
    assert resp["tenant_id"] == "tenant_b" and resp["role"] == "user"


# ---- Spec gaps --------------------------------------------------------------- #
@pytest.mark.xfail(reason="nginx has fixed server_names only; no wildcard/regex block for <tenant>.app.saas.local")
@pytest.mark.static
def test_nginx_has_wildcard_server_for_tenant_subdomains():
    assert re.search(r"server_name\s+[^;]*(\*\.app\.saas\.local|~\^\(\?<tenant>)", NGINX)


@pytest.mark.xfail(reason="nginx does not forward the resolved tenant (X-Tenant-ID) to the API")
@pytest.mark.static
def test_nginx_forwards_tenant_identity_to_the_api():
    assert "X-Tenant-ID" in NGINX or "X-Forwarded-Host" in NGINX


@pytest.mark.xfail(reason="login ignores Host; tenant_id must come from the form")
def test_login_resolves_tenant_from_host_header(api):
    resp = api.client.post(
        "/api/v1/auth/login",
        json={"email": "user1@alfa.com", "password": "password123"},
        headers={"X-Forwarded-Host": "tenant_a.app.saas.local"},
    )
    assert resp.status_code == 200 and resp.json()["tenant_id"] == "tenant_a"


@pytest.mark.xfail(reason="login does not cross-check body tenant_id against the Host tenant")
def test_login_rejects_tenant_mismatch_between_host_and_body(api):
    resp = api.login("tenant_b", "user1@beta.com", "password123",
                     headers={"X-Forwarded-Host": "tenant_a.app.saas.local"})
    assert resp.status_code in (400, 403)


@pytest.mark.xfail(reason="API does not compare token tenant with the Host tenant")
def test_token_of_tenant_a_is_rejected_on_tenant_b_host(api):
    headers = api.user_headers("tenant_a")
    headers["X-Forwarded-Host"] = "tenant_b.app.saas.local"
    assert api.client.get("/api/v1/app/doc", headers=headers).status_code in (401, 403)


@pytest.mark.xfail(reason="no storage backend abstraction yet (app.storage); needed to swap folder -> real Linux VM")
def test_storage_backend_abstraction_exists():
    import importlib

    storage = importlib.import_module("app.storage")
    assert hasattr(storage, "get_backend")
    backend = storage.get_backend("tenant_a")
    for method in ("put", "open", "delete", "exists"):
        assert callable(getattr(backend, method))


@pytest.mark.xfail(reason="tenants has no vm_host / vm_type column to point a tenant at a real Linux VM")
@pytest.mark.static
def test_schema_can_describe_a_real_vm_per_tenant():
    sql = (BACKEND_DIR / "scripts" / "init_db.sql").read_text(encoding="utf-8")
    assert "vm_host" in sql and "vm_backend" in sql

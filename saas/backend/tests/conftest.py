"""Shared fixtures for the unit and acceptance suites.

PostgreSQL strategy (first match wins):
  1. ``TEST_DATABASE_URL`` (e.g. the docker-compose ``db`` service).
  2. A throw-away local cluster started with ``initdb``/``pg_ctl`` found under
     ``/usr/lib/postgresql/*/bin`` or on ``PATH``.
  3. Otherwise every test marked ``db`` is skipped (unit tests still run).
  ``TEST_SKIP_DB=1`` forces the skip (static/unit checks only).

Storage never touches the real ``vm_storage/``: ``STORAGE_BASE_PATH`` points to
a temp directory created before the app is imported.
"""

import glob
import os
import shutil
import socket
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
INIT_SQL = BACKEND_DIR / "scripts" / "init_db.sql"

# Must happen before ``app.database`` is imported (value is read at import time).
_STORAGE_ROOT = tempfile.mkdtemp(prefix="mvp_saas_vm_storage_")
os.environ["STORAGE_BASE_PATH"] = _STORAGE_ROOT
os.environ.setdefault("FRONTEND_TRANSFER_URL", "http://app.saas.local")


# --------------------------------------------------------------------------- #
# PostgreSQL provisioning
# --------------------------------------------------------------------------- #
def _find_pg_bin(name):
    found = shutil.which(name)
    if found:
        return found
    candidates = sorted(glob.glob(f"/usr/lib/postgresql/*/bin/{name}"), reverse=True)
    return candidates[0] if candidates else None


def _free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class _PgInfo:
    """Connection parameters for the database used by the test session."""

    def __init__(self, user, password, host, port, dbname):
        self.user, self.password = user, password
        self.host, self.port, self.dbname = host, str(port), dbname


@pytest.fixture(scope="session")
def pg_info():
    if os.getenv("TEST_SKIP_DB"):
        pytest.skip("TEST_SKIP_DB is set")
    url = os.getenv("TEST_DATABASE_URL")
    if url:
        parsed = urlparse(url)
        yield _PgInfo(
            parsed.username or "postgres",
            parsed.password or "",
            parsed.hostname or "localhost",
            parsed.port or 5432,
            (parsed.path or "/saas_db").lstrip("/"),
        )
        return

    initdb, pg_ctl = _find_pg_bin("initdb"), _find_pg_bin("pg_ctl")
    if not initdb or not pg_ctl:
        pytest.skip("PostgreSQL not available (set TEST_DATABASE_URL or install server binaries)")

    data_dir = tempfile.mkdtemp(prefix="mvp_saas_pg_")
    sock_dir = tempfile.mkdtemp(prefix="mvp_saas_pgsock_")
    port = _free_port()
    subprocess.run(
        [initdb, "-D", data_dir, "-U", "postgres", "-A", "trust", "-E", "UTF8"],
        check=True, capture_output=True,
    )
    subprocess.run(
        [pg_ctl, "-D", data_dir, "-w", "-l", os.path.join(data_dir, "pg.log"),
         "-o", f"-p {port} -k {sock_dir} -c listen_addresses=127.0.0.1 -c fsync=off",
         "start"],
        check=True, capture_output=True,
    )
    try:
        yield _PgInfo("postgres", "", "127.0.0.1", port, "postgres")
    finally:
        subprocess.run([pg_ctl, "-D", data_dir, "-m", "immediate", "stop"],
                       capture_output=True)
        shutil.rmtree(data_dir, ignore_errors=True)
        shutil.rmtree(sock_dir, ignore_errors=True)


@pytest.fixture(scope="session")
def _configured_settings(pg_info):
    """Point the app settings at the test database (instance-level override)."""
    from app.config import settings

    settings.POSTGRES_USER = pg_info.user
    settings.POSTGRES_PASSWORD = pg_info.password
    settings.POSTGRES_SERVER = pg_info.host
    settings.POSTGRES_PORT = pg_info.port
    settings.POSTGRES_DB = pg_info.dbname
    return settings


def _reset_database(settings):
    import psycopg2

    conn = psycopg2.connect(settings.DATABASE_URL)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(INIT_SQL.read_text(encoding="utf-8"))
        cur.execute("TRUNCATE audit_logs, transfers, users, tenants RESTART IDENTITY CASCADE")
        cur.execute(INIT_SQL.read_text(encoding="utf-8"))  # re-seed demo rows
        # The seed hard-codes the container path; redirect it to the temp root.
        cur.execute(
            "UPDATE tenants SET vm_storage_path = %s || '/' || tenant_id "
            "WHERE vm_storage_path LIKE '/app/vm_storage/%%'",
            (_STORAGE_ROOT,),
        )
    conn.close()


def _reset_storage():
    for entry in Path(_STORAGE_ROOT).iterdir():
        shutil.rmtree(entry, ignore_errors=True) if entry.is_dir() else entry.unlink()


@pytest.fixture
def db_settings(_configured_settings):
    """Fresh seeded schema + empty storage root for every test."""
    _reset_database(_configured_settings)
    _reset_storage()
    return _configured_settings


@pytest.fixture
def storage_root():
    return Path(_STORAGE_ROOT)


# --------------------------------------------------------------------------- #
# Outbound mail capture
# --------------------------------------------------------------------------- #
@pytest.fixture
def outbox(monkeypatch):
    """Capture transfer + activation emails instead of talking to MailHog."""
    sent = {"transfer": [], "activation": []}

    def fake_transfer(recipient, sender, file_name, download_url, otp_code):
        sent["transfer"].append(dict(recipient=recipient, sender=sender,
                                     file_name=file_name, download_url=download_url,
                                     otp_code=otp_code))

    def fake_activation(recipient, tenant_id, company, password, **kwargs):
        sent["activation"].append(dict(recipient=recipient, tenant_id=tenant_id,
                                       company=company, password=password, **kwargs))

    monkeypatch.setattr("app.routers.doc_router.send_transfer_email", fake_transfer)
    monkeypatch.setattr("app.routers.webhook_router.send_activation_email", fake_activation)
    return sent


# --------------------------------------------------------------------------- #
# HTTP client + helpers
# --------------------------------------------------------------------------- #
@pytest.fixture
def client(db_settings, outbox):
    from fastapi.testclient import TestClient

    from app.main import app

    # raise_server_exceptions=False: an unhandled error is a 500 the spec can assert on.
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


class Api:
    """Tiny helper that speaks the public API the way the SPA does."""

    def __init__(self, client):
        self.client = client

    def login(self, tenant_id, email, password, headers=None):
        return self.client.post(
            "/api/v1/auth/login",
            json={"tenant_id": tenant_id, "email": email, "password": password},
            headers=headers,
        )

    def token(self, tenant_id, email, password):
        resp = self.login(tenant_id, email, password)
        assert resp.status_code == 200, resp.text
        return resp.json()["access_token"]

    @staticmethod
    def bearer(token):
        return {"Authorization": f"Bearer {token}"}

    def admin_headers(self):
        return self.bearer(self.token("admin", "admin@saas.com", "adminpassword"))

    def user_headers(self, tenant_id="tenant_a", email=None, password="password123"):
        email = email or {"tenant_a": "user1@alfa.com", "tenant_b": "user1@beta.com"}[tenant_id]
        return self.bearer(self.token(tenant_id, email, password))

    def upload(self, headers, name="hello.txt", content=b"hello", recipient=None, title=None):
        data = {}
        if recipient:
            data["recipient"] = recipient
        if title:
            data["title"] = title
        return self.client.post(
            "/api/v1/app/doc", headers=headers, data=data,
            files={"file": (name, content, "application/octet-stream")},
        )

    def documents(self, headers):
        resp = self.client.get("/api/v1/app/doc", headers=headers)
        assert resp.status_code == 200, resp.text
        return resp.json()

    def create_tenant(self, tenant_id, email=None, password="pw-12345", **extra):
        body = {"tenant_id": tenant_id, "name": f"Org {tenant_id}",
                "email": email or f"owner@{tenant_id}.test", "password": password}
        body.update(extra)
        return self.client.post("/api/v1/admin/tenants", json=body,
                                headers=self.admin_headers())


@pytest.fixture
def api(client):
    return Api(client)


@pytest.fixture
def db_conn(db_settings):
    """Direct psycopg2 connection for arranging/inspecting rows."""
    import psycopg2
    from psycopg2.extras import RealDictCursor

    conn = psycopg2.connect(db_settings.DATABASE_URL, cursor_factory=RealDictCursor)
    conn.autocommit = True
    yield conn
    conn.close()


# --------------------------------------------------------------------------- #
# Marker plumbing
# --------------------------------------------------------------------------- #
def pytest_collection_modifyitems(items):
    """Everything under tests/acceptance is an acceptance test; tag DB users."""
    for item in items:
        path = str(item.fspath)
        if f"{os.sep}acceptance{os.sep}" in path:
            item.add_marker(pytest.mark.acceptance)
        if {"api", "client", "db_conn", "db_settings"} & set(item.fixturenames):
            item.add_marker(pytest.mark.db)

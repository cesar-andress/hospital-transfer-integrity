"""Acceptance battery for the 2026-12-02 path-guards milestone.

See ``docs/NEXT.md`` (path-guards milestone).

Daniel: implement the guards, make every test in this file pass, then remove
**all** ``TODO(path-guards)`` comments and ``@pytest.mark.xfail`` markers tied
to this milestone (this file + ``test_storage_paths.py`` + the matching xfails
in ``test_tenant_isolation.py`` / ``test_otp_download.py``).

Out of scope here: OTP lockout, single-use links, Host binding, credits, Alessa IVS.
"""

import os
from pathlib import Path

import pytest

pytestmark = [pytest.mark.acceptance, pytest.mark.db]


def _files_under(root: Path):
    if not root.exists():
        return []
    return [p for p in root.rglob("*") if p.is_file()]


def _verify(api, transfer_id, otp):
    return api.client.post(
        f"/api/v1/app/download/{transfer_id}/verify-otp",
        json={"otp_code": otp},
    )


# --------------------------------------------------------------------------- #
# Upload sanitisation
# --------------------------------------------------------------------------- #
@pytest.mark.xfail(reason="TODO(path-guards): upload title with ../ must not 500; prefer 400")
def test_upload_rejects_traversal_title_with_client_error(api, storage_root):
    # TODO(path-guards): remove xfail when upload returns 4xx and never writes outside tenant root
    headers = api.user_headers("tenant_a")
    resp = api.upload(headers, "x.txt", b"pwn", title="../../evil.txt")
    assert resp.status_code == 400
    assert not (storage_root.parent / "evil.txt").exists()
    for stored in _files_under(storage_root / "tenant_a"):
        assert os.path.abspath(str(stored)).startswith(str(storage_root / "tenant_a") + os.sep)


@pytest.mark.xfail(reason="TODO(path-guards): absolute-looking titles must be rejected")
def test_upload_rejects_absolute_title(api, storage_root):
    # TODO(path-guards)
    headers = api.user_headers("tenant_a")
    before = set(_files_under(storage_root / "tenant_a"))
    resp = api.upload(headers, "x.txt", b"pwn", title="/tmp/evil.txt")
    assert resp.status_code == 400
    after = set(_files_under(storage_root / "tenant_a"))
    assert after == before
    for stored in after:
        assert os.path.abspath(str(stored)).startswith(str(storage_root / "tenant_a") + os.sep)


@pytest.mark.xfail(reason="TODO(path-guards): vm_storage_path outside STORAGE_BASE_PATH must be refused")
def test_upload_rejects_storage_path_outside_base(api, db_conn, storage_root):
    # TODO(path-guards)
    with db_conn.cursor() as cur:
        cur.execute(
            "UPDATE tenants SET vm_storage_path = %s WHERE tenant_id = 'tenant_a'",
            (str(storage_root.parent / "outside"),),
        )
    resp = api.upload(api.user_headers("tenant_a"), "x.txt", b"data")
    assert resp.status_code >= 400
    assert not (storage_root.parent / "outside").exists()


# --------------------------------------------------------------------------- #
# OTP download re-check
# --------------------------------------------------------------------------- #
@pytest.fixture
def sent(api, outbox):
    content = b"path-guard-payload"
    resp = api.upload(
        api.user_headers("tenant_a"),
        "contract.pdf",
        content,
        recipient="client@ext.test",
    )
    assert resp.status_code == 200, resp.text
    mail = outbox["transfer"][0]
    return resp.json()["transfer_id"], mail["otp_code"], content


@pytest.mark.xfail(reason="TODO(path-guards): OTP must not serve a path outside the tenant root")
def test_otp_refuses_file_outside_tenant_root(api, sent, db_conn, tmp_path):
    # TODO(path-guards)
    transfer_id, otp, _ = sent
    secret = tmp_path / "outside-secret.txt"
    secret.write_text("not a tenant file")
    with db_conn.cursor() as cur:
        cur.execute(
            "UPDATE transfers SET file_path = %s WHERE id = %s::uuid",
            (str(secret), transfer_id),
        )
    resp = _verify(api, transfer_id, otp)
    assert resp.status_code in (403, 404)
    assert b"not a tenant file" not in resp.content


@pytest.mark.xfail(reason="TODO(path-guards): OTP must not serve another tenant's file")
def test_otp_refuses_file_in_other_tenant_root(api, sent, db_conn, storage_root):
    # TODO(path-guards)
    transfer_id, otp, _ = sent
    foreign = storage_root / "tenant_b" / "other.txt"
    foreign.parent.mkdir(parents=True, exist_ok=True)
    foreign.write_text("tenant-b-private")
    with db_conn.cursor() as cur:
        cur.execute(
            "UPDATE transfers SET file_path = %s WHERE id = %s::uuid",
            (str(foreign), transfer_id),
        )
    resp = _verify(api, transfer_id, otp)
    assert resp.status_code in (403, 404)
    assert b"tenant-b-private" not in resp.content


@pytest.mark.xfail(reason="TODO(path-guards): symlink escape should be rejected if present")
def test_otp_refuses_symlink_escape(api, sent, db_conn, storage_root, tmp_path):
    # TODO(path-guards): if the platform allows symlinks under the VM root
    transfer_id, otp, _ = sent
    outside = tmp_path / "linked-secret.txt"
    outside.write_text("via-symlink")
    link = storage_root / "tenant_a" / "link.txt"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("symlinks not available")
    with db_conn.cursor() as cur:
        cur.execute(
            "UPDATE transfers SET file_path = %s WHERE id = %s::uuid",
            (str(link), transfer_id),
        )
    resp = _verify(api, transfer_id, otp)
    assert resp.status_code in (403, 404)
    assert b"via-symlink" not in resp.content

"""Spec: every tenant owns exactly one storage root (its "VM" filesystem).

Upload / list / delete are always scoped to the caller's tenant and files of
different tenants never collide on disk.
"""

import os
from pathlib import Path

import pytest


def _files_under(root: Path):
    return sorted(p for p in root.rglob("*") if p.is_file())


def test_seeded_tenants_have_distinct_non_nested_storage_roots(db_conn):
    with db_conn.cursor() as cur:
        cur.execute("SELECT tenant_id, vm_storage_path FROM tenants ORDER BY tenant_id")
        rows = {r["tenant_id"]: os.path.abspath(r["vm_storage_path"]) for r in cur.fetchall()}
    assert rows["tenant_a"] != rows["tenant_b"]
    assert not rows["tenant_b"].startswith(rows["tenant_a"] + os.sep)
    assert not rows["tenant_a"].startswith(rows["tenant_b"] + os.sep)


def test_prefix_similar_tenant_ids_get_separate_roots(api, storage_root, db_conn):
    assert api.create_tenant("acme").status_code == 201
    assert api.create_tenant("acme_2").status_code == 201
    a, b = storage_root / "acme", storage_root / "acme_2"
    assert a.is_dir() and b.is_dir()
    assert not str(b).startswith(str(a) + os.sep)


def test_admin_rejects_path_traversal_tenant_ids(api, storage_root):
    for bad in ("../evil", "a/b", ".."):
        assert api.create_tenant(bad).status_code in (400, 422)
    assert not (storage_root.parent / "evil").exists()


def test_admin_create_tenant_creates_storage_root_and_first_user(api, storage_root, db_conn):
    resp = api.create_tenant("newco", max_accounts=3, quota_limit=7)
    assert resp.status_code == 201
    assert (storage_root / "newco").is_dir()
    with db_conn.cursor() as cur:
        cur.execute("SELECT count(*) AS n FROM users WHERE tenant_id = 'newco'")
        assert cur.fetchone()["n"] == 1
    # The owner can log in right away.
    assert api.login("newco", "owner@newco.test", "pw-12345").status_code == 200


def test_upload_lands_only_under_the_callers_tenant_root(api, storage_root):
    headers = api.user_headers("tenant_a")
    assert api.upload(headers, "report.txt", b"alpha").status_code == 200
    assert len(_files_under(storage_root / "tenant_a")) == 1
    assert _files_under(storage_root / "tenant_b") == []


def test_same_filename_in_two_tenants_does_not_collide(api, storage_root):
    api.upload(api.user_headers("tenant_a"), "same.txt", b"A-data")
    api.upload(api.user_headers("tenant_b"), "same.txt", b"B-data")
    (fa,) = _files_under(storage_root / "tenant_a")
    (fb,) = _files_under(storage_root / "tenant_b")
    assert fa.read_bytes() == b"A-data" and fb.read_bytes() == b"B-data"


def test_same_filename_twice_in_one_tenant_keeps_both_versions(api, storage_root):
    headers = api.user_headers("tenant_a")
    api.upload(headers, "dup.txt", b"v1")
    api.upload(headers, "dup.txt", b"v2")
    assert sorted(p.read_bytes() for p in _files_under(storage_root / "tenant_a")) == [b"v1", b"v2"]


def test_listing_is_scoped_to_the_callers_tenant(api):
    api.upload(api.user_headers("tenant_a"), "a-only.txt")
    docs_a = api.documents(api.user_headers("tenant_a"))
    docs_b = api.documents(api.user_headers("tenant_b"))
    assert [d["title"] for d in docs_a["documents"]] == ["a-only.txt"]
    assert docs_b["documents"] == []
    assert docs_a["tenant_id"] == "tenant_a" and docs_b["tenant_id"] == "tenant_b"


def test_other_tenant_cannot_delete_my_document_and_file_survives(api, storage_root):
    owner = api.user_headers("tenant_a")
    transfer_id = api.upload(owner, "keep.txt").json()["transfer_id"]
    resp = api.client.delete(f"/api/v1/app/doc/{transfer_id}", headers=api.user_headers("tenant_b"))
    assert resp.status_code == 404
    assert len(_files_under(storage_root / "tenant_a")) == 1
    assert len(api.documents(owner)["documents"]) == 1


def test_owner_delete_removes_row_and_file(api, storage_root):
    owner = api.user_headers("tenant_a")
    transfer_id = api.upload(owner, "gone.txt").json()["transfer_id"]
    assert api.client.delete(f"/api/v1/app/doc/{transfer_id}", headers=owner).status_code == 200
    assert _files_under(storage_root / "tenant_a") == []
    assert api.documents(owner)["documents"] == []


def test_deleting_a_tenant_purges_only_its_own_storage(api, storage_root):
    api.upload(api.user_headers("tenant_a"), "a.txt")
    api.upload(api.user_headers("tenant_b"), "b.txt")
    resp = api.client.delete("/api/v1/admin/tenants/tenant_a", headers=api.admin_headers())
    assert resp.status_code == 200
    assert not (storage_root / "tenant_a").exists()
    assert len(_files_under(storage_root / "tenant_b")) == 1


def test_deactivated_tenant_token_is_revoked_immediately(api, db_conn):
    headers = api.user_headers("tenant_a")
    with db_conn.cursor() as cur:
        cur.execute("UPDATE tenants SET is_active = FALSE WHERE tenant_id = 'tenant_a'")
    assert api.client.get("/api/v1/app/doc", headers=headers).status_code == 401
    assert api.login("tenant_a", "user1@alfa.com", "password123").status_code == 403


def test_tenant_user_cannot_use_admin_endpoints(api):
    resp = api.client.get("/api/v1/admin/tenants", headers=api.user_headers("tenant_a"))
    assert resp.status_code == 403


def test_credentials_of_one_tenant_do_not_work_in_another(api):
    assert api.login("tenant_b", "user1@alfa.com", "password123").status_code == 401


# ---- Spec gaps (living spec: flip to passing, then remove the xfail) ------- #
@pytest.mark.xfail(reason="TODO(path-guards): upload does not sanitize `title`; traversal names currently crash (500)")
def test_upload_filename_traversal_is_neutralised(api, storage_root):
    headers = api.user_headers("tenant_a")
    resp = api.upload(headers, "x.txt", b"pwn", title="../../evil.txt")
    assert resp.status_code < 500
    assert not (storage_root.parent / "evil.txt").exists()
    for stored in _files_under(storage_root / "tenant_a"):
        assert os.path.abspath(stored).startswith(str(storage_root / "tenant_a") + os.sep)


@pytest.mark.xfail(reason="TODO(path-guards): upload trusts tenants.vm_storage_path; never re-validated under STORAGE_BASE_PATH")
def test_upload_rejects_tenant_whose_storage_path_escapes_base(api, db_conn, storage_root):
    with db_conn.cursor() as cur:
        cur.execute("UPDATE tenants SET vm_storage_path = %s WHERE tenant_id = 'tenant_a'",
                    (str(storage_root.parent / "outside"),))
    resp = api.upload(api.user_headers("tenant_a"), "x.txt")
    assert resp.status_code >= 400
    assert not (storage_root.parent / "outside").exists()

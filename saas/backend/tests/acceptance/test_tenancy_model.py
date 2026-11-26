"""Spec: one VM filesystem per tenant, N users per tenant, shared front end.

Also covers provisioning via the WooCommerce webhook (shop purchase -> tenant).
"""

import pytest


def _order(email="boss@newco.test", company="NewCo SL", cif="B12345678", **extra):
    payload = {"billing": {"email": email, "company": company, "cif_nif": cif}}
    payload.update(extra)
    return payload


# ---- Many users, one filesystem ------------------------------------------- #
def test_users_of_a_tenant_share_the_same_filesystem(api):
    u1 = api.user_headers("tenant_a", "user1@alfa.com")
    u2 = api.user_headers("tenant_a", "user2@alfa.com")
    api.upload(u1, "shared.txt", b"from-user1")
    titles = [d["title"] for d in api.documents(u2)["documents"]]
    assert titles == ["shared.txt"], "colleagues in the same tenant see the same VM files"


def test_users_table_has_no_private_storage_path(db_conn):
    with db_conn.cursor() as cur:
        cur.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'users'"
        )
        columns = {r["column_name"] for r in cur.fetchall()}
    assert "vm_storage_path" not in columns


def test_each_tenant_has_exactly_one_storage_root(db_conn):
    with db_conn.cursor() as cur:
        cur.execute("SELECT count(*) AS total, count(DISTINCT vm_storage_path) AS d FROM tenants")
        row = cur.fetchone()
    assert row["total"] == row["d"]


# ---- Provisioning via WooCommerce webhook --------------------------------- #
def test_webhook_provision_creates_tenant_user_and_storage_root(api, db_conn, storage_root, outbox):
    resp = api.client.post("/api/v1/webhooks/woocommerce", json=_order())
    assert resp.status_code == 200
    tenant_id = resp.json()["tenant_id"]
    assert tenant_id.startswith("tenant_")

    assert (storage_root / tenant_id).is_dir(), "storage root (the tenant VM) must exist"
    with db_conn.cursor() as cur:
        cur.execute("SELECT * FROM tenants WHERE tenant_id = %s", (tenant_id,))
        tenant = cur.fetchone()
        cur.execute("SELECT email FROM users WHERE tenant_id = %s", (tenant_id,))
        users = [r["email"] for r in cur.fetchall()]
    assert tenant["quota_limit"] == 100 and tenant["max_accounts"] == 10
    assert tenant["vm_storage_path"] == str(storage_root / tenant_id)
    assert users == ["boss@newco.test"]
    assert outbox["activation"][0]["tenant_id"] == tenant_id


def test_webhook_provisioned_owner_can_log_in_with_emailed_password(api, outbox):
    api.client.post("/api/v1/webhooks/woocommerce", json=_order())
    mail = outbox["activation"][0]
    assert api.login(mail["tenant_id"], mail["recipient"], mail["password"]).status_code == 200


def test_second_order_same_cif_upgrades_instead_of_creating_second_vm(api, db_conn, storage_root):
    first = api.client.post("/api/v1/webhooks/woocommerce", json=_order()).json()
    second = api.client.post("/api/v1/webhooks/woocommerce", json=_order()).json()
    assert second["tenant_id"] == first["tenant_id"]
    with db_conn.cursor() as cur:
        cur.execute("SELECT count(*) AS n, max(quota_limit) AS q FROM tenants WHERE tenant_id LIKE 'tenant_newco%%'")
        row = cur.fetchone()
    assert row["n"] == 1 and row["q"] == 200
    assert len([p for p in storage_root.iterdir() if p.name.startswith("tenant_newco")]) == 1


def test_two_different_companies_get_two_separate_vms(api, storage_root):
    a = api.client.post("/api/v1/webhooks/woocommerce", json=_order("a@a.test", "Same Name", "A1")).json()
    b = api.client.post("/api/v1/webhooks/woocommerce", json=_order("b@b.test", "Same Name", "B2")).json()
    assert a["tenant_id"] != b["tenant_id"]
    assert (storage_root / a["tenant_id"]).is_dir() and (storage_root / b["tenant_id"]).is_dir()


def test_webhook_ping_without_billing_email_creates_nothing(api, db_conn):
    resp = api.client.post("/api/v1/webhooks/woocommerce", json={"id": 1})
    assert resp.status_code == 200
    with db_conn.cursor() as cur:
        cur.execute("SELECT count(*) AS n FROM tenants")
        assert cur.fetchone()["n"] == 2  # only the seeded demo tenants


def test_resend_activation_unknown_email_is_404(api):
    resp = api.client.post("/api/v1/webhooks/resend-activation", json={"email": "nobody@x.test"})
    assert resp.status_code == 404


def test_check_company_reports_existing_and_unknown_companies(api):
    api.client.post("/api/v1/webhooks/woocommerce", json=_order())
    known = api.client.get("/api/v1/webhooks/check-company", params={"cif_nif": "b12345678"}).json()
    unknown = api.client.get("/api/v1/webhooks/check-company", params={"cif_nif": "NOPE"}).json()
    assert known["exists"] is True and known["tenant_id"].startswith("tenant_")
    assert unknown == {"exists": False}


# ---- Spec gaps -------------------------------------------------------------- #
@pytest.mark.xfail(reason="no endpoint to add users to a tenant yet; max_accounts is never enforced")
def test_tenant_cannot_exceed_max_accounts(api):
    api.create_tenant("tiny", max_accounts=2)
    admin = api.admin_headers()
    statuses = []
    for i in range(3):  # owner already counts as account #1
        resp = api.client.post(
            "/api/v1/admin/tenants/tiny/users",
            json={"email": f"u{i}@tiny.test", "password": "pw-12345", "name": f"U{i}"},
            headers=admin,
        )
        statuses.append(resp.status_code)
    assert statuses[0] == 201, "second account fits the limit"
    assert statuses[1] in (403, 409, 422), "third account exceeds max_accounts=2"


@pytest.mark.xfail(reason="tenant owner cannot invite colleagues yet (no /app/users endpoint)")
def test_tenant_owner_can_invite_a_colleague_into_the_same_vm(api):
    owner = api.user_headers("tenant_a")
    resp = api.client.post("/api/v1/app/users", json={"email": "new@alfa.com", "name": "New"}, headers=owner)
    assert resp.status_code == 201


@pytest.mark.xfail(reason="WooCommerce webhook is unauthenticated (demo); needs HMAC X-WC-Webhook-Signature")
def test_webhook_rejects_unsigned_requests(api, db_conn):
    resp = api.client.post("/api/v1/webhooks/woocommerce", json=_order("evil@x.test", "Evil", "Z9"))
    assert resp.status_code in (401, 403)


@pytest.mark.xfail(reason="activation mail contains the plaintext password; spec wants a one-time set-password link")
def test_activation_email_does_not_contain_plaintext_password(api, outbox):
    api.client.post("/api/v1/webhooks/woocommerce", json=_order())
    assert "password" not in outbox["activation"][0] or not outbox["activation"][0]["password"]


@pytest.mark.xfail(reason="passwords are stored in plaintext in the demo seed/login")
def test_passwords_are_hashed_at_rest(db_conn):
    with db_conn.cursor() as cur:
        cur.execute("SELECT password FROM users WHERE email = 'user1@alfa.com'")
        stored = cur.fetchone()["password"]
    assert stored != "password123"

"""Spec: credits are consumed on upload AND on download (OTP redeem).

Today the MVP exposes credits as ``quota_limit - COUNT(transfers)`` and
only "upload" consumes. Tests marked xfail describe the target behaviour.
"""

import pytest


@pytest.fixture
def sent(api, outbox):
    resp = api.upload(api.user_headers("tenant_a"), "doc.pdf", b"payload", recipient="c@ext.test")
    assert resp.status_code == 200
    return resp.json()["transfer_id"], outbox["transfer"][0]["otp_code"]


def _remaining(api, tenant="tenant_a"):
    return api.documents(api.user_headers(tenant))["quota_remaining"]


def _download(api, transfer_id, otp):
    return api.client.post(f"/api/v1/app/download/{transfer_id}/verify-otp", json={"otp_code": otp})


def test_new_tenant_starts_with_full_credits(api):
    assert _remaining(api, "tenant_a") == 100
    assert _remaining(api, "tenant_b") == 5


def test_upload_debits_one_credit(api):
    before = _remaining(api)
    api.upload(api.user_headers("tenant_a"), "a.txt")
    assert _remaining(api) == before - 1


def test_personal_upload_without_recipient_also_debits(api):
    before = _remaining(api)
    api.upload(api.user_headers("tenant_a"), "personal.txt")
    assert _remaining(api) == before - 1


def test_credits_are_per_tenant(api):
    api.upload(api.user_headers("tenant_a"), "a.txt")
    assert _remaining(api, "tenant_b") == 5


def test_upload_is_refused_when_credits_are_exhausted(api, storage_root):
    headers = api.user_headers("tenant_b")  # quota 5
    for i in range(5):
        assert api.upload(headers, f"f{i}.txt").status_code == 200
    resp = api.upload(headers, "over.txt")
    assert resp.status_code in (402, 429)
    assert _remaining(api, "tenant_b") == 0
    assert len(list((storage_root / "tenant_b").iterdir())) == 5, "refused upload must not hit disk"


def test_failed_otp_does_not_debit(api, sent):
    transfer_id, otp = sent
    before = _remaining(api)
    wrong = "000000" if otp != "000000" else "111111"
    assert _download(api, transfer_id, wrong).status_code == 401
    assert _remaining(api) == before


def test_webhook_upgrade_adds_100_credits(api):
    api.client.post("/api/v1/webhooks/woocommerce",
                    json={"billing": {"email": "user1@beta.com", "company": "Beta"}})
    assert _remaining(api, "tenant_b") == 105


def test_admin_listing_shows_remaining_credits(api):
    api.upload(api.user_headers("tenant_a"), "a.txt")
    rows = {r["tenant_id"]: r for r in api.client.get("/api/v1/admin/tenants", headers=api.admin_headers()).json()}
    assert rows["tenant_a"]["quota_remaining"] == 99


# ---- Spec gaps -------------------------------------------------------------- #
@pytest.mark.xfail(reason="OTP download does not debit a credit yet")
def test_successful_download_debits_one_credit(api, sent):
    transfer_id, otp = sent
    before = _remaining(api)
    assert _download(api, transfer_id, otp).status_code == 200
    assert _remaining(api) == before - 1


@pytest.mark.xfail(reason="download is served even when the sender tenant has no credits left")
def test_download_is_refused_when_tenant_has_no_credits(api, sent, db_conn):
    transfer_id, otp = sent
    with db_conn.cursor() as cur:
        cur.execute("UPDATE tenants SET quota_limit = 1 WHERE tenant_id = 'tenant_a'")  # 1 used, 0 left
    assert _remaining(api) == 0
    assert _download(api, transfer_id, otp).status_code in (402, 429)


@pytest.mark.xfail(reason="credits = limit - COUNT(transfers), so deleting a file refunds the upload credit")
def test_deleting_a_transfer_does_not_refund_credits(api):
    headers = api.user_headers("tenant_a")
    transfer_id = api.upload(headers, "a.txt").json()["transfer_id"]
    after_upload = _remaining(api)
    api.client.delete(f"/api/v1/app/doc/{transfer_id}", headers=headers)
    assert _remaining(api) == after_upload


@pytest.mark.xfail(reason="no credit ledger: movements are not recorded as CREDIT_DEBIT audit events")
def test_each_debit_is_recorded_in_the_audit_log(api, sent, db_conn):
    transfer_id, otp = sent
    _download(api, transfer_id, otp)
    with db_conn.cursor() as cur:
        cur.execute("SELECT count(*) AS n FROM audit_logs WHERE action = 'CREDIT_DEBIT'")
        assert cur.fetchone()["n"] == 2  # one for the upload, one for the download


@pytest.mark.xfail(reason="no atomic credit check: concurrent uploads can overshoot the limit (read-then-insert)")
def test_credit_check_and_debit_are_atomic(api, db_conn):
    import inspect

    from app.routers import doc_router

    src = inspect.getsource(doc_router.upload_and_send_file)
    assert "FOR UPDATE" in src or "SERIALIZABLE" in src

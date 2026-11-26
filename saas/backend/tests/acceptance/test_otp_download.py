"""Spec: OTP links for external recipients, bound to the sender tenant's VM."""

import os
from datetime import datetime, timedelta

import pytest


@pytest.fixture
def sent(api, outbox):
    """Upload as tenant_a with a recipient; return (transfer_id, otp, content)."""
    content = b"top-secret-payload"
    resp = api.upload(api.user_headers("tenant_a"), "contract.pdf", content, recipient="client@ext.test")
    assert resp.status_code == 200, resp.text
    mail = outbox["transfer"][0]
    return resp.json()["transfer_id"], mail["otp_code"], content


def _verify(api, transfer_id, otp, headers=None):
    return api.client.post(
        f"/api/v1/app/download/{transfer_id}/verify-otp", json={"otp_code": otp}, headers=headers
    )


def test_upload_with_recipient_emails_link_and_six_digit_otp(api, outbox, sent):
    transfer_id, otp, _ = sent
    mail = outbox["transfer"][0]
    assert mail["recipient"] == "client@ext.test" and mail["sender"] == "user1@alfa.com"
    assert len(otp) == 6 and otp.isdigit()
    assert mail["download_url"].endswith(f"/download/{transfer_id}")


def test_upload_without_recipient_is_personal_and_has_no_otp(api, outbox, db_conn):
    resp = api.upload(api.user_headers("tenant_a"), "mine.txt")
    assert resp.json()["download_url"] is None
    assert outbox["transfer"] == []
    with db_conn.cursor() as cur:
        cur.execute("SELECT otp_code FROM transfers WHERE id = %s::uuid", (resp.json()["transfer_id"],))
        assert cur.fetchone()["otp_code"] is None


def test_correct_otp_returns_the_file_without_login(api, sent):
    transfer_id, otp, content = sent
    resp = _verify(api, transfer_id, otp)  # no Authorization header: recipient is external
    assert resp.status_code == 200
    assert resp.content == content
    assert "contract.pdf" in resp.headers["content-disposition"]


def test_successful_download_marks_otp_verified(api, sent, db_conn):
    transfer_id, otp, _ = sent
    _verify(api, transfer_id, otp)
    with db_conn.cursor() as cur:
        cur.execute("SELECT otp_verified FROM transfers WHERE id = %s::uuid", (transfer_id,))
        assert cur.fetchone()["otp_verified"] is True


def test_wrong_otp_is_401_and_audited(api, sent, db_conn):
    transfer_id, otp, _ = sent
    wrong = "000000" if otp != "000000" else "111111"
    assert _verify(api, transfer_id, wrong).status_code == 401
    with db_conn.cursor() as cur:
        cur.execute("SELECT count(*) AS n FROM audit_logs WHERE action = 'OTP_FAILED'")
        assert cur.fetchone()["n"] == 1


def test_unknown_transfer_is_404(api):
    assert _verify(api, "00000000-0000-0000-0000-000000000000", "123456").status_code == 404


def test_expired_link_is_410(api, sent, db_conn):
    transfer_id, otp, _ = sent
    with db_conn.cursor() as cur:
        cur.execute("UPDATE transfers SET expires_at = %s WHERE id = %s::uuid",
                    (datetime.utcnow() - timedelta(minutes=1), transfer_id))
    assert _verify(api, transfer_id, otp).status_code == 410


def test_link_expires_in_24_hours(api, sent, db_conn):
    transfer_id, _, _ = sent
    with db_conn.cursor() as cur:
        cur.execute("SELECT expires_at FROM transfers WHERE id = %s::uuid", (transfer_id,))
        ttl = cur.fetchone()["expires_at"] - datetime.utcnow()  # app writes naive UTC
    assert timedelta(hours=23, minutes=55) <= ttl <= timedelta(hours=24, minutes=5)


def test_missing_physical_file_is_404(api, sent, db_conn):
    transfer_id, otp, _ = sent
    with db_conn.cursor() as cur:
        cur.execute("SELECT file_path FROM transfers WHERE id = %s::uuid", (transfer_id,))
        os.remove(cur.fetchone()["file_path"])
    assert _verify(api, transfer_id, otp).status_code == 404


def test_send_and_download_events_are_audited_per_tenant(api, sent, db_conn):
    transfer_id, otp, _ = sent
    _verify(api, transfer_id, otp)
    with db_conn.cursor() as cur:
        cur.execute("SELECT action, tenant_id FROM audit_logs WHERE action IN ('SEND_LINK','DOWNLOAD')")
        rows = {r["action"]: r["tenant_id"] for r in cur.fetchall()}
    assert rows == {"SEND_LINK": "tenant_a", "DOWNLOAD": "tenant_a"}


def test_deleted_transfer_link_stops_working(api, sent):
    transfer_id, otp, _ = sent
    api.client.delete(f"/api/v1/app/doc/{transfer_id}", headers=api.user_headers("tenant_a"))
    assert _verify(api, transfer_id, otp).status_code == 404


# ---- Spec gaps -------------------------------------------------------------- #
@pytest.mark.xfail(reason="TODO(path-guards): verify-otp serves transfers.file_path as-is; no under-tenant-root check")
def test_otp_download_refuses_file_outside_tenant_root(api, sent, db_conn, storage_root, tmp_path):
    transfer_id, otp, _ = sent
    secret = tmp_path / "outside-secret.txt"
    secret.write_text("not a tenant file")
    with db_conn.cursor() as cur:
        cur.execute("UPDATE transfers SET file_path = %s WHERE id = %s::uuid", (str(secret), transfer_id))
    resp = _verify(api, transfer_id, otp)
    assert resp.status_code in (403, 404)
    assert resp.content != b"not a tenant file"


@pytest.mark.xfail(reason="TODO(path-guards): no check that tenant_a transfer stays inside tenant_a's root (not tenant_b)")
def test_otp_download_refuses_file_in_another_tenants_root(api, sent, db_conn, storage_root):
    transfer_id, otp, _ = sent
    foreign = storage_root / "tenant_b" / "other.txt"
    foreign.parent.mkdir(parents=True, exist_ok=True)
    foreign.write_text("tenant-b-private")
    with db_conn.cursor() as cur:
        cur.execute("UPDATE transfers SET file_path = %s WHERE id = %s::uuid", (str(foreign), transfer_id))
    resp = _verify(api, transfer_id, otp)
    assert resp.status_code in (403, 404)
    assert resp.content != b"tenant-b-private"


@pytest.mark.xfail(reason="OTP brute force is unbounded (6 digits, no lockout / rate limit)")
def test_otp_is_locked_after_five_failed_attempts(api, sent):
    transfer_id, otp, _ = sent
    wrong = "000000" if otp != "000000" else "111111"
    last = None
    for _ in range(6):
        last = _verify(api, transfer_id, wrong)
    assert last.status_code in (423, 429)
    assert _verify(api, transfer_id, otp).status_code in (423, 429), "even the right OTP is locked"


@pytest.mark.xfail(reason="links are multi-use inside the 24 h window; spec wants single-use (or configurable max downloads)")
def test_otp_link_is_single_use(api, sent):
    transfer_id, otp, _ = sent
    assert _verify(api, transfer_id, otp).status_code == 200
    assert _verify(api, transfer_id, otp).status_code in (403, 410)


@pytest.mark.xfail(reason="OTP is stored in clear in transfers.otp_code; spec wants a hash")
def test_otp_is_not_stored_in_clear(api, sent, db_conn):
    transfer_id, otp, _ = sent
    with db_conn.cursor() as cur:
        cur.execute("SELECT otp_code FROM transfers WHERE id = %s::uuid", (transfer_id,))
        assert cur.fetchone()["otp_code"] != otp


@pytest.mark.xfail(reason="OTP link is not bound to the tenant host: any Host can redeem any tenant's link")
def test_link_is_only_redeemable_on_the_owning_tenant_host(api, sent):
    transfer_id, otp, _ = sent
    resp = _verify(api, transfer_id, otp, headers={"Host": "tenant_b.saas.local"})
    assert resp.status_code in (403, 404)

"""Tenant workspace: upload, list, delete transfers and public OTP download."""

import os
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.auth.middleware import get_current_tenant_user
from app.database import STORAGE_BASE_PATH, get_db, log_audit
from app.email_utils import send_transfer_email
from app.integrity_client import register_baseline_for_file
from app.metrics.prometheus import TENANT_QUOTA_REMAINING, TENANT_REQUESTS

router = APIRouter(prefix="/api/v1/app", tags=["Documents & Transfers"])

FRONTEND_TRANSFER_URL = os.getenv("FRONTEND_TRANSFER_URL", "http://app.saas.local")


class OTPVerifyRequest(BaseModel):
    otp_code: str


@router.get("/doc")
def get_documents(
    current_user: dict = Depends(get_current_tenant_user),
    conn=Depends(get_db),
):
    """List transfers for the caller's tenant and update quota metrics."""
    tenant_id = current_user.get("tenant_id")
    user_email = current_user.get("sub")

    with conn.cursor() as cur:
        cur.execute("SELECT quota_limit FROM tenants WHERE tenant_id = %s", (tenant_id,))
        tenant = cur.fetchone()
        quota_limit = tenant["quota_limit"] if tenant else current_user.get("quota_limit", 100)

        cur.execute(
            """
            SELECT id::text, tenant_id, sender_email AS sender, recipient_email AS recipient,
                   file_name AS title, file_size_bytes, otp_verified, expires_at, created_at
            FROM transfers
            WHERE tenant_id = %s
            ORDER BY created_at DESC
            """,
            (tenant_id,),
        )
        tenant_docs = cur.fetchall()

    used_quota = len(tenant_docs)
    quota_remaining = max(0, quota_limit - used_quota)

    TENANT_REQUESTS.labels(tenant_id=tenant_id, endpoint="/app/doc", status_code="200").inc()
    TENANT_QUOTA_REMAINING.labels(tenant_id=tenant_id).set(quota_remaining)

    return {
        "tenant_id": tenant_id,
        "current_user": user_email,
        "quota_remaining": quota_remaining,
        "documents": tenant_docs,
    }


@router.post("/doc")
async def upload_and_send_file(
    request: Request,
    file: UploadFile = File(...),
    recipient: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_tenant_user),
    conn=Depends(get_db),
):
    """
    Store a file under the tenant VM path.

    If ``recipient`` is set, generate an OTP, email the download link, and
    count the transfer against the tenant quota (quota = number of files).
    """
    tenant_id = current_user.get("tenant_id")
    sender_email = current_user.get("sub")
    client_ip = request.client.host if request.client else None

    with conn.cursor() as cur:
        cur.execute(
            "SELECT quota_limit, vm_storage_path FROM tenants WHERE tenant_id = %s",
            (tenant_id,),
        )
        tenant = cur.fetchone()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")

        quota_limit = tenant["quota_limit"]
        vm_path = tenant["vm_storage_path"] or os.path.join(STORAGE_BASE_PATH, tenant_id)

        cur.execute(
            "SELECT COUNT(*)::int AS total FROM transfers WHERE tenant_id = %s",
            (tenant_id,),
        )
        used_quota = cur.fetchone()["total"]

    if used_quota >= quota_limit:
        TENANT_REQUESTS.labels(tenant_id=tenant_id, endpoint="/app/doc", status_code="429").inc()
        TENANT_QUOTA_REMAINING.labels(tenant_id=tenant_id).set(0)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Quota exceeded for tenant '{tenant_id}'. Max: {quota_limit}.",
        )

    os.makedirs(vm_path, exist_ok=True)
    transfer_id = str(uuid.uuid4())
    safe_filename = title.strip() if title and title.strip() else file.filename
    stored_filename = f"{transfer_id}_{safe_filename}"
    file_path = os.path.join(vm_path, stored_filename)

    file_bytes = await file.read()
    with open(file_path, "wb") as out:
        out.write(file_bytes)

    file_size = len(file_bytes)
    recipient_val = recipient.strip() if recipient and recipient.strip() else None
    otp_code = f"{secrets.randbelow(1000000):06d}" if recipient_val else None
    expires_at = datetime.utcnow() + timedelta(hours=24)

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO transfers
                (id, tenant_id, sender_email, recipient_email, file_name,
                 file_path, file_size_bytes, otp_code, expires_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                transfer_id,
                tenant_id,
                sender_email,
                recipient_val,
                safe_filename,
                file_path,
                file_size,
                otp_code,
                expires_at,
            ),
        )
    conn.commit()

    # Soft call into Alessa's IVS (echo stub until her service is ready).
    integrity = register_baseline_for_file(
        tenant_id=tenant_id,
        transfer_id=transfer_id,
        filename=safe_filename,
        content=file_bytes,
        media_type=file.content_type or "application/octet-stream",
    )
    if integrity:
        log_audit(
            conn,
            tenant_id,
            sender_email,
            "INTEGRITY_BASELINE",
            safe_filename,
            client_ip,
            f"baseline={integrity.get('baseline_id')} status={integrity.get('status')}",
        )

    download_url = f"{FRONTEND_TRANSFER_URL}/download/{transfer_id}"
    if recipient_val:
        send_transfer_email(
            recipient_val, sender_email, safe_filename, download_url, otp_code
        )
        log_audit(
            conn,
            tenant_id,
            sender_email,
            "SEND_LINK",
            safe_filename,
            client_ip,
            f"Sent to {recipient_val} (ID: {transfer_id})",
        )
        msg_out = f"File '{safe_filename}' uploaded and sent to {recipient_val}."
    else:
        log_audit(
            conn,
            tenant_id,
            sender_email,
            "UPLOAD_PERSONAL",
            safe_filename,
            client_ip,
            f"Stored on tenant VM (ID: {transfer_id})",
        )
        msg_out = f"File '{safe_filename}' saved to personal workspace."

    TENANT_REQUESTS.labels(tenant_id=tenant_id, endpoint="/app/doc", status_code="201").inc()
    TENANT_QUOTA_REMAINING.labels(tenant_id=tenant_id).set(
        max(0, quota_limit - used_quota - 1)
    )

    return {
        "status": "OK",
        "transfer_id": transfer_id,
        "download_url": download_url if recipient_val else None,
        "message": msg_out,
    }


@router.post("/download/{transfer_id}/verify-otp")
def verify_otp_and_download(
    transfer_id: str,
    body: OTPVerifyRequest,
    request: Request,
    conn=Depends(get_db),
):
    """Public endpoint: validate OTP and stream the file from disk."""
    client_ip = request.client.host if request.client else None

    with conn.cursor() as cur:
        cur.execute("SELECT * FROM transfers WHERE id = %s::uuid", (transfer_id,))
        transfer = cur.fetchone()

    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer link not found.")

    if transfer["expires_at"] and datetime.utcnow() > transfer["expires_at"]:
        raise HTTPException(status_code=410, detail="Download link has expired.")

    if transfer["otp_code"] != body.otp_code.strip():
        log_audit(
            conn,
            transfer["tenant_id"],
            transfer["recipient_email"],
            "OTP_FAILED",
            transfer["file_name"],
            client_ip,
            f"Failed OTP for ID: {transfer_id}",
        )
        raise HTTPException(status_code=401, detail="Incorrect OTP code.")

    if not os.path.exists(transfer["file_path"]):
        raise HTTPException(status_code=404, detail="Physical file no longer exists on the VM.")

    with conn.cursor() as cur:
        cur.execute(
            "UPDATE transfers SET otp_verified = TRUE WHERE id = %s::uuid",
            (transfer_id,),
        )
    conn.commit()

    log_audit(
        conn,
        transfer["tenant_id"],
        transfer["recipient_email"],
        "DOWNLOAD",
        transfer["file_name"],
        client_ip,
        f"OTP-verified download (ID: {transfer_id})",
    )

    return FileResponse(
        path=transfer["file_path"],
        filename=transfer["file_name"],
        media_type="application/octet-stream",
    )


@router.delete("/doc/{transfer_id}")
def delete_document(
    transfer_id: str,
    request: Request,
    current_user: dict = Depends(get_current_tenant_user),
    conn=Depends(get_db),
):
    """Delete a transfer row scoped to the caller's tenant and remove the file."""
    tenant_id = current_user.get("tenant_id")
    client_ip = request.client.host if request.client else None

    with conn.cursor() as cur:
        cur.execute(
            """
            DELETE FROM transfers
            WHERE id = %s::uuid AND tenant_id = %s
            RETURNING file_name, file_path
            """,
            (transfer_id, tenant_id),
        )
        deleted = cur.fetchone()

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Document not found or does not belong to this tenant",
        )

    conn.commit()

    if deleted["file_path"] and os.path.exists(deleted["file_path"]):
        os.remove(deleted["file_path"])

    log_audit(
        conn,
        tenant_id,
        current_user.get("sub"),
        "DELETE_FILE",
        deleted["file_name"],
        client_ip,
        f"Deleted ID: {transfer_id}",
    )

    return {
        "status": "OK",
        "message": f"File '{deleted['file_name']}' deleted successfully.",
    }

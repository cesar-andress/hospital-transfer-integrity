"""SuperAdmin routes: list / create / delete tenants and purge storage."""

import os
import re
import shutil

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth.middleware import get_current_tenant_user
from app.database import STORAGE_BASE_PATH, get_db, log_audit
from app.models.tenants import TenantCreate

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


def verify_superadmin(current_user: dict = Depends(get_current_tenant_user)):
    """Reject any JWT that is not role=admin."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: global SuperAdmin privileges required",
        )
    return current_user


@router.get("/tenants")
def list_tenants(admin: dict = Depends(verify_superadmin), conn=Depends(get_db)):
    """Return all tenants with used / remaining transfer quota."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                t.tenant_id,
                t.name,
                t.email,
                t.max_accounts,
                t.quota_limit,
                t.vm_storage_path,
                t.is_active,
                t.created_at,
                COUNT(tr.id)::int AS used_quota,
                GREATEST(0, t.quota_limit - COUNT(tr.id))::int AS quota_remaining
            FROM tenants t
            LEFT JOIN transfers tr ON t.tenant_id = tr.tenant_id
            GROUP BY t.tenant_id
            ORDER BY t.created_at ASC
            """
        )
        return cur.fetchall()


@router.post("/tenants", status_code=status.HTTP_201_CREATED)
def create_tenant(
    tenant_in: TenantCreate,
    request: Request,
    admin: dict = Depends(verify_superadmin),
    conn=Depends(get_db),
):
    """Create a tenant row, first user, and empty on-disk storage folder."""
    if not re.match(r"^[a-zA-Z0-9_-]+$", tenant_in.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="tenant_id may only contain letters, numbers, hyphens and underscores.",
        )

    vm_path = os.path.join(STORAGE_BASE_PATH, tenant_in.tenant_id)

    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM tenants WHERE tenant_id = %s",
                (tenant_in.tenant_id,),
            )
            if cur.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"tenant_id '{tenant_in.tenant_id}' is already registered.",
                )

            cur.execute(
                """
                INSERT INTO tenants
                    (tenant_id, name, email, max_accounts, quota_limit, vm_storage_path)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING tenant_id, name, email, max_accounts, quota_limit,
                          vm_storage_path, is_active, created_at
                """,
                (
                    tenant_in.tenant_id,
                    tenant_in.name,
                    tenant_in.email,
                    tenant_in.max_accounts,
                    tenant_in.quota_limit,
                    vm_path,
                ),
            )
            new_tenant = cur.fetchone()

            cur.execute(
                """
                INSERT INTO users (tenant_id, email, password, name, role)
                VALUES (%s, %s, %s, %s, 'user')
                """,
                (
                    tenant_in.tenant_id,
                    tenant_in.email.strip(),
                    tenant_in.password,
                    tenant_in.name,
                ),
            )

        os.makedirs(vm_path, exist_ok=True)
        conn.commit()
    except HTTPException:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating tenant in PostgreSQL: {exc}",
        )

    client_ip = request.client.host if request.client else None
    log_audit(
        conn,
        tenant_in.tenant_id,
        admin.get("sub"),
        "TENANT_CREATED",
        vm_path,
        client_ip,
        f"Manual organization create: {tenant_in.name}",
    )

    return {"status": "OK", "message": "Tenant created successfully", "tenant": new_tenant}


@router.delete("/tenants/{tenant_id}")
def delete_tenant(
    tenant_id: str,
    request: Request,
    admin: dict = Depends(verify_superadmin),
    conn=Depends(get_db),
):
    """Cascade-delete the tenant in Postgres and purge its storage directory."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM tenants WHERE tenant_id = %s RETURNING tenant_id, vm_storage_path",
                (tenant_id,),
            )
            deleted = cur.fetchone()

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found",
            )

        conn.commit()
    except HTTPException:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting tenant: {exc}",
        )

    # Only delete paths that stay under STORAGE_BASE_PATH (path-traversal guard).
    vm_path = deleted.get("vm_storage_path")
    if vm_path:
        abs_base = os.path.abspath(STORAGE_BASE_PATH)
        abs_vm = os.path.abspath(vm_path)
        if abs_vm.startswith(abs_base + os.sep) and os.path.exists(abs_vm):
            shutil.rmtree(abs_vm, ignore_errors=True)

    client_ip = request.client.host if request.client else None
    log_audit(
        conn,
        tenant_id,
        admin.get("sub"),
        "TENANT_DELETED",
        tenant_id,
        client_ip,
        "Tenant and files purged",
    )

    return {
        "status": "OK",
        "message": f"Tenant '{tenant_id}' and all related data were deleted",
    }

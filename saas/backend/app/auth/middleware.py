"""Bearer-token dependency used by protected routes."""

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.jwt import decode_access_token
from app.database import get_db

security = HTTPBearer()


def get_current_tenant_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    conn=Depends(get_db),
) -> dict:
    """
    Extract and validate the Bearer JWT on each protected request.

    Non-admin tokens are rejected immediately if the tenant was deleted
    or deactivated (hard isolation / revocation).
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    tenant_id = payload.get("tenant_id")
    role = payload.get("role")

    if role != "admin":
        with conn.cursor() as cur:
            cur.execute(
                "SELECT tenant_id, is_active FROM tenants WHERE tenant_id = %s",
                (tenant_id,),
            )
            tenant = cur.fetchone()

        if not tenant or not tenant["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tenant associated with this account was deleted or deactivated",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return payload

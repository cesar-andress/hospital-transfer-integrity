"""Authentication routes: SuperAdmin demo login and tenant user login."""

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth.jwt import create_access_token
from app.database import get_db, log_audit
from app.models.user import TokenResponse, UserLogin

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])

# Demo-only SuperAdmin (not stored in Postgres). Replace before any real deploy.
ADMIN_CREDENTIALS = {
    "tenant_id": "admin",
    "email": "admin@saas.com",
    "password": "adminpassword",
}


@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin, request: Request, conn=Depends(get_db)):
    """Issue a JWT for SuperAdmin or a tenant user (plaintext password check in MVP)."""
    client_ip = request.client.host if request.client else None

    if credentials.tenant_id == "admin":
        if (
            credentials.email == ADMIN_CREDENTIALS["email"]
            and credentials.password == ADMIN_CREDENTIALS["password"]
        ):
            token_data = {
                "sub": credentials.email,
                "tenant_id": "admin",
                "role": "admin",
                "quota_limit": 999999,
            }
            token = create_access_token(data=token_data)
            log_audit(
                conn, "admin", credentials.email, "LOGIN_ADMIN",
                "auth/login", client_ip, "SuperAdmin access",
            )
            return TokenResponse(
                access_token=token,
                tenant_id="admin",
                role="admin",
                quota_limit=999999,
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid SuperAdmin credentials",
        )

    with conn.cursor() as cur:
        cur.execute(
            "SELECT tenant_id, quota_limit, is_active FROM tenants WHERE tenant_id = %s",
            (credentials.tenant_id,),
        )
        tenant = cur.fetchone()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant '{credentials.tenant_id}' does not exist",
        )

    if not tenant["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Tenant '{credentials.tenant_id}' is deactivated",
        )

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT email, password, role
            FROM users
            WHERE tenant_id = %s AND LOWER(email) = LOWER(%s)
            """,
            (credentials.tenant_id, credentials.email.strip()),
        )
        valid_user = cur.fetchone()

    if not valid_user or valid_user["password"] != credentials.password:
        log_audit(
            conn,
            credentials.tenant_id,
            credentials.email,
            "LOGIN_FAILED",
            "auth/login",
            client_ip,
            "Invalid credentials",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password for this tenant",
        )

    token_data = {
        "sub": valid_user["email"],
        "tenant_id": tenant["tenant_id"],
        "role": valid_user["role"],
        "quota_limit": tenant["quota_limit"],
    }
    token = create_access_token(data=token_data)

    log_audit(
        conn,
        tenant["tenant_id"],
        valid_user["email"],
        "LOGIN",
        "auth/login",
        client_ip,
        "Successful login",
    )

    return TokenResponse(
        access_token=token,
        tenant_id=tenant["tenant_id"],
        role=valid_user["role"],
        quota_limit=tenant["quota_limit"],
    )

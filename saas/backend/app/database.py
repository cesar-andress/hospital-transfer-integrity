"""PostgreSQL connection helpers and GDPR-oriented audit logging."""

import os

import psycopg2
from fastapi import HTTPException, status
from psycopg2.extras import RealDictCursor

from app.config import settings

STORAGE_BASE_PATH = os.getenv("STORAGE_BASE_PATH", "/app/vm_storage")


def get_db_connection():
    """Open a direct psycopg2 connection (RealDictCursor rows)."""
    try:
        return psycopg2.connect(
            settings.DATABASE_URL,
            cursor_factory=RealDictCursor,
        )
    except Exception as exc:
        print(f"PostgreSQL connection error: {exc}")
        return None


def get_db():
    """FastAPI dependency: yield a connection and always close it."""
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not connect to PostgreSQL.",
        )
    try:
        yield conn
    finally:
        conn.close()


def log_audit(
    conn,
    tenant_id: str,
    user_email: str,
    action: str,
    target_resource: str = None,
    ip_address: str = None,
    details: str = None,
):
    """Insert one row into audit_logs (best-effort; never breaks the request)."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO audit_logs
                    (tenant_id, user_email, action, target_resource, ip_address, details)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (tenant_id, user_email, action, target_resource, ip_address, details),
            )
        conn.commit()
    except Exception as exc:
        conn.rollback()
        print(f"Audit log error: {exc}")

"""Pydantic schemas for tenant administration."""

from datetime import datetime

from pydantic import BaseModel


class TenantCreate(BaseModel):
    """Payload to provision a tenant and its first user."""

    tenant_id: str
    name: str
    email: str
    password: str
    max_accounts: int = 10
    quota_limit: int = 100


class TenantResponse(BaseModel):
    """Tenant summary returned by admin endpoints."""

    tenant_id: str
    name: str
    email: str
    max_accounts: int
    quota_limit: int
    created_at: datetime

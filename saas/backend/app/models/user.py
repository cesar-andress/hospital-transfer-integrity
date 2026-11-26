"""Pydantic schemas for authentication."""

from pydantic import BaseModel


class UserLogin(BaseModel):
    """Login payload. Use tenant_id=\"admin\" for the SuperAdmin demo account."""

    email: str
    password: str
    tenant_id: str


class TokenResponse(BaseModel):
    """JWT response returned after a successful login."""

    access_token: str
    token_type: str = "bearer"
    tenant_id: str
    role: str
    quota_limit: int

"""Pure-logic tests for JWT helpers (no database needed)."""

import jwt as pyjwt

from app.auth.jwt import create_access_token, decode_access_token
from app.config import settings


def test_roundtrip_keeps_tenant_role_and_quota_claims():
    token = create_access_token(
        {"sub": "user1@alfa.com", "tenant_id": "tenant_a", "role": "user", "quota_limit": 100}
    )
    payload = decode_access_token(token)
    assert payload["tenant_id"] == "tenant_a"
    assert payload["role"] == "user"
    assert payload["sub"] == "user1@alfa.com"
    assert "exp" in payload


def test_tampered_token_is_rejected():
    token = create_access_token({"tenant_id": "tenant_a", "role": "user"})
    assert decode_access_token(token[:-2] + "xx") is None


def test_token_signed_with_other_secret_is_rejected():
    forged = pyjwt.encode({"tenant_id": "tenant_a", "role": "admin"}, "other", algorithm="HS256")
    assert decode_access_token(forged) is None


def test_expired_token_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", -5)
    token = create_access_token({"tenant_id": "tenant_a", "role": "user"})
    assert decode_access_token(token) is None


def test_none_algorithm_token_is_rejected():
    unsigned = pyjwt.encode({"tenant_id": "tenant_a", "role": "admin"}, None, algorithm="none")
    assert decode_access_token(unsigned) is None

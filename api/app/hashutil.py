"""Hash helpers for M1 (sha256 only). Signatures arrive in M2."""

from __future__ import annotations

import hashlib
import re

_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def is_sha256_hex(value: str | None) -> bool:
    return bool(value and _SHA256_RE.match(value))


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_sha256(value: str) -> str:
    return value.lower()

"""HTTP client for Alessa's Integrity Verification Service (IVS).

When INTEGRITY_ENABLED is false or the remote call fails, callers soft-fail:
the transfer SaaS must keep working. The default compose target is the local
echo stub under services/integrity-stub/.
"""

from __future__ import annotations

import hashlib
import os
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import json

CONTRACT_VERSION = "0.1.0"


def _enabled() -> bool:
    return os.getenv("INTEGRITY_ENABLED", "true").lower() in {"1", "true", "yes"}


def _base_url() -> str:
    return os.getenv("INTEGRITY_API_BASE_URL", "http://integrity-stub:8090").rstrip("/")


def _token() -> Optional[str]:
    return os.getenv("INTEGRITY_SHARED_TOKEN") or None


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    url = f"{_base_url()}{path}"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    token = _token()
    if token:
        headers["X-Integrity-Token"] = token
    body = json.dumps(payload).encode("utf-8")
    req = Request(url, data=body, headers=headers, method="POST")
    with urlopen(req, timeout=5) as resp:
        return json.loads(resp.read().decode("utf-8"))


def register_baseline_for_file(
    *,
    tenant_id: str,
    transfer_id: str,
    filename: str,
    content: bytes,
    media_type: str = "application/octet-stream",
) -> Optional[dict[str, Any]]:
    """Best-effort baseline registration after a successful upload."""
    if not _enabled():
        return None
    payload = {
        "contract_version": CONTRACT_VERSION,
        "tenant_id": tenant_id,
        "object": {
            "kind": "file",
            "transfer_id": transfer_id,
            "filename": filename,
            "media_type": media_type,
            "size_bytes": len(content),
            "sha256": sha256_hex(content),
        },
        "context": {"source": "mvp-saas-upload", "case": "file"},
    }
    try:
        return _post("/v1/baselines", payload)
    except (URLError, HTTPError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        print(f"integrity baseline soft-fail: {exc}")
        return {"status": "error", "error": str(exc), "contract_version": CONTRACT_VERSION}


def verify_object(payload: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Best-effort verification (drills / admin tools)."""
    if not _enabled():
        return None
    payload = {**payload, "contract_version": payload.get("contract_version", CONTRACT_VERSION)}
    try:
        return _post("/v1/verifications", payload)
    except (URLError, HTTPError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        print(f"integrity verify soft-fail: {exc}")
        return {"verdict": "unknown", "error": str(exc), "contract_version": CONTRACT_VERSION}

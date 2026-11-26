"""Integrity Verification Service, contract v0.1.0 (M0/M1 skeleton).

Daniel's MVP-Saas calls these paths. Later milestones add signatures, EHR/DICOM
cases, attack simulation, metrics and SIEM export. See docs/PLANNING.md.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse

from app import __contract_version__
from app.hashutil import is_sha256_hex, normalize_sha256
from app.models import (
    BaselineRequest,
    BaselineResponse,
    ReportDocument,
    VerificationRequest,
    VerificationResponse,
)
from app.store import BaselineRecord, VerificationRecord, store

CONTRACT = os.getenv("IVS_CONTRACT_VERSION", __contract_version__)
REQUIRE_TOKEN = os.getenv("IVS_REQUIRE_TOKEN", "false").lower() in {"1", "true", "yes"}
SHARED_TOKEN = os.getenv("IVS_SHARED_TOKEN", "")

app = FastAPI(
    title="Clinical Integrity Verification Service (IVS)",
    version=CONTRACT,
    description="Alessa Renata Comparini Ceroni, callee for Daniel's MVP-Saas",
)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _check_token(x_integrity_token: str | None) -> None:
    if not REQUIRE_TOKEN:
        return
    if not SHARED_TOKEN or x_integrity_token != SHARED_TOKEN:
        raise HTTPException(status_code=401, detail="invalid or missing X-Integrity-Token")


@app.get("/v1/health")
def health():
    return {"status": "ok", "service": "ivs", "contract_version": CONTRACT}


@app.post("/v1/baselines", response_model=BaselineResponse)
def create_baseline(
    body: BaselineRequest,
    x_integrity_token: str | None = Header(default=None),
):
    _check_token(x_integrity_token)
    if body.contract_version != CONTRACT:
        raise HTTPException(
            status_code=400,
            detail=f"unsupported contract_version (want {CONTRACT})",
        )
    sha = body.object.sha256
    if not is_sha256_hex(sha):
        raise HTTPException(status_code=400, detail="object.sha256 must be a 64-char hex digest")
    sha = normalize_sha256(sha)
    baseline_id = f"bl_{uuid4().hex[:16]}"
    record = BaselineRecord(
        baseline_id=baseline_id,
        tenant_id=body.tenant_id,
        kind=body.object.kind,
        sha256=sha,
        algorithm="sha256",
        registered_at=_now(),
        object_meta=body.object.model_dump(exclude_none=True),
        context=body.context or {},
    )
    store.put_baseline(record)
    return BaselineResponse(
        contract_version=CONTRACT,
        baseline_id=baseline_id,
        status="registered",
        algorithm="sha256",
        registered_at=record.registered_at,
    )


@app.post("/v1/verifications", response_model=VerificationResponse)
def verify(
    body: VerificationRequest,
    x_integrity_token: str | None = Header(default=None),
):
    _check_token(x_integrity_token)
    if body.contract_version != CONTRACT:
        raise HTTPException(
            status_code=400,
            detail=f"unsupported contract_version (want {CONTRACT})",
        )
    sha = body.object.sha256
    if not is_sha256_hex(sha):
        raise HTTPException(status_code=400, detail="object.sha256 must be a 64-char hex digest")
    sha = normalize_sha256(sha)

    baseline = None
    if body.baseline_id:
        baseline = store.get_baseline(body.baseline_id)
        if baseline is None:
            raise HTTPException(status_code=404, detail="baseline_id not found")
        if baseline.tenant_id != body.tenant_id:
            raise HTTPException(status_code=403, detail="baseline belongs to another tenant")
    else:
        baseline = store.find_baseline(body.tenant_id, sha)

    verification_id = f"vr_{uuid4().hex[:16]}"
    if baseline is None:
        verdict = "unknown"
        detail = {"hash_match": False, "reason": "no_baseline"}
        baseline_id = None
    elif baseline.sha256 == sha:
        verdict = "intact"
        detail = {"hash_match": True, "signature_valid": None, "algorithm": baseline.algorithm}
        baseline_id = baseline.baseline_id
    else:
        verdict = "altered"
        detail = {
            "hash_match": False,
            "expected_sha256": baseline.sha256,
            "observed_sha256": sha,
            "signature_valid": None,
        }
        baseline_id = baseline.baseline_id

    checked_at = _now()
    store.put_verification(
        VerificationRecord(
            verification_id=verification_id,
            baseline_id=baseline_id,
            tenant_id=body.tenant_id,
            verdict=verdict,
            detail=detail,
            checked_at=checked_at,
            object_meta=body.object.model_dump(exclude_none=True),
        )
    )
    return VerificationResponse(
        contract_version=CONTRACT,
        verification_id=verification_id,
        baseline_id=baseline_id,
        verdict=verdict,
        detail=detail,
        checked_at=checked_at,
    )


@app.get("/v1/reports/{verification_id}")
def report(verification_id: str, x_integrity_token: str | None = Header(default=None)):
    _check_token(x_integrity_token)
    rec = store.get_verification(verification_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="verification_id not found")
    summary = {
        "intact": "Object matches the registered baseline hash.",
        "altered": "Object hash differs from the registered baseline.",
        "encrypted_or_unreadable": "Object could not be read or appears encrypted.",
        "unknown": "No baseline was available for comparison.",
        "passthrough": "Passthrough (should not appear in real IVS).",
    }.get(rec.verdict, rec.verdict)
    doc = ReportDocument(
        verification_id=rec.verification_id,
        baseline_id=rec.baseline_id,
        tenant_id=rec.tenant_id,
        verdict=rec.verdict,  # type: ignore[arg-type]
        summary=summary,
        detail=rec.detail,
        checked_at=rec.checked_at,
        siem_event=None,
    )
    return JSONResponse(content=doc.model_dump())

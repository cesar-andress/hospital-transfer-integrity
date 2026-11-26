"""Echo Integrity Verification Service — replace with Alessa's IVS behind the same paths."""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse

CONTRACT = "0.1.0"

app = FastAPI(title="integrity-stub", version=CONTRACT)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@app.get("/v1/health")
def health():
    return {"status": "ok", "service": "integrity-stub", "contract_version": CONTRACT}


@app.post("/v1/baselines")
async def baselines(body: dict, x_integrity_token: str | None = Header(default=None)):
    _ = x_integrity_token
    return {
        "contract_version": CONTRACT,
        "baseline_id": f"bl_stub_{uuid4().hex[:12]}",
        "status": "passthrough",
        "algorithm": "none-stub",
        "registered_at": _now(),
        "echo": body,
    }


@app.post("/v1/verifications")
async def verifications(body: dict, x_integrity_token: str | None = Header(default=None)):
    _ = x_integrity_token
    return {
        "contract_version": CONTRACT,
        "verification_id": f"vr_stub_{uuid4().hex[:12]}",
        "baseline_id": body.get("baseline_id"),
        "verdict": "passthrough",
        "detail": {"stub": True, "note": "Alessa IVS will compute a real verdict"},
        "checked_at": _now(),
        "echo": body,
    }


@app.get("/v1/reports/{verification_id}")
def reports(verification_id: str):
    return JSONResponse(
        status_code=501,
        content={
            "error": "not_implemented",
            "message": "Reports are owned by Alessa's IVS",
            "verification_id": verification_id,
        },
    )

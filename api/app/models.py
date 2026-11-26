"""Request/response shapes aligned with contract v0.1.0."""

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

Verdict = Literal["intact", "altered", "encrypted_or_unreadable", "unknown", "passthrough"]
ObjectKind = Literal["file", "ehr_record", "dicom_study"]


class ObjectRef(BaseModel):
    kind: ObjectKind
    transfer_id: Optional[str] = None
    filename: Optional[str] = None
    media_type: Optional[str] = None
    size_bytes: Optional[int] = None
    sha256: Optional[str] = None
    clinical: Optional[dict[str, Any]] = None


class BaselineRequest(BaseModel):
    contract_version: str
    tenant_id: str
    object: ObjectRef
    context: Optional[dict[str, Any]] = None


class BaselineResponse(BaseModel):
    contract_version: str
    baseline_id: str
    status: str
    algorithm: str
    registered_at: str


class VerificationRequest(BaseModel):
    contract_version: str
    tenant_id: str
    object: ObjectRef
    baseline_id: Optional[str] = None
    context: Optional[dict[str, Any]] = None


class VerificationResponse(BaseModel):
    contract_version: str
    verification_id: str
    baseline_id: Optional[str] = None
    verdict: Verdict
    detail: dict[str, Any] = Field(default_factory=dict)
    checked_at: str


class ReportDocument(BaseModel):
    verification_id: str
    baseline_id: Optional[str] = None
    tenant_id: str
    verdict: Verdict
    summary: str
    detail: dict[str, Any] = Field(default_factory=dict)
    checked_at: str
    siem_event: Optional[dict[str, Any]] = None

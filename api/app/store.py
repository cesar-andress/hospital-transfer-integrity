"""In-memory store for M0/M1. Replace with durable storage in later milestones."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Optional


@dataclass
class BaselineRecord:
    baseline_id: str
    tenant_id: str
    kind: str
    sha256: str
    algorithm: str
    registered_at: str
    object_meta: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class VerificationRecord:
    verification_id: str
    baseline_id: Optional[str]
    tenant_id: str
    verdict: str
    detail: dict[str, Any]
    checked_at: str
    object_meta: dict[str, Any] = field(default_factory=dict)


class MemoryStore:
    def __init__(self) -> None:
        self._baselines: dict[str, BaselineRecord] = {}
        self._verifications: dict[str, VerificationRecord] = {}
        self._lock = Lock()

    def put_baseline(self, record: BaselineRecord) -> None:
        with self._lock:
            self._baselines[record.baseline_id] = record

    def get_baseline(self, baseline_id: str) -> Optional[BaselineRecord]:
        with self._lock:
            return self._baselines.get(baseline_id)

    def find_baseline(self, tenant_id: str, sha256: str) -> Optional[BaselineRecord]:
        with self._lock:
            for rec in self._baselines.values():
                if rec.tenant_id == tenant_id and rec.sha256 == sha256:
                    return rec
        return None

    def put_verification(self, record: VerificationRecord) -> None:
        with self._lock:
            self._verifications[record.verification_id] = record

    def get_verification(self, verification_id: str) -> Optional[VerificationRecord]:
        with self._lock:
            return self._verifications.get(verification_id)

    def clear(self) -> None:
        with self._lock:
            self._baselines.clear()
            self._verifications.clear()


store = MemoryStore()

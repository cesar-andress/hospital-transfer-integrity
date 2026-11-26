"""Unit tests for the in-memory store."""

import pytest

from app.store import BaselineRecord, MemoryStore, VerificationRecord

pytestmark = [pytest.mark.unit]


def test_put_and_get_baseline():
    s = MemoryStore()
    rec = BaselineRecord(
        baseline_id="bl_1",
        tenant_id="t1",
        kind="file",
        sha256="a" * 64,
        algorithm="sha256",
        registered_at="2026-11-26T00:00:00Z",
    )
    s.put_baseline(rec)
    assert s.get_baseline("bl_1") is rec
    assert s.get_baseline("missing") is None


def test_find_baseline_by_tenant_and_hash():
    s = MemoryStore()
    s.put_baseline(
        BaselineRecord("bl_1", "t1", "file", "a" * 64, "sha256", "t")
    )
    s.put_baseline(
        BaselineRecord("bl_2", "t2", "file", "a" * 64, "sha256", "t")
    )
    found = s.find_baseline("t1", "a" * 64)
    assert found and found.baseline_id == "bl_1"
    assert s.find_baseline("t1", "b" * 64) is None


def test_verification_roundtrip():
    s = MemoryStore()
    s.put_verification(
        VerificationRecord("vr_1", "bl_1", "t1", "intact", {}, "t")
    )
    assert s.get_verification("vr_1").verdict == "intact"


def test_clear_empties_both_maps():
    s = MemoryStore()
    s.put_baseline(BaselineRecord("bl_1", "t1", "file", "a" * 64, "sha256", "t"))
    s.put_verification(VerificationRecord("vr_1", "bl_1", "t1", "intact", {}, "t"))
    s.clear()
    assert s.get_baseline("bl_1") is None
    assert s.get_verification("vr_1") is None

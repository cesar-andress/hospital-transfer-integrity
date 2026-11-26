"""Extra unit coverage: hashing clinical-ish byte payloads."""

import pytest

from app.hashutil import sha256_hex

pytestmark = [pytest.mark.unit]


def test_empty_payload_has_known_digest():
    assert sha256_hex(b"") == (
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )


def test_distinct_payloads_differ():
    assert sha256_hex(b"ehr-v1") != sha256_hex(b"ehr-v1-tampered")


def test_dicom_standin_bytes_stable():
    # Stand-in until real DICOM fixtures land in M3
    blob = b"DICM" + b"\x00" * 128 + b"synthetic-study"
    assert len(sha256_hex(blob)) == 64

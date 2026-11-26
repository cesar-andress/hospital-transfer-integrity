"""Unit tests for hash helpers (M1)."""

import pytest

from app.hashutil import is_sha256_hex, normalize_sha256, sha256_hex

pytestmark = [pytest.mark.unit]


def test_sha256_hex_of_known_vector():
    # echo -n "test" | sha256sum
    assert sha256_hex(b"test") == (
        "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
    )


def test_is_sha256_hex_accepts_64_hex():
    assert is_sha256_hex("ab" * 32)
    assert is_sha256_hex("AB" * 32)


@pytest.mark.parametrize(
    "bad",
    [None, "", "abc", "g" * 64, "a" * 63, "a" * 65, " " * 64],
)
def test_is_sha256_hex_rejects_bad(bad):
    assert not is_sha256_hex(bad)


def test_normalize_lowercases():
    assert normalize_sha256("AA" * 32) == "aa" * 32

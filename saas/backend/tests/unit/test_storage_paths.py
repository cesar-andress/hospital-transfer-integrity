"""Unit tests for path-guard helpers (milestone 2026-12-02).

TODO(path-guards): implement ``app.storage_paths``, make these pass, then delete
every ``TODO(path-guards)`` marker and the ``xfail`` on this module's tests.
"""

import os
from pathlib import Path

import pytest

pytestmark = [
    pytest.mark.unit,
]


def _import_storage_paths():
    # TODO(path-guards): module missing today — tests stay xfail until it exists
    from app import storage_paths

    return storage_paths


@pytest.mark.xfail(reason="TODO(path-guards): app.storage_paths.safe_join not implemented")
def test_safe_join_keeps_result_under_root(tmp_path):
    sp = _import_storage_paths()
    root = (tmp_path / "tenant_a").resolve()
    root.mkdir()
    out = Path(sp.safe_join(str(root), "doc.pdf")).resolve()
    assert str(out).startswith(str(root) + os.sep) or out.parent == root


@pytest.mark.xfail(reason="TODO(path-guards): safe_join must reject .. traversal")
def test_safe_join_rejects_parent_segments(tmp_path):
    sp = _import_storage_paths()
    root = tmp_path / "tenant_a"
    root.mkdir()
    with pytest.raises((ValueError, OSError)):
        sp.safe_join(str(root), "../../etc/passwd")


@pytest.mark.xfail(reason="TODO(path-guards): assert_under_root missing")
def test_assert_under_root_accepts_nested_file(tmp_path):
    sp = _import_storage_paths()
    root = tmp_path / "tenant_a"
    nested = root / "a" / "b.txt"
    nested.parent.mkdir(parents=True)
    nested.write_text("ok")
    sp.assert_under_root(str(root), str(nested))


@pytest.mark.xfail(reason="TODO(path-guards): assert_under_root must reject escape")
def test_assert_under_root_rejects_outside(tmp_path):
    sp = _import_storage_paths()
    root = tmp_path / "tenant_a"
    root.mkdir()
    outside = tmp_path / "evil.txt"
    outside.write_text("nope")
    with pytest.raises((ValueError, OSError, PermissionError)):
        sp.assert_under_root(str(root), str(outside))

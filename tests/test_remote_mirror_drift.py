"""Data Truth round 2 (2026-11-02): code drift by LF-normalised content hash, not file size.
All but the helper test failed on origin/data-truth-100 ff53514.

    PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider tests/test_remote_mirror_drift.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dashboard_data import remote_mirror as rm  # noqa: E402


@pytest.fixture
def slim(tmp_path, monkeypatch):
    d = tmp_path / "deploy"
    d.mkdir()
    monkeypatch.setenv("WOWZA_SLIM", "1")
    monkeypatch.setattr(rm, "ROOT", tmp_path)
    monkeypatch.setattr(rm, "FULL_CHECKOUT_SENTINEL", tmp_path / "nope")
    monkeypatch.setattr(rm, "MANIFEST", d / "dashboard_manifest.json")
    monkeypatch.setattr(rm, "BUILD_INFO", d / "BUILD_INFO.json")
    monkeypatch.setattr(rm, "SYNC_FILE", d / ".mirror_sync.json")
    monkeypatch.setattr(rm, "V9_MANIFEST_COPY", d / ".v9_manifest_at_data.json")
    (d / "BUILD_INFO.json").write_text(json.dumps({"schema_version": 1}))
    (d / ".mirror_sync.json").write_text(json.dumps({"synced_at_utc": "2026-11-02T00:00:00Z",
                                                     "sha": "abc"}))

    def write(own_code, v9_code, files=None):
        for rel, body in (files or {}).items():
            (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
            (tmp_path / rel).write_bytes(body)
        rm.MANIFEST.write_text(json.dumps({"schema_version": 1, "code": own_code, "data": []}))
        rm.V9_MANIFEST_COPY.write_text(json.dumps({"schema_version": 1, "code": v9_code,
                                                   "data": []}))
    return write


def _e(path, body: bytes, hashed=True):
    e = {"path": path, "bytes": len(body)}
    if hashed:
        e["sha256_lf"] = rm.content_sha(body)
    return e


def test_same_size_different_code_is_drift(slim):
    """`x = 1` -> `x = 2`: same byte count. The size check called this COMPATIBLE."""
    a, b = b"x = 1\n", b"x = 2\n"
    slim([_e("app.py", a)], [_e("app.py", b)], {"app.py": a})
    c = rm.compatibility()
    assert c["status"] == "STALE_BUILD" and c["code_files_differ"] == ["app.py"]
    assert c["drift_basis"] == "sha256_lf"


def test_line_endings_alone_are_not_drift(slim):
    """CRLF vs LF, same code: the size check called this STALE_BUILD."""
    lf, crlf = b"a = 1\nb = 2\n", b"a = 1\r\nb = 2\r\n"
    slim([_e("app.py", crlf)], [_e("app.py", lf)], {"app.py": crlf})
    c = rm.compatibility()
    assert c["status"] == "COMPATIBLE" and c["healthy"]


def test_manifest_without_hashes_is_unknown_not_compatible(slim):
    a = b"x = 1\n"
    slim([_e("app.py", a, hashed=False)], [_e("app.py", a, hashed=False)], {"app.py": a})
    c = rm.compatibility()
    assert c["status"] == "UNKNOWN" and not c["healthy"]


def test_a_hand_edited_deployed_file_is_drift(slim):
    a = b"x = 1\n"
    slim([_e("app.py", a)], [_e("app.py", a)], {"app.py": b"x = 9\n"})
    c = rm.compatibility()
    assert c["status"] == "STALE_BUILD" and c["deployed_files_modified"] == ["app.py"]


def test_file_entry_carries_the_normalised_hash(tmp_path):
    (tmp_path / "f.py").write_bytes(b"a\r\nb\r\n")
    e = rm.file_entry(tmp_path, "f.py")
    assert e["sha256_lf"] == rm.content_sha(b"a\nb\n") and e["bytes"] == 6

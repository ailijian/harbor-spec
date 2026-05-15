from pathlib import Path
import textwrap
import json
import os
from types import SimpleNamespace

from harbor.core.index import IndexBuilder
from harbor.core.sync import SyncEngine
from harbor.test_utils import harbor_ddt_target


def write_module(tmp_path: Path, content: str, name: str = "mod.py") -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


@harbor_ddt_target(func="harbor.core.sync.SyncEngine.check_status", l3_version=1, strategy="strict")
def test_sync_engine_drift_detection(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cache_dir = tmp_path / ".harbor" / "cache"
    code_root = tmp_path / "src"
    code_root.mkdir(parents=True, exist_ok=True)

    src1 = textwrap.dedent(
        """
        def foo(a, b):
            \"\"\"Doc.

            Args:
              a (int): A.
              b (int): B.

            Returns:
              int: Sum.
            \"\"\"
            x = a + b
            return x
        """
    ).strip()
    p = write_module(code_root, src1)

    builder = IndexBuilder(code_roots=[str(code_root)], cache_dir=cache_dir)
    builder.build(incremental=True)

    src2 = textwrap.dedent(
        """
        def foo(a, b):
            \"\"\"Doc.

            Args:
              a (int): A.
              b (int): B.

            Returns:
              int: Sum.
            \"\"\"
            x = a + b
            pass
            return x
        """
    ).strip()
    write_module(code_root, src2)

    eng = SyncEngine()
    eng.code_roots = [str(code_root)]
    eng.cache_file = cache_dir / "l3_index.json"
    rep = eng.check_status()
    assert rep.counts["drift"] >= 1
    ids = [e.id for e in rep.drift]
    assert any(id_.endswith(".foo") for id_ in ids)


def test_compare_snapshots_ignores_public_boundary_metadata_only_changes():
    eng = SyncEngine()
    item_id = "typescript:src/service.ts:function:api"
    old_snapshot = {
        "src/service.ts": {
            item_id: {
                "id": item_id,
                "file_path": "src/service.ts",
                "body_hash": "body-1",
                "contract_hash": "contract-1",
                "contract_presence": "present",
                "contract_required": True,
                "public_boundary_state": "direct_export_only",
                "public_boundary_confidence": "low",
                "public_boundary_evidence_kinds": ["direct_export"],
                "public_boundary_evidence_items": [
                    {"kind": "direct_export", "confidence": "low"}
                ],
                "public_boundary_reason": "Target is exported directly.",
                "boundary_preset_mode": "legacy_exported",
            }
        }
    }
    new_snapshot = {
        "src/service.ts": {
            item_id: {
                "id": item_id,
                "file_path": "src/service.ts",
                "body_hash": "body-1",
                "contract_hash": "contract-1",
                "contract_presence": "present",
                "contract_required": True,
                "public_boundary_state": "package_export_surface",
                "public_boundary_confidence": "high",
                "public_boundary_evidence_kinds": ["direct_export", "package_export"],
                "public_boundary_evidence_items": [
                    {"kind": "direct_export", "confidence": "low"},
                    {"kind": "package_export", "confidence": "high"},
                ],
                "public_boundary_reason": "Target is confirmed by package export evidence.",
                "boundary_preset_mode": "package_public",
            }
        }
    }

    rep = eng._compare_snapshots(
        old_snapshot=old_snapshot,
        new_snapshot=new_snapshot,
        baseline_source="accepted_artifact",
    )

    assert rep.counts["drift"] == 0
    assert rep.counts["modified"] == 0
    assert rep.counts["contract_changed"] == 0
    assert rep.counts["contract_gap"] == 0
    assert rep.counts["untracked"] == 0
    assert rep.counts["missing"] == 0


def test_sync_engine_contract_gap_for_required_target_without_docstring(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cache_dir = tmp_path / ".harbor" / "cache"
    code_root = tmp_path / "harbor" / "core"
    code_root.mkdir(parents=True, exist_ok=True)

    src1 = textwrap.dedent(
        """
        def write_report(x):
            return x
        """
    ).strip()
    p = write_module(code_root, src1, name="gap_case.py")

    builder = IndexBuilder(code_roots=[str(tmp_path / "harbor")], cache_dir=cache_dir)
    builder.build(incremental=True)

    src2 = textwrap.dedent(
        """
        def write_report(x):
            y = x + 1
            return y
        """
    ).strip()
    write_module(code_root, src2, name="gap_case.py")

    eng = SyncEngine()
    eng.code_roots = [str(tmp_path / "harbor")]
    rep = eng.check_status()
    assert rep.counts["contract_gap"] >= 1
    assert rep.counts["drift"] == 0


def test_sync_engine_preserves_accepted_required_contract_gap_when_only_mtime_changes(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cache_dir = tmp_path / ".harbor" / "cache"
    code_root = tmp_path / "harbor" / "core"
    code_root.mkdir(parents=True, exist_ok=True)

    src = textwrap.dedent(
        """
        def write_report(x):
            return x
        """
    ).strip()
    target = write_module(code_root, src, name="accepted_gap.py")

    builder = IndexBuilder(code_roots=[str(tmp_path / "harbor")], cache_dir=cache_dir)
    builder.build(incremental=True)

    original_mtime = target.stat().st_mtime
    target.touch()
    if target.stat().st_mtime == original_mtime:
        os.utime(target, (original_mtime + 5, original_mtime + 5))

    eng = SyncEngine()
    eng.code_roots = [str(tmp_path / "harbor")]
    rep = eng.check_status()

    assert rep.counts["contract_gap"] == 0
    assert rep.counts["untracked"] == 0
    assert rep.counts["missing"] == 0


def test_sync_engine_skipped_no_contract_for_internal_helper_without_docstring(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    code_root = tmp_path / "src"
    code_root.mkdir(parents=True, exist_ok=True)

    src = textwrap.dedent(
        """
        def _helper(x):
            return x + 1
        """
    ).strip()
    write_module(code_root, src, name="helpers.py")

    eng = SyncEngine()
    eng.code_roots = [str(code_root)]
    rep = eng.check_status()

    assert rep.counts["skipped_no_contract"] >= 1
    assert any(entry.id.endswith("._helper") for entry in rep.skipped_no_contract)


def test_sync_engine_contract_parse_error_when_contract_presence_is_malformed(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    code_root = tmp_path / "src"
    code_root.mkdir(parents=True, exist_ok=True)

    src = textwrap.dedent(
        """
        def foo(x):
            return x
        """
    ).strip()
    write_module(code_root, src)

    monkeypatch.setattr(
        "harbor.core.sync.evaluate_contract_presence",
        lambda fc, fp: SimpleNamespace(presence="malformed", required=True, reason="Malformed contract source"),
    )

    eng = SyncEngine()
    eng.code_roots = [str(code_root)]
    rep = eng.check_status()

    assert rep.counts["contract_parse_error"] >= 1
    assert any(entry.id.endswith(".foo") for entry in rep.contract_parse_error)

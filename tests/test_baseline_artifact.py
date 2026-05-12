from pathlib import Path

import pytest

from harbor.core.baseline_artifact import (
    AcceptedBaselineInvalidError,
    build_checkpoint_baseline_artifact,
    load_checkpoint_baseline_artifact,
    normalize_baseline_item_path,
    write_checkpoint_baseline_artifact,
)


def _baseline_item(**overrides):
    item = {
        "id": "harbor.core.sample.run",
        "target_id": "python:harbor/core/sample.py:function:harbor.core.sample.run",
        "func_id": "harbor.core.sample.run",
        "language": "python",
        "symbol_kind": "function",
        "file_path": "harbor/core/sample.py",
        "body_hash": "a" * 64,
        "contract_hash": "b" * 64,
        "contract_presence": "present",
        "contract_required": True,
    }
    item.update(overrides)
    return item


def test_write_and_load_checkpoint_baseline_artifact(tmp_path: Path):
    artifact = build_checkpoint_baseline_artifact(items=[_baseline_item()])
    target = tmp_path / ".harbor" / "baseline" / "accepted-checkpoint.json"
    written = write_checkpoint_baseline_artifact(artifact, path=target, project_root=tmp_path)
    loaded = load_checkpoint_baseline_artifact(target, project_root=tmp_path)

    assert written == target.resolve()
    assert loaded["kind"] == "accepted_checkpoint_baseline"
    assert loaded["baseline"]["items"][0]["file_path"] == "harbor/core/sample.py"


def test_normalize_baseline_item_path_converts_windows_style_input(tmp_path: Path):
    sample = tmp_path / "harbor" / "core" / "sample.py"
    sample.parent.mkdir(parents=True, exist_ok=True)
    sample.write_text("def run():\n    return 1\n", encoding="utf-8")

    normalized = normalize_baseline_item_path(str(sample).replace("/", "\\"), project_root=tmp_path)
    assert normalized == "harbor/core/sample.py"


def test_build_checkpoint_baseline_artifact_rejects_duplicate_target_ids():
    with pytest.raises(AcceptedBaselineInvalidError, match="duplicate baseline item target_id"):
        build_checkpoint_baseline_artifact(
            items=[
                _baseline_item(id="one", func_id="one"),
                _baseline_item(id="two", func_id="two"),
            ]
        )


def test_load_checkpoint_baseline_artifact_rejects_missing_required_field(tmp_path: Path):
    bad = tmp_path / ".harbor" / "baseline" / "accepted-checkpoint.json"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_text(
        """
{
  "schema_version": "1.0",
  "kind": "accepted_checkpoint_baseline",
  "accepted_at": "2026-05-12T00:00:00Z",
  "accepted_by": "harbor accept",
  "harbor_version": "1.4.1",
  "baseline": {
    "items": [
      {
        "id": "harbor.core.sample.run"
      }
    ]
  }
}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(AcceptedBaselineInvalidError, match="target_id"):
        load_checkpoint_baseline_artifact(bad, project_root=tmp_path)

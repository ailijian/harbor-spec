import json
import sys
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

import pytest

import harbor.cli.main as cli_main
from harbor.cli.main import main
from harbor.core.baseline_artifact import build_checkpoint_baseline_artifact, write_checkpoint_baseline_artifact
from harbor.core.sync import SyncEngine


@pytest.fixture(autouse=True)
def _force_en_locale(monkeypatch):
    monkeypatch.setenv("HARBOR_LANGUAGE", "en")


@pytest.fixture(autouse=True)
def _disable_change_window_writes(monkeypatch):
    monkeypatch.setattr(cli_main, "write_change_window_snapshot", lambda *args, **kwargs: None)


@pytest.fixture(autouse=True)
def _disable_ddt(monkeypatch):
    class _FakeDDTScanner:
        def scan_tests(self):
            return []

    class _FakeDDTValidator:
        def validate(self, bindings):
            return type(
                "DDTReport",
                (),
                {"valid": [], "violations": [], "advisory": [], "counts": {"valid": 0, "violations": 0, "advisory": 0}},
            )()

    monkeypatch.setattr(cli_main, "DDTScanner", _FakeDDTScanner)
    monkeypatch.setattr(cli_main, "DDTValidator", _FakeDDTValidator)


def run_cmd(argv):
    out = StringIO()
    err = StringIO()
    code = 0
    with redirect_stdout(out), redirect_stderr(err):
        sys.argv = ["harbor"] + argv
        try:
            main()
        except SystemExit as ex:
            code = ex.code if isinstance(ex.code, int) else 1
    return code, out.getvalue(), err.getvalue()


def _write_sample_repo(tmp_path: Path, *, body: str = "return value") -> Path:
    sample = tmp_path / "harbor" / "core" / "sample.py"
    sample.parent.mkdir(parents=True, exist_ok=True)
    sample.write_text(
        f'''def run(value: int) -> int:
    """Return the current value.

    Behavior:
      - Returns the provided integer unchanged.

    Args:
      value (int): Input integer.

    Returns:
      int: Same integer value.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    """
    {body}
''',
        encoding="utf-8",
    )
    return sample


def _write_typescript_repo(tmp_path: Path) -> Path:
    sample = tmp_path / "src" / "service.ts"
    sample.parent.mkdir(parents=True, exist_ok=True)
    sample.write_text(
        """/**
 * @param value Input integer.
 * @returns Same integer value.
 */
export function api(value: number): number { return value; }
""",
        encoding="utf-8",
    )
    config = tmp_path / ".harbor" / "config.yaml"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        """code_roots:
  - src
languages:
  python:
    enabled: true
  typescript:
    enabled: true
""",
        encoding="utf-8",
    )
    return sample


def _write_artifact_from_current_snapshot(tmp_path: Path) -> Path:
    snapshot = SyncEngine().collect_current_snapshot()
    items = []
    for file_path in sorted(snapshot.keys()):
        for item_id in sorted(snapshot[file_path].keys()):
            row = snapshot[file_path][item_id]
            items.append(
                {
                    "id": row["id"],
                    "target_id": row["target_id"],
                    "func_id": row["func_id"],
                    "language": row["language"],
                    "symbol_kind": row["symbol_kind"],
                    "file_path": row["file_path"],
                    "body_hash": row["body_hash"],
                    "contract_hash": row["contract_hash"],
                    "contract_presence": row["contract_presence"],
                    "contract_required": row["contract_required"],
                }
            )
    artifact = build_checkpoint_baseline_artifact(items=items)
    return write_checkpoint_baseline_artifact(artifact, project_root=tmp_path)


def test_checkpoint_ci_passes_with_accepted_baseline_artifact(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_sample_repo(tmp_path)
    _write_artifact_from_current_snapshot(tmp_path)

    code, out, err = run_cmd(["checkpoint", "--ci", "--format", "json"])
    payload = json.loads(out)

    assert code == 0
    assert err == ""
    assert payload["status"] == "pass"
    assert payload["baseline_source"] == "accepted_artifact"
    assert payload["baseline_path"] == ".harbor/baseline/accepted-checkpoint.json"
    assert payload["baseline_found"] is True
    assert payload["writes_files"] is False


def test_checkpoint_ci_passes_with_typescript_subject_from_accepted_artifact(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_typescript_repo(tmp_path)
    _write_artifact_from_current_snapshot(tmp_path)

    code, out, err = run_cmd(["checkpoint", "--ci", "--format", "json"])
    payload = json.loads(out)

    assert code == 0
    assert err == ""
    assert payload["status"] == "pass"
    assert payload["baseline_source"] == "accepted_artifact"
    assert payload["baseline_found"] is True


def test_checkpoint_ci_fails_when_accepted_baseline_artifact_missing(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_sample_repo(tmp_path)
    calls = []

    class _GuardSyncEngine:
        def check_status(self, baseline_snapshot=None, baseline_source="runtime_cache"):
            calls.append((baseline_snapshot, baseline_source))
            raise AssertionError("checkpoint --ci must not fall back to runtime cache")

    monkeypatch.setattr(cli_main, "SyncEngine", _GuardSyncEngine)
    code, out, err = run_cmd(["checkpoint", "--ci", "--format", "json"])
    payload = json.loads(out)

    assert code == 1
    assert err == ""
    assert calls == []
    assert payload["baseline_found"] is False
    assert payload["ci_failures"][0]["category"] == "accepted_baseline_missing"


def test_checkpoint_ci_fails_when_accepted_baseline_artifact_invalid(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_sample_repo(tmp_path)
    artifact = tmp_path / ".harbor" / "baseline" / "accepted-checkpoint.json"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text('{"kind":"accepted_checkpoint_baseline"}\n', encoding="utf-8")

    code, out, err = run_cmd(["checkpoint", "--ci", "--format", "json"])
    payload = json.loads(out)

    assert code == 1
    assert err == ""
    assert payload["baseline_found"] is False
    assert payload["ci_failures"][0]["category"] == "accepted_baseline_invalid"


def test_checkpoint_ci_fails_on_body_change_against_artifact(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    sample = _write_sample_repo(tmp_path)
    _write_artifact_from_current_snapshot(tmp_path)
    sample.write_text(sample.read_text(encoding="utf-8").replace("return value", "return value + 1"), encoding="utf-8")

    code, out, err = run_cmd(["checkpoint", "--ci", "--format", "json"])
    payload = json.loads(out)

    assert code == 1
    assert err == ""
    assert payload["baseline_found"] is True
    assert any(item["category"] == "possible_semantic_drift" for item in payload["ci_failures"])

import json
import sys
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace

import pytest

import harbor.cli.main as cli_main
from harbor.cli.main import main


@pytest.fixture(autouse=True)
def _force_en_locale(monkeypatch):
    monkeypatch.setenv("HARBOR_LANGUAGE", "en")


@pytest.fixture(autouse=True)
def _disable_change_window_writes(monkeypatch):
    monkeypatch.setattr(cli_main, "write_change_window_snapshot", lambda *args, **kwargs: None)


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


def _write_sample_repo(tmp_path: Path) -> None:
    sample = tmp_path / "harbor" / "core" / "sample.py"
    sample.parent.mkdir(parents=True, exist_ok=True)
    sample.write_text(
        '''def run(value: int) -> int:
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
    return value
''',
        encoding="utf-8",
    )


def test_accept_writes_canonical_baseline_artifact_json(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_sample_repo(tmp_path)

    code, out, err = run_cmd(["accept", "--no-cache-refresh", "--format", "json"])
    payload = json.loads(out)
    artifact_path = tmp_path / ".harbor" / "baseline" / "accepted-checkpoint.json"

    assert code == 0
    assert err == ""
    assert payload["artifact_written"] is True
    assert payload["artifact_path"] == ".harbor/baseline/accepted-checkpoint.json"
    assert payload["artifact_items"] == 1
    assert payload["cache_refreshed"] is False
    assert artifact_path.exists()


def test_accept_supports_custom_output_and_default_cache_refresh(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_sample_repo(tmp_path)

    class _FakeDB:
        def __init__(self):
            self.db_path = tmp_path / ".harbor" / "cache" / "harbor.db"

        def get_all_files(self):
            return []

    class _FakeIndexBuilder:
        def __init__(self, code_roots=None, cache_dir=None):
            self.db = _FakeDB()

        def iter_build(self, incremental=True):
            yield SimpleNamespace(total=1, status="scanning", path="harbor/core/sample.py", items_count=0)
            yield SimpleNamespace(total=1, status="parsed", path="harbor/core/sample.py", items_count=1)

    monkeypatch.setattr(cli_main, "IndexBuilder", _FakeIndexBuilder)

    code, out, err = run_cmd(["accept", "--output", "custom/accepted.json"])

    assert code == 0
    assert err == ""
    assert "Artifact path: custom/accepted.json" in out
    assert "cache_refreshed=true" in out
    assert (tmp_path / "custom" / "accepted.json").exists()

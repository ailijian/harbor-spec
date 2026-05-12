import json
import sys
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

import pytest
from rich.prompt import Prompt

import harbor.cli.main as cli_main
from harbor.cli.main import main
from harbor.core.diary import DiaryManager
from harbor.core.log_draft import _normalize_cli_input_path


@pytest.fixture(autouse=True)
def _force_en_locale(monkeypatch):
    monkeypatch.setenv("HARBOR_LANGUAGE", "en")


@pytest.fixture(autouse=True)
def _isolate_workspace(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def run_cmd(argv):
    out = StringIO()
    err = StringIO()
    code = 0
    with redirect_stdout(out), redirect_stderr(err):
        sys.argv = ["harbor"] + argv
        try:
            main()
        except SystemExit as exc:
            code = exc.code if isinstance(exc.code, int) else 1
    return code, out.getvalue(), err.getvalue()


def _sample_draft_payload() -> dict:
    return {
        "schema_version": "1.0",
        "kind": "diary_draft",
        "summary": "Task E2 adds controlled written diary entry support.",
        "why": "Need an explicit write path from latest draft without exposing file bodies or diff bodies.",
        "affected_areas": {
            "production_code": ["harbor/cli/main.py", "harbor/core/log_draft.py"],
            "tests": ["tests/test_log_write_from_draft.py"],
        },
        "contract_impact": "yes",
        "validation": {"pytest": "pass", "checkpoint": "pass", "stale": "pass", "doctor": "pass"},
        "evidence": {
            "snapshots": [
                {"event": "checkpoint", "timestamp": "2026-05-11T12:00:00Z", "git_head": "abc123"},
            ],
            "reports": [
                {"command": "checkpoint", "status": "pass", "path": ".harbor/reports/checkpoint.json"},
            ],
            "changed_files": [
                {
                    "path": "harbor/cli/main.py",
                    "status": "M",
                },
                {
                    "path": "harbor/cli/main.py",
                    "status": "MM",
                    "body": "def leaked_body(): pass",
                    "diff": "diff --git a/x b/x",
                },
                {
                    "path": ".env",
                    "status": "M",
                    "secret": "API_KEY=shh",
                },
            ],
        },
        "risks": [
            "Keep file body redacted.",
            "Do not keep API_KEY=secret-value in the written entry.",
        ],
        "suggested_diary_entry": (
            "[Diary Draft]\n"
            "- Summary: Controlled log write from latest draft.\n"
            "- Reason: Preserve explicit confirmation and runtime-safety boundaries.\n"
        ),
    }


def _write_json_draft(repo_root: Path, relative_path: str, *, wrap_latest: bool = False) -> Path:
    payload = _sample_draft_payload()
    target = repo_root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    if wrap_latest:
        body = {
            "schema_version": "1.0",
            "kind": "diary_draft",
            "created_at": "2026-05-11T12:30:00Z",
            "source": "harbor log draft",
            "draft": payload,
            "markdown_path": ".harbor/state/log/latest-draft.md",
        }
    else:
        body = payload
    target.write_text(json.dumps(body, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return target


def _write_markdown_draft(repo_root: Path, relative_path: str, body: str) -> Path:
    target = repo_root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")
    return target


def _read_single_diary_entry(repo_root: Path) -> tuple[Path, dict]:
    diary_files = sorted((repo_root / ".harbor" / "diary").glob("*.jsonl"))
    assert len(diary_files) == 1
    lines = diary_files[0].read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    return diary_files[0], json.loads(lines[0])


def _read_last_marker(repo_root: Path) -> dict:
    marker = repo_root / ".harbor" / "state" / "log" / "last_log_marker.json"
    return json.loads(marker.read_text(encoding="utf-8"))


def test_log_write_requires_latest_draft_by_default(tmp_path: Path):
    code, out, err = run_cmd(["log", "write", "--yes"])

    assert code == 1
    assert out == ""
    assert "Latest draft is missing" in err


def test_log_write_yes_writes_from_latest_json_and_updates_marker(tmp_path: Path):
    _write_json_draft(tmp_path, ".harbor/state/log/latest-draft.json", wrap_latest=True)

    code, out, err = run_cmd(["log", "write", "--yes"])
    diary_path, entry = _read_single_diary_entry(tmp_path)
    marker = _read_last_marker(tmp_path)
    rows = DiaryManager(repo_root=tmp_path).load_active(min_visibility="repo")

    assert code == 0
    assert err == ""
    assert entry["schema_version"] == "1.0"
    assert entry["kind"] == "written_diary_entry"
    assert entry["ver"] == 1
    assert entry["author"] == "harbor"
    assert entry["type"] == "decision"
    assert entry["importance"] == "medium"
    assert entry["visibility"] == "repo"
    assert entry["summary"] == "Task E2 adds controlled written diary entry support."
    assert entry["details"].startswith("[Diary Draft]\n")
    assert "Reason: Need an explicit write path from latest draft without exposing file bodies or diff bodies." in entry["details"]
    assert entry["source"] == "harbor log write"
    assert entry["source_draft"] == ".harbor/state/log/latest-draft.json"
    assert entry["contract_impact"] == "yes"
    assert entry["validation"]["pytest"] == "pass"
    assert entry["evidence"]["changed_files"] == [
        {"path": ".env", "status": "M"},
        {"path": "harbor/cli/main.py", "status": "MM"},
    ]
    assert "leaked_body" not in json.dumps(entry, ensure_ascii=False)
    assert "diff --git" not in json.dumps(entry, ensure_ascii=False)
    assert "secret-value" not in json.dumps(entry, ensure_ascii=False)
    assert marker["schema_version"] == "1.0"
    assert marker["last_log_at"] == entry["ts"]
    assert marker["last_draft_path"] == ".harbor/state/log/latest-draft.json"
    assert marker["last_git_head"] == "abc123"
    assert marker["last_snapshot"] == "2026-05-11T12:00:00Z"
    assert marker["diary_path"] == f".harbor/diary/{diary_path.name}"
    assert any(row.summary == entry["summary"] for row in rows)
    assert out.startswith(f"Diary path: .harbor/diary/{diary_path.name}")
    assert "Summary: Task E2 adds controlled written diary entry support." in out
    assert "Source: .harbor/state/log/latest-draft.json" in out
    assert "Marker: .harbor/state/log/last_log_marker.json" in out
    assert '"kind": "written_diary_entry"' not in out


def test_log_write_from_latest_draft_flag_writes_successfully(tmp_path: Path):
    _write_json_draft(tmp_path, ".harbor/state/log/latest-draft.json", wrap_latest=True)

    code, out, err = run_cmd(["log", "write", "--from-latest-draft", "--yes"])
    _, entry = _read_single_diary_entry(tmp_path)

    assert code == 0
    assert err == ""
    assert entry["source"] == "harbor log write --from-latest-draft"
    assert "Source: .harbor/state/log/latest-draft.json" in out


def test_log_write_interactive_yes_writes_diary(monkeypatch, tmp_path: Path):
    _write_json_draft(tmp_path, ".harbor/state/log/latest-draft.json", wrap_latest=True)
    monkeypatch.setattr(cli_main, "_is_log_write_interactive", lambda: True)
    monkeypatch.setattr(Prompt, "ask", staticmethod(lambda *args, **kwargs: "y"))

    code, out, err = run_cmd(["log", "write"])

    assert code == 0
    assert err == ""
    assert "Ready to write Diary entry" in out
    assert "Summary: Task E2 adds controlled written diary entry support." in out
    assert (tmp_path / ".harbor" / "diary").exists()


def test_log_write_interactive_no_cancels_without_writing(monkeypatch, tmp_path: Path):
    _write_json_draft(tmp_path, ".harbor/state/log/latest-draft.json", wrap_latest=True)
    marker_path = tmp_path / ".harbor" / "state" / "log" / "last_log_marker.json"
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_text('{"last_log_at":"2026-05-11T11:59:00Z"}\n', encoding="utf-8")
    before = marker_path.read_text(encoding="utf-8")
    monkeypatch.setattr(cli_main, "_is_log_write_interactive", lambda: True)
    monkeypatch.setattr(Prompt, "ask", staticmethod(lambda *args, **kwargs: "n"))

    code, out, err = run_cmd(["log", "write"])

    assert code == 0
    assert err == ""
    assert "Canceled. No diary written." in out
    assert not (tmp_path / ".harbor" / "diary").exists()
    assert marker_path.read_text(encoding="utf-8") == before


def test_log_write_non_interactive_without_yes_is_rejected(tmp_path: Path):
    _write_json_draft(tmp_path, ".harbor/state/log/latest-draft.json", wrap_latest=True)
    marker_path = tmp_path / ".harbor" / "state" / "log" / "last_log_marker.json"
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_text('{"last_log_at":"2026-05-11T11:59:00Z"}\n', encoding="utf-8")
    before = marker_path.read_text(encoding="utf-8")

    code, out, err = run_cmd(["log", "write"])

    assert code == 1
    assert out == ""
    assert "requires `--yes`" in err
    assert not (tmp_path / ".harbor" / "diary").exists()
    assert marker_path.read_text(encoding="utf-8") == before


@pytest.mark.parametrize(
    ("draft_arg", "expect_success"),
    [
        (".harbor/reports/from-report.md", True),
        (".harbor/reports/from-report.json", True),
        (r".harbor\reports\from-report.json", True),
        (".harbor/diary/blocked.md", False),
        (r".harbor\diary\blocked.md", False),
        (".env", False),
        ("secrets/token.txt", False),
        (".harbor/../.harbor/diary/blocked.md", False),
        ("../outside.md", False),
    ],
)
def test_log_write_from_draft_path_policy(tmp_path: Path, draft_arg: str, expect_success: bool):
    marker_path = tmp_path / ".harbor" / "state" / "log" / "last_log_marker.json"
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_text('{"last_log_at":"2026-05-11T11:59:00Z"}\n', encoding="utf-8")
    before = marker_path.read_text(encoding="utf-8")
    if "reports" in draft_arg.replace("\\", "/"):
        source = draft_arg.replace("\\", "/")
        if source.endswith(".json"):
            _write_json_draft(tmp_path, source)
        else:
            _write_markdown_draft(
                tmp_path,
                source,
                "# Diary Draft\n\n## Summary\n\nReport-based write.\n",
            )
    elif "diary" in draft_arg.replace("\\", "/"):
        _write_markdown_draft(tmp_path, draft_arg.replace("\\", "/"), "# blocked")
    elif draft_arg == ".env":
        _write_markdown_draft(tmp_path, draft_arg, "API_KEY=secret")
    elif draft_arg.startswith("secrets/"):
        _write_markdown_draft(tmp_path, draft_arg, "top-secret")

    code, out, err = run_cmd(["log", "write", "--from-draft", draft_arg, "--yes"])

    if expect_success:
        assert code == 0
        assert err == ""
        _, entry = _read_single_diary_entry(tmp_path)
        assert entry["source_draft"].startswith(".harbor/reports/")
    else:
        assert code == 1
        assert out == ""
        assert "Rejected unsafe `--from-draft` path" in err or "Failed to read draft source" in err
        diary_jsonl = list((tmp_path / ".harbor" / "diary").glob("*.jsonl")) if (tmp_path / ".harbor" / "diary").exists() else []
        assert diary_jsonl == []
        assert marker_path.read_text(encoding="utf-8") == before


def test_log_write_rejects_repo_external_absolute_path(tmp_path: Path):
    outside = tmp_path.parent / "outside-draft.md"
    outside.write_text("# outside", encoding="utf-8")

    code, out, err = run_cmd(["log", "write", "--from-draft", str(outside), "--yes"])

    assert code == 1
    assert out == ""
    assert "Rejected unsafe `--from-draft` path" in err


def test_normalize_cli_input_path_converts_repo_relative_windows_separators():
    assert _normalize_cli_input_path(Path(r".harbor\reports\from-report.json")) == Path(".harbor/reports/from-report.json")
    assert _normalize_cli_input_path(Path(r".harbor\diary\blocked.md")) == Path(".harbor/diary/blocked.md")
    absolute = Path(r"C:\temp\draft.json")
    assert _normalize_cli_input_path(absolute) == absolute


def test_log_write_markdown_fallback_uses_safe_excerpt_only(tmp_path: Path):
    markdown = (
        "# Diary Draft\n\n"
        "```diff\n"
        "diff --git a/x b/x\n"
        "+ leaked\n"
        "```\n\n"
        "API_KEY=super-secret\n\n"
        "This is the first safe block. " + ("x" * 1300) + "\n"
    )
    _write_markdown_draft(tmp_path, ".harbor/reports/fallback.md", markdown)

    code, out, err = run_cmd(["log", "write", "--from-draft", ".harbor/reports/fallback.md", "--yes"])
    _, entry = _read_single_diary_entry(tmp_path)

    assert code == 0
    assert err == ""
    assert entry["contract_impact"] == "uncertain"
    assert len(entry["details"]) <= 1000
    assert "diff --git" not in entry["details"]
    assert "super-secret" not in entry["details"]
    assert "This is the first safe block." in entry["details"]
    assert ".harbor/reports/fallback.md" in out


def test_log_write_markdown_draft_maps_structured_quality_fields(tmp_path: Path):
    markdown = (
        "# Diary Draft\n\n"
        "## Summary\n\n"
        "Release prep closeout for diary type alignment and markdown write quality.\n\n"
        "## Why\n\n"
        "Need deterministic structured conversion without changing the overall CLI workflow.\n\n"
        "## Affected Areas\n\n"
        "- production code: harbor/cli/main.py, harbor/core/log_draft.py\n"
        "- tests: tests/test_log_write_from_draft.py\n"
        "- generated context: .harbor/views/l2/harbor/cli/README.md\n"
        "- reports: .harbor/reports/log-draft-20260512.md\n\n"
        "## Contract Impact\n\n"
        "yes\n\n"
        "## Validation\n\n"
        "- pytest: unknown\n"
        "- checkpoint: pass\n"
        "- stale: pass\n"
        "- doctor: unknown\n\n"
        "## Risks / Notes\n\n"
        "- Keep raw diff bodies out of the written diary entry.\n"
        "- SECRET_TOKEN=top-secret must be redacted.\n\n"
        "## Suggested Diary Entry\n\n"
        "[Diary Draft]\n"
        "- Type: decision\n"
        "- Importance: high\n"
        "- Visibility: repo\n"
        "- Module: tests, generated context, reports, docs\n"
        "- Contract Impact: yes\n"
        "- Breaking Change: uncertain\n"
        "- Summary: Diary type alignment release prep closeout.\n"
        "- Reason: Preserve deterministic write quality without changing the CLI workflow semantics.\n"
        "- Changes:\n"
        "  - Added structured markdown extraction for summary, reason, validation, and risks.\n"
        "  - Removed duplicate changed_files noise and diff-body leakage.\n"
        "- Tests:\n"
        "  - pytest: unknown\n"
        "  - checkpoint: pass\n"
        "  - stale: pass\n"
        "  - doctor: unknown\n"
        "- Risks:\n"
        "  - diff --git a/x b/x must never appear in details.\n"
        "  - API_KEY=super-secret must never appear in details.\n"
    )
    _write_markdown_draft(tmp_path, ".harbor/reports/log-draft-quality.md", markdown)

    code, out, err = run_cmd(["log", "write", "--from-draft", ".harbor/reports/log-draft-quality.md", "--yes"])
    _, entry = _read_single_diary_entry(tmp_path)
    entry_json = json.dumps(entry, ensure_ascii=False)

    assert code == 0
    assert err == ""
    assert entry["summary"] == "Diary type alignment release prep closeout."
    assert not entry["summary"].startswith("[Diary Draft]")
    assert entry["type"] == "decision"
    assert entry["importance"] == "high"
    assert entry["visibility"] == "repo"
    assert entry["contract_impact"] == "yes"
    assert entry["validation"]["checkpoint"] == "pass"
    assert entry["validation"]["stale"] == "pass"
    assert entry["validation"]["pytest"] == "unknown"
    assert entry["validation"]["doctor"] == "unknown"
    assert "Keep raw diff bodies out of the written diary entry." in entry["risks"]
    assert "Reason: Preserve deterministic write quality without changing the CLI workflow semantics." in entry["details"]
    assert "Validation: pytest=unknown, checkpoint=pass, stale=pass, doctor=unknown" in entry["details"]
    assert "Changes: Added structured markdown extraction for summary, reason, validation, and risks.; Removed duplicate changed_files noise and diff-body leakage." in entry["details"]
    assert "Affected Areas:" in entry["details"]
    assert "generated_context=.harbor/views/l2/harbor/cli/README.md" in entry["details"]
    assert "tests=tests/test_log_write_from_draft.py" in entry["details"]
    assert "areas=tests, generated context, reports, docs" in entry["details"]
    assert entry["details"].startswith("[Diary Draft]\n")
    assert "## Suggested Diary Entry" not in entry["details"]
    assert "# Diary Draft" not in entry["details"]
    assert "diff --git" not in entry["details"]
    assert "API_KEY" not in entry_json
    assert "super-secret" not in entry_json
    assert "top-secret" not in entry_json
    assert len(entry["details"]) <= 2000
    assert ".harbor/reports/log-draft-quality.md" in out


def test_log_write_marker_failure_warns_without_rolling_back_diary(monkeypatch, tmp_path: Path):
    _write_json_draft(tmp_path, ".harbor/state/log/latest-draft.json", wrap_latest=True)
    original_write_text = Path.write_text

    def _failing_write_text(self, data, *args, **kwargs):
        if self.name == "last_log_marker.json":
            raise OSError("disk full")
        return original_write_text(self, data, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", _failing_write_text)

    code, out, err = run_cmd(["log", "write", "--yes"])
    diary_path, entry = _read_single_diary_entry(tmp_path)

    assert code == 0
    assert f"Diary path: .harbor/diary/{diary_path.name}" in out
    assert entry["kind"] == "written_diary_entry"
    assert "Last log marker warning for .harbor/state/log/last_log_marker.json: Failed to write last log marker" in err
    assert not (tmp_path / ".harbor" / "state" / "log" / "last_log_marker.json").exists()

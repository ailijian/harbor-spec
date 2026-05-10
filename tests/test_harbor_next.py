import json
import sys
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from harbor.cli.main import main


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


def test_next_reads_checkpoint_report_and_groups_output(tmp_path: Path):
    report = {
        "command": "checkpoint",
        "ci_failures": [
            {
                "category": "possible_semantic_drift",
                "func_id": "harbor.core.foo.bar",
                "file_path": "harbor/core/foo.py",
            }
        ],
        "advisory": [
            {
                "category": "ddt_version_baseline_missing",
                "func_id": "harbor.core.foo.bar",
                "file_path": "tests/test_foo.py",
            }
        ],
    }
    report_path = tmp_path / "checkpoint.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    code, out, _ = run_cmd(["next", "--from", str(report_path)])
    assert code == 0
    assert "Blocking failures:" in out
    assert "Advisory:" in out
    assert "possible_semantic_drift" in out
    assert "ddt_version_baseline_missing" in out


def test_next_json_output_contract(tmp_path: Path):
    report = {"command": "checkpoint", "ci_failures": [], "advisory": []}
    report_path = tmp_path / "checkpoint.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    code, out, _ = run_cmd(["next", "--from", str(report_path), "--format", "json"])
    payload = json.loads(out)
    assert code == 0
    assert payload["command"] == "next"
    assert payload["source_command"] == "checkpoint"
    assert payload["llm_used"] is False
    assert payload["writes_files"] is False


def test_next_json_items_include_blocking_and_status_is_ok_even_for_fail_report(tmp_path: Path):
    report = {
        "command": "checkpoint",
        "status": "fail",
        "ci_failures": [{"category": "contract_gap"}],
        "advisory": [{"category": "ddt_version_baseline_missing"}],
    }
    report_path = tmp_path / "checkpoint.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    code, out, _ = run_cmd(["next", "--from", str(report_path), "--format", "json"])
    payload = json.loads(out)
    assert code == 0
    assert payload["status"] == "ok"
    assert payload["items"][0]["blocking"] is True
    assert payload["items"][1]["blocking"] is False


def test_next_unknown_category_graceful_degrade(tmp_path: Path):
    report = {
        "command": "checkpoint",
        "ci_failures": [{"category": "unknown_category"}],
        "advisory": [],
    }
    report_path = tmp_path / "checkpoint.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    code, out, _ = run_cmd(["next", "--from", str(report_path), "--format", "json"])
    payload = json.loads(out)
    assert code == 0
    assert payload["items"]
    guidance = payload["items"][0]["guidance"]
    assert guidance["decision_required"] is True
    assert guidance["safe_to_auto_fix"] is False
    assert guidance["automation_policy"] == "plan_only"


def test_next_can_read_utf16_report(tmp_path: Path):
    report = {"command": "checkpoint", "ci_failures": [], "advisory": []}
    report_path = tmp_path / "checkpoint-utf16.json"
    report_path.write_text(json.dumps(report), encoding="utf-16")
    code, out, _ = run_cmd(["next", "--from", str(report_path), "--format", "json"])
    payload = json.loads(out)
    assert code == 0
    assert payload["command"] == "next"

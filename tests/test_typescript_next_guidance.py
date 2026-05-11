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


def _write_report(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_next_explains_typescript_contract_gap(tmp_path: Path):
    report = {
        "command": "checkpoint",
        "ci_failures": [
            {
                "category": "contract_gap",
                "func_id": "typescript:src/service.ts:function:api",
                "target_id": "typescript:src/service.ts:function:api",
                "language": "typescript",
                "symbol_kind": "function",
                "adapter": "typescript",
            }
        ],
        "advisory": [],
    }
    report_path = tmp_path / "checkpoint-ts-gap.json"
    _write_report(report_path, report)
    code, out, _ = run_cmd(["next", "--from", str(report_path), "--format", "json"])
    payload = json.loads(out)
    assert code == 0
    guidance = payload["items"][0]["guidance"]
    assert "JSDoc/TSDoc" in guidance["recommended_action"]
    assert "signature alone" in guidance.get("anti_action", "")
    assert guidance["safe_to_auto_fix"] is False


def test_next_explains_typescript_skipped_no_contract(tmp_path: Path):
    report = {
        "command": "checkpoint",
        "ci_failures": [],
        "advisory": [
            {
                "category": "skipped_no_contract",
                "func_id": "typescript:src/helper.ts:function:helper",
                "target_id": "typescript:src/helper.ts:function:helper",
                "language": "typescript",
                "symbol_kind": "function",
                "adapter": "typescript",
            }
        ],
    }
    report_path = tmp_path / "checkpoint-ts-skip.json"
    _write_report(report_path, report)
    code, out, _ = run_cmd(["next", "--from", str(report_path), "--format", "json"])
    payload = json.loads(out)
    assert code == 0
    guidance = payload["items"][0]["guidance"]
    assert "contract-not-required" in guidance["what_happened"]
    assert "No action is required" in guidance["recommended_action"]
    assert guidance["safe_to_auto_fix"] is False


def test_next_explains_typescript_unsupported_syntax_advisory(tmp_path: Path):
    report = {
        "command": "checkpoint",
        "ci_failures": [],
        "advisory": [
            {
                "category": "unsupported_syntax_advisory",
                "func_id": "typescript:src/unsupported.ts:function:odd",
                "target_id": "typescript:src/unsupported.ts:function:odd",
                "language": "typescript",
                "symbol_kind": "function",
                "adapter": "typescript",
            }
        ],
    }
    report_path = tmp_path / "checkpoint-ts-unsupported.json"
    _write_report(report_path, report)
    code, out, _ = run_cmd(["next", "--from", str(report_path), "--format", "json"])
    payload = json.loads(out)
    assert code == 0
    guidance = payload["items"][0]["guidance"]
    assert "lightweight parser" in guidance["what_happened"]
    assert "future AST backend/framework preset" in guidance["recommended_action"]
    assert guidance["safe_to_auto_fix"] is False


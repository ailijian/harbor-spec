import json
import sys
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from harbor.cli.main import main


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_PUBLIC_EXAMPLE = REPO_ROOT / "examples" / "typescript-verification-preview" / "package-public"
SEMANTIC_AUDIT_EXAMPLE = REPO_ROOT / "examples" / "typescript-verification-preview" / "semantic-audit-preview"


def _run_cmd(cwd: Path, argv: list[str], monkeypatch) -> tuple[int, str, str]:
    out = StringIO()
    err = StringIO()
    code = 0
    monkeypatch.chdir(cwd)
    with redirect_stdout(out), redirect_stderr(err):
        sys.argv = ["harbor"] + argv
        try:
            main()
        except SystemExit as ex:
            code = ex.code if isinstance(ex.code, int) else 1
    return code, out.getvalue(), err.getvalue()


def test_package_public_preview_example_matches_documented_checkpoint_and_next(monkeypatch, tmp_path: Path) -> None:
    code, out, _ = _run_cmd(
        PACKAGE_PUBLIC_EXAMPLE,
        ["checkpoint", "--ci", "--format", "json", "--detail", "full"],
        monkeypatch,
    )
    payload = json.loads(out)

    assert code == 1
    assert payload["summary"]["typescript_ddt_preview_bindings"] == 1
    assert payload["summary"]["typescript_ddt_preview_valid"] == 1
    assert payload["summary"]["typescript_ddt_preview_advisory"] == 0
    finding = payload["typescript_ddt_preview"]["findings"][0]
    assert finding["status"] == "preview_valid"
    assert finding["binding_id"] == "api-binding"
    assert finding["target_id"] == "typescript:src/index.ts:function:api"
    assert finding["test_asset_path"] == "tests/api.test.ts"
    assert finding["boundary_preset_mode"] == "package_public"
    assert finding["public_boundary_state"] == "package_export_surface"
    assert finding["blocking"] is False
    assert finding["preview"] is True
    assert any(item["category"] == "accepted_baseline_missing" for item in payload["ci_failures"])

    report_path = tmp_path / "checkpoint-demo.json"
    report_path.write_text(out, encoding="utf-8")
    next_code, next_out, _ = _run_cmd(
        PACKAGE_PUBLIC_EXAMPLE,
        ["next", "--from", str(report_path), "--format", "json"],
        monkeypatch,
    )
    next_payload = json.loads(next_out)

    assert next_code == 0
    preview_items = [item for item in next_payload["items"] if item["category"] == "preview_valid"]
    assert len(preview_items) == 1
    assert preview_items[0]["binding_id"] == "api-binding"
    assert preview_items[0]["target_id"] == "typescript:src/index.ts:function:api"
    assert preview_items[0]["blocking"] is False
    assert preview_items[0]["preview"] is True


def test_semantic_audit_preview_example_matches_documented_jsonl_output(monkeypatch) -> None:
    code, out, _ = _run_cmd(
        SEMANTIC_AUDIT_EXAMPLE,
        ["check", "--format", "jsonl"],
        monkeypatch,
    )
    json_rows = [json.loads(line) for line in out.splitlines() if line.lstrip().startswith("{")]

    assert code == 0
    assert len(json_rows) == 1
    row = json_rows[0]
    assert row["status"] == "SKIPPED_NO_CONTRACT"
    assert row["file_path"] == "src/index.ts"
    assert row["preview"] is True
    assert row["eligible"] is False
    assert row["eligibility_reason"] == "behavior_contract_missing"
    assert row["llm_called"] is False
    assert row["language"] == "typescript"
    assert row["symbol_kind"] == "function"
    assert row["target_id"].endswith("/examples/typescript-verification-preview/semantic-audit-preview/src/index.ts:function:noDoc")

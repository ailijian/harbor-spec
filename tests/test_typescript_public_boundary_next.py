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


def test_next_text_explains_package_public_boundary_relationship(tmp_path: Path):
    report = {
        "command": "checkpoint",
        "ci_failures": [],
        "advisory": [
            {
                "category": "skipped_no_contract",
                "func_id": "typescript:src/index.ts:function:api",
                "file_path": "src/index.ts",
                "language": "typescript",
                "public_boundary_state": "package_export_surface",
                "public_boundary_confidence": "high",
                "public_boundary_evidence_kinds": ["direct_export", "package_export"],
                "public_boundary_reason": "Target is confirmed by package export evidence.",
                "boundary_preset_mode": "package_public",
            }
        ],
    }
    report_path = tmp_path / "checkpoint-ts-next.txt.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")

    code, out, _ = run_cmd(["next", "--from", str(report_path)])

    assert code == 0
    assert "boundary_preset_mode=package_public" in out
    assert "public_boundary_state=package_export_surface" in out
    assert "Preset package_public treats package exports as the strongest public boundary signal." in out
    assert "Boundary state is package_export_surface" in out
    assert "Evidence: direct export, package export." in out


def test_next_json_adds_boundary_explanation_and_guidance_notes(tmp_path: Path):
    report = {
        "command": "checkpoint",
        "ci_failures": [],
        "advisory": [
            {
                "category": "contract_gap",
                "func_id": "typescript:src/internal/service.ts:function:api",
                "file_path": "src/internal/service.ts",
                "language": "typescript",
                "public_boundary_state": "configured_entrypoint_surface",
                "public_boundary_confidence": "medium",
                "public_boundary_evidence_kinds": [
                    "direct_export",
                    "named_re_export",
                    "configured_entrypoint",
                ],
                "public_boundary_reason": "Target is confirmed by configured entrypoint evidence.",
                "boundary_preset_mode": "custom_entrypoints",
            }
        ],
    }
    report_path = tmp_path / "checkpoint-ts-next.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")

    code, out, _ = run_cmd(["next", "--from", str(report_path), "--format", "json"])
    payload = json.loads(out)

    assert code == 0
    item = payload["items"][0]
    assert item["boundary_explanation"].startswith(
        "Preset custom_entrypoints confirms public boundary from configured entrypoints."
    )
    assert "configured entrypoint" in item["boundary_explanation"]
    assert item["guidance"]["notes"][-1] == item["boundary_explanation"]

import json
import sys
import textwrap
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace

import yaml

from harbor.cli.main import main
from harbor.core.ci import build_checkpoint_ci_result, checkpoint_ci_result_to_dict
from harbor.core.contract_impact import ContractImpactLevel, ContractImpactReport
from harbor.core.verification import validate_typescript_ddt_preview


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _config(*, enabled: bool = True, require_public_boundary: bool = False) -> dict:
    return {
        "code_roots": ["src"],
        "languages": {
            "python": {"enabled": True},
            "typescript": {"enabled": True},
        },
        "verification": {
            "typescript_ddt_preview": {
                "enabled": enabled,
                "bindings_file": ".harbor/ddt/typescript-bindings.yaml",
                "require_contract_source": True,
                "require_public_boundary": require_public_boundary,
            }
        },
    }


def _empty_status_report():
    return SimpleNamespace(
        drift=[],
        modified=[],
        contract_changed=[],
        contract_gap=[],
        skipped_no_contract=[],
        contract_parse_error=[],
        unsupported_syntax_advisory=[],
        untracked=[],
        missing=[],
        counts={},
    )


def _empty_ddt_report():
    return SimpleNamespace(valid=[], violations=[], advisory=[], counts={"valid": 0, "violations": 0, "advisory": 0})


def _empty_contract_report() -> ContractImpactReport:
    return ContractImpactReport(
        level=ContractImpactLevel.NO_CONTRACT_IMPACT,
        categories=[],
        findings=[],
        summary_counts={
            ContractImpactLevel.NO_CONTRACT_IMPACT.value: 0,
            ContractImpactLevel.POSSIBLE_CONTRACT_IMPACT.value: 0,
            ContractImpactLevel.CONFIRMED_CONTRACT_IMPACT.value: 0,
            ContractImpactLevel.UNKNOWN.value: 0,
        },
        notable_findings=[],
    )


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


def test_typescript_ddt_preview_validator_reports_preview_valid(tmp_path: Path) -> None:
    _write(
        tmp_path / "src" / "api.ts",
        textwrap.dedent(
            """
            /**
             * @param x value
             * @returns value
             */
            export function api(x: number): number { return x + 1; }
            """
        ).strip(),
    )
    _write(tmp_path / "tests" / "api.test.ts", "test('api', () => {});\n")
    _write_yaml(
        tmp_path / ".harbor" / "ddt" / "typescript-bindings.yaml",
        {
            "schema_version": "1.0",
            "bindings": [
                {
                    "binding_id": "api-binding",
                    "target_id": "typescript:src/api.ts:function:api",
                    "test_asset": {"path": "tests/api.test.ts", "label": "api smoke"},
                    "strategy": "preview_reference",
                }
            ],
        },
    )

    report = validate_typescript_ddt_preview(tmp_path, _config())

    assert report is not None
    assert report.bindings_count == 1
    assert report.valid_count == 1
    assert report.advisory_count == 0
    assert [finding.status for finding in report.findings] == ["preview_valid"]
    assert report.findings[0].target_id == "typescript:src/api.ts:function:api"


def test_typescript_ddt_preview_validator_reports_duplicate_binding_id(tmp_path: Path) -> None:
    _write(
        tmp_path / "src" / "api.ts",
        "/** @param x value @returns value */\nexport function api(x: number): number { return x + 1; }\n",
    )
    _write(tmp_path / "tests" / "api.test.ts", "test('api', () => {});\n")
    _write_yaml(
        tmp_path / ".harbor" / "ddt" / "typescript-bindings.yaml",
        {
            "schema_version": "1.0",
            "bindings": [
                {
                    "binding_id": "dup-binding",
                    "target_id": "typescript:src/api.ts:function:api",
                    "test_asset": {"path": "tests/api.test.ts"},
                    "strategy": "preview_reference",
                },
                {
                    "binding_id": "dup-binding",
                    "target_id": "typescript:src/api.ts:function:api",
                    "test_asset": {"path": "tests/api.test.ts"},
                    "strategy": "preview_reference",
                },
            ],
        },
    )

    report = validate_typescript_ddt_preview(tmp_path, _config())

    assert report is not None
    assert report.valid_count == 0
    assert report.advisory_count == 1
    assert [finding.status for finding in report.findings] == ["duplicate_binding_id"]


def test_typescript_ddt_preview_validator_reports_target_not_found_and_test_asset_missing(tmp_path: Path) -> None:
    _write_yaml(
        tmp_path / ".harbor" / "ddt" / "typescript-bindings.yaml",
        {
            "schema_version": "1.0",
            "bindings": [
                {
                    "binding_id": "missing-target",
                    "target_id": "typescript:src/missing.ts:function:api",
                    "test_asset": {"path": "tests/missing.test.ts"},
                    "strategy": "preview_reference",
                }
            ],
        },
    )

    report = validate_typescript_ddt_preview(tmp_path, _config())

    assert report is not None
    assert [finding.status for finding in report.findings] == ["target_not_found"]


def test_typescript_ddt_preview_validator_reports_test_asset_missing(tmp_path: Path) -> None:
    _write(
        tmp_path / "src" / "api.ts",
        "/** @param x value @returns value */\nexport function api(x: number): number { return x + 1; }\n",
    )
    _write_yaml(
        tmp_path / ".harbor" / "ddt" / "typescript-bindings.yaml",
        {
            "schema_version": "1.0",
            "bindings": [
                {
                    "binding_id": "missing-test",
                    "target_id": "typescript:src/api.ts:function:api",
                    "test_asset": {"path": "tests/missing.test.ts"},
                    "strategy": "preview_reference",
                }
            ],
        },
    )

    report = validate_typescript_ddt_preview(tmp_path, _config())

    assert report is not None
    assert [finding.status for finding in report.findings] == ["test_asset_missing"]


def test_typescript_ddt_preview_validator_reports_contract_source_missing(tmp_path: Path) -> None:
    _write(tmp_path / "src" / "api.ts", "export function api(x: number): number { return x + 1; }\n")
    _write(tmp_path / "tests" / "api.test.ts", "test('api', () => {});\n")
    _write_yaml(
        tmp_path / ".harbor" / "ddt" / "typescript-bindings.yaml",
        {
            "schema_version": "1.0",
            "bindings": [
                {
                    "binding_id": "missing-contract",
                    "target_id": "typescript:src/api.ts:function:api",
                    "test_asset": {"path": "tests/api.test.ts"},
                    "strategy": "preview_reference",
                }
            ],
        },
    )

    report = validate_typescript_ddt_preview(tmp_path, _config())

    assert report is not None
    assert [finding.status for finding in report.findings] == ["contract_source_missing"]


def test_typescript_ddt_preview_validator_reports_public_boundary_unconfirmed(tmp_path: Path) -> None:
    _write(
        tmp_path / "src" / "internal.ts",
        textwrap.dedent(
            """
            /**
             * @param x value
             * @returns value
             */
            function helper(x: number): number { return x + 1; }
            export { helper };
            """
        ).strip(),
    )
    _write(tmp_path / "tests" / "internal.test.ts", "test('helper', () => {});\n")
    _write_yaml(
        tmp_path / ".harbor" / "ddt" / "typescript-bindings.yaml",
        {
            "schema_version": "1.0",
            "bindings": [
                {
                    "binding_id": "boundary-check",
                    "target_id": "typescript:src/internal.ts:function:helper",
                    "test_asset": {"path": "tests/internal.test.ts"},
                    "strategy": "preview_reference",
                }
            ],
        },
    )

    report = validate_typescript_ddt_preview(tmp_path, _config(require_public_boundary=True))

    assert report is not None
    assert [finding.status for finding in report.findings] == ["public_boundary_unconfirmed"]


def test_typescript_ddt_preview_validator_reports_binding_schema_invalid(tmp_path: Path) -> None:
    _write_yaml(
        tmp_path / ".harbor" / "ddt" / "typescript-bindings.yaml",
        {
            "schema_version": "1.0",
            "bindings": [
                {
                    "binding_id": "bad-binding",
                    "target_id": "typescript:src/api.ts:function:api",
                    "test_asset": {"path": "../outside.test.ts"},
                    "strategy": "preview_auto",
                }
            ],
        },
    )

    report = validate_typescript_ddt_preview(tmp_path, _config())

    assert report is not None
    assert [finding.status for finding in report.findings] == ["binding_schema_invalid"]


def test_typescript_ddt_preview_validator_dedupes_and_sorts_findings_deterministically(tmp_path: Path) -> None:
    _write(tmp_path / "src" / "a.ts", "export function a(): number { return 1; }\n")
    _write(tmp_path / "src" / "b.ts", "export function b(): number { return 2; }\n")
    _write_yaml(
        tmp_path / ".harbor" / "ddt" / "typescript-bindings.yaml",
        {
            "schema_version": "1.0",
            "bindings": [
                {
                    "binding_id": "b-binding",
                    "target_id": "typescript:src/b.ts:function:b",
                    "test_asset": {"path": "tests/b.test.ts"},
                    "strategy": "preview_reference",
                },
                {
                    "binding_id": "a-binding",
                    "target_id": "typescript:src/a.ts:function:a",
                    "test_asset": {"path": "tests/a.test.ts"},
                    "strategy": "preview_reference",
                },
            ],
        },
    )

    report = validate_typescript_ddt_preview(tmp_path, _config())

    assert report is not None
    assert [finding.status for finding in report.findings] == [
        "test_asset_missing",
        "test_asset_missing",
        "contract_source_missing",
        "contract_source_missing",
    ]
    assert [finding.binding_id for finding in report.findings] == [
        "a-binding",
        "b-binding",
        "a-binding",
        "b-binding",
    ]


def test_typescript_ddt_preview_disabled_has_no_side_effect(tmp_path: Path) -> None:
    _write(tmp_path / ".harbor" / "ddt" / "typescript-bindings.yaml", "schema_version: [invalid")
    assert validate_typescript_ddt_preview(tmp_path, _config(enabled=False)) is None


def test_checkpoint_json_adds_typescript_ddt_preview_without_polluting_ci_failures(tmp_path: Path) -> None:
    _write(
        tmp_path / "src" / "api.ts",
        "/** @param x value @returns value */\nexport function api(x: number): number { return x + 1; }\n",
    )
    _write(tmp_path / "tests" / "api.test.ts", "test('api', () => {});\n")
    _write_yaml(
        tmp_path / ".harbor" / "ddt" / "typescript-bindings.yaml",
        {
            "schema_version": "1.0",
            "bindings": [
                {
                    "binding_id": "api-binding",
                    "target_id": "typescript:src/api.ts:function:api",
                    "test_asset": {"path": "tests/api.test.ts"},
                    "strategy": "preview_reference",
                }
            ],
        },
    )
    preview_report = validate_typescript_ddt_preview(tmp_path, _config())
    payload = checkpoint_ci_result_to_dict(
        build_checkpoint_ci_result(
            status_report=_empty_status_report(),
            ddt_report=_empty_ddt_report(),
            contract_impact_report=_empty_contract_report(),
            typescript_ddt_preview=preview_report,
        )
    )

    assert payload["ci_failures"] == []
    assert payload["exit_code"] == 0
    assert "typescript_ddt_preview" in payload
    assert payload["typescript_ddt_preview"]["advisory_count"] >= 0


def test_checkpoint_json_omits_typescript_ddt_preview_when_disabled() -> None:
    payload = checkpoint_ci_result_to_dict(
        build_checkpoint_ci_result(
            status_report=_empty_status_report(),
            ddt_report=_empty_ddt_report(),
            contract_impact_report=_empty_contract_report(),
            typescript_ddt_preview=None,
        )
    )

    assert "typescript_ddt_preview" not in payload


def test_next_consumes_checkpoint_preview_findings_and_keeps_them_non_blocking(tmp_path: Path) -> None:
    report = {
        "command": "checkpoint",
        "ci_failures": [],
        "advisory": [],
        "typescript_ddt_preview": {
            "bindings_file": ".harbor/ddt/typescript-bindings.yaml",
            "bindings_count": 2,
            "valid_count": 1,
            "advisory_count": 1,
            "findings": [
                {
                    "status": "preview_valid",
                    "category": "preview_valid",
                    "binding_id": "api-binding",
                    "target_id": "typescript:src/api.ts:function:api",
                    "test_asset_path": "tests/api.test.ts",
                    "reason": "TypeScript DDT preview binding is declared, resolved, and currently advisory-valid.",
                    "language": "typescript",
                    "symbol_kind": "function",
                    "adapter": "typescript",
                    "preview": True,
                    "advisory": True,
                    "blocking": False,
                },
                {
                    "status": "contract_source_missing",
                    "category": "contract_source_missing",
                    "binding_id": "missing-contract",
                    "target_id": "typescript:src/no-doc.ts:function:noDoc",
                    "test_asset_path": "tests/no-doc.test.ts",
                    "reason": "Required TypeScript contract source is missing or not contract-like for preview validation.",
                    "language": "typescript",
                    "symbol_kind": "function",
                    "adapter": "typescript",
                    "preview": True,
                    "advisory": True,
                    "blocking": False,
                },
            ],
        },
    }
    report_path = tmp_path / "checkpoint.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")

    code, out, _ = run_cmd(["next", "--from", str(report_path), "--format", "json"])
    payload = json.loads(out)

    assert code == 0
    categories = [item["category"] for item in payload["items"]]
    assert "preview_valid" in categories
    assert "contract_source_missing" in categories
    preview_items = [item for item in payload["items"] if item["category"] in {"preview_valid", "contract_source_missing"}]
    assert preview_items
    assert all(item["blocking"] is False for item in preview_items)


def test_next_text_explains_preview_binding_context(tmp_path: Path) -> None:
    report = {
        "command": "checkpoint",
        "ci_failures": [],
        "advisory": [],
        "typescript_ddt_preview": {
            "bindings_file": ".harbor/ddt/typescript-bindings.yaml",
            "bindings_count": 1,
            "valid_count": 0,
            "advisory_count": 1,
            "findings": [
                {
                    "status": "public_boundary_unconfirmed",
                    "category": "public_boundary_unconfirmed",
                    "binding_id": "boundary-check",
                    "target_id": "typescript:src/internal.ts:function:helper",
                    "test_asset_path": "tests/internal.test.ts",
                    "reason": "TypeScript public boundary is not confirmed strongly enough for preview validation.",
                    "language": "typescript",
                    "symbol_kind": "function",
                    "adapter": "typescript",
                    "preview": True,
                    "advisory": True,
                    "blocking": False,
                    "public_boundary_state": "internal_or_unconfirmed",
                    "public_boundary_confidence": "low",
                    "boundary_preset_mode": "legacy_exported",
                    "public_boundary_reason": "Target is internal or has no confirmed public boundary evidence.",
                }
            ],
        },
    }
    report_path = tmp_path / "checkpoint.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")

    code, out, _ = run_cmd(["next", "--from", str(report_path)])

    assert code == 0
    assert "public_boundary_unconfirmed" in out
    assert "Binding: boundary-check" in out
    assert "Test asset: tests/internal.test.ts" in out
    assert "preview_only=true" in out

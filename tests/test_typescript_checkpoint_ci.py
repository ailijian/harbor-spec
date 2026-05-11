import textwrap
from pathlib import Path
from types import SimpleNamespace

import yaml

from harbor.core.ci import build_checkpoint_ci_result, checkpoint_ci_result_to_dict
from harbor.core.contract_impact import ContractImpactLevel, ContractImpactReport
from harbor.core.sync import SyncEngine


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_config(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _empty_ddt_report():
    return SimpleNamespace(valid=[], violations=[], advisory=[], counts={"valid": 0, "violations": 0, "advisory": 0})


def _empty_contract_report():
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


def _checkpoint_payload(tmp_path: Path, *, ts_enabled: bool = True):
    cfg_path = tmp_path / ".harbor" / "config.yaml"
    _write_config(
        cfg_path,
        {
            "code_roots": [str(tmp_path / "src")],
            "languages": {
                "python": {"enabled": True},
                "typescript": {"enabled": ts_enabled},
            },
        },
    )
    engine = SyncEngine(config_path=cfg_path)
    engine.code_roots = [str(tmp_path / "src")]
    report = engine.check_status()
    payload = checkpoint_ci_result_to_dict(
        build_checkpoint_ci_result(
            status_report=report,
            ddt_report=_empty_ddt_report(),
            contract_impact_report=_empty_contract_report(),
        )
    )
    return payload


def test_ts_enabled_exported_function_without_jsdoc_becomes_contract_gap(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write(tmp_path / "src" / "service.ts", "export function api(x: number): number { return x + 1; }\n")
    payload = _checkpoint_payload(tmp_path, ts_enabled=True)
    rows = [row for row in payload["ci_failures"] if row.get("language") == "typescript"]
    assert payload["exit_code"] == 1
    assert len(rows) == 1
    assert rows[0]["category"] == "contract_gap"
    assert rows[0]["reason"] == "Required TypeScript contract source is missing or not contract-like."


def test_ts_enabled_high_confidence_jsdoc_avoids_contract_gap(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write(
        tmp_path / "src" / "service.ts",
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
    payload = _checkpoint_payload(tmp_path, ts_enabled=True)
    ts_rows = [row for row in payload["ci_failures"] + payload["advisory"] if row.get("language") == "typescript"]
    assert payload["exit_code"] == 0
    assert ts_rows == []


def test_ts_enabled_internal_helper_without_jsdoc_becomes_skipped_advisory(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write(tmp_path / "src" / "helper.ts", "function helper(x: number): number { return x + 1; }\n")
    payload = _checkpoint_payload(tmp_path, ts_enabled=True)
    advisory = [row for row in payload["advisory"] if row.get("language") == "typescript"]
    assert payload["exit_code"] == 0
    assert len(advisory) == 1
    assert advisory[0]["category"] == "skipped_no_contract"
    assert advisory[0]["reason"] == "No contract required for this TypeScript target; semantic comparison skipped."


def test_ts_enabled_medium_block_comment_is_contract_gap(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write(
        tmp_path / "src" / "medium.ts",
        textwrap.dedent(
            """
            /**
             * This function is used by callers.
             */
            export function api(x: number): number { return x + 1; }
            """
        ).strip(),
    )
    payload = _checkpoint_payload(tmp_path, ts_enabled=True)
    rows = [row for row in payload["ci_failures"] if row.get("language") == "typescript"]
    assert len(rows) == 1
    assert rows[0]["category"] == "contract_gap"


def test_ts_enabled_unsupported_syntax_emits_non_blocking_advisory(tmp_path: Path, monkeypatch):
    status_report = SimpleNamespace(
        drift=[],
        modified=[],
        contract_changed=[],
        contract_gap=[],
        skipped_no_contract=[],
        unsupported_syntax_advisory=[
            SimpleNamespace(
                id="typescript:src/unsupported.ts:function:odd",
                file_path="src/unsupported.ts",
                details="TypeScript MVP parser could not safely classify this target.",
                language="typescript",
                symbol_kind="function",
                adapter="typescript",
                target_id="typescript:src/unsupported.ts:function:odd",
            )
        ],
        contract_parse_error=[],
        untracked=[],
        missing=[],
        counts={},
    )
    payload = checkpoint_ci_result_to_dict(
        build_checkpoint_ci_result(
            status_report=status_report,
            ddt_report=_empty_ddt_report(),
            contract_impact_report=_empty_contract_report(),
        )
    )
    rows = [row for row in payload["advisory"] if row.get("category") == "unsupported_syntax_advisory"]
    assert payload["exit_code"] == 0
    assert len(rows) == 1
    assert rows[0]["category"] == "unsupported_syntax_advisory"
    assert rows[0]["reason"] == "TypeScript MVP parser could not safely classify this target."


def test_ts_disabled_keeps_typescript_out_of_checkpoint(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write(tmp_path / "src" / "service.ts", "export function api(x: number): number { return x + 1; }\n")
    payload = _checkpoint_payload(tmp_path, ts_enabled=False)
    ts_rows = [row for row in payload["ci_failures"] + payload["advisory"] if row.get("language") == "typescript"]
    assert payload["exit_code"] == 0
    assert ts_rows == []


def test_typescript_default_excluded_extensions_do_not_enter_checkpoint(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write(tmp_path / "src" / "v.tsx", "export const v = 1;\n")
    _write(tmp_path / "src" / "a.js", "export const a = 1;\n")
    _write(tmp_path / "src" / "b.jsx", "export const b = 1;\n")
    _write(tmp_path / "src" / "types.d.ts", "export type X = string;\n")
    payload = _checkpoint_payload(tmp_path, ts_enabled=True)
    ts_rows = [row for row in payload["ci_failures"] + payload["advisory"] if row.get("language") == "typescript"]
    assert payload["exit_code"] == 0
    assert ts_rows == []


def test_typescript_checkpoint_categories_and_identity_fields_are_constrained(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write(tmp_path / "src" / "gap.ts", "export function api(x: number): number { return x + 1; }\n")
    _write(tmp_path / "src" / "skip.ts", "function helper(x: number): number { return x + 1; }\n")
    payload = _checkpoint_payload(tmp_path, ts_enabled=True)

    ts_rows = [row for row in payload["ci_failures"] + payload["advisory"] if row.get("language") == "typescript"]
    assert ts_rows
    assert {row["category"] for row in ts_rows}.issubset(
        {"contract_gap", "skipped_no_contract", "unsupported_syntax_advisory"}
    )
    for row in ts_rows:
        assert row.get("target_id", "").startswith("typescript:")
        assert row.get("language") == "typescript"
        assert row.get("symbol_kind") in {"function", "method"}
        assert row.get("adapter") == "typescript"
        assert row.get("func_id", "").startswith("typescript:")

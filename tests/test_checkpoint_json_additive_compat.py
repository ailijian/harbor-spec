import json
from pathlib import Path
from types import SimpleNamespace

from harbor.adapters.typescript.adapter import TypeScriptAdapter
from harbor.core.ci import (
    build_checkpoint_ci_result,
    checkpoint_ci_result_to_dict,
)
from harbor.core.contract_impact import ContractImpactLevel, ContractImpactReport


def _status_entry(func_id: str, file_path: str, details: str, **kwargs):
    base = {
        "id": func_id,
        "file_path": file_path,
        "details": details,
    }
    base.update(kwargs)
    return SimpleNamespace(**base)


def _status_report(
    *,
    drift=None,
    modified=None,
    contract_changed=None,
    contract_gap=None,
    skipped_no_contract=None,
    contract_parse_error=None,
    untracked=None,
    missing=None,
):
    drift = list(drift or [])
    modified = list(modified or [])
    contract_changed = list(contract_changed or [])
    contract_gap = list(contract_gap or [])
    skipped_no_contract = list(skipped_no_contract or [])
    contract_parse_error = list(contract_parse_error or [])
    untracked = list(untracked or [])
    missing = list(missing or [])
    return SimpleNamespace(
        drift=drift,
        modified=modified,
        contract_changed=contract_changed,
        contract_gap=contract_gap,
        skipped_no_contract=skipped_no_contract,
        contract_parse_error=contract_parse_error,
        untracked=untracked,
        missing=missing,
        counts={
            "drift": len(drift),
            "modified": len(modified),
            "contract_changed": len(contract_changed),
            "contract_gap": len(contract_gap),
            "skipped_no_contract": len(skipped_no_contract),
            "contract_parse_error": len(contract_parse_error),
            "untracked": len(untracked),
            "missing": len(missing),
        },
    )


def _ddt_report():
    return SimpleNamespace(
        valid=[],
        violations=[],
        advisory=[],
        counts={"valid": 0, "violations": 0, "advisory": 0},
    )


def _contract_report():
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


def test_python_checkpoint_json_keeps_legacy_fields_and_adds_identity_fields():
    status = _status_report(
        contract_changed=[
            _status_entry(
                "harbor.core.ci.checkpoint_ci_result_to_dict",
                "harbor/core/ci.py",
                "Contract updated",
            )
        ]
    )
    payload = checkpoint_ci_result_to_dict(
        build_checkpoint_ci_result(
            status_report=status,
            ddt_report=_ddt_report(),
            contract_impact_report=_contract_report(),
        )
    )

    row = payload["ci_failures"][0]
    assert row["category"] == "contract_changed"
    assert row["reason"]
    assert row["func_id"] == "harbor.core.ci.checkpoint_ci_result_to_dict"
    assert row["file_path"] == "harbor/core/ci.py"
    assert row["target_id"] == "python:harbor/core/ci.py:function:checkpoint_ci_result_to_dict"
    assert row["language"] == "python"
    assert row["symbol_kind"] == "function"
    assert row["adapter"] == "python"


def test_python_method_symbol_kind_and_func_id_stay_compatible():
    status = _status_report(
        contract_changed=[
            _status_entry(
                "harbor.core.ci.CheckpointCIItem.to_dict",
                "harbor/core/ci.py",
                "Contract updated",
            )
        ]
    )
    payload = checkpoint_ci_result_to_dict(
        build_checkpoint_ci_result(
            status_report=status,
            ddt_report=_ddt_report(),
            contract_impact_report=_contract_report(),
        )
    )
    row = payload["ci_failures"][0]
    assert row["func_id"] == "harbor.core.ci.CheckpointCIItem.to_dict"
    assert row["symbol_kind"] == "method"
    assert row["target_id"] == "python:harbor/core/ci.py:method:CheckpointCIItem.to_dict"


def test_python_checkpoint_pass_fail_semantics_unchanged():
    clean_payload = checkpoint_ci_result_to_dict(
        build_checkpoint_ci_result(
            status_report=_status_report(),
            ddt_report=_ddt_report(),
            contract_impact_report=_contract_report(),
        )
    )
    failing_payload = checkpoint_ci_result_to_dict(
        build_checkpoint_ci_result(
            status_report=_status_report(
                missing=[_status_entry("harbor.core.foo.gone", "harbor/core/foo.py", "removed")]
            ),
            ddt_report=_ddt_report(),
            contract_impact_report=_contract_report(),
        )
    )
    assert clean_payload["status"] == "pass"
    assert clean_payload["exit_code"] == 0
    assert failing_payload["status"] == "fail"
    assert failing_payload["exit_code"] == 1
    assert failing_payload["ci_failures"][0]["category"] == "missing_function"


def test_typescript_contract_subject_json_has_task6a_ready_fields():
    fixture = Path(__file__).resolve().parent / "fixtures" / "ts_project_basic" / "src" / "exports.ts"
    adapter = TypeScriptAdapter()
    subject = next(item for item in adapter.parse_file(fixture) if item.qualified_name == "foo")
    data = subject.to_dict()

    assert data["target_id"] == f"typescript:{fixture.as_posix()}:function:foo"
    assert data["legacy_func_id"] == data["target_id"]
    assert data["language"] == "typescript"
    assert data["symbol_kind"] == "function"
    assert data["file_path"] == fixture.as_posix()


def test_non_function_symbol_kind_does_not_enter_blocking_checkpoint_failures():
    status = _status_report(
        contract_gap=[
            _status_entry(
                "harbor.core.sample.Model",
                "harbor/core/sample.py",
                "No contract source found",
                symbol_kind="class",
                language="python",
                adapter="python",
            )
        ]
    )
    payload = checkpoint_ci_result_to_dict(
        build_checkpoint_ci_result(
            status_report=status,
            ddt_report=_ddt_report(),
            contract_impact_report=_contract_report(),
        )
    )
    assert payload["ci_failures"] == []
    assert payload["status"] == "pass"
    assert payload["exit_code"] == 0


def test_checkpoint_json_additive_shape_is_stable_for_golden_assert():
    status = _status_report(
        contract_changed=[
            _status_entry(
                "harbor.core.ci.CIFailure.to_dict",
                "harbor/core/ci.py",
                "Contract updated",
            )
        ]
    )
    payload = checkpoint_ci_result_to_dict(
        build_checkpoint_ci_result(
            status_report=status,
            ddt_report=_ddt_report(),
            contract_impact_report=_contract_report(),
        )
    )
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)
    parsed = json.loads(rendered)
    row = parsed["ci_failures"][0]

    assert set(row.keys()) >= {
        "category",
        "reason",
        "func_id",
        "file_path",
        "target_id",
        "language",
        "symbol_kind",
        "adapter",
    }


def test_typescript_checkpoint_json_adds_task6_metadata_without_changing_category():
    status = _status_report(
        skipped_no_contract=[
            _status_entry(
                "typescript:src/models.ts:interface:User",
                "src/models.ts",
                "No contract required for this target",
                target_id="typescript:src/models.ts:interface:User",
                language="typescript",
                symbol_kind="interface",
                adapter="typescript",
                data_contract_kind="interface",
                contract_source_kinds=["typescript_interface"],
                contract_source_fingerprints=["abc123"],
                source_confidence_summary="high",
            )
        ]
    )
    payload = checkpoint_ci_result_to_dict(
        build_checkpoint_ci_result(
            status_report=status,
            ddt_report=_ddt_report(),
            contract_impact_report=_contract_report(),
        )
    )

    row = payload["advisory"][0]
    assert row["category"] == "skipped_no_contract"
    assert row["language"] == "typescript"
    assert row["symbol_kind"] == "interface"
    assert row["data_contract_kind"] == "interface"
    assert row["contract_source_kinds"] == ["typescript_interface"]
    assert row["contract_source_fingerprints"] == ["abc123"]
    assert row["source_confidence_summary"] == "high"
    assert (
        row["reason"]
        == "TypeScript exported data contract target is tracked in advisory-first mode; blocking semantic comparison is skipped."
    )


def test_typescript_checkpoint_json_explains_low_confidence_doc_as_contract_gap():
    status = _status_report(
        contract_gap=[
            _status_entry(
                "typescript:src/api.ts:function:api",
                "src/api.ts",
                "Required TypeScript contract source is missing or not contract-like.",
                target_id="typescript:src/api.ts:function:api",
                language="typescript",
                symbol_kind="function",
                adapter="typescript",
                contract_source_kinds=["tsdoc"],
                contract_source_fingerprints=["docfp"],
                source_confidence_summary="medium",
            )
        ]
    )
    payload = checkpoint_ci_result_to_dict(
        build_checkpoint_ci_result(
            status_report=status,
            ddt_report=_ddt_report(),
            contract_impact_report=_contract_report(),
        )
    )

    row = payload["ci_failures"][0]
    assert row["category"] == "contract_gap"
    assert row["contract_source_kinds"] == ["tsdoc"]
    assert row["source_confidence_summary"] == "medium"
    assert (
        row["reason"]
        == "TypeScript doc comment was detected, but its confidence is not high enough to count as a contract source."
    )

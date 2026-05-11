import json
from pathlib import Path
from types import SimpleNamespace

from harbor.adapters.python.parser import FunctionContract
from harbor.adapters.typescript.adapter import TypeScriptAdapter
from harbor.core.audit import MockProvider, SemanticGuard
from harbor.core.ci import build_checkpoint_ci_result, checkpoint_ci_result_to_dict
from harbor.core.contract_impact import ContractImpactLevel, ContractImpactReport
from harbor.core.ddt import DDTBinding, DDTValidator


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


def _empty_ddt_report():
    return SimpleNamespace(valid=[], violations=[], advisory=[], counts={"valid": 0, "violations": 0, "advisory": 0})


def test_typescript_semantic_audit_is_skipped_without_contract_presence_or_ast(monkeypatch):
    def _should_not_call(*args, **kwargs):
        raise AssertionError("TypeScript semantic audit must short-circuit before Python-specific calls")

    monkeypatch.setattr("harbor.core.audit.evaluate_contract_presence", _should_not_call)
    monkeypatch.setattr("harbor.core.audit.find_function_node", _should_not_call)

    class _ShouldNotCallProvider(MockProvider):
        def infer(self, prompt: str) -> str:
            raise AssertionError("LLM must not be called for TypeScript semantic audit")

    contract = FunctionContract(
        id="typescript:src/api.ts:function:api",
        name="api",
        qualified_name="api",
        signature_hash="sig",
        docstring=None,
        docstring_raw_hash=None,
        contract_hash=None,
        lineno=1,
        col_offset=0,
    )
    res = SemanticGuard().audit(contract, "export function api(){ return 1; }", _ShouldNotCallProvider(), file_path="src/api.ts")
    assert res.status in {"SKIPPED_NO_CONTRACT", "NOT_SUPPORTED"}
    assert "TypeScript semantic audit is not supported in v1.4.0" in (res.reason or "")
    assert res.prompt is None
    assert res.raw_output is None


def test_typescript_ddt_binding_is_advisory_not_supported(tmp_path: Path):
    validator = DDTValidator(
        index_path=tmp_path / ".harbor" / "cache" / "l3_index.json",
        map_path=tmp_path / ".harbor" / "cache" / "l3_hash_map.json",
    )
    rep = validator.validate(
        [
            DDTBinding(
                func_id="typescript:src/service.ts:function:api",
                l3_version=1,
                strategy="strict",
                file_path="tests/test_ts.py",
                test_name="test_api",
            )
        ]
    )
    assert rep.counts["violations"] == 0
    assert rep.counts["valid"] == 0
    assert rep.counts["advisory"] == 1
    assert rep.advisory[0].category == "ddt_not_supported"
    assert "TypeScript DDT is not supported in v1.4.0" in rep.advisory[0].message


def test_typescript_adapter_discover_only_ts_and_excludes_js_family(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir(parents=True, exist_ok=True)
    (src / "a.ts").write_text("export function a(){ return 1; }\n", encoding="utf-8")
    (src / "b.tsx").write_text("export const b = () => 1;\n", encoding="utf-8")
    (src / "c.js").write_text("export const c = 1;\n", encoding="utf-8")
    (src / "d.jsx").write_text("export const d = 1;\n", encoding="utf-8")
    (src / "types.d.ts").write_text("export type X = string;\n", encoding="utf-8")

    files = TypeScriptAdapter().discover_files([src])
    rels = {path.resolve().relative_to(src.resolve()).as_posix() for path in files}
    assert rels == {"a.ts"}


def test_non_function_typescript_targets_do_not_enter_blocking_checkpoint():
    status_report = SimpleNamespace(
        drift=[],
        modified=[],
        contract_changed=[],
        contract_gap=[
            SimpleNamespace(
                id="typescript:src/models.ts:interface:User",
                file_path="src/models.ts",
                details="Required TypeScript contract source is missing or not contract-like.",
                language="typescript",
                symbol_kind="interface",
                adapter="typescript",
                target_id="typescript:src/models.ts:interface:User",
            )
        ],
        skipped_no_contract=[],
        unsupported_syntax_advisory=[],
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
    ts_failures = [row for row in payload["ci_failures"] if row.get("language") == "typescript"]
    assert ts_failures == []
    assert payload["exit_code"] == 0


def test_typescript_unsupported_syntax_advisory_remains_non_blocking():
    status_report = SimpleNamespace(
        drift=[],
        modified=[],
        contract_changed=[],
        contract_gap=[],
        skipped_no_contract=[],
        unsupported_syntax_advisory=[
            SimpleNamespace(
                id="typescript:src/unsupported.ts:function:weird",
                file_path="src/unsupported.ts",
                details="TypeScript MVP parser could not safely classify this target.",
                language="typescript",
                symbol_kind="function",
                adapter="typescript",
                target_id="typescript:src/unsupported.ts:function:weird",
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
    assert payload["exit_code"] == 0
    assert [row["category"] for row in payload["advisory"]] == ["unsupported_syntax_advisory"]


def test_python_audit_provider_behavior_unchanged():
    class _CountProvider(MockProvider):
        def __init__(self) -> None:
            self.calls = 0

        def infer(self, prompt: str) -> str:
            self.calls += 1
            return json.dumps({"status": "OK"})

    contract = FunctionContract(
        id="pkg.mod.f",
        name="f",
        qualified_name="pkg.mod.f",
        signature_hash="sig",
        docstring="Args:\n  x (int): value\nReturns:\n  int: value",
        docstring_raw_hash="raw",
        contract_hash="hash",
        lineno=1,
        col_offset=0,
    )
    provider = _CountProvider()
    res = SemanticGuard().audit(
        contract,
        'def f(x: int) -> int:\n    """Args:\\n  x (int): value\\nReturns:\\n  int: value"""\n    return x\n',
        provider,
        file_path="pkg/mod.py",
    )
    assert res.status == "OK"
    assert provider.calls == 1


def test_python_ddt_strict_and_latest_rules_unchanged(tmp_path: Path):
    cache = tmp_path / ".harbor" / "cache"
    cache.mkdir(parents=True, exist_ok=True)
    (cache / "l3_index.json").write_text(
        json.dumps(
            {
                "meta": {"schema_version": "1.0.2"},
                "files": {
                    "src/mod.py": {
                        "mtime": 0.0,
                        "file_hash": "",
                        "items": [
                            {
                                "id": "src.mod.target",
                                "strictness": "strict",
                                "contract_hash": "h1",
                            }
                        ],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    (cache / "l3_hash_map.json").write_text(
        json.dumps(
            {
                "src.mod.target": {
                    "l3_version": 1,
                    "contract_hash": "h1",
                }
            }
        ),
        encoding="utf-8",
    )
    validator = DDTValidator(index_path=cache / "l3_index.json", map_path=cache / "l3_hash_map.json")
    rep = validator.validate(
        [
            DDTBinding(
                func_id="src.mod.target",
                l3_version=1,
                strategy="strict",
                file_path="tests/test_mod.py",
                test_name="test_target_strict",
            ),
            DDTBinding(
                func_id="src.mod.target",
                l3_version=None,
                strategy="latest",
                file_path="tests/test_mod.py",
                test_name="test_target_latest",
            ),
        ]
    )
    assert rep.counts["valid"] == 1
    assert rep.counts["violations"] == 1
    assert rep.violations[0][0] == "strict_forbid_latest"

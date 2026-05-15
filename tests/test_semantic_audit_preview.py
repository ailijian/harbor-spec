import json
import textwrap
from pathlib import Path
from types import SimpleNamespace

from harbor.core.audit import (
    AuditEligibility,
    AuditEvidence,
    AuditPromptContext,
    AuditSubject,
    MockProvider,
    SemanticGuard,
    build_typescript_semantic_audit_preview,
)
from harbor.core.ci import (
    build_checkpoint_ci_result,
    checkpoint_ci_result_to_dict,
    checkpoint_ci_summary_to_dict,
)
from harbor.core.contract_impact import ContractImpactLevel, ContractImpactReport


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _config(*, enabled: bool = True) -> dict:
    return {
        "code_roots": ["src"],
        "languages": {
            "python": {"enabled": True},
            "typescript": {"enabled": True},
        },
        "verification": {
            "semantic_audit": {
                "typescript_preview": {
                    "enabled": enabled,
                }
            }
        },
    }


def _status_entry(
    target_id: str,
    file_path: str,
    *,
    name: str,
    symbol_kind: str,
    contract_source_kinds=None,
    source_confidence_summary=None,
    public_boundary_state=None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=target_id,
        target_id=target_id,
        name=name,
        file_path=file_path,
        language="typescript",
        symbol_kind=symbol_kind,
        adapter="typescript",
        contract_source_kinds=list(contract_source_kinds or []),
        source_confidence_summary=source_confidence_summary,
        public_boundary_state=public_boundary_state,
        public_boundary_confidence=None,
        public_boundary_evidence_kinds=[],
        public_boundary_reason=None,
        boundary_preset_mode=None,
    )


def _empty_status_report(**overrides):
    base = {
        "drift": [],
        "modified": [],
        "contract_changed": [],
        "contract_gap": [],
        "skipped_no_contract": [],
        "unsupported_syntax_advisory": [],
        "contract_parse_error": [],
        "untracked": [],
        "missing": [],
        "counts": {},
    }
    base.update(overrides)
    return SimpleNamespace(**base)


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


def test_audit_foundation_models_serialize_stably():
    evidence = AuditEvidence(kind="tsdoc", text="Returns stable result", confidence="high")
    subject = AuditSubject(
        language="typescript",
        subject_id="typescript:src/api.ts:function:api",
        target_id="typescript:src/api.ts:function:api",
        func_id="typescript:src/api.ts:function:api",
        qualified_name="api",
        symbol_kind="function",
        source_path="src/api.ts",
        source_excerpt="export function api(): number { return 1; }",
        contract_evidence=(evidence,),
        public_boundary_context={"public_boundary_state": "direct_export_only"},
        preview_only=True,
        notes=("preview only",),
        metadata={"contract_presence": "present"},
    )
    prompt_context = AuditPromptContext(
        language="typescript",
        subject_id=subject.subject_id,
        target_id=subject.target_id,
        qualified_name=subject.qualified_name,
        symbol_kind=subject.symbol_kind,
        source_path=subject.source_path,
        source_excerpt=subject.source_excerpt,
        contract_text=evidence.text,
        contract_evidence_kinds=("tsdoc",),
        public_boundary_context=subject.public_boundary_context,
        preview_only=True,
        notes=("prompt",),
    )
    eligibility = AuditEligibility(
        eligible=True,
        reason="eligible_behavior_contract_present",
        notes=("high confidence tsdoc",),
        evidence_kinds=("tsdoc",),
        preview_only=True,
    )

    assert subject.to_dict()["contract_evidence"][0]["kind"] == "tsdoc"
    assert prompt_context.to_dict()["preview_only"] is True
    assert eligibility.to_dict()["reason"] == "eligible_behavior_contract_present"


def test_python_semantic_audit_zero_regression():
    class _Provider(MockProvider):
        def __init__(self) -> None:
            self.calls = 0

        def infer(self, prompt: str) -> str:
            self.calls += 1
            return json.dumps({"status": "OK"})

    provider = _Provider()
    contract = SimpleNamespace(
        id="pkg.mod.fn",
        name="fn",
        qualified_name="pkg.mod.fn",
        signature_hash="sig",
        docstring="Args:\n  x (int): input\nReturns:\n  int: output",
        docstring_raw_hash="raw",
        contract_hash="hash",
        lineno=1,
        col_offset=0,
        scope=None,
        strictness=None,
        is_method=False,
    )
    result = SemanticGuard().audit(
        contract,
        'def fn(x: int) -> int:\n    """Args:\\n  x (int): input\\nReturns:\\n  int: output"""\n    return x\n',
        provider,
        file_path="pkg/mod.py",
    )
    assert result.status == "OK"
    assert provider.calls == 1
    assert result.preview is False


def test_typescript_eligible_target_enters_preview(tmp_path: Path):
    _write(
        tmp_path / "src" / "api.ts",
        textwrap.dedent(
            """
            /**
             * Returns the incremented value.
             *
             * @param x Input value.
             * @returns Incremented value.
             */
            export function api(x: number): number {
              return x + 1;
            }
            """
        ).strip(),
    )
    status_report = _empty_status_report(
        drift=[
            _status_entry(
                "typescript:src/api.ts:function:api",
                "src/api.ts",
                name="api",
                symbol_kind="function",
                contract_source_kinds=["tsdoc"],
                source_confidence_summary="high",
                public_boundary_state="direct_export_only",
            )
        ]
    )

    class _Provider(MockProvider):
        def infer(self, prompt: str) -> str:
            return json.dumps({"status": "OK"})

    report = build_typescript_semantic_audit_preview(
        tmp_path,
        status_report,
        config=_config(),
        provider=_Provider(),
    )

    assert report is not None
    assert report.targets_count == 1
    assert report.eligible_count == 1
    assert report.previewed_count == 1
    assert [finding.status for finding in report.findings] == ["preview_ok"]
    assert report.findings[0].preview is True
    assert report.findings[0].eligible is True
    assert report.findings[0].eligibility_reason == "eligible_behavior_contract_present"
    assert report.findings[0].evidence_kinds == ("tsdoc",)


def test_typescript_without_behavior_contract_does_not_enter_preview(tmp_path: Path):
    _write(
        tmp_path / "src" / "api.ts",
        "export function api(x: number): number { return x + 1; }\n",
    )
    status_report = _empty_status_report(
        contract_gap=[
            _status_entry(
                "typescript:src/api.ts:function:api",
                "src/api.ts",
                name="api",
                symbol_kind="function",
            )
        ]
    )

    class _Provider(MockProvider):
        def infer(self, prompt: str) -> str:
            raise AssertionError("provider must not be called for ineligible preview targets")

    report = build_typescript_semantic_audit_preview(
        tmp_path,
        status_report,
        config=_config(),
        provider=_Provider(),
    )

    assert report is not None
    assert report.eligible_count == 0
    assert report.previewed_count == 0
    assert report.ineligible_count == 1
    assert [finding.status for finding in report.findings] == ["preview_ineligible"]
    assert report.findings[0].eligibility_reason == "behavior_contract_missing"


def test_interface_type_zod_are_auxiliary_only_and_do_not_trigger_preview(tmp_path: Path):
    _write(
        tmp_path / "src" / "schema.ts",
        textwrap.dedent(
            """
            import { z } from "zod";

            export const UserSchema = z.object({
              id: z.string(),
            });
            """
        ).strip(),
    )
    status_report = _empty_status_report(
        skipped_no_contract=[
            _status_entry(
                "typescript:src/schema.ts:const:UserSchema",
                "src/schema.ts",
                name="UserSchema",
                symbol_kind="const",
                contract_source_kinds=["zod_schema"],
                source_confidence_summary="high",
                public_boundary_state="direct_export_only",
            )
        ]
    )

    class _Provider(MockProvider):
        def infer(self, prompt: str) -> str:
            raise AssertionError("provider must not be called for auxiliary-only preview targets")

    report = build_typescript_semantic_audit_preview(
        tmp_path,
        status_report,
        config=_config(),
        provider=_Provider(),
    )

    assert report is not None
    assert report.eligible_count == 0
    assert report.previewed_count == 0
    assert report.findings[0].status == "preview_ineligible"
    assert report.findings[0].eligibility_reason == "auxiliary_evidence_only"
    assert report.findings[0].evidence_kinds == ("zod_schema",)


def test_semantic_audit_preview_disabled_has_no_side_effect(monkeypatch, tmp_path: Path):
    def _should_not_call(*args, **kwargs):
        raise AssertionError("typescript parsing must not run when preview is disabled")

    monkeypatch.setattr("harbor.core.audit.TypeScriptAdapter.parse_file", _should_not_call)
    status_report = _empty_status_report(
        drift=[
            _status_entry(
                "typescript:src/api.ts:function:api",
                "src/api.ts",
                name="api",
                symbol_kind="function",
            )
        ]
    )
    assert build_typescript_semantic_audit_preview(tmp_path, status_report, config=_config(enabled=False)) is None


def test_checkpoint_json_adds_semantic_audit_preview_without_changing_exit_code(tmp_path: Path):
    _write(
        tmp_path / "src" / "api.ts",
        "/** @param x Input value. @returns Incremented value. */\nexport function api(x: number): number { return x + 1; }\n",
    )
    preview_status = _empty_status_report(
        drift=[
            _status_entry(
                "typescript:src/api.ts:function:api",
                "src/api.ts",
                name="api",
                symbol_kind="function",
                contract_source_kinds=["tsdoc"],
                source_confidence_summary="high",
                public_boundary_state="direct_export_only",
            )
        ]
    )

    class _Provider(MockProvider):
        def infer(self, prompt: str) -> str:
            return json.dumps({"status": "OK"})

    preview_report = build_typescript_semantic_audit_preview(
        tmp_path,
        preview_status,
        config=_config(),
        provider=_Provider(),
    )
    payload = checkpoint_ci_result_to_dict(
        build_checkpoint_ci_result(
            status_report=_empty_status_report(),
            ddt_report=_empty_ddt_report(),
            contract_impact_report=_empty_contract_report(),
            semantic_audit_preview=preview_report,
        )
    )
    summary_payload = checkpoint_ci_summary_to_dict(
        build_checkpoint_ci_result(
            status_report=_empty_status_report(),
            ddt_report=_empty_ddt_report(),
            contract_impact_report=_empty_contract_report(),
            semantic_audit_preview=preview_report,
        )
    )

    assert payload["exit_code"] == 0
    assert payload["ci_failures"] == []
    assert "semantic_audit_preview" in payload
    assert payload["semantic_audit_preview"]["previewed_count"] == 1
    assert summary_payload["semantic_audit_preview"]["eligible_count"] == 1


def test_checkpoint_json_omits_semantic_audit_preview_when_disabled():
    payload = checkpoint_ci_result_to_dict(
        build_checkpoint_ci_result(
            status_report=_empty_status_report(),
            ddt_report=_empty_ddt_report(),
            contract_impact_report=_empty_contract_report(),
            semantic_audit_preview=None,
        )
    )
    assert "semantic_audit_preview" not in payload

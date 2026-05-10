import json
import re
import sys
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace

import pytest

import harbor.cli.main as cli_main
from harbor.cli.main import main
from harbor.core.contract_impact import (
    ContractImpactCategory,
    ContractImpactFinding,
    ContractImpactLevel,
    ContractImpactReport,
)


@pytest.fixture(autouse=True)
def _force_en_locale(monkeypatch):
    monkeypatch.setenv("HARBOR_LANGUAGE", "en")


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


def _status_entry(func_id: str, file_path: str, details: str):
    return SimpleNamespace(id=func_id, file_path=file_path, details=details)


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


def _ddt_report(*, violations=None, advisory=None):
    violations = list(violations or [])
    advisory = list(advisory or [])
    return SimpleNamespace(
        valid=[],
        violations=violations,
        advisory=advisory,
        counts={"valid": 0, "violations": len(violations), "advisory": len(advisory)},
    )


def _contract_report(*, findings=None):
    findings = list(findings or [])
    counts = {
        ContractImpactLevel.NO_CONTRACT_IMPACT.value: 0,
        ContractImpactLevel.POSSIBLE_CONTRACT_IMPACT.value: 0,
        ContractImpactLevel.CONFIRMED_CONTRACT_IMPACT.value: 0,
        ContractImpactLevel.UNKNOWN.value: 0,
    }
    for item in findings:
        counts[item.level.value] += 1
    level = ContractImpactLevel.NO_CONTRACT_IMPACT
    if counts[ContractImpactLevel.CONFIRMED_CONTRACT_IMPACT.value]:
        level = ContractImpactLevel.CONFIRMED_CONTRACT_IMPACT
    elif counts[ContractImpactLevel.POSSIBLE_CONTRACT_IMPACT.value]:
        level = ContractImpactLevel.POSSIBLE_CONTRACT_IMPACT
    elif counts[ContractImpactLevel.UNKNOWN.value]:
        level = ContractImpactLevel.UNKNOWN
    return ContractImpactReport(
        level=level,
        categories=[],
        findings=findings,
        summary_counts=counts,
        notable_findings=findings[:5],
    )


def _patch_checkpoint_inputs(monkeypatch, *, status=None, ddt=None, contract_report=None):
    class _FakeSyncEngine:
        def check_status(self):
            return status or _status_report()

    class _FakeDDTScanner:
        def scan_tests(self):
            return []

    class _FakeDDTValidator:
        def validate(self, bindings):
            return ddt or _ddt_report()

    monkeypatch.setattr(cli_main, "SyncEngine", _FakeSyncEngine)
    monkeypatch.setattr(cli_main, "DDTScanner", _FakeDDTScanner)
    monkeypatch.setattr(cli_main, "DDTValidator", _FakeDDTValidator)
    monkeypatch.setattr(cli_main, "build_contract_impact_report", lambda records: (contract_report or _contract_report()))


def test_checkpoint_ci_pass_when_clean(monkeypatch):
    _patch_checkpoint_inputs(monkeypatch)
    code, out, _ = run_cmd(["checkpoint", "--ci"])
    assert code == 0
    assert "Harbor Checkpoint CI" in out
    assert "CI gate: PASS" in out


def test_checkpoint_ci_fail_on_missing_function(monkeypatch):
    status = _status_report(missing=[_status_entry("harbor.core.foo.missing", "harbor/core/foo.py", "Function removed")])
    _patch_checkpoint_inputs(monkeypatch, status=status)
    code, out, _ = run_cmd(["checkpoint", "--ci"])
    assert code == 1
    assert "missing_function" in out


def test_checkpoint_ci_fail_on_untracked_function(monkeypatch):
    status = _status_report(untracked=[_status_entry("harbor.core.foo.new_func", "harbor/core/foo.py", "New function")])
    _patch_checkpoint_inputs(monkeypatch, status=status)
    code, out, _ = run_cmd(["checkpoint", "--ci"])
    assert code == 1
    assert "untracked_function" in out


def test_checkpoint_ci_fail_on_body_changed_contract_static(monkeypatch):
    status = _status_report(drift=[_status_entry("harbor.core.bar.run", "harbor/core/bar.py", "Body changed, Contract static")])
    _patch_checkpoint_inputs(monkeypatch, status=status)
    code, out, _ = run_cmd(["checkpoint", "--ci"])
    assert code == 1
    assert "possible_semantic_drift" in out


def test_checkpoint_ci_fail_on_contract_gap(monkeypatch):
    status = _status_report(contract_gap=[_status_entry("harbor.core.bar.write_report", "harbor/core/bar.py", "No contract source found")])
    _patch_checkpoint_inputs(monkeypatch, status=status)
    code, out, _ = run_cmd(["checkpoint", "--ci"])
    assert code == 1
    assert "contract_gap" in out


def test_checkpoint_ci_contract_parse_error_blocks(monkeypatch):
    status = _status_report(contract_parse_error=[_status_entry("harbor.core.bar.run", "harbor/core/bar.py", "Contract source malformed")])
    _patch_checkpoint_inputs(monkeypatch, status=status)
    code, out, _ = run_cmd(["checkpoint", "--ci"])
    assert code == 1
    assert "contract_parse_error" in out


def test_checkpoint_ci_skipped_no_contract_is_advisory(monkeypatch):
    status = _status_report(skipped_no_contract=[_status_entry("harbor.core.bar._helper", "harbor/core/bar.py", "No contract required")])
    _patch_checkpoint_inputs(monkeypatch, status=status)
    code, out, _ = run_cmd(["checkpoint", "--ci"])
    assert code == 0
    assert "skipped_no_contract" in out


def test_checkpoint_ci_json_includes_ddt_baseline_missing_advisory_without_blocking(monkeypatch):
    binding = SimpleNamespace(
        func_id="harbor.core.sync.SyncEngine.check_status",
        file_path="harbor/core/sync.py",
        l3_version=1,
        strategy="strict",
        test_name="test_sync_engine_drift_detection",
    )
    ddt_advisory = SimpleNamespace(
        category="ddt_version_baseline_missing",
        binding=binding,
        message=(
            "Strict DDT binding is structurally valid, but no L3 contract baseline was found. "
            "Version bump cannot be verified."
        ),
        suggested_action="Run harbor checkpoint after baseline initialization and review l3_version before harbor accept.",
    )
    _patch_checkpoint_inputs(monkeypatch, ddt=_ddt_report(advisory=[ddt_advisory]))
    code, out, _ = run_cmd(["checkpoint", "--ci", "--format", "json"])
    payload = json.loads(out)
    assert code == 0
    assert payload["exit_code"] == 0
    assert payload["writes_files"] is False
    assert payload["ci_failures"] == []
    assert any(item.get("category") == "ddt_version_baseline_missing" for item in payload["advisory"])


def test_checkpoint_ci_fail_on_contract_changed(monkeypatch):
    status = _status_report(contract_changed=[_status_entry("harbor.core.bar.run", "harbor/core/bar.py", "Contract updated")])
    _patch_checkpoint_inputs(monkeypatch, status=status)
    code, out, _ = run_cmd(["checkpoint", "--ci"])
    assert code == 1
    assert "contract_changed" in out


def test_checkpoint_ci_fail_on_confirmed_contract_impact(monkeypatch):
    finding = ContractImpactFinding(
        level=ContractImpactLevel.CONFIRMED_CONTRACT_IMPACT,
        categories=[ContractImpactCategory.CLI_JSON_OUTPUT],
        func_id="harbor.core.stale.stale_report_to_dict",
        file_path="harbor/core/stale.py",
        reason="confirmed contract surface change",
        evidence="change_type=Contract Changed",
        suggested_action="review contract impact",
        confidence="high",
        source="status_record",
    )
    _patch_checkpoint_inputs(monkeypatch, contract_report=_contract_report(findings=[finding]))
    code, out, _ = run_cmd(["checkpoint", "--ci"])
    assert code == 1
    assert "confirmed_contract_impact" in out


def test_checkpoint_ci_does_not_fail_on_possible_contract_impact_alone(monkeypatch):
    finding = ContractImpactFinding(
        level=ContractImpactLevel.POSSIBLE_CONTRACT_IMPACT,
        categories=[ContractImpactCategory.CLI_JSON_OUTPUT],
        func_id="harbor.core.stale.stale_report_to_dict",
        file_path="harbor/core/stale.py",
        reason="possible contract surface change",
        evidence="change_type=Modified",
        suggested_action="review",
        confidence="medium",
        source="status_record",
    )
    _patch_checkpoint_inputs(monkeypatch, contract_report=_contract_report(findings=[finding]))
    code, out, _ = run_cmd(["checkpoint", "--ci"])
    assert code == 0
    assert "Advisory:" in out
    assert "possible_contract_impact" in out


def test_checkpoint_ci_json_single_object_and_required_fields(monkeypatch):
    status = _status_report(
        contract_changed=[_status_entry("harbor.core.stale.stale_report_to_dict", "C:/tmp/harbor/core/stale.py", "Contract updated")]
    )
    _patch_checkpoint_inputs(monkeypatch, status=status)
    code, out, _ = run_cmd(["checkpoint", "--ci", "--format", "json"])
    payload = json.loads(out)
    assert code == 1
    assert out.strip() == json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)
    assert payload["command"] == "checkpoint"
    assert payload["ci"] is True
    assert payload["writes_files"] is False
    assert payload["exit_code"] == 1
    assert "ci_failures" in payload
    assert "advisory" in payload
    assert re.search(r"(?i)[a-z]:[\\/]", out) is None


def test_checkpoint_ci_failure_dedupe_keeps_readable_ci_failures(monkeypatch):
    status = _status_report(contract_changed=[_status_entry("harbor.core.stale.stale_report_to_dict", "harbor/core/stale.py", "Contract updated")])
    finding = ContractImpactFinding(
        level=ContractImpactLevel.CONFIRMED_CONTRACT_IMPACT,
        categories=[ContractImpactCategory.CLI_JSON_OUTPUT],
        func_id="harbor.core.stale.stale_report_to_dict",
        file_path="harbor/core/stale.py",
        reason="confirmed contract surface change",
        evidence="change_type=Contract Changed",
        suggested_action="review",
        confidence="high",
        source="status_record",
    )
    _patch_checkpoint_inputs(monkeypatch, status=status, contract_report=_contract_report(findings=[finding]))
    code, out, _ = run_cmd(["checkpoint", "--ci", "--format", "json"])
    payload = json.loads(out)
    assert code == 1
    assert payload["summary"]["confirmed_contract_impact"] == 1
    assert len(payload["ci_failures"]) == 1
    assert payload["ci_failures"][0]["category"] == "contract_changed"


def test_checkpoint_ci_dedupe_prefers_contract_changed_over_confirmed_contract_impact(monkeypatch):
    target_id = "harbor.core.ci.CIFailure.to_dict"
    status = _status_report(contract_changed=[_status_entry(target_id, "E:/project/harbor-spec/harbor/core/ci.py", "Contract updated")])
    finding = ContractImpactFinding(
        level=ContractImpactLevel.CONFIRMED_CONTRACT_IMPACT,
        categories=[ContractImpactCategory.CLI_JSON_OUTPUT],
        func_id=target_id,
        file_path="harbor/core/ci.py",
        reason="confirmed contract impact",
        evidence="change_type=Contract Changed",
        suggested_action="review",
        confidence="high",
        source="status_record",
    )
    _patch_checkpoint_inputs(monkeypatch, status=status, contract_report=_contract_report(findings=[finding]))
    code, out, _ = run_cmd(["checkpoint", "--ci", "--format", "json"])
    payload = json.loads(out)
    assert code == 1
    target_rows = [row for row in payload["ci_failures"] if row.get("func_id") == target_id]
    assert len(target_rows) == 1
    assert target_rows[0]["category"] == "contract_changed"


def test_checkpoint_ci_dedupe_prefers_contract_and_body_changed_over_confirmed_contract_impact(monkeypatch):
    target_id = "harbor.cli.main.main"
    status = _status_report(modified=[_status_entry(target_id, "E:/project/harbor-spec/harbor/cli/main.py", "Body and contract changed")])
    finding = ContractImpactFinding(
        level=ContractImpactLevel.CONFIRMED_CONTRACT_IMPACT,
        categories=[ContractImpactCategory.CLI_JSON_OUTPUT],
        func_id=target_id,
        file_path="harbor/cli/main.py",
        reason="confirmed contract impact",
        evidence="change_type=Modified",
        suggested_action="review",
        confidence="high",
        source="status_record",
    )
    _patch_checkpoint_inputs(monkeypatch, status=status, contract_report=_contract_report(findings=[finding]))
    code, out, _ = run_cmd(["checkpoint", "--ci", "--format", "json"])
    payload = json.loads(out)
    assert code == 1
    target_rows = [row for row in payload["ci_failures"] if row.get("func_id") == target_id]
    assert len(target_rows) == 1
    assert target_rows[0]["category"] == "contract_and_body_changed"


def test_checkpoint_ci_keeps_confirmed_contract_impact_when_no_status_failure_covers_target(monkeypatch):
    target_id = "harbor.core.contract_impact.classify_contract_impact_for_file_path"
    finding = ContractImpactFinding(
        level=ContractImpactLevel.CONFIRMED_CONTRACT_IMPACT,
        categories=[ContractImpactCategory.CLI_JSON_OUTPUT],
        func_id=target_id,
        file_path="harbor/core/contract_impact.py",
        reason="confirmed contract impact",
        evidence="change_type=Contract Changed",
        suggested_action="review",
        confidence="high",
        source="status_record",
    )
    _patch_checkpoint_inputs(monkeypatch, contract_report=_contract_report(findings=[finding]))
    code, out, _ = run_cmd(["checkpoint", "--ci", "--format", "json"])
    payload = json.loads(out)
    assert code == 1
    target_rows = [row for row in payload["ci_failures"] if row.get("func_id") == target_id]
    assert len(target_rows) == 1
    assert target_rows[0]["category"] == "confirmed_contract_impact"


def test_checkpoint_ci_ddt_baseline_missing_stays_advisory_not_failure(monkeypatch):
    target_id = "harbor.core.sync.SyncEngine.check_status"
    binding = SimpleNamespace(
        func_id=target_id,
        file_path="harbor/core/sync.py",
        l3_version=1,
        strategy="strict",
        test_name="test_sync_engine_drift_detection",
    )
    ddt_advisory = SimpleNamespace(
        category="ddt_version_baseline_missing",
        binding=binding,
        message="baseline missing advisory",
        suggested_action="review baseline",
    )
    _patch_checkpoint_inputs(monkeypatch, ddt=_ddt_report(advisory=[ddt_advisory]))
    code, out, _ = run_cmd(["checkpoint", "--ci", "--format", "json"])
    payload = json.loads(out)
    assert code == 0
    assert all(item.get("category") != "ddt_version_baseline_missing" for item in payload["ci_failures"])
    assert any(item.get("category") == "ddt_version_baseline_missing" for item in payload["advisory"])


def test_checkpoint_ci_no_write_regression(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    targets = [
        tmp_path / ".harbor" / "views" / "l2" / "harbor" / "core" / "README.md",
        tmp_path / ".harbor" / "diary" / "2026-05.jsonl",
        tmp_path / ".harbor" / "config" / "harbor.yaml",
        tmp_path / "docs" / "harbor" / "project-structure.md",
        tmp_path / "specs" / "diary" / "2026-05.jsonl",
        tmp_path / "harbor" / "core" / "README.md",
    ]
    for path in targets:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"seed::{path.name}", encoding="utf-8")
    before = {p.as_posix(): (p.read_text(encoding="utf-8"), p.stat().st_mtime_ns) for p in targets}
    _patch_checkpoint_inputs(monkeypatch)
    code, _, _ = run_cmd(["checkpoint", "--ci"])
    after = {p.as_posix(): (p.read_text(encoding="utf-8"), p.stat().st_mtime_ns) for p in targets}
    assert code == 0
    assert before.keys() == after.keys()
    for key in before:
        assert before[key][0] == after[key][0]
        assert before[key][1] == after[key][1]


def test_checkpoint_default_behavior_unchanged(monkeypatch):
    _patch_checkpoint_inputs(monkeypatch)
    code, out, _ = run_cmd(["checkpoint"])
    assert code == 0
    assert "Harbor Checkpoint:" in out
    assert "Harbor Check Report:" in out
    assert "Harbor Checkpoint CI" not in out


def test_checkpoint_format_json_requires_ci_mode():
    code, _, err = run_cmd(["checkpoint", "--format", "json"])
    assert code == 2
    assert "applies to CI mode only" in err


def test_checkpoint_ci_zh_text_labels(monkeypatch):
    _patch_checkpoint_inputs(monkeypatch)
    monkeypatch.setenv("HARBOR_LANGUAGE", "zh")
    code, out, _ = run_cmd(["checkpoint", "--ci"])
    assert code == 0
    assert "CI 模式已启用" in out
    assert "CI 门禁：" in out
    assert "下一步：" in out or "建议下一步：" in out

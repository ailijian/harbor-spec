import json
import sys
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from types import SimpleNamespace

import harbor.cli.main as cli_main
from harbor.cli.main import main
from harbor.core.contract_impact import ContractImpactLevel, ContractImpactReport


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


def _status_entry(func_id: str, file_path: str):
    return SimpleNamespace(id=func_id, file_path=file_path, details="d")


def _status_report(**kwargs):
    defaults = {
        "drift": [],
        "modified": [],
        "contract_changed": [],
        "contract_gap": [],
        "skipped_no_contract": [],
        "contract_parse_error": [],
        "untracked": [],
        "missing": [],
    }
    defaults.update(kwargs)
    for key in list(defaults.keys()):
        defaults[key] = list(defaults[key] or [])
    defaults["counts"] = {k: len(v) for k, v in defaults.items() if isinstance(v, list)}
    return SimpleNamespace(**defaults)


def _ddt_report(*, advisory=None):
    return SimpleNamespace(valid=[], violations=[], advisory=list(advisory or []), counts={"valid": 0, "violations": 0, "advisory": len(list(advisory or []))})


def _patch_inputs(monkeypatch, *, status=None, ddt=None):
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
    monkeypatch.setattr(
        cli_main,
        "build_contract_impact_report",
        lambda records: ContractImpactReport(
            level=ContractImpactLevel.NO_CONTRACT_IMPACT,
            categories=[],
            findings=[],
            summary_counts={
                "no_contract_impact": 0,
                "possible_contract_impact": 0,
                "confirmed_contract_impact": 0,
                "unknown": 0,
            },
            notable_findings=[],
        ),
    )


def test_contract_gap_guidance_in_checkpoint_json(monkeypatch):
    status = _status_report(contract_gap=[_status_entry("harbor.core.a.f", "harbor/core/a.py")])
    _patch_inputs(monkeypatch, status=status)
    code, out, _ = run_cmd(["checkpoint", "--ci", "--format", "json"])
    payload = json.loads(out)
    assert code == 1
    row = payload["ci_failures"][0]
    assert row["category"] == "contract_gap"
    assert row["guidance"]["suggested_skill"] == "harbor-contract-change"
    assert row["guidance"]["safe_to_auto_fix"] is False


def test_possible_semantic_drift_guidance_is_conservative(monkeypatch):
    status = _status_report(drift=[_status_entry("harbor.core.a.f", "harbor/core/a.py")])
    _patch_inputs(monkeypatch, status=status)
    code, out, _ = run_cmd(["checkpoint", "--ci", "--format", "json"])
    payload = json.loads(out)
    assert code == 1
    row = payload["ci_failures"][0]
    assert row["category"] == "possible_semantic_drift"
    assert row["guidance"]["decision_required"] is True
    assert row["guidance"]["safe_to_auto_fix"] is False
    anti_action = row["guidance"].get("anti_action", "")
    assert "Do not automatically rewrite implementation to match the existing contract." in anti_action


def test_ddt_baseline_missing_is_advisory_with_guidance(monkeypatch):
    binding = SimpleNamespace(func_id="harbor.core.x.y", file_path="tests/test_x.py")
    advisory = [SimpleNamespace(category="ddt_version_baseline_missing", binding=binding, message="m", suggested_action="s")]
    _patch_inputs(monkeypatch, ddt=_ddt_report(advisory=advisory))
    code, out, _ = run_cmd(["checkpoint", "--ci", "--format", "json"])
    payload = json.loads(out)
    assert code == 0
    assert payload["ci_failures"] == []
    row = payload["advisory"][0]
    assert row["category"] == "ddt_version_baseline_missing"
    assert row["guidance"]["decision_required"] is True
    assert "Do not blindly bump l3_version" in row["guidance"].get("anti_action", "")


def test_advice_off_removes_guidance_field(monkeypatch):
    status = _status_report(contract_gap=[_status_entry("harbor.core.a.f", "harbor/core/a.py")])
    _patch_inputs(monkeypatch, status=status)
    code, out, _ = run_cmd(["checkpoint", "--ci", "--format", "json", "--advice", "off"])
    payload = json.loads(out)
    assert code == 1
    row = payload["ci_failures"][0]
    assert "guidance" not in row
    assert "reason" in row and "category" in row


def test_checkpoint_json_output_is_single_json_object(monkeypatch):
    _patch_inputs(monkeypatch)
    code, out, _ = run_cmd(["checkpoint", "--ci", "--format", "json"])
    assert code == 0
    parsed = json.loads(out)
    assert out.strip().startswith("{")
    assert out.strip().endswith("}")
    assert parsed["command"] == "checkpoint"

from pathlib import Path

from harbor.core.repair_guidance import (
    generic_conservative_guidance,
    guidance_for_checkpoint_category,
    guidance_for_doctor_item,
    guidance_for_stale_item,
)


def test_contract_gap_guidance_defaults():
    guidance = guidance_for_checkpoint_category("contract_gap")
    assert guidance.suggested_skill == "harbor-contract-change"
    assert guidance.safe_to_auto_fix is False
    assert guidance.automation_policy == "plan_only"


def test_possible_semantic_drift_requires_decision_and_is_conservative():
    guidance = guidance_for_checkpoint_category("possible_semantic_drift")
    assert guidance.decision_required is True
    assert guidance.safe_to_auto_fix is False
    assert guidance.suggested_skill == "harbor-code-review"
    assert "Do not automatically rewrite implementation to match the existing contract." in (guidance.anti_action or "")
    assert "fix implementation" in " ".join(guidance.notes).lower()
    assert "update contract" in " ".join(guidance.notes).lower()


def test_ddt_version_baseline_missing_guidance_is_manual():
    guidance = guidance_for_checkpoint_category("ddt_version_baseline_missing")
    assert guidance.decision_required is True
    assert guidance.safe_to_auto_fix is False
    assert "Do not blindly bump l3_version" in (guidance.anti_action or "")


def test_stale_view_guidance_maps_context_refresh():
    guidance = guidance_for_stale_item(kind="view", view="l2_readme", status="stale")
    assert guidance is not None
    assert guidance.suggested_skill == "harbor-context-refresh"
    assert guidance.safe_to_auto_fix is False
    assert guidance.automation_policy == "safe_command_only"
    assert any("harbor finish --sync-context" in cmd for cmd in guidance.suggested_validation)


def test_doctor_fail_guidance_is_conservative():
    guidance = guidance_for_doctor_item(check="workspace migration", status="fail")
    assert guidance is not None
    assert guidance.automation_policy == "plan_only"
    assert guidance.safe_to_auto_fix is False


def test_unknown_checkpoint_category_graceful_degrade():
    guidance = guidance_for_checkpoint_category("totally_unknown")
    assert guidance.decision_required is True
    assert guidance.safe_to_auto_fix is False
    assert guidance.automation_policy == "plan_only"


def test_repair_guidance_has_no_llm_integration_symbols():
    src = (Path(__file__).resolve().parents[1] / "harbor" / "core" / "repair_guidance.py").read_text(encoding="utf-8")
    assert "OpenAI" not in src
    assert "resolve_provider" not in src
    assert "SemanticGuard" not in src
    assert "automatically fix implementation" not in src.lower()
    assert generic_conservative_guidance().safe_to_auto_fix is False

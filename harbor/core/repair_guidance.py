from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

AutomationPolicy = Literal["plan_only", "safe_command_only", "manual_decision_required"]
RiskLevel = Literal["low", "medium", "high"]


@dataclass
class RepairGuidance:
    what_happened: str
    recommended_action: str
    anti_action: Optional[str] = None
    suggested_skill: Optional[str] = None
    suggested_validation: List[str] = field(default_factory=list)
    decision_required: bool = False
    safe_to_auto_fix: bool = False
    automation_policy: AutomationPolicy = "plan_only"
    user_feedback_required: bool = False
    risk_level: RiskLevel = "medium"
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize deterministic repair guidance into a JSON-compatible dict.

        Behavior:
          - Serializes deterministic advisory metadata only.
          - Always includes core fields:
            `what_happened`, `recommended_action`, `suggested_validation`,
            `decision_required`, `safe_to_auto_fix`, `automation_policy`,
            `user_feedback_required`, `risk_level`, `notes`.
          - Optional fields (`anti_action`, `suggested_skill`) are included only
            when non-empty; no synthetic placeholder values are emitted.
          - `safe_to_auto_fix` / `automation_policy` / `decision_required` and
            related fields are recommendation metadata, not execution commands.

        Non-Goals:
          - Does not call any LLM/provider.
          - Does not write files.
          - Does not execute repair commands.
          - Does not change checkpoint/stale/doctor CI gate outcomes.

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: read-only
        """
        payload: Dict[str, object] = {
            "what_happened": self.what_happened,
            "recommended_action": self.recommended_action,
            "suggested_validation": list(self.suggested_validation),
            "decision_required": self.decision_required,
            "safe_to_auto_fix": self.safe_to_auto_fix,
            "automation_policy": self.automation_policy,
            "user_feedback_required": self.user_feedback_required,
            "risk_level": self.risk_level,
            "notes": list(self.notes),
        }
        if self.anti_action:
            payload["anti_action"] = self.anti_action
        if self.suggested_skill:
            payload["suggested_skill"] = self.suggested_skill
        return payload


def generic_conservative_guidance(*, what_happened: str = "This item requires conservative manual triage.") -> RepairGuidance:
    return RepairGuidance(
        what_happened=what_happened,
        recommended_action="Review the related target, contract, implementation, and tests before deciding next steps.",
        anti_action="Do not apply automatic code, contract, baseline, or version changes.",
        suggested_skill=None,
        suggested_validation=["harbor checkpoint --ci --format json"],
        decision_required=True,
        safe_to_auto_fix=False,
        automation_policy="plan_only",
        user_feedback_required=True,
        risk_level="medium",
        notes=["If intent is unclear, ask the user before making changes."],
    )


def guidance_for_checkpoint_category(category: str, *, language: Optional[str] = None) -> RepairGuidance:
    cat = str(category or "").strip()
    lang = str(language or "").strip().lower()
    if cat == "contract_gap":
        if lang == "typescript":
            return RepairGuidance(
                what_happened="This TypeScript target requires a contract source, but no contract-like JSDoc/TSDoc was found.",
                recommended_action=(
                    "Add an adjacent JSDoc/TSDoc contract source for the target, or reclassify the target as "
                    "internal/light if strict contract is not required."
                ),
                anti_action="TypeScript signature alone does not satisfy strict semantic contract requirements.",
                suggested_skill="harbor-contract-change",
                suggested_validation=[
                    "harbor checkpoint --ci --format json",
                ],
                decision_required=False,
                safe_to_auto_fix=False,
                automation_policy="plan_only",
                user_feedback_required=False,
                risk_level="medium",
            )
        return RepairGuidance(
            what_happened="This target requires a contract, but no valid contract source was found.",
            recommended_action="Inspect the target and add/update a Harbor contract docstring or equivalent contract source.",
            anti_action="Do not hide the gap by downgrading strictness unless the target truly should not be contract-bearing.",
            suggested_skill="harbor-contract-change",
            suggested_validation=[
                "harbor check --format jsonl",
                "harbor checkpoint --ci --format json",
            ],
            decision_required=False,
            safe_to_auto_fix=False,
            automation_policy="plan_only",
            user_feedback_required=False,
            risk_level="medium",
        )
    if cat == "contract_parse_error":
        return RepairGuidance(
            what_happened="A contract source exists, but Harbor could not parse it reliably.",
            recommended_action="Inspect and fix the contract format.",
            suggested_skill="harbor-contract-change",
            suggested_validation=[
                "harbor check --format jsonl",
                "harbor checkpoint --ci --format json",
            ],
            decision_required=False,
            safe_to_auto_fix=False,
            automation_policy="plan_only",
            user_feedback_required=False,
            risk_level="medium",
        )
    if cat == "possible_semantic_drift":
        return RepairGuidance(
            what_happened="A comparable contract exists, but implementation may no longer match it.",
            recommended_action=(
                "Inspect implementation, contract source, and related tests/DDT. "
                "Decide whether the implementation is wrong or the contract is stale."
            ),
            anti_action=(
                "Do not automatically rewrite implementation to match the existing contract. "
                "Do not automatically rewrite contract to match implementation without confirming intent."
            ),
            suggested_skill="harbor-code-review",
            suggested_validation=[
                "run targeted tests",
                "harbor check --format jsonl",
                "harbor checkpoint --ci --format json",
            ],
            decision_required=True,
            safe_to_auto_fix=False,
            automation_policy="manual_decision_required",
            user_feedback_required=True,
            risk_level="high",
            notes=[
                "If implementation is wrong, fix implementation.",
                "If implementation is intended, update contract and tests.",
                "If unclear, ask the user.",
            ],
        )
    if cat == "contract_changed":
        return RepairGuidance(
            what_happened="Contract changed and baseline has not been accepted yet.",
            recommended_action=(
                "Review whether the contract change is intentional and whether tests/DDT/generated context remain aligned."
            ),
            anti_action="Do not run harbor accept automatically.",
            suggested_skill="harbor-contract-change",
            suggested_validation=[
                "harbor check --format jsonl",
                "harbor checkpoint --ci --format json",
            ],
            decision_required=True,
            safe_to_auto_fix=False,
            automation_policy="manual_decision_required",
            user_feedback_required=True,
            risk_level="medium",
        )
    if cat == "contract_and_body_changed":
        return RepairGuidance(
            what_happened="Implementation and contract changed, but baseline has not been accepted yet.",
            recommended_action=(
                "Review implementation, contract, tests, and DDT together. "
                "Confirm this is an intentional synchronized change."
            ),
            anti_action=(
                "Do not accept baseline automatically. "
                "Do not assume body and contract changed consistently."
            ),
            suggested_skill="harbor-contract-change",
            suggested_validation=[
                "run targeted tests",
                "harbor check --format jsonl",
                "harbor checkpoint --ci --format json",
            ],
            decision_required=True,
            safe_to_auto_fix=False,
            automation_policy="manual_decision_required",
            user_feedback_required=True,
            risk_level="high",
        )
    if cat == "accepted_baseline_missing":
        return RepairGuidance(
            what_happened="The accepted checkpoint baseline artifact is missing in CI mode.",
            recommended_action=(
                "Run harbor accept locally after review, then commit "
                ".harbor/baseline/accepted-checkpoint.json."
            ),
            anti_action="Do not fall back to runtime cache in CI. Do not run harbor lock in CI as a workaround.",
            suggested_skill="harbor-contract-change",
            suggested_validation=["harbor checkpoint --ci --format json"],
            decision_required=True,
            safe_to_auto_fix=False,
            automation_policy="manual_decision_required",
            user_feedback_required=True,
            risk_level="high",
        )
    if cat == "accepted_baseline_invalid":
        return RepairGuidance(
            what_happened="The accepted checkpoint baseline artifact exists, but its schema or content is invalid.",
            recommended_action=(
                "Fix the artifact locally so file paths are repo-relative POSIX paths and required fields are valid, "
                "then commit the corrected artifact."
            ),
            anti_action="Do not ignore artifact schema errors. Do not fall back to runtime cache in CI.",
            suggested_skill="harbor-contract-change",
            suggested_validation=["harbor checkpoint --ci --format json"],
            decision_required=True,
            safe_to_auto_fix=False,
            automation_policy="manual_decision_required",
            user_feedback_required=True,
            risk_level="high",
        )
    if cat == "confirmed_contract_impact":
        return RepairGuidance(
            what_happened="A confirmed public contract impact was detected.",
            recommended_action=(
                "Review public contract impact and ensure implementation, tests, docs, "
                "and generated context are aligned."
            ),
            anti_action="Do not treat confirmed contract impact as automatically safe.",
            suggested_skill="harbor-contract-change",
            suggested_validation=[
                "run targeted tests",
                "harbor checkpoint --ci --format json",
            ],
            decision_required=True,
            safe_to_auto_fix=False,
            automation_policy="manual_decision_required",
            user_feedback_required=True,
            risk_level="high",
        )
    if cat == "possible_contract_impact":
        return RepairGuidance(
            what_happened="A possible public contract impact was detected.",
            recommended_action=(
                "Inspect whether the change affects public behavior, schema, CLI, JSON output, "
                "file write target, or generated view format."
            ),
            suggested_skill="harbor-code-review",
            suggested_validation=["harbor checkpoint --ci --format json"],
            decision_required=True,
            safe_to_auto_fix=False,
            automation_policy="plan_only",
            user_feedback_required=False,
            risk_level="medium",
        )
    if cat == "skipped_no_contract":
        if lang == "typescript":
            return RepairGuidance(
                what_happened="This TypeScript target is currently classified as contract-not-required.",
                recommended_action="No action is required unless contract_required classification is incorrect.",
                suggested_skill=None,
                suggested_validation=["harbor checkpoint --ci --format json"],
                decision_required=False,
                safe_to_auto_fix=False,
                automation_policy="plan_only",
                user_feedback_required=False,
                risk_level="low",
            )
        return RepairGuidance(
            what_happened="This target does not require a contract, so semantic audit was skipped.",
            recommended_action=(
                "Usually no action is required. Review only if strictness or contract_required "
                "classification looks wrong."
            ),
            suggested_skill=None,
            suggested_validation=["harbor checkpoint --ci --format json"],
            decision_required=False,
            safe_to_auto_fix=False,
            automation_policy="plan_only",
            user_feedback_required=False,
            risk_level="low",
        )
    if cat == "preview_valid":
        return RepairGuidance(
            what_happened="This TypeScript DDT preview binding is currently valid in advisory-only preview mode.",
            recommended_action=(
                "Use this preview result for explainability only and continue reviewing contract, target, and test alignment."
            ),
            anti_action="Do not treat preview_valid as a default CI blocker or as proof of test sufficiency.",
            suggested_skill="harbor-contract-change",
            suggested_validation=["harbor checkpoint --ci --format json --advice basic"],
            decision_required=False,
            safe_to_auto_fix=False,
            automation_policy="plan_only",
            user_feedback_required=False,
            risk_level="low",
            notes=["TypeScript DDT preview remains preview-only and advisory-first in v1.4.4."],
        )
    if cat == "target_not_found":
        return RepairGuidance(
            what_happened="A TypeScript DDT preview binding points to a target_id that was not found in the current workspace scan.",
            recommended_action=(
                "Review the target_id, verify TypeScript source discovery under code_roots, and confirm the target still exists."
            ),
            anti_action="Do not convert this preview finding into a default blocker or silently rewrite target_id values.",
            suggested_skill="harbor-contract-change",
            suggested_validation=["harbor checkpoint --ci --format json --advice basic"],
            decision_required=True,
            safe_to_auto_fix=False,
            automation_policy="plan_only",
            user_feedback_required=True,
            risk_level="medium",
            notes=["Preview findings stay outside ci_failures and exit-code semantics."],
        )
    if cat == "test_asset_missing":
        return RepairGuidance(
            what_happened="A TypeScript DDT preview binding references a test asset path that does not exist.",
            recommended_action="Review the repo-relative test_asset.path and either restore the test file or update the binding declaration.",
            anti_action="Do not treat missing preview test assets as proof of runtime failure or as a default blocker.",
            suggested_skill="harbor-contract-change",
            suggested_validation=["harbor checkpoint --ci --format json --advice basic"],
            decision_required=True,
            safe_to_auto_fix=False,
            automation_policy="plan_only",
            user_feedback_required=True,
            risk_level="medium",
        )
    if cat == "contract_source_missing":
        return RepairGuidance(
            what_happened="The preview-bound TypeScript target does not currently have enough contract evidence for preview validation.",
            recommended_action=(
                "Add or improve adjacent JSDoc/TSDoc contract evidence for the target, then rerun checkpoint/next preview diagnostics."
            ),
            anti_action="Do not assume TypeScript signatures or data-contract evidence alone satisfy function-level preview validation.",
            suggested_skill="harbor-contract-change",
            suggested_validation=["harbor checkpoint --ci --format json --advice basic"],
            decision_required=False,
            safe_to_auto_fix=False,
            automation_policy="plan_only",
            user_feedback_required=False,
            risk_level="medium",
        )
    if cat == "public_boundary_unconfirmed":
        return RepairGuidance(
            what_happened="The preview-bound TypeScript target does not yet have strong enough public-boundary confirmation for the configured preview check.",
            recommended_action=(
                "Review public boundary evidence, preset mode, and entrypoint/export configuration, then decide whether the preview binding should remain advisory."
            ),
            anti_action="Do not promote this preview-only boundary result into a default blocking gate.",
            suggested_skill="harbor-contract-change",
            suggested_validation=["harbor checkpoint --ci --format json --advice basic"],
            decision_required=True,
            safe_to_auto_fix=False,
            automation_policy="plan_only",
            user_feedback_required=True,
            risk_level="medium",
        )
    if cat == "binding_schema_invalid":
        return RepairGuidance(
            what_happened="The TypeScript DDT preview sidecar schema is invalid or contains unsupported binding fields.",
            recommended_action="Fix the sidecar schema, required fields, path values, or frozen strategy enum values.",
            anti_action="Do not bypass invalid preview sidecar structure by treating it as an accepted baseline change.",
            suggested_skill="harbor-contract-change",
            suggested_validation=["harbor checkpoint --ci --format json --advice basic"],
            decision_required=False,
            safe_to_auto_fix=False,
            automation_policy="plan_only",
            user_feedback_required=False,
            risk_level="medium",
        )
    if cat == "duplicate_binding_id":
        return RepairGuidance(
            what_happened="Multiple TypeScript DDT preview bindings declare the same binding_id.",
            recommended_action="Keep binding_id unique across the sidecar and review which declaration should remain.",
            anti_action="Do not rely on duplicate binding_id ordering or assume Harbor will pick one binding implicitly.",
            suggested_skill="harbor-contract-change",
            suggested_validation=["harbor checkpoint --ci --format json --advice basic"],
            decision_required=True,
            safe_to_auto_fix=False,
            automation_policy="plan_only",
            user_feedback_required=True,
            risk_level="medium",
        )
    if cat == "unsupported_syntax_advisory":
        return RepairGuidance(
            what_happened="TypeScript lightweight parser could not safely classify this target.",
            recommended_action=(
                "Simplify the export form to the supported MVP patterns, or keep this as advisory and "
                "wait for a future AST backend/framework preset."
            ),
            anti_action="Do not force this into contract_parse_error or blocking gate in v1.4.0 MVP.",
            suggested_skill="harbor-contract-change",
            suggested_validation=["harbor checkpoint --ci --format json"],
            decision_required=False,
            safe_to_auto_fix=False,
            automation_policy="plan_only",
            user_feedback_required=False,
            risk_level="low",
        )
    if cat == "ddt_version_baseline_missing":
        return RepairGuidance(
            what_happened="Strict DDT binding is structurally valid, but no L3 contract version baseline was found.",
            recommended_action="Review baseline state before deciding whether l3_version should be changed.",
            anti_action="Do not blindly bump l3_version. Do not run harbor accept automatically.",
            suggested_skill="harbor-ddt-diary",
            suggested_validation=[
                "harbor check --format jsonl",
                "harbor checkpoint --ci --format json",
            ],
            decision_required=True,
            safe_to_auto_fix=False,
            automation_policy="manual_decision_required",
            user_feedback_required=True,
            risk_level="medium",
        )
    if cat == "ddt_binding":
        return RepairGuidance(
            what_happened="DDT binding violation detected.",
            recommended_action=(
                "Fix DDT binding violation. Strict targets must use explicit l3_version "
                "and must not use strategy='latest'."
            ),
            suggested_skill="harbor-ddt-diary",
            suggested_validation=[
                "harbor check --format jsonl",
                "harbor checkpoint --ci --format json",
            ],
            decision_required=False,
            safe_to_auto_fix=False,
            automation_policy="plan_only",
            user_feedback_required=False,
            risk_level="medium",
        )
    if cat == "missing_function":
        return RepairGuidance(
            what_happened="A baseline function is missing from implementation.",
            recommended_action=(
                "Review whether the function removal is intentional. If intentional, update "
                "contracts/tests/generated context; otherwise restore it."
            ),
            anti_action="Do not accept baseline automatically.",
            suggested_skill="harbor-code-review",
            suggested_validation=[
                "harbor check --format jsonl",
                "harbor checkpoint --ci --format json",
            ],
            decision_required=True,
            safe_to_auto_fix=False,
            automation_policy="manual_decision_required",
            user_feedback_required=False,
            risk_level="high",
        )
    if cat == "untracked_function":
        return RepairGuidance(
            what_happened="A new function is not tracked in Harbor baseline.",
            recommended_action=(
                "Review whether the new function should be added to Harbor baseline and "
                "whether it needs a contract."
            ),
            anti_action="Do not accept baseline automatically.",
            suggested_skill="harbor-code-review",
            suggested_validation=[
                "harbor check --format jsonl",
                "harbor checkpoint --ci --format json",
            ],
            decision_required=True,
            safe_to_auto_fix=False,
            automation_policy="manual_decision_required",
            user_feedback_required=False,
            risk_level="medium",
        )
    return generic_conservative_guidance(
        what_happened=f"Checkpoint item category '{cat or 'unknown'}' is not recognized by explicit rules."
    )


def guidance_for_stale_item(*, kind: Optional[str], view: Optional[str], status: Optional[str]) -> Optional[RepairGuidance]:
    kind_v = str(kind or "").strip()
    view_v = str(view or "").strip()
    status_v = str(status or "").strip()
    if kind_v == "view" and view_v in ("l2_readme", "module_capsule") and status_v in ("stale", "unknown"):
        return RepairGuidance(
            what_happened="Generated context view is stale or unknown.",
            recommended_action="Refresh generated context using Harbor commands.",
            suggested_skill="harbor-context-refresh",
            suggested_validation=[
                "harbor finish --sync-context",
                "harbor stale --ci --format json",
                "harbor doctor --ci --format json",
            ],
            decision_required=False,
            safe_to_auto_fix=False,
            automation_policy="safe_command_only",
            user_feedback_required=False,
            risk_level="low",
            notes=["safe_command_only means suggested safe commands only; no automatic command execution."],
        )
    return None


def guidance_for_doctor_item(*, check: Optional[str], status: Optional[str]) -> Optional[RepairGuidance]:
    status_v = str(status or "").strip().lower()
    if status_v != "fail":
        return None
    check_v = str(check or "").strip().lower()
    suggested_skill: Optional[str] = None
    if any(token in check_v for token in ("safety", "protected", "permission")):
        suggested_skill = "harbor-safety-preflight"
    elif any(token in check_v for token in ("stale", "generated", "derived view", "context")):
        suggested_skill = "harbor-context-refresh"
    elif any(token in check_v for token in ("workspace", "migration", "migrate")):
        suggested_skill = "harbor-workspace-migration-plan"
    return RepairGuidance(
        what_happened="A Harbor workspace health check failed.",
        recommended_action="Inspect the doctor check result and follow the suggested command if it is safe.",
        suggested_skill=suggested_skill,
        suggested_validation=["harbor doctor --ci --format json"],
        decision_required=True,
        safe_to_auto_fix=False,
        automation_policy="plan_only",
        user_feedback_required=False,
        risk_level="medium",
    )

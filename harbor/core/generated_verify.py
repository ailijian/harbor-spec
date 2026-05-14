from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from harbor.core.advice_config import AdviceSettings
from harbor.core.ci import CIFailure, CIResult
from harbor.core.context_integrity import (
    build_context_integrity_metadata,
    compose_markdown_with_frontmatter,
    content_without_generated_at_for_compare,
    extract_integrity_fingerprints,
    strip_frontmatter,
)
from harbor.core.l2 import L2Generator
from harbor.core.module_capsule import (
    build_module_card_frontmatter,
    collect_module_context,
    compute_module_fingerprint,
    normalize_module_path,
    preview_module_capsule,
)
from harbor.core.project_structure import (
    collect_project_structure_integrity_inputs,
    collect_project_structure_context,
    generate_project_structure_markdown,
)
from harbor.core.workspace import load_workspace_config, load_workspace_paths, parse_workspace_export_options
from harbor.core.repair_guidance import generic_conservative_guidance
from harbor.utils.i18n import t


ARTIFACT_STATUS_UP_TO_DATE = "up_to_date"
ARTIFACT_STATUS_FAIL = "fail"
ARTIFACT_STATUS_MISSING = "missing"
ARTIFACT_STATUS_DISABLED = "disabled"
ARTIFACT_STATUS_BLOCKED = "blocked"
ARTIFACT_STATUS_UNKNOWN = "unknown"

REPORT_STATUS_PASS = "pass"
REPORT_STATUS_WARN = "warn"
REPORT_STATUS_FAIL = "fail"


@dataclass
class GeneratedArtifactVerification:
    artifact: str
    status: str
    reason: Optional[str] = None
    module: Optional[str] = None
    path: Optional[str] = None
    suggested_command: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialize one verified artifact row to a stable JSON-compatible mapping.

        Returns:
          dict: Artifact payload with sanitized relative path fields.

        Side Effects:
          - Performs no file writes and no auto-fix.

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: read-only
        """
        payload: Dict[str, Any] = {
            "artifact": str(self.artifact),
            "status": str(self.status),
            "reason": self.reason,
            "path": _sanitize_rel_path(self.path),
            "suggested_command": self.suggested_command,
            "details": _sanitize_details(self.details),
        }
        if self.module:
            payload["module"] = normalize_module_path(self.module)
        return payload


@dataclass
class ModuleGeneratedVerification:
    module: str
    artifacts: List[GeneratedArtifactVerification]

    def to_dict(self) -> dict:
        """Serialize one module verification group to a stable JSON-compatible mapping.

        Returns:
          dict: Module payload with normalized module path and serialized artifacts.

        Side Effects:
          - Performs no file writes and no auto-fix.

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: read-only
        """
        return {
            "module": normalize_module_path(self.module),
            "artifacts": [item.to_dict() for item in self.artifacts],
        }


@dataclass
class ProjectGeneratedVerification:
    artifacts: List[GeneratedArtifactVerification]

    def to_dict(self) -> dict:
        """Serialize project-level verification rows to a stable JSON-compatible mapping.

        Returns:
          dict: Project payload containing serialized project artifacts.

        Side Effects:
          - Performs no file writes and no auto-fix.

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: read-only
        """
        return {
            "artifacts": [item.to_dict() for item in self.artifacts],
        }


@dataclass
class GeneratedVerificationReport:
    scope: str
    project: ProjectGeneratedVerification
    modules: List[ModuleGeneratedVerification]
    status: str
    summary: Dict[str, int]
    repair_commands: List[str]
    writes_files: bool = False

    def to_dict(self) -> dict:
        """Serialize the verify-generated domain report via the public report serializer.

        Returns:
          dict: Public non-CI verify-generated JSON payload.

        Side Effects:
          - Performs no file writes and no auto-fix.

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: read-only
        """
        return generated_verification_report_to_dict(self)


def build_generated_verification_report(*, scope: str, modules: Sequence[str]) -> GeneratedVerificationReport:
    """Verify tracked generated context by recomputing expected artifacts from current source truth.

    Behavior:
      - Rebuilds expected project-level and module-level generated artifacts from fresh source-derived inputs.
      - Compares current tracked files against the recomputed expectations while ignoring timestamp-only drift.
      - Reports mismatches and missing artifacts but never performs repair automatically.

    Args:
      scope (str): Verification scope label such as ``changed``, ``all``, or ``module:<name>``.
      modules (Sequence[str]): Module paths to verify after normalization and deduplication.

    Returns:
      GeneratedVerificationReport: Stable report model for text/json/CI output.

    Side Effects:
      - Reads workspace config, source files, cache/index files, and generated context files.
      - Writes no files and performs no auto-fix.

    Idempotency:
      - Deterministic for the same workspace state.

    Security:
      - Sanitizes report paths to repo-relative form before serialization.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: read-only
    """
    normalized_modules = sorted({normalize_module_path(module) for module in modules if str(module or "").strip()})

    project_artifacts = [
        verify_project_structure(),
        verify_l2_meta(normalized_modules),
    ]
    module_reports = [verify_module_generated(module) for module in normalized_modules]

    summary = _build_summary(project_artifacts, module_reports)
    status = _derive_report_status(summary)
    repair_commands = _collect_repair_commands(project_artifacts, module_reports)
    return GeneratedVerificationReport(
        scope=str(scope or "changed"),
        project=ProjectGeneratedVerification(artifacts=project_artifacts),
        modules=module_reports,
        status=status,
        summary=summary,
        repair_commands=repair_commands,
        writes_files=False,
    )


def verify_project_structure() -> GeneratedArtifactVerification:
    root = Path.cwd().resolve()
    workspace_paths = load_workspace_paths(root, enforce_write_safety=True)
    canonical_path = workspace_paths.project_structure_path
    display_path = _repo_display_path(canonical_path)

    context = collect_project_structure_context(root)
    expected_body = generate_project_structure_markdown(context)
    expected_markdown = _compose_expected_project_structure_markdown(context, expected_body, root=root)

    if not canonical_path.exists():
        return GeneratedArtifactVerification(
            artifact="project_structure",
            status=ARTIFACT_STATUS_MISSING,
            reason="missing_project_structure",
            path=display_path,
            suggested_command="harbor project structure --write",
        )

    try:
        current_markdown = canonical_path.read_text(encoding="utf-8")
    except Exception:
        return GeneratedArtifactVerification(
            artifact="project_structure",
            status=ARTIFACT_STATUS_FAIL,
            reason="project_structure_unreadable",
            path=display_path,
            suggested_command="harbor project structure --write",
        )

    if content_without_generated_at_for_compare(current_markdown) != content_without_generated_at_for_compare(expected_markdown):
        return GeneratedArtifactVerification(
            artifact="project_structure",
            status=ARTIFACT_STATUS_FAIL,
            reason="project_structure_mismatch",
            path=display_path,
            suggested_command="harbor project structure --write",
        )

    return GeneratedArtifactVerification(
        artifact="project_structure",
        status=ARTIFACT_STATUS_UP_TO_DATE,
        reason=None,
        path=display_path,
        suggested_command=None,
    )


def verify_l2_meta(modules: Sequence[str]) -> GeneratedArtifactVerification:
    gen = L2Generator(prefer_fresh_source=True)
    display_path = _repo_display_path(gen.meta_path)
    meta_exists = gen.meta_path.exists() or gen.legacy_meta_path.exists()
    if not meta_exists:
        return GeneratedArtifactVerification(
            artifact="l2_meta",
            status=ARTIFACT_STATUS_MISSING,
            reason="missing_l2_meta_file",
            path=display_path,
            suggested_command=_suggest_docs_refresh(modules),
        )

    current_meta = gen._load_meta()
    for module in modules:
        expected_hash = gen.compute_meta_hash(gen.generate(module))
        current_hash = str(current_meta.get(module) or "").strip()
        if not current_hash:
            return GeneratedArtifactVerification(
                artifact="l2_meta",
                status=ARTIFACT_STATUS_MISSING,
                reason="missing_l2_meta_entry",
                path=display_path,
                suggested_command=f"harbor docs --module {module} --write",
                details={"module": module, "expected_hash": expected_hash},
            )
        if current_hash != expected_hash:
            return GeneratedArtifactVerification(
                artifact="l2_meta",
                status=ARTIFACT_STATUS_FAIL,
                reason="l2_meta_hash_mismatch",
                path=display_path,
                suggested_command=f"harbor docs --module {module} --write",
                details={
                    "module": module,
                    "current_hash": current_hash,
                    "expected_hash": expected_hash,
                },
            )

    return GeneratedArtifactVerification(
        artifact="l2_meta",
        status=ARTIFACT_STATUS_UP_TO_DATE,
        reason=None,
        path=display_path,
        suggested_command=None,
    )


def verify_module_generated(module: str) -> ModuleGeneratedVerification:
    normalized = normalize_module_path(module)
    l2_context = collect_module_context(normalized, prefer_fresh_source=True)
    l2_artifact = verify_canonical_l2_readme(normalized, context=l2_context)
    export_artifact = verify_export_l2_readme(normalized, canonical_artifact=l2_artifact)
    capsule_artifacts = verify_module_capsule(normalized, context=l2_context)
    return ModuleGeneratedVerification(
        module=normalized,
        artifacts=[l2_artifact, export_artifact, *capsule_artifacts],
    )


def verify_canonical_l2_readme(
    module: str,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> GeneratedArtifactVerification:
    normalized = normalize_module_path(module)
    l2_context = context or collect_module_context(normalized, prefer_fresh_source=True)
    gen = L2Generator(prefer_fresh_source=True)
    display_path = _repo_display_path(gen.canonical_readme_path(normalized))

    if not l2_context.get("key_files") and not l2_context.get("contracts"):
        return GeneratedArtifactVerification(
            artifact="canonical_l2_readme",
            module=normalized,
            status=ARTIFACT_STATUS_UNKNOWN,
            reason="no_indexed_records_for_module",
            path=display_path,
            suggested_command=None,
        )

    expected_body = gen.generate(normalized)
    expected_markdown = _compose_expected_canonical_l2_markdown(gen, normalized, expected_body)
    current_path = gen.canonical_readme_path(normalized)

    if not current_path.exists():
        return GeneratedArtifactVerification(
            artifact="canonical_l2_readme",
            module=normalized,
            status=ARTIFACT_STATUS_MISSING,
            reason="missing_l2_readme",
            path=display_path,
            suggested_command=f"harbor docs --module {normalized} --write",
        )

    try:
        current_markdown = current_path.read_text(encoding="utf-8")
    except Exception:
        return GeneratedArtifactVerification(
            artifact="canonical_l2_readme",
            module=normalized,
            status=ARTIFACT_STATUS_FAIL,
            reason="l2_read_error",
            path=display_path,
            suggested_command=f"harbor docs --module {normalized} --write",
        )

    if content_without_generated_at_for_compare(current_markdown) == content_without_generated_at_for_compare(expected_markdown):
        return GeneratedArtifactVerification(
            artifact="canonical_l2_readme",
            module=normalized,
            status=ARTIFACT_STATUS_UP_TO_DATE,
            reason=None,
            path=display_path,
            suggested_command=None,
        )

    current_fp = extract_integrity_fingerprints(current_markdown)
    expected_fp = extract_integrity_fingerprints(expected_markdown)
    reason = "l2_body_mismatch"
    for key, mapped_reason in (
        ("source_fingerprint", "l2_source_fingerprint_mismatch"),
        ("contract_fingerprint", "l2_contract_fingerprint_mismatch"),
        ("generator_fingerprint", "l2_generator_fingerprint_mismatch"),
    ):
        if str(current_fp.get(key) or "") != str(expected_fp.get(key) or ""):
            reason = mapped_reason
            break

    return GeneratedArtifactVerification(
        artifact="canonical_l2_readme",
        module=normalized,
        status=ARTIFACT_STATUS_FAIL,
        reason=reason,
        path=display_path,
        suggested_command=f"harbor docs --module {normalized} --write",
        details={
            "current_source_fingerprint": current_fp.get("source_fingerprint"),
            "expected_source_fingerprint": expected_fp.get("source_fingerprint"),
            "current_contract_fingerprint": current_fp.get("contract_fingerprint"),
            "expected_contract_fingerprint": expected_fp.get("contract_fingerprint"),
            "current_generator_fingerprint": current_fp.get("generator_fingerprint"),
            "expected_generator_fingerprint": expected_fp.get("generator_fingerprint"),
        },
    )


def verify_export_l2_readme(
    module: str,
    *,
    canonical_artifact: GeneratedArtifactVerification,
) -> GeneratedArtifactVerification:
    normalized = normalize_module_path(module)
    loaded = load_workspace_config(Path.cwd())
    cfg = loaded.get("config") or {}
    export_options = parse_workspace_export_options(cfg)
    module_readme_options = ((export_options.get("l2", {}) or {}).get("module_readme", {}) or {})
    export_enabled = bool(module_readme_options.get("enabled", True))
    export_path = (Path.cwd().resolve() / normalized / "README.md").resolve()
    display_path = _repo_display_path(export_path)

    if not export_enabled:
        return GeneratedArtifactVerification(
            artifact="export_l2_readme",
            module=normalized,
            status=ARTIFACT_STATUS_DISABLED,
            reason="export_disabled",
            path=display_path,
            suggested_command=None,
        )

    if canonical_artifact.status != ARTIFACT_STATUS_UP_TO_DATE:
        return GeneratedArtifactVerification(
            artifact="export_l2_readme",
            module=normalized,
            status=ARTIFACT_STATUS_BLOCKED,
            reason="export_blocked_by_canonical",
            path=display_path,
            suggested_command=None,
        )

    if not export_path.exists():
        return GeneratedArtifactVerification(
            artifact="export_l2_readme",
            module=normalized,
            status=ARTIFACT_STATUS_MISSING,
            reason="missing_export_readme",
            path=display_path,
            suggested_command=f"harbor docs --module {normalized} --write",
        )

    gen = L2Generator(prefer_fresh_source=True)
    expected_body = gen.generate(normalized)
    try:
        current_text = export_path.read_text(encoding="utf-8")
    except Exception:
        return GeneratedArtifactVerification(
            artifact="export_l2_readme",
            module=normalized,
            status=ARTIFACT_STATUS_FAIL,
            reason="export_read_error",
            path=display_path,
            suggested_command=f"harbor docs --module {normalized} --write",
        )

    if _normalize_body(current_text) != _normalize_body(expected_body):
        return GeneratedArtifactVerification(
            artifact="export_l2_readme",
            module=normalized,
            status=ARTIFACT_STATUS_FAIL,
            reason="export_body_mismatch",
            path=display_path,
            suggested_command=f"harbor docs --module {normalized} --write",
        )

    return GeneratedArtifactVerification(
        artifact="export_l2_readme",
        module=normalized,
        status=ARTIFACT_STATUS_UP_TO_DATE,
        reason=None,
        path=display_path,
        suggested_command=None,
    )


def verify_module_capsule(module: str, *, context: Optional[Dict[str, Any]] = None) -> List[GeneratedArtifactVerification]:
    normalized = normalize_module_path(module)
    capsule_context = context or collect_module_context(normalized, prefer_fresh_source=True)
    previews = preview_module_capsule(capsule_context)
    module_fp = compute_module_fingerprint(capsule_context)
    root = Path.cwd().resolve()
    source_paths = sorted({str(p).replace("\\", "/").strip("/") for p in (capsule_context.get("key_files") or []) if str(p)})
    contract_records = list(capsule_context.get("contracts") or [])
    generation_command = f"harbor module seal {normalized} --write"
    workspace_paths = load_workspace_paths(root, enforce_write_safety=True)
    canonical_dir = workspace_paths.modules_view_root / Path(normalized)

    expected_markdown = {
        "module-card.md": _compose_expected_module_card_markdown(
            module=normalized,
            body=previews["module-card.md"],
            source_paths=source_paths,
            contract_records=contract_records,
            generation_command=generation_command,
            fingerprint=module_fp,
            repo_root=root,
        ),
        "review-checklist.md": _compose_expected_capsule_markdown(
            view_type="review_checklist",
            module=normalized,
            body=previews["review-checklist.md"],
            source_paths=source_paths,
            contract_records=contract_records,
            generation_command=generation_command,
            repo_root=root,
        ),
        "debug-playbook.md": _compose_expected_capsule_markdown(
            view_type="debug_playbook",
            module=normalized,
            body=previews["debug-playbook.md"],
            source_paths=source_paths,
            contract_records=contract_records,
            generation_command=generation_command,
            repo_root=root,
        ),
    }

    artifacts: List[GeneratedArtifactVerification] = []
    for file_name, artifact_name, missing_reason, body_reason in (
        ("module-card.md", "module_card", "missing_module_card", "module_card_body_mismatch"),
        ("review-checklist.md", "review_checklist", "missing_review_checklist", "review_checklist_body_mismatch"),
        ("debug-playbook.md", "debug_playbook", "missing_debug_playbook", "debug_playbook_body_mismatch"),
    ):
        current_path = canonical_dir / file_name
        display_path = _repo_display_path(current_path)
        if not current_path.exists():
            artifacts.append(
                GeneratedArtifactVerification(
                    artifact=artifact_name,
                    module=normalized,
                    status=ARTIFACT_STATUS_MISSING,
                    reason=missing_reason,
                    path=display_path,
                    suggested_command=f"harbor module seal {normalized} --write",
                )
            )
            continue

        try:
            current_markdown = current_path.read_text(encoding="utf-8")
        except Exception:
            artifacts.append(
                GeneratedArtifactVerification(
                    artifact=artifact_name,
                    module=normalized,
                    status=ARTIFACT_STATUS_FAIL,
                    reason="module_capsule_read_error",
                    path=display_path,
                    suggested_command=f"harbor module seal {normalized} --write",
                )
            )
            continue

        expected = expected_markdown[file_name]
        if content_without_generated_at_for_compare(current_markdown) == content_without_generated_at_for_compare(expected):
            artifacts.append(
                GeneratedArtifactVerification(
                    artifact=artifact_name,
                    module=normalized,
                    status=ARTIFACT_STATUS_UP_TO_DATE,
                    reason=None,
                    path=display_path,
                    suggested_command=None,
                )
            )
            continue

        reason = body_reason
        details: Dict[str, Any] = {}
        if file_name == "module-card.md":
            current_fp = extract_integrity_fingerprints(current_markdown)
            expected_fp = extract_integrity_fingerprints(expected)
            if str(current_fp.get("view_fingerprint") or "") != str(expected_fp.get("view_fingerprint") or ""):
                reason = "module_capsule_fingerprint_mismatch"
                details = {
                    "current_fingerprint": current_fp.get("view_fingerprint"),
                    "expected_fingerprint": expected_fp.get("view_fingerprint"),
                }
        artifacts.append(
            GeneratedArtifactVerification(
                artifact=artifact_name,
                module=normalized,
                status=ARTIFACT_STATUS_FAIL,
                reason=reason,
                path=display_path,
                suggested_command=f"harbor module seal {normalized} --write",
                details=details,
            )
        )

    return artifacts


def generated_verification_report_to_dict(report: GeneratedVerificationReport) -> dict:
    """Serialize the verify-generated domain report to the public non-CI JSON payload.

    Output Contract:
      - Returns a single JSON-compatible object with stable top-level keys:
        ``command``, ``scope``, ``status``, ``writes_files``, ``summary``,
        ``project``, ``modules``, and ``repair_commands``.
      - ``writes_files`` is always ``false`` because verification is read-only.
      - Paths and nested details are sanitized to avoid leaking machine-local absolute paths.

    Args:
      report (GeneratedVerificationReport): Domain report produced by verify-generated.

    Returns:
      dict: Public non-CI JSON payload for ``verify-generated --format json``.

    Side Effects:
      - Serializes only; does not refresh context, repair files, or change workspace state.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: read-only
    """
    return {
        "command": "verify-generated",
        "scope": str(report.scope),
        "status": str(report.status),
        "writes_files": False,
        "summary": dict(report.summary),
        "project": report.project.to_dict(),
        "modules": [item.to_dict() for item in report.modules],
        "repair_commands": list(report.repair_commands),
    }


def build_generated_verification_ci_result(
    report: GeneratedVerificationReport,
    advice_settings: Optional[AdviceSettings] = None,
) -> CIResult:
    """Build the public CI gate result for verify-generated.

    Behavior:
      - Converts verify-generated mismatches and missing artifacts into blocking ``ci_failures``.
      - Converts blocked/unknown outcomes into advisory items.
      - Produces a non-zero exit code when blocking mismatches are present.
      - Attaches deterministic conservative guidance only when advice mode enables it.

    Args:
      report (GeneratedVerificationReport): Domain verification report.
      advice_settings (Optional[AdviceSettings]): Optional advice emission settings.

    Returns:
      CIResult: Public CI result consumed by ``--ci`` JSON/text output and ``harbor next --from``.

    Side Effects:
      - Writes no files and performs no automatic repair.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: read-only
    """
    settings = advice_settings or AdviceSettings()
    ci_failures: List[CIFailure] = []
    advisory: List[CIFailure] = []

    all_artifacts: List[GeneratedArtifactVerification] = list(report.project.artifacts)
    for module_report in report.modules:
        all_artifacts.extend(module_report.artifacts)

    for artifact in all_artifacts:
        row = CIFailure(
            kind="view",
            module=artifact.module,
            view=artifact.artifact,
            status=artifact.status,
            reason=artifact.reason,
            suggested_command=artifact.suggested_command,
            guidance=(
                generic_conservative_guidance(
                    what_happened=f"Generated artifact '{artifact.artifact}' requires manual verification."
                )
                if settings.enabled and artifact.status in (ARTIFACT_STATUS_FAIL, ARTIFACT_STATUS_MISSING)
                else None
            ),
        )
        if artifact.status in (ARTIFACT_STATUS_FAIL, ARTIFACT_STATUS_MISSING):
            ci_failures.append(row)
        elif artifact.status in (ARTIFACT_STATUS_BLOCKED, ARTIFACT_STATUS_UNKNOWN):
            advisory.append(row)

    exit_code = 1 if ci_failures else 0
    return CIResult(
        command="verify-generated",
        status="fail" if ci_failures else "pass",
        exit_code=exit_code,
        summary={
            "scope": str(report.scope),
            "modules_checked": int(report.summary.get("modules_checked", 0)),
            "ci_failures": len(ci_failures),
            "advisory_items": len(advisory),
        },
        ci_failures=ci_failures,
        advisory=advisory,
        next_steps=list(report.repair_commands),
        advice_mode=settings.mode,
        include_in_ci_json=settings.include_in_ci_json,
        include_in_text=settings.include_in_text,
    )


def format_generated_verification_report(report: GeneratedVerificationReport, *, scope_text: str) -> str:
    lines: List[str] = [
        t("cli.verify_generated.title"),
        "",
        f"{t('cli.verify_generated.scope_label')}: {scope_text}",
        f"{t('cli.verify_generated.status_label')}: {t(f'cli.verify_generated.status.{report.status}')}",
        "",
        t("cli.verify_generated.project_section"),
    ]
    lines.extend(_format_artifact_lines(report.project.artifacts))

    for module_report in report.modules:
        lines.append("")
        lines.append(module_report.module)
        lines.extend(_format_artifact_lines(module_report.artifacts))

    if report.status == REPORT_STATUS_PASS:
        lines.append("")
        lines.append(t("cli.verify_generated.all_up_to_date"))

    if report.repair_commands:
        lines.append("")
        lines.append(t("cli.verify_generated.repair_summary"))
        for command in report.repair_commands:
            lines.append(f"- {command}")

    return "\n".join(lines)


def _format_artifact_lines(artifacts: Sequence[GeneratedArtifactVerification]) -> List[str]:
    lines: List[str] = []
    for artifact in artifacts:
        label = t(f"cli.verify_generated.artifact.{artifact.artifact}")
        lines.append(f"- {label}: {artifact.status}")
        if artifact.reason:
            lines.append(f"  {t('cli.verify_generated.reason_label')}: {artifact.reason}")
        if artifact.suggested_command:
            lines.append(f"  {t('cli.verify_generated.suggested_label')}: {artifact.suggested_command}")
    return lines


def _derive_report_status(summary: Dict[str, int]) -> str:
    if int(summary.get("failures", 0)) > 0 or int(summary.get("missing", 0)) > 0:
        return REPORT_STATUS_FAIL
    if int(summary.get("blocked", 0)) > 0 or int(summary.get("unknown", 0)) > 0:
        return REPORT_STATUS_WARN
    return REPORT_STATUS_PASS


def _build_summary(
    project_artifacts: Sequence[GeneratedArtifactVerification],
    module_reports: Sequence[ModuleGeneratedVerification],
) -> Dict[str, int]:
    counts = {
        "modules_checked": len(module_reports),
        "artifacts_checked": 0,
        "up_to_date": 0,
        "failures": 0,
        "missing": 0,
        "disabled": 0,
        "blocked": 0,
        "unknown": 0,
        "repair_commands": 0,
    }
    all_artifacts: List[GeneratedArtifactVerification] = list(project_artifacts)
    for module_report in module_reports:
        all_artifacts.extend(module_report.artifacts)
    counts["artifacts_checked"] = len(all_artifacts)

    for artifact in all_artifacts:
        if artifact.status == ARTIFACT_STATUS_UP_TO_DATE:
            counts["up_to_date"] += 1
        elif artifact.status == ARTIFACT_STATUS_FAIL:
            counts["failures"] += 1
        elif artifact.status == ARTIFACT_STATUS_MISSING:
            counts["missing"] += 1
        elif artifact.status == ARTIFACT_STATUS_DISABLED:
            counts["disabled"] += 1
        elif artifact.status == ARTIFACT_STATUS_BLOCKED:
            counts["blocked"] += 1
        elif artifact.status == ARTIFACT_STATUS_UNKNOWN:
            counts["unknown"] += 1

    counts["repair_commands"] = len(_collect_repair_commands(project_artifacts, module_reports))
    return counts


def _collect_repair_commands(
    project_artifacts: Sequence[GeneratedArtifactVerification],
    module_reports: Sequence[ModuleGeneratedVerification],
) -> List[str]:
    commands: List[str] = []
    for artifact in project_artifacts:
        if artifact.suggested_command:
            commands.append(artifact.suggested_command)
    for module_report in sorted(module_reports, key=lambda item: item.module):
        for artifact in module_report.artifacts:
            if artifact.suggested_command:
                commands.append(artifact.suggested_command)
    deduped: List[str] = []
    seen = set()
    for command in commands:
        key = str(command).strip()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(key)
    return deduped


def _compose_expected_project_structure_markdown(context, body: str, *, root: Path) -> str:
    source_paths, contract_records = collect_project_structure_integrity_inputs(root)
    metadata = build_context_integrity_metadata(
        view_type="project_structure",
        module=None,
        generation_command="harbor project structure --write",
        source_paths=source_paths,
        contract_records=contract_records,
        repo_root=root,
    )
    return compose_markdown_with_frontmatter("", metadata, body)


def _compose_expected_canonical_l2_markdown(gen: L2Generator, module: str, body: str) -> str:
    source_paths, contract_records = gen._collect_integrity_inputs(module)
    metadata = build_context_integrity_metadata(
        view_type="l2_readme",
        module=module,
        generation_command=f"harbor docs --module {module} --write",
        source_paths=source_paths,
        contract_records=contract_records,
        repo_root=gen.repo_root,
    )
    return compose_markdown_with_frontmatter("", metadata, body)


def _compose_expected_module_card_markdown(
    *,
    module: str,
    body: str,
    source_paths: List[str],
    contract_records: List[Dict[str, Any]],
    generation_command: str,
    fingerprint: str,
    repo_root: Path,
) -> str:
    metadata = build_module_card_frontmatter(
        module,
        source_paths=source_paths,
        contract_records=contract_records,
        repo_root=repo_root,
        generation_command=generation_command,
        fingerprint=fingerprint,
    )
    return compose_markdown_with_frontmatter("", metadata, body)


def _compose_expected_capsule_markdown(
    *,
    view_type: str,
    module: str,
    body: str,
    source_paths: List[str],
    contract_records: List[Dict[str, Any]],
    generation_command: str,
    repo_root: Path,
) -> str:
    metadata = build_context_integrity_metadata(
        view_type=view_type,
        module=module,
        generation_command=generation_command,
        source_paths=source_paths,
        contract_records=contract_records,
        repo_root=repo_root,
    )
    return compose_markdown_with_frontmatter("", metadata, body)


def _suggest_docs_refresh(modules: Sequence[str]) -> str:
    normalized = [normalize_module_path(module) for module in modules if str(module or "").strip()]
    if not normalized:
        return "harbor docs --changed --write"
    if len(normalized) == 1:
        return f"harbor docs --module {normalized[0]} --write"
    return "harbor docs --changed --write"


def _normalize_body(text: str) -> str:
    return "\n".join(line.rstrip() for line in str(text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")).strip()


def _repo_display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except Exception:
        return path.as_posix()


def _sanitize_rel_path(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    text = str(value).replace("\\", "/")
    if re_match_absolute_path(text):
        try:
            text = Path(text).resolve().relative_to(Path.cwd().resolve()).as_posix()
        except Exception:
            text = Path(text).name
    return text


def _sanitize_details(details: Dict[str, Any]) -> Dict[str, Any]:
    payload: Dict[str, Any] = {}
    for key, value in (details or {}).items():
        if isinstance(value, str):
            payload[str(key)] = _sanitize_rel_path(value) if "path" in str(key) else value
        elif isinstance(value, list):
            payload[str(key)] = [
                _sanitize_rel_path(item) if isinstance(item, str) and "path" in str(key) else item for item in value
            ]
        else:
            payload[str(key)] = value
    return payload


def re_match_absolute_path(value: str) -> bool:
    text = str(value or "")
    return (":/" in text[:4]) or (":\\" in text[:4]) or text.startswith("/")

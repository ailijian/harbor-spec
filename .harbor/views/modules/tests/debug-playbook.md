---
generated_by: "harbor-spec"
harbor_version: "1.4.5"
view_type: "debug_playbook"
module: "tests"
generated_at: "2026-05-22T08:23:42Z"
generation_command: "harbor module seal tests --write"
stale_policy: "advisory"
source_path_count: 112
source_paths_truncated: false
source_paths:
  - "tests/__init__.py"
  - "tests/conftest.py"
  - "tests/core/test_index_sync_sqlite.py"
  - "tests/core/test_storage_migration.py"
  - "tests/fixtures_sqlite/sample.py"
  - "tests/test_accept_cli.py"
  - "tests/test_adapter_basic.py"
  - "tests/test_adapter_registry.py"
  - "tests/test_adopted_roots.py"
  - "tests/test_audit.py"
  - "tests/test_baseline_artifact.py"
  - "tests/test_cache_isolation_hardening.py"
  - "tests/test_change_window_snapshot.py"
  - "tests/test_changed_scope.py"
  - "tests/test_checkpoint_ci.py"
  - "tests/test_checkpoint_ci_baseline_artifact.py"
  - "tests/test_checkpoint_ci_guidance.py"
  - "tests/test_checkpoint_json_additive_compat.py"
  - "tests/test_ci_mode.py"
  - "tests/test_ci_workflow.py"
  - "tests/test_cli_config.py"
  - "tests/test_cli_decorate.py"
  - "tests/test_cli_docs_modes.py"
  - "tests/test_cli_doctor.py"
  - "tests/test_cli_finish_sync_context.py"
  - "tests/test_cli_help_and_ux.py"
  - "tests/test_cli_i18n.py"
  - "tests/test_cli_i18n_env.py"
  - "tests/test_cli_init_output.py"
  - "tests/test_cli_json_output.py"
  - "tests/test_cli_module_capsule.py"
  - "tests/test_cli_module_capsule_batch.py"
  - "tests/test_cli_module_capsule_stale.py"
  - "tests/test_cli_module_skill.py"
  - "tests/test_cli_progress.py"
  - "tests/test_cli_project_structure.py"
  - "tests/test_cli_stale.py"
  - "tests/test_cli_v2.py"
  - "tests/test_cli_verify_generated.py"
  - "tests/test_cli_workspace_inspect.py"
  - "tests/test_cli_workspace_migrate.py"
  - "tests/test_config_update.py"
  - "tests/test_context_integrity.py"
  - "tests/test_contract_impact.py"
  - "tests/test_contract_presence.py"
  - "tests/test_contract_subject_model.py"
  - "tests/test_ddt_validate.py"
  - "tests/test_ddt_version_baseline.py"
  - "tests/test_decorator_engine.py"
  - "tests/test_derive_adopted_roots.py"
  - "tests/test_diary_workspace_paths.py"
  - "tests/test_doctor.py"
  - "tests/test_drafting.py"
  - "tests/test_drafting_json_parse.py"
  - "tests/test_generated_verify.py"
  - "tests/test_gitignore_prune.py"
  - "tests/test_harbor_next.py"
  - "tests/test_index_builder.py"
  - "tests/test_index_builder_bad_syntax.py"
  - "tests/test_index_builder_registry_integration.py"
  - "tests/test_index_progress.py"
  - "tests/test_init_detector.py"
  - "tests/test_init_governance.py"
  - "tests/test_init_llm_env.py"
  - "tests/test_init_typescript_guidance.py"
  - "tests/test_init_wizard.py"
  - "tests/test_initializer.py"
  - "tests/test_l2_paths.py"
  - "tests/test_lock_flags.py"
  - "tests/test_lock_register_adopted.py"
  - "tests/test_log_draft.py"
  - "tests/test_log_draft_cli.py"
  - "tests/test_log_write_from_draft.py"
  - "tests/test_min_count_one.py"
  - "tests/test_module_capsule.py"
  - "tests/test_module_capsule_stale.py"
  - "tests/test_module_skill.py"
  - "tests/test_performance_baseline.py"
  - "tests/test_project_structure.py"
  - "tests/test_python_adapter_compat.py"
  - "tests/test_python_audit_regression.py"
  - "tests/test_python_contract_source_recognition.py"
  - "tests/test_python_ddt_regression.py"
  - "tests/test_release_packaging.py"
  - "tests/test_repair_guidance.py"
  - "tests/test_semantic_audit_contract_gap.py"
  - "tests/test_semantic_audit_preview.py"
  - "tests/test_stale.py"
  - "tests/test_sync_engine.py"
  - "tests/test_sync_engine_registry_integration.py"
  - "tests/test_typescript_adapter_mvp.py"
  - "tests/test_typescript_boundary_resolution_paths.py"
  - "tests/test_typescript_checkpoint_ci.py"
  - "tests/test_typescript_contract_presence.py"
  - "tests/test_typescript_ddt_preview.py"
  - "tests/test_typescript_next_guidance.py"
  - "tests/test_typescript_not_supported_boundaries.py"
  - "tests/test_typescript_package_exports.py"
  - "tests/test_typescript_preview_productization_assets.py"
  - "tests/test_typescript_public_boundary_evidence.py"
  - "tests/test_typescript_public_boundary_next.py"
  - "tests/test_typescript_public_boundary_presets.py"
  - "tests/test_typescript_re_export_resolver.py"
  - "tests/test_utils_format.py"
  - "tests/test_verification_foundation.py"
  - "tests/test_windows_abs_path_prefix.py"
  - "tests/test_windows_json_stdio_regression.py"
  - "tests/test_workspace_gitignore_policy.py"
  - "tests/test_workspace_i18n.py"
  - "tests/test_workspace_inspect.py"
  - "tests/test_workspace_migrate.py"
  - "tests/test_workspace_paths.py"
source_fingerprint: "sha256:8b890a35c2a2a674a72a2a195863142b2eff86e5ef530d6294cbc8283d5f79d4"
contract_fingerprint: "sha256:f082d0580080a4d15492c7177e584fe4523f61a08ae69f289f67a1fc22dadeb9"
generator_fingerprint: "sha256:65ccddc1bc55583c079e9298ea5bae682ed823de056cc87d2d5a103de17b5441"
---

# Debug Playbook: tests

> This file is generated by Harbor-spec.
> It is a derived debug guide, not a source of truth.

## First Files to Inspect

- tests/fixtures_sqlite/sample.py (indexed contracts, strict target)
- tests/core/test_index_sync_sqlite.py (indexed contracts, covered by matching tests)
- tests/core/test_storage_migration.py (indexed contracts, covered by matching tests)

## Minimal Checks

Run targeted tests first if available.

```powershell
pytest tests/test_change_window_snapshot.py
pytest tests/test_checkpoint_ci_guidance.py
pytest tests/test_cli_finish_sync_context.py
```

## Why These Tests

- tests/test_change_window_snapshot.py (file-name match, imports target symbols)
- tests/test_checkpoint_ci_guidance.py (file-name match, imports target symbols)
- tests/test_cli_finish_sync_context.py (file-name match, imports target symbols)

## Common Debug Questions

* What changed since the last passing state?
* Did Contract Impact occur?
* Did schema/type shape change?
* Did a strict target lose DDT coverage?
* Did implementation drift from docstring or schema?
* Did path normalization or platform-specific behavior change?
* Did the fix require a regression test?

## Safe Fix Order

1. Reproduce the issue.
2. Identify relevant contract and schema.
3. Add or update failing test if possible.
4. Fix implementation.
5. Re-run targeted tests.
6. Check semantic drift.
7. Draft Diary entry if the fix is important.

## When to Escalate

Escalate to full Harbor workflow if the fix touches:

* public API
* schema
* parser/export/writeback
* workflow
* migration
* security
* user-visible behavior

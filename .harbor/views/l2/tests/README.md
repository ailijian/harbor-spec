---
generated_by: "harbor-spec"
harbor_version: "1.4.1"
view_type: "l2_readme"
module: "tests"
generated_at: "2026-05-12T11:48:59Z"
generation_command: "harbor docs --module tests --write"
stale_policy: "advisory"
source_path_count: 90
source_paths_truncated: false
source_paths:
  - "tests/__init__.py"
  - "tests/conftest.py"
  - "tests/core/test_index_sync_sqlite.py"
  - "tests/core/test_storage_migration.py"
  - "tests/fixtures_sqlite/sample.py"
  - "tests/test_adapter_basic.py"
  - "tests/test_adapter_registry.py"
  - "tests/test_adopted_roots.py"
  - "tests/test_audit.py"
  - "tests/test_cache_isolation_hardening.py"
  - "tests/test_change_window_snapshot.py"
  - "tests/test_checkpoint_ci.py"
  - "tests/test_checkpoint_ci_guidance.py"
  - "tests/test_checkpoint_json_additive_compat.py"
  - "tests/test_ci_mode.py"
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
  - "tests/test_cli_project_structure.py"
  - "tests/test_cli_stale.py"
  - "tests/test_cli_v2.py"
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
  - "tests/test_gitignore_prune.py"
  - "tests/test_harbor_next.py"
  - "tests/test_index_builder.py"
  - "tests/test_index_builder_bad_syntax.py"
  - "tests/test_index_builder_registry_integration.py"
  - "tests/test_index_progress.py"
  - "tests/test_init_detector.py"
  - "tests/test_init_governance.py"
  - "tests/test_init_llm_env.py"
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
  - "tests/test_project_structure.py"
  - "tests/test_python_adapter_compat.py"
  - "tests/test_python_audit_regression.py"
  - "tests/test_python_ddt_regression.py"
  - "tests/test_release_packaging.py"
  - "tests/test_repair_guidance.py"
  - "tests/test_semantic_audit_contract_gap.py"
  - "tests/test_stale.py"
  - "tests/test_sync_engine.py"
  - "tests/test_sync_engine_registry_integration.py"
  - "tests/test_typescript_adapter_mvp.py"
  - "tests/test_typescript_checkpoint_ci.py"
  - "tests/test_typescript_contract_presence.py"
  - "tests/test_typescript_next_guidance.py"
  - "tests/test_typescript_not_supported_boundaries.py"
  - "tests/test_utils_format.py"
  - "tests/test_windows_abs_path_prefix.py"
  - "tests/test_workspace_gitignore_policy.py"
  - "tests/test_workspace_i18n.py"
  - "tests/test_workspace_inspect.py"
  - "tests/test_workspace_migrate.py"
  - "tests/test_workspace_paths.py"
source_fingerprint: "sha256:a64164e2e3128d057348c5ba4014bc04eb5564e4ab3a70172c1b41548809563c"
contract_fingerprint: "sha256:2db1525ce451a31cff08c3376c6d3bf24e4096dc166ae722ad75b357ca09edd2"
generator_fingerprint: "sha256:49c406651f0550ace951edd5aae0f6a03ed8d94240c13ad846bb5e6a31da5ae5"
---

# Module: tests

## Public API
| Function | Summary | Strictness | DDT Status |
|---|---|---|---|
| tests.fixtures_sqlite.sample.func1 | 测试函数。 | strict | ❌ Missing |

## Internal Details (optional)
<details>
<summary>Internal functions</summary>

| Function | Summary | Strictness | DDT Status |
|---|---|---|---|
| tests.test_change_window_snapshot._FakeSyncEngine.__init__ | — | standard | ⚪ Missing |
| tests.test_ddt_version_baseline._build_strict_target | — | standard | ⚪ Missing |
| tests.test_typescript_checkpoint_ci._checkpoint_payload | — | standard | ⚪ Missing |
| tests.test_cli_v2._clean_status_report | — | standard | ⚪ Missing |
| tests.test_change_window_snapshot._configure_accept_cli | — | standard | ⚪ Missing |
| tests.test_change_window_snapshot._configure_finish_cli | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci._contract_report | — | standard | ⚪ Missing |
| tests.test_checkpoint_json_additive_compat._contract_report | — | standard | ⚪ Missing |
| tests.test_change_window_snapshot._contract_report | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci._ddt_report | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci_guidance._ddt_report | — | standard | ⚪ Missing |
| tests.test_checkpoint_json_additive_compat._ddt_report | — | standard | ⚪ Missing |
| tests.test_change_window_snapshot._ddt_report | — | standard | ⚪ Missing |
| tests.test_cli_finish_sync_context._disable_change_window_writes | — | standard | ⚪ Missing |
| tests.test_ci_mode._disable_change_window_writes | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci._disable_change_window_writes | — | standard | ⚪ Missing |
| tests.test_typescript_checkpoint_ci._empty_contract_report | — | standard | ⚪ Missing |
| tests.test_typescript_not_supported_boundaries._empty_contract_report | — | standard | ⚪ Missing |
| tests.test_typescript_checkpoint_ci._empty_ddt_report | — | standard | ⚪ Missing |
| tests.test_typescript_not_supported_boundaries._empty_ddt_report | — | standard | ⚪ Missing |
| tests.test_cli_doctor._empty_status_report | — | standard | ⚪ Missing |
| tests.test_cli_finish_sync_context._empty_status_report | — | standard | ⚪ Missing |
| tests.test_cli_module_capsule_stale._empty_status_report | — | standard | ⚪ Missing |
| tests.test_cli_stale._empty_status_report | — | standard | ⚪ Missing |
| tests.test_cli_docs_modes._empty_status_report | — | standard | ⚪ Missing |
| tests.test_cli_module_capsule_batch._empty_status_report | — | standard | ⚪ Missing |
| tests.test_doctor._empty_status_report | — | standard | ⚪ Missing |
| tests.test_cli_finish_sync_context._empty_validation_report | — | standard | ⚪ Missing |
| tests.test_cli_v2._empty_validation_report | — | standard | ⚪ Missing |
| tests.test_contract_presence._fc | — | standard | ⚪ Missing |
| tests.test_cache_isolation_hardening._fingerprint | — | standard | ⚪ Missing |
| tests.test_workspace_migrate._fingerprint_tree | — | standard | ⚪ Missing |
| tests.test_typescript_contract_presence._fixture_root | — | standard | ⚪ Missing |
| tests.test_typescript_adapter_mvp._fixture_root | — | standard | ⚪ Missing |
| tests.test_cli_help_and_ux._force_en_locale | — | standard | ⚪ Missing |
| tests.test_cli_doctor._force_en_locale | — | standard | ⚪ Missing |
| tests.test_cli_module_capsule._force_en_locale | — | standard | ⚪ Missing |
| tests.test_cli_module_skill._force_en_locale | — | standard | ⚪ Missing |
| tests.test_cli_finish_sync_context._force_en_locale | — | standard | ⚪ Missing |
| tests.test_cli_module_capsule_stale._force_en_locale | — | standard | ⚪ Missing |
| tests.test_cli_json_output._force_en_locale | — | standard | ⚪ Missing |
| tests.test_cli_project_structure._force_en_locale | — | standard | ⚪ Missing |
| tests.test_cli_stale._force_en_locale | — | standard | ⚪ Missing |
| tests.test_cli_docs_modes._force_en_locale | — | standard | ⚪ Missing |
| tests.test_cli_module_capsule_batch._force_en_locale | — | standard | ⚪ Missing |
| tests.test_cli_v2._force_en_locale | — | standard | ⚪ Missing |
| tests.test_release_packaging._force_en_locale | — | standard | ⚪ Missing |
| tests.test_doctor._force_en_locale | — | standard | ⚪ Missing |
| tests.test_cli_workspace_migrate._force_en_locale | — | standard | ⚪ Missing |
| tests.test_workspace_inspect._force_en_locale | — | standard | ⚪ Missing |
| tests.test_workspace_migrate._force_en_locale | — | standard | ⚪ Missing |
| tests.test_cli_workspace_inspect._force_en_locale | — | standard | ⚪ Missing |
| tests.test_ci_mode._force_en_locale | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci._force_en_locale | — | standard | ⚪ Missing |
| tests.test_log_draft._force_en_locale | — | standard | ⚪ Missing |
| tests.test_log_draft_cli._force_en_locale | — | standard | ⚪ Missing |
| tests.test_log_write_from_draft._force_en_locale | — | standard | ⚪ Missing |
| tests.test_workspace_gitignore_policy._gitignore_entries | — | standard | ⚪ Missing |
| tests.test_change_window_snapshot._init_git_repo | — | standard | ⚪ Missing |
| tests.test_workspace_gitignore_policy._is_ignored | — | standard | ⚪ Missing |
| tests.conftest._isolate_harbor_language_env | 避免外部 CI/发布环境变量污染测试语言分支。 | standard | ⚪ Missing |
| tests.test_cli_v2._isolate_workspace | — | standard | ⚪ Missing |
| tests.test_log_draft_cli._isolate_workspace | — | standard | ⚪ Missing |
| tests.test_log_write_from_draft._isolate_workspace | — | standard | ⚪ Missing |
| tests.test_diary_workspace_paths._month_pair | — | standard | ⚪ Missing |
| tests.test_drafting_json_parse._parse | — | standard | ⚪ Missing |
| tests.test_cli_doctor._pass_report | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci._patch_checkpoint_inputs | — | standard | ⚪ Missing |
| tests.test_cli_finish_sync_context._patch_finish_basics | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci_guidance._patch_inputs | — | standard | ⚪ Missing |
| tests.test_lock_flags._prepare_proj | — | standard | ⚪ Missing |
| tests.test_log_write_from_draft._read_last_marker | — | standard | ⚪ Missing |
| tests.test_change_window_snapshot._read_runtime_diagnostics | — | standard | ⚪ Missing |
| tests.test_log_write_from_draft._read_single_diary_entry | — | standard | ⚪ Missing |
| tests.test_drafting._rep_with | — | standard | ⚪ Missing |
| tests.test_release_packaging._repo_root | — | standard | ⚪ Missing |
| tests.test_workspace_gitignore_policy._repo_root | — | standard | ⚪ Missing |
| tests.test_change_window_snapshot._run_cli | — | standard | ⚪ Missing |
| tests.test_cache_isolation_hardening._run_cmd | — | standard | ⚪ Missing |
| tests.test_diary_workspace_paths._run_cmd | — | standard | ⚪ Missing |
| tests.test_change_window_snapshot._run_git | — | standard | ⚪ Missing |
| tests.test_release_packaging._run_help | — | standard | ⚪ Missing |
| tests.test_python_adapter_compat._sample_contract | — | standard | ⚪ Missing |
| tests.test_cli_json_output._sample_doctor_report | — | standard | ⚪ Missing |
| tests.test_log_write_from_draft._sample_draft_payload | — | standard | ⚪ Missing |
| tests.test_cli_json_output._sample_stale_summary | — | standard | ⚪ Missing |
| tests.test_cli_stale._sample_summary | — | standard | ⚪ Missing |
| tests.test_doctor._sample_summary | — | standard | ⚪ Missing |
| tests.test_log_draft_cli._seed_draft_evidence | — | standard | ⚪ Missing |
| tests.test_cache_isolation_hardening._snapshot_repo_cache | — | standard | ⚪ Missing |
| tests.test_ci_mode._stale_summary | — | standard | ⚪ Missing |
| tests.test_init_governance._starter_targets | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci._status_entry | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci_guidance._status_entry | — | standard | ⚪ Missing |
| tests.test_checkpoint_json_additive_compat._status_entry | — | standard | ⚪ Missing |
| tests.test_change_window_snapshot._status_entry | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci._status_report | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci_guidance._status_report | — | standard | ⚪ Missing |
| tests.test_checkpoint_json_additive_compat._status_report | — | standard | ⚪ Missing |
| tests.test_change_window_snapshot._status_report | — | standard | ⚪ Missing |
| tests.test_cli_finish_sync_context._status_report_with_changed | — | standard | ⚪ Missing |
| tests.test_typescript_contract_presence._subject_by_name | — | standard | ⚪ Missing |
| tests.test_typescript_adapter_mvp._to_rel | — | standard | ⚪ Missing |
| tests.test_workspace_inspect._touch | — | standard | ⚪ Missing |
| tests.test_workspace_migrate._touch | — | standard | ⚪ Missing |
| tests.test_sync_engine_registry_integration._write | — | standard | ⚪ Missing |
| tests.test_typescript_checkpoint_ci._write | — | standard | ⚪ Missing |
| tests.test_python_ddt_regression._write | — | standard | ⚪ Missing |
| tests.test_index_builder_registry_integration._write_config | — | standard | ⚪ Missing |
| tests.test_sync_engine_registry_integration._write_config | — | standard | ⚪ Missing |
| tests.test_typescript_checkpoint_ci._write_config | — | standard | ⚪ Missing |
| tests.test_index_builder_registry_integration._write_file | — | standard | ⚪ Missing |
| tests.test_cli_module_capsule._write_index | — | standard | ⚪ Missing |
| tests.test_cli_module_skill._write_index | — | standard | ⚪ Missing |
| tests.test_cli_module_capsule_stale._write_index | — | standard | ⚪ Missing |
| tests.test_cli_project_structure._write_index | — | standard | ⚪ Missing |
| tests.test_cli_module_capsule_batch._write_index | — | standard | ⚪ Missing |
| tests.test_module_skill._write_index | — | standard | ⚪ Missing |
| tests.test_module_capsule_stale._write_index | — | standard | ⚪ Missing |
| tests.test_module_capsule._write_index | — | standard | ⚪ Missing |
| tests.test_project_structure._write_index | — | standard | ⚪ Missing |
| tests.test_stale._write_index | — | standard | ⚪ Missing |
| tests.test_log_write_from_draft._write_json_draft | — | standard | ⚪ Missing |
| tests.test_stale._write_l2_export_config | — | standard | ⚪ Missing |
| tests.test_log_draft._write_latest_json_draft | — | standard | ⚪ Missing |
| tests.test_log_write_from_draft._write_markdown_draft | — | standard | ⚪ Missing |
| tests.test_typescript_next_guidance._write_report | — | standard | ⚪ Missing |
| tests.test_log_draft._write_report | — | standard | ⚪ Missing |
| tests.test_log_draft_cli._write_report | — | standard | ⚪ Missing |
| tests.test_log_draft._write_snapshot | — | standard | ⚪ Missing |
| tests.test_log_draft_cli._write_snapshot | — | standard | ⚪ Missing |
| tests.test_cli_project_structure._write_workspace_config | — | standard | ⚪ Missing |
| tests.test_cli_module_capsule_batch._write_workspace_config | — | standard | ⚪ Missing |
| tests.test_diary_workspace_paths._write_workspace_config | — | standard | ⚪ Missing |
| tests.test_workspace_inspect._write_workspace_config | — | standard | ⚪ Missing |
| tests.test_workspace_migrate._write_workspace_config | — | standard | ⚪ Missing |
| tests.test_cli_workspace_migrate._write_workspace_fixture | — | standard | ⚪ Missing |
| tests.test_cli_workspace_inspect._write_workspace_fixture | — | standard | ⚪ Missing |
| tests.test_workspace_i18n._write_workspace_fixture | — | standard | ⚪ Missing |
| tests.test_l2_paths._write_yaml | — | standard | ⚪ Missing |
| tests.test_workspace_paths._write_yaml | — | standard | ⚪ Missing |
| tests.test_drafting._EngStub.check_status | — | standard | ⚪ Missing |
| tests.test_change_window_snapshot._FakeSyncEngine.check_status | — | standard | ⚪ Missing |
| tests.test_drafting._OKProvider.infer | — | standard | ⚪ Missing |
| tests.test_semantic_audit_contract_gap._ShouldNotCallProvider.infer | — | standard | ⚪ Missing |
| tests.test_index_builder.read_index | — | standard | ⚪ Missing |
| tests.test_cli_help_and_ux.run_cmd | — | standard | ⚪ Missing |
| tests.test_cli_i18n.run_cmd | — | standard | ⚪ Missing |
| tests.test_cli_i18n_env.run_cmd | — | standard | ⚪ Missing |
| tests.test_cli_doctor.run_cmd | — | standard | ⚪ Missing |
| tests.test_cli_init_output.run_cmd | — | standard | ⚪ Missing |
| tests.test_cli_module_capsule.run_cmd | — | standard | ⚪ Missing |
| tests.test_cli_module_skill.run_cmd | — | standard | ⚪ Missing |
| tests.test_cli_finish_sync_context.run_cmd | — | standard | ⚪ Missing |
| tests.test_cli_module_capsule_stale.run_cmd | — | standard | ⚪ Missing |
| tests.test_cli_json_output.run_cmd | — | standard | ⚪ Missing |
| tests.test_cli_project_structure.run_cmd | — | standard | ⚪ Missing |
| tests.test_cli_stale.run_cmd | — | standard | ⚪ Missing |
| tests.test_cli_docs_modes.run_cmd | — | standard | ⚪ Missing |
| tests.test_cli_module_capsule_batch.run_cmd | — | standard | ⚪ Missing |
| tests.test_cli_v2.run_cmd | — | standard | ⚪ Missing |
| tests.test_cli_workspace_migrate.run_cmd | — | standard | ⚪ Missing |
| tests.test_cli_workspace_inspect.run_cmd | — | standard | ⚪ Missing |
| tests.test_ci_mode.run_cmd | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci.run_cmd | — | standard | ⚪ Missing |
| tests.test_init_governance.run_cmd | — | standard | ⚪ Missing |
| tests.test_workspace_i18n.run_cmd | — | standard | ⚪ Missing |
| tests.test_harbor_next.run_cmd | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci_guidance.run_cmd | — | standard | ⚪ Missing |
| tests.test_typescript_next_guidance.run_cmd | — | standard | ⚪ Missing |
| tests.test_log_draft_cli.run_cmd | — | standard | ⚪ Missing |
| tests.test_log_write_from_draft.run_cmd | — | standard | ⚪ Missing |
| tests.test_cli_i18n_env.run_cmd_with_code | — | standard | ⚪ Missing |
| tests.test_cli_i18n.run_cmd_with_err | — | standard | ⚪ Missing |
| tests.test_cli_doctor.run_cmd_with_err | — | standard | ⚪ Missing |
| tests.test_cli_json_output.run_cmd_with_err | — | standard | ⚪ Missing |
| tests.test_cli_workspace_migrate.run_cmd_with_err | — | standard | ⚪ Missing |
| tests.test_cli_workspace_inspect.run_cmd_with_err | — | standard | ⚪ Missing |
| tests.test_cli_help_and_ux.run_help | — | standard | ⚪ Missing |
| tests.test_change_window_snapshot._FakeDDTScanner.scan_tests | — | standard | ⚪ Missing |
| tests.test_change_window_snapshot.test_accept_and_finish_invoke_snapshot_events | — | standard | ⚪ Missing |
| tests.test_cli_v2.test_accept_maps_to_lock_logic | — | standard | ⚪ Missing |
| tests.test_change_window_snapshot.test_accept_snapshot_write_failure_does_not_change_exit_code | — | standard | ⚪ Missing |
| tests.test_change_window_snapshot.test_accept_writes_accept_snapshot_and_can_be_read | — | standard | ⚪ Missing |
| tests.test_adapter_basic.test_adapter_parses_itself | — | standard | ⚪ Missing |
| tests.test_adopted_roots.test_adopted_roots_write_and_remove | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci_guidance.test_advice_off_removes_guidance_field | — | standard | ⚪ Missing |
| tests.test_decorator_engine.test_aggressive_inserts_todo_docstring | — | standard | ⚪ Missing |
| tests.test_log_draft.test_auto_discovery_skips_non_utf8_reports | — | standard | ⚪ Missing |
| tests.test_change_window_snapshot.test_bad_json_snapshot_is_skipped_with_warning | — | standard | ⚪ Missing |
| tests.test_log_draft.test_bad_snapshot_json_is_skipped_without_crashing | — | standard | ⚪ Missing |
| tests.test_log_draft.test_build_diary_draft_classifies_diary_paths_separately | — | standard | ⚪ Missing |
| tests.test_log_draft.test_build_diary_draft_collects_required_fields_and_evidence | — | standard | ⚪ Missing |
| tests.test_log_draft.test_build_diary_draft_does_not_modify_existing_last_log_marker | — | standard | ⚪ Missing |
| tests.test_doctor.test_build_doctor_report_is_read_only | — | standard | ⚪ Missing |
| tests.test_index_builder_registry_integration.test_build_keeps_python_entry_shape_stable | — | standard | ⚪ Missing |
| tests.test_log_draft.test_build_saved_diary_draft_output_path_uses_reports_root_and_format | — | standard | ⚪ Missing |
| tests.test_cli_i18n.test_canonical_config_language_wins_over_legacy | — | standard | ⚪ Missing |
| tests.test_module_capsule_stale.test_capsule_stale_uses_view_fingerprint_not_source_fingerprint | — | standard | ⚪ Missing |
| tests.test_cli_docs_modes.test_changed_modules_detect_and_generate_each | — | standard | ⚪ Missing |
| tests.test_module_skill.test_check_capsule_ready_legacy_exists_but_canonical_missing | — | standard | ⚪ Missing |
| tests.test_module_skill.test_check_capsule_ready_missing_capsule | — | standard | ⚪ Missing |
| tests.test_module_skill.test_check_capsule_ready_stale_capsule | — | standard | ⚪ Missing |
| tests.test_module_skill.test_check_capsule_ready_unknown_module | — | standard | ⚪ Missing |
| tests.test_cli_v2.test_check_ddt_baseline_missing_default_aggregated | — | standard | ⚪ Missing |
| tests.test_cli_v2.test_check_ddt_baseline_missing_verbose_lists_bindings | — | standard | ⚪ Missing |
| tests.test_workspace_inspect.test_check_git_ignored_directory_rule_uses_nested_probe | — | standard | ⚪ Missing |
| tests.test_stale.test_check_module_derived_views_stale_returns_both_views | — | standard | ⚪ Missing |
| tests.test_stale.test_check_module_derived_views_stale_unknown_consistency_when_no_indexed_records | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci.test_checkpoint_ci_contract_parse_error_blocks | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci.test_checkpoint_ci_ddt_baseline_missing_stays_advisory_not_failure | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci.test_checkpoint_ci_dedupe_prefers_contract_and_body_changed_over_confirmed_contract_impact | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci.test_checkpoint_ci_dedupe_prefers_contract_changed_over_confirmed_contract_impact | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci.test_checkpoint_ci_does_not_fail_on_possible_contract_impact_alone | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci.test_checkpoint_ci_fail_on_body_changed_contract_static | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci.test_checkpoint_ci_fail_on_confirmed_contract_impact | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci.test_checkpoint_ci_fail_on_contract_changed | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci.test_checkpoint_ci_fail_on_contract_gap | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci.test_checkpoint_ci_fail_on_missing_function | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci.test_checkpoint_ci_fail_on_untracked_function | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci.test_checkpoint_ci_failure_dedupe_keeps_readable_ci_failures | — | standard | ⚪ Missing |
| tests.test_cli_v2.test_checkpoint_ci_json_advisory_unchanged_with_advice_modes | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci.test_checkpoint_ci_json_includes_ddt_baseline_missing_advisory_without_blocking | — | standard | ⚪ Missing |
| tests.test_cli_v2.test_checkpoint_ci_json_recognized | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci.test_checkpoint_ci_json_single_object_and_required_fields | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci.test_checkpoint_ci_keeps_confirmed_contract_impact_when_no_status_failure_covers_target | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci.test_checkpoint_ci_no_write_regression | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci.test_checkpoint_ci_pass_when_clean | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci.test_checkpoint_ci_skipped_no_contract_is_advisory | — | standard | ⚪ Missing |
| tests.test_change_window_snapshot.test_checkpoint_ci_snapshot_write_failure_does_not_change_exit_code | — | standard | ⚪ Missing |
| tests.test_change_window_snapshot.test_checkpoint_ci_writes_snapshot_without_changing_pass_semantics | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci.test_checkpoint_ci_zh_text_labels | — | standard | ⚪ Missing |
| tests.test_cli_v2.test_checkpoint_command_recognized | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci.test_checkpoint_default_behavior_unchanged | — | standard | ⚪ Missing |
| tests.test_cli_v2.test_checkpoint_does_not_trigger_semantic_audit | — | standard | ⚪ Missing |
| tests.test_cli_i18n.test_checkpoint_format_error_uses_zh_i18n | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci.test_checkpoint_format_json_requires_ci_mode | — | standard | ⚪ Missing |
| tests.test_checkpoint_json_additive_compat.test_checkpoint_json_additive_shape_is_stable_for_golden_assert | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci_guidance.test_checkpoint_json_output_is_single_json_object | — | standard | ⚪ Missing |
| tests.test_cli_v2.test_checkpoint_prints_contract_impact_summary_when_dirty | — | standard | ⚪ Missing |
| tests.test_cli_json_output.test_ci_json_fields_use_ci_failures_and_advisory | — | standard | ⚪ Missing |
| tests.test_cli_json_output.test_ci_json_stdout_is_single_object | — | standard | ⚪ Missing |
| tests.test_ci_mode.test_ci_mode_i18n_labels_follow_language | — | standard | ⚪ Missing |
| tests.test_ci_mode.test_ci_mode_no_write_regression | — | standard | ⚪ Missing |
| tests.test_ci_mode.test_ci_next_steps_excludes_accept_log_lock | — | standard | ⚪ Missing |
| tests.test_project_structure.test_classify_project_area_is_stable | — | standard | ⚪ Missing |
| tests.test_cli_decorate.test_cli_dry_run_preview_counts | — | standard | ⚪ Missing |
| tests.test_diary_workspace_paths.test_cli_log_message_accepts_supported_legacy_types_in_isolated_workspace | — | standard | ⚪ Missing |
| tests.test_contract_impact.test_cli_main_change_is_possible_with_cli_categories | — | standard | ⚪ Missing |
| tests.test_cache_isolation_hardening.test_cli_status_writes_cache_in_tmp_workspace_only | — | standard | ⚪ Missing |
| tests.test_cli_workspace_inspect.test_cli_workspace_inspect_invalid_format_returns_argparse_error | — | standard | ⚪ Missing |
| tests.test_cli_workspace_inspect.test_cli_workspace_inspect_json_single_object_and_expected_keys | — | standard | ⚪ Missing |
| tests.test_cli_workspace_inspect.test_cli_workspace_inspect_no_write_regression | — | standard | ⚪ Missing |
| tests.test_cli_workspace_inspect.test_cli_workspace_inspect_text_exits_0_and_contains_sections | — | standard | ⚪ Missing |
| tests.test_cli_workspace_migrate.test_cli_workspace_migrate_invalid_format_argparse_error | — | standard | ⚪ Missing |
| tests.test_cli_workspace_migrate.test_cli_workspace_migrate_json_single_object | — | standard | ⚪ Missing |
| tests.test_cli_workspace_migrate.test_cli_workspace_migrate_no_write_regression | — | standard | ⚪ Missing |
| tests.test_cli_workspace_migrate.test_cli_workspace_migrate_text_exit_0_and_contains_required_lines | — | standard | ⚪ Missing |
| tests.test_cli_workspace_migrate.test_cli_workspace_migrate_without_dry_run_fails | — | standard | ⚪ Missing |
| tests.test_cli_docs_modes.test_collect_all_indexed_modules_from_index_records | — | standard | ⚪ Missing |
| tests.test_cli_docs_modes.test_collect_all_indexed_modules_normalizes_repo_absolute_file_paths | — | standard | ⚪ Missing |
| tests.test_module_capsule.test_collect_module_context_matches_prefix_only | — | standard | ⚪ Missing |
| tests.test_doctor.test_collect_next_steps_filters_high_impact_commands | — | standard | ⚪ Missing |
| tests.test_project_structure.test_collect_project_structure_context_builds_expected_flags_and_counts | — | standard | ⚪ Missing |
| tests.test_project_structure.test_collect_project_structure_context_filters_windows_absolute_paths_on_posix | — | standard | ⚪ Missing |
| tests.test_project_structure.test_collect_project_structure_context_uses_filesystem_fallback_when_index_missing | — | standard | ⚪ Missing |
| tests.test_project_structure.test_collect_project_structure_reads_metadata_from_pyproject | — | standard | ⚪ Missing |
| tests.test_cli_v2.test_commit_alias_unchanged_maps_to_lock | — | standard | ⚪ Missing |
| tests.test_module_capsule_stale.test_compute_module_fingerprint_is_stable_and_normalized | — | standard | ⚪ Missing |
| tests.test_cli_config.test_config_add_list_remove | — | standard | ⚪ Missing |
| tests.test_adapter_registry.test_config_can_disable_python | — | standard | ⚪ Missing |
| tests.test_cli_i18n.test_config_list_zh | — | standard | ⚪ Missing |
| tests.test_diary_workspace_paths.test_configured_diary_root_within_repo_is_used | — | standard | ⚪ Missing |
| tests.test_init_wizard.test_confirm_accepts_chinese_yes_no | — | standard | ⚪ Missing |
| tests.test_init_wizard.test_confirm_accepts_english_yes_no | — | standard | ⚪ Missing |
| tests.test_init_wizard.test_confirm_shows_yes_no_labels_by_language | — | standard | ⚪ Missing |
| tests.test_context_integrity.test_content_without_generated_at_for_compare_ignores_only_timestamp | — | standard | ⚪ Missing |
| tests.test_repair_guidance.test_contract_gap_guidance_defaults | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci_guidance.test_contract_gap_guidance_in_checkpoint_json | — | standard | ⚪ Missing |
| tests.test_contract_subject_model.test_contract_source_fingerprint_changes_on_text_change | — | standard | ⚪ Missing |
| tests.test_contract_subject_model.test_contract_source_fingerprint_is_stable_for_same_text | — | standard | ⚪ Missing |
| tests.test_contract_subject_model.test_contract_subject_min_serialization_is_stable | — | standard | ⚪ Missing |
| tests.test_contract_subject_model.test_contract_subject_required_fields_are_present | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci_guidance.test_ddt_baseline_missing_is_advisory_with_guidance | — | standard | ⚪ Missing |
| tests.test_cli_v2.test_ddt_validate_maps_to_check_fast | — | standard | ⚪ Missing |
| tests.test_ddt_validate.test_ddt_validate_matrix | — | standard | ⚪ Missing |
| tests.test_repair_guidance.test_ddt_version_baseline_missing_guidance_is_manual | — | standard | ⚪ Missing |
| tests.test_cli_v2.test_decorate_maps_to_adopt_dry_run | — | standard | ⚪ Missing |
| tests.test_log_draft.test_default_log_draft_falls_back_to_latest_accept_when_marker_missing | — | standard | ⚪ Missing |
| tests.test_log_draft.test_default_log_draft_falls_back_to_recent_when_marker_and_accept_are_missing | — | standard | ⚪ Missing |
| tests.test_log_draft.test_default_log_draft_prefers_last_log_marker_boundary | — | standard | ⚪ Missing |
| tests.test_workspace_paths.test_default_paths | — | standard | ⚪ Missing |
| tests.test_adapter_registry.test_default_registry_disables_typescript | — | standard | ⚪ Missing |
| tests.test_adapter_registry.test_default_registry_enables_python | — | standard | ⚪ Missing |
| tests.test_cli_json_output.test_default_text_output_for_stale_and_doctor_is_unchanged | — | standard | ⚪ Missing |
| tests.test_derive_adopted_roots.test_derive_adopted_roots_basic | — | standard | ⚪ Missing |
| tests.test_doctor.test_derived_views_check_legacy_diary_coexistence_single_advisory_and_no_mutation | — | standard | ⚪ Missing |
| tests.test_doctor.test_derived_views_check_legacy_diary_empty_dir_no_warning | — | standard | ⚪ Missing |
| tests.test_doctor.test_derived_views_check_marks_unknown_detail_as_unknown_not_stale | — | standard | ⚪ Missing |
| tests.test_doctor.test_derived_views_check_reuses_stale_results | — | standard | ⚪ Missing |
| tests.test_doctor.test_derived_views_check_shows_disabled_without_counting_warn | — | standard | ⚪ Missing |
| tests.test_doctor.test_derived_views_check_warns_for_legacy_diary_jsonl | — | standard | ⚪ Missing |
| tests.test_doctor.test_derived_views_check_warns_for_legacy_metadata_but_never_fail | — | standard | ⚪ Missing |
| tests.test_doctor.test_derived_views_check_warns_when_frontmatter_missing | — | standard | ⚪ Missing |
| tests.test_initializer.test_detect_fallback | — | standard | ⚪ Missing |
| tests.test_initializer.test_detect_package_layout | — | standard | ⚪ Missing |
| tests.test_initializer.test_detect_script_layout | — | standard | ⚪ Missing |
| tests.test_initializer.test_detect_src_layout | — | standard | ⚪ Missing |
| tests.test_cli_v2.test_diary_export_maps_to_log_export | — | standard | ⚪ Missing |
| tests.test_log_draft.test_diary_only_changed_files_are_insufficient_for_writable_draft | — | standard | ⚪ Missing |
| tests.test_typescript_adapter_mvp.test_discover_files_default_excludes_standard_build_directories | — | standard | ⚪ Missing |
| tests.test_typescript_adapter_mvp.test_discover_files_default_excludes_tsx_js_jsx_dts | — | standard | ⚪ Missing |
| tests.test_typescript_adapter_mvp.test_discover_files_default_only_ts | — | standard | ⚪ Missing |
| tests.test_init_detector.test_django_detection | — | standard | ⚪ Missing |
| tests.test_cache_isolation_hardening.test_docs_all_external_only_index_is_isolated | — | standard | ⚪ Missing |
| tests.test_cli_docs_modes.test_docs_all_preview_does_not_write | — | standard | ⚪ Missing |
| tests.test_cli_docs_modes.test_docs_all_write_only_unsafe_modules_returns_zero_and_does_not_write | — | standard | ⚪ Missing |
| tests.test_cli_docs_modes.test_docs_all_write_skips_unsafe_indexed_modules_and_continues | — | standard | ⚪ Missing |
| tests.test_cli_docs_modes.test_docs_all_write_supports_repo_absolute_file_candidate | — | standard | ⚪ Missing |
| tests.test_cli_docs_modes.test_docs_all_write_updates_each_module | — | standard | ⚪ Missing |
| tests.test_cli_docs_modes.test_docs_changed_and_all_args_are_recognized | — | standard | ⚪ Missing |
| tests.test_cli_docs_modes.test_docs_changed_write_skips_external_changed_module_and_writes_safe | — | standard | ⚪ Missing |
| tests.test_workspace_gitignore_policy.test_docs_design_paths_are_trackable | — | standard | ⚪ Missing |
| tests.test_workspace_gitignore_policy.test_docs_harbor_project_structure_remains_non_canonical_export_target | — | standard | ⚪ Missing |
| tests.test_cli_help_and_ux.test_docs_help_lists_changed_all_and_write_flags | — | standard | ⚪ Missing |
| tests.test_cli_docs_modes.test_docs_mode_flags_are_mutually_exclusive | — | standard | ⚪ Missing |
| tests.test_cli_help_and_ux.test_docs_modes_error_message_is_friendly_and_clear | — | standard | ⚪ Missing |
| tests.test_cli_docs_modes.test_docs_module_mode_still_works | — | standard | ⚪ Missing |
| tests.test_cli_docs_modes.test_docs_module_write_canonical_first_and_filters_meta | — | standard | ⚪ Missing |
| tests.test_cli_docs_modes.test_docs_module_write_canonical_has_frontmatter_export_plain | — | standard | ⚪ Missing |
| tests.test_cli_docs_modes.test_docs_module_write_rejects_explicit_unsafe_module | — | standard | ⚪ Missing |
| tests.test_python_adapter_compat.test_docstring_maps_to_docstring_contract_source | — | standard | ⚪ Missing |
| tests.test_cli_doctor.test_doctor_changed_and_all_args_are_recognized | — | standard | ⚪ Missing |
| tests.test_cli_doctor.test_doctor_ci_arg_is_recognized | — | standard | ⚪ Missing |
| tests.test_ci_mode.test_doctor_ci_fail_on_fail_check | — | standard | ⚪ Missing |
| tests.test_ci_mode.test_doctor_ci_json_single_object_and_no_abs_path | — | standard | ⚪ Missing |
| tests.test_ci_mode.test_doctor_ci_warn_only_is_pass | — | standard | ⚪ Missing |
| tests.test_cli_doctor.test_doctor_default_is_changed_scope | — | standard | ⚪ Missing |
| tests.test_repair_guidance.test_doctor_fail_guidance_is_conservative | — | standard | ⚪ Missing |
| tests.test_cli_help_and_ux.test_doctor_help_lists_changed_all_and_module_flags | — | standard | ⚪ Missing |
| tests.test_cli_doctor.test_doctor_is_advisory_and_does_not_trigger_write_or_llm_paths | — | standard | ⚪ Missing |
| tests.test_cli_json_output.test_doctor_json_derived_view_detail_keeps_unknown_semantics | — | standard | ⚪ Missing |
| tests.test_cli_json_output.test_doctor_json_includes_legacy_diary_advisory | — | standard | ⚪ Missing |
| tests.test_cli_json_output.test_doctor_json_output_has_required_fields_and_summary | — | standard | ⚪ Missing |
| tests.test_cli_json_output.test_doctor_json_scope_for_module | — | standard | ⚪ Missing |
| tests.test_cli_doctor.test_doctor_modes_are_mutually_exclusive | — | standard | ⚪ Missing |
| tests.test_cli_doctor.test_doctor_module_mode_runs | — | standard | ⚪ Missing |
| tests.test_doctor.test_doctor_report_formats_pass_warn_fail_skip | — | standard | ⚪ Missing |
| tests.test_doctor.test_doctor_report_includes_suggestions | — | standard | ⚪ Missing |
| tests.test_cli_doctor.test_doctor_text_output_includes_legacy_diary_advisory | — | standard | ⚪ Missing |
| tests.test_cli_doctor.test_doctor_text_output_uses_unknown_for_no_indexed_records | — | standard | ⚪ Missing |
| tests.test_init_wizard.test_dry_run_non_tty_uses_safe_defaults | — | standard | ⚪ Missing |
| tests.test_diary_workspace_paths.test_dual_read_merge_with_stable_normalized_hash_dedupe | — | standard | ⚪ Missing |
| tests.test_cli_i18n_env.test_env_language_controls_ci_text | — | standard | ⚪ Missing |
| tests.test_cli_i18n_env.test_env_language_overrides_config | — | standard | ⚪ Missing |
| tests.test_init_detector.test_excludes_do_not_override_code_roots | — | standard | ⚪ Missing |
| tests.test_init_wizard.test_existing_project_next_steps_include_checkpoint_and_adopt | — | standard | ⚪ Missing |
| tests.test_log_draft.test_explicit_from_report_still_builds_writable_draft_without_changed_files_or_snapshots | — | standard | ⚪ Missing |
| tests.test_workspace_paths.test_export_options_parsing | — | standard | ⚪ Missing |
| tests.test_typescript_contract_presence.test_exported_class_public_method_with_tsdoc_is_present_and_required | — | standard | ⚪ Missing |
| tests.test_typescript_contract_presence.test_exported_function_without_tsdoc_is_missing_and_required | — | standard | ⚪ Missing |
| tests.test_cache_isolation_hardening.test_external_temp_paths_only_land_in_isolated_workspace_index | — | standard | ⚪ Missing |
| tests.test_decorator_engine.test_filters_out_internal_and_testlike_names | — | standard | ⚪ Missing |
| tests.test_cli_v2.test_finish_command_recognized | — | standard | ⚪ Missing |
| tests.test_cli_finish_sync_context.test_finish_default_does_not_run_sync_context_flow | — | standard | ⚪ Missing |
| tests.test_cli_v2.test_finish_does_not_auto_run_docs_log_lock | — | standard | ⚪ Missing |
| tests.test_change_window_snapshot.test_finish_snapshot_write_failure_does_not_change_exit_code | — | standard | ⚪ Missing |
| tests.test_cli_finish_sync_context.test_finish_sync_context_ignores_changed_modules_outside_workspace | — | standard | ⚪ Missing |
| tests.test_cli_finish_sync_context.test_finish_sync_context_no_changed_modules_friendly | — | standard | ⚪ Missing |
| tests.test_cli_finish_sync_context.test_finish_sync_context_runs_status_check_docs_seal_stale | — | standard | ⚪ Missing |
| tests.test_cli_finish_sync_context.test_finish_sync_context_write_boundary_only_allows_docs_and_capsules | — | standard | ⚪ Missing |
| tests.test_change_window_snapshot.test_finish_sync_context_writes_finish_snapshot_and_can_be_read | — | standard | ⚪ Missing |
| tests.test_change_window_snapshot.test_finish_writes_finish_snapshot_and_can_be_read | — | standard | ⚪ Missing |
| tests.test_utils_format.test_format_size_bytes | — | standard | ⚪ Missing |
| tests.test_utils_format.test_format_size_kb | — | standard | ⚪ Missing |
| tests.test_utils_format.test_format_size_mb | — | standard | ⚪ Missing |
| tests.test_utils_format.test_format_size_negative_raises | — | standard | ⚪ Missing |
| tests.test_log_draft.test_from_report_requires_valid_json | — | standard | ⚪ Missing |
| tests.test_context_integrity.test_frontmatter_render_parse_roundtrip | — | standard | ⚪ Missing |
| tests.test_python_adapter_compat.test_function_contract_maps_to_contract_subject | — | standard | ⚪ Missing |
| tests.test_cli_v2.test_gen_l2_maps_to_docs | — | standard | ⚪ Missing |
| tests.test_drafting.test_generate_draft_parses_json | — | standard | ⚪ Missing |
| tests.test_drafting.test_generate_draft_returns_none_when_no_changes | — | standard | ⚪ Missing |
| tests.test_project_structure.test_generate_markdown_contains_required_sections_and_is_deterministic | — | standard | ⚪ Missing |
| tests.test_module_skill.test_generate_module_skill_contains_thin_template | — | standard | ⚪ Missing |
| tests.test_contract_impact.test_generated_view_modules_hit_generated_view_format | — | standard | ⚪ Missing |
| tests.test_module_capsule.test_generators_include_required_sections | — | standard | ⚪ Missing |
| tests.test_adapter_registry.test_get_adapter_python_returns_python_adapter_instance | — | standard | ⚪ Missing |
| tests.test_adapter_registry.test_get_enabled_languages_output_is_stable | — | standard | ⚪ Missing |
| tests.test_workspace_paths.test_gitignore_does_not_ignore_harbor_views_modules_in_repo | — | standard | ⚪ Missing |
| tests.test_workspace_gitignore_policy.test_gitignore_does_not_use_broad_harbor_ignore | — | standard | ⚪ Missing |
| tests.test_init_llm_env.test_gitignore_has_separate_managed_blocks | — | standard | ⚪ Missing |
| tests.test_workspace_gitignore_policy.test_gitignore_ignores_required_local_runtime_paths | — | standard | ⚪ Missing |
| tests.test_init_llm_env.test_gitignore_managed_blocks_are_idempotent | — | standard | ⚪ Missing |
| tests.test_init_detector.test_gitignore_mapping | — | standard | ⚪ Missing |
| tests.test_gitignore_prune.test_gitignore_prunes_node_modules | — | standard | ⚪ Missing |
| tests.test_init_detector.test_gitignore_py_pattern_is_skipped_with_warning | — | standard | ⚪ Missing |
| tests.test_workspace_gitignore_policy.test_harbor_canonical_and_runtime_ignore_policy | — | standard | ⚪ Missing |
| tests.test_cli_init_output.test_harbor_wrapper_output_matches_python_module | — | standard | ⚪ Missing |
| tests.test_release_packaging.test_help_recognizes_core_release_commands | — | standard | ⚪ Missing |
| tests.test_typescript_contract_presence.test_high_confidence_tsdoc_marks_present_and_required | — | standard | ⚪ Missing |
| tests.core.test_index_sync_sqlite.test_index_and_sync_detects_body_drift | — | standard | ⚪ Missing |
| tests.test_index_builder.test_index_build_incremental_and_docstring_stability | — | standard | ⚪ Missing |
| tests.test_index_builder_registry_integration.test_index_builder_default_registry_python_only | — | standard | ⚪ Missing |
| tests.test_index_builder_registry_integration.test_index_builder_file_discovery_matches_python_only_when_ts_enabled | — | standard | ⚪ Missing |
| tests.test_index_builder_bad_syntax.test_index_builder_skips_bad_syntax | — | standard | ⚪ Missing |
| tests.test_cache_isolation_hardening.test_index_builder_uses_isolated_cache_dir_without_touching_repo_cache | — | standard | ⚪ Missing |
| tests.test_cli_docs_modes.test_infer_module_from_path_supports_windows_and_posix | — | standard | ⚪ Missing |
| tests.test_cli_init_output.test_init_detects_django | — | standard | ⚪ Missing |
| tests.test_cli_init_output.test_init_detects_node | — | standard | ⚪ Missing |
| tests.test_init_governance.test_init_dry_run_with_full_flags_writes_nothing | — | standard | ⚪ Missing |
| tests.test_init_governance.test_init_existing_files_are_skipped_unless_force | — | standard | ⚪ Missing |
| tests.test_init_governance.test_init_governance_creates_starter_files_without_project_rules | — | standard | ⚪ Missing |
| tests.test_cli_help_and_ux.test_init_help_lists_wizard_flags | — | standard | ⚪ Missing |
| tests.test_cli_i18n.test_init_provider_prompt_i18n_text | — | standard | ⚪ Missing |
| tests.test_release_packaging.test_init_templates_package_resources_are_loadable | — | standard | ⚪ Missing |
| tests.test_init_wizard.test_init_wizard_dry_run_i18n_purity | — | standard | ⚪ Missing |
| tests.test_init_wizard.test_init_wizard_prompts_are_single_language_after_selection | — | standard | ⚪ Missing |
| tests.test_init_wizard.test_init_wizard_repair_guidance_mode_prompt_is_localized | — | standard | ⚪ Missing |
| tests.test_init_wizard.test_init_wizard_source_has_no_legacy_yes_no_prompt_tokens | — | standard | ⚪ Missing |
| tests.test_init_llm_env.test_init_wizard_source_removes_legacy_yes_no_brackets | — | standard | ⚪ Missing |
| tests.test_typescript_contract_presence.test_internal_helper_is_not_required | — | standard | ⚪ Missing |
| tests.test_cli_json_output.test_invalid_format_values_return_argparse_error | — | standard | ⚪ Missing |
| tests.test_log_draft.test_invalid_marker_falls_back_to_accept_with_explicit_note | — | standard | ⚪ Missing |
| tests.test_index_progress.test_iter_build_emits_progress_and_counts | — | standard | ⚪ Missing |
| tests.test_cli_json_output.test_json_output_does_not_include_absolute_paths | — | standard | ⚪ Missing |
| tests.test_drafting_json_parse.test_kv_fallback_lines_parse | — | standard | ⚪ Missing |
| tests.test_l2_paths.test_l2_absolute_module_path_outside_repo_still_rejected | — | standard | ⚪ Missing |
| tests.test_l2_paths.test_l2_canonical_root_cannot_escape_repo_root | — | standard | ⚪ Missing |
| tests.test_stale.test_l2_export_disabled_is_explicit_and_not_warn_counter | — | standard | ⚪ Missing |
| tests.test_l2_paths.test_l2_export_module_readme_disabled_writes_only_canonical | — | standard | ⚪ Missing |
| tests.test_stale.test_l2_export_ok_when_canonical_has_frontmatter_and_export_is_plain_body | — | standard | ⚪ Missing |
| tests.test_stale.test_l2_export_ok_when_canonical_up_to_date_and_export_matches | — | standard | ⚪ Missing |
| tests.test_stale.test_l2_export_skips_compare_when_canonical_unavailable | — | standard | ⚪ Missing |
| tests.test_stale.test_l2_export_warn_when_canonical_up_to_date_but_export_mismatch | — | standard | ⚪ Missing |
| tests.test_stale.test_l2_export_warn_when_canonical_up_to_date_but_export_missing | — | standard | ⚪ Missing |
| tests.test_l2_paths.test_l2_meta_reads_legacy_then_writes_canonical_only | — | standard | ⚪ Missing |
| tests.test_l2_paths.test_l2_module_path_traversal_rejected_with_export_disabled | — | standard | ⚪ Missing |
| tests.test_l2_paths.test_l2_module_path_traversal_rejected_with_export_enabled | — | standard | ⚪ Missing |
| tests.test_stale.test_l2_readme_check_does_not_write_file | — | standard | ⚪ Missing |
| tests.test_stale.test_l2_readme_stale_when_content_differs | — | standard | ⚪ Missing |
| tests.test_stale.test_l2_readme_stale_when_missing | — | standard | ⚪ Missing |
| tests.test_stale.test_l2_readme_unknown_when_no_indexed_records | — | standard | ⚪ Missing |
| tests.test_stale.test_l2_readme_up_to_date_when_content_matches_except_timestamp | — | standard | ⚪ Missing |
| tests.test_l2_paths.test_l2_repeat_write_keeps_canonical_content_when_body_unchanged | — | standard | ⚪ Missing |
| tests.test_l2_paths.test_l2_write_writes_canonical_and_module_readme_export_by_default | — | standard | ⚪ Missing |
| tests.test_log_draft.test_last_log_marker_round_trip_prefers_last_log_at_and_keeps_legacy_aliases | — | standard | ⚪ Missing |
| tests.test_diary_workspace_paths.test_legacy_chore_type_remains_supported | — | standard | ⚪ Missing |
| tests.test_workspace_paths.test_legacy_config_read | — | standard | ⚪ Missing |
| tests.test_module_capsule_stale.test_legacy_exists_but_canonical_missing_is_stale | — | standard | ⚪ Missing |
| tests.test_python_adapter_compat.test_legacy_func_id_keeps_original_function_contract_id | — | standard | ⚪ Missing |
| tests.test_typescript_contract_presence.test_line_comment_is_not_contract_source | — | standard | ⚪ Missing |
| tests.test_change_window_snapshot.test_list_change_windows_sorts_newest_first_and_get_latest_filters_event | — | standard | ⚪ Missing |
| tests.test_init_llm_env.test_llm_env_append_missing_only_and_force_does_not_overwrite | — | standard | ⚪ Missing |
| tests.test_init_llm_env.test_llm_provider_alias_custom_writes_env | — | standard | ⚪ Missing |
| tests.test_init_llm_env.test_llm_provider_alias_number_2_writes_deepseek_env | — | standard | ⚪ Missing |
| tests.test_init_llm_env.test_llm_provider_alias_openai_writes_env | — | standard | ⚪ Missing |
| tests.test_diary_workspace_paths.test_load_active_keeps_recent_two_month_window | — | standard | ⚪ Missing |
| tests.test_diary_workspace_paths.test_load_active_reads_legacy_only_without_mutation | — | standard | ⚪ Missing |
| tests.test_lock_flags.test_lock_no_register_adopted | — | standard | ⚪ Missing |
| tests.test_lock_register_adopted.test_lock_register_adopted | — | standard | ⚪ Missing |
| tests.test_lock_flags.test_lock_register_scan | — | standard | ⚪ Missing |
| tests.test_log_draft_cli.test_log_draft_cache_warning_does_not_fail_command | — | standard | ⚪ Missing |
| tests.test_log_draft_cli.test_log_draft_default_json_prefers_last_log_marker_boundary | — | standard | ⚪ Missing |
| tests.test_log_draft_cli.test_log_draft_default_outputs_markdown_and_does_not_call_log_write | — | standard | ⚪ Missing |
| tests.test_log_draft_cli.test_log_draft_diary_only_outputs_insufficient_evidence_without_write_hints | — | standard | ⚪ Missing |
| tests.test_log_draft_cli.test_log_draft_from_report_bad_json_returns_clear_error | — | standard | ⚪ Missing |
| tests.test_log_draft_cli.test_log_draft_from_report_still_generates_writable_draft | — | standard | ⚪ Missing |
| tests.test_cli_i18n.test_log_draft_insufficient_evidence_uses_zh_i18n_without_next_actions | — | standard | ⚪ Missing |
| tests.test_log_draft_cli.test_log_draft_json_output_is_stable | — | standard | ⚪ Missing |
| tests.test_log_draft_cli.test_log_draft_json_reports_invalid_marker_fallback_without_polluting_json | — | standard | ⚪ Missing |
| tests.test_cli_i18n.test_log_draft_next_actions_use_zh_i18n | — | standard | ⚪ Missing |
| tests.test_log_draft_cli.test_log_draft_output_path_takes_precedence_over_save | — | standard | ⚪ Missing |
| tests.test_log_draft_cli.test_log_draft_output_rejects_diary_path | — | standard | ⚪ Missing |
| tests.test_log_draft_cli.test_log_draft_output_writes_reports_file_and_keeps_stdout | — | standard | ⚪ Missing |
| tests.test_log_draft_cli.test_log_draft_reports_only_json_is_pure_and_marks_insufficient_evidence | — | standard | ⚪ Missing |
| tests.test_log_draft_cli.test_log_draft_reports_only_outputs_insufficient_evidence_without_write_hints | — | standard | ⚪ Missing |
| tests.test_log_draft_cli.test_log_draft_save_does_not_modify_existing_marker | — | standard | ⚪ Missing |
| tests.test_log_draft_cli.test_log_draft_save_json_writes_timestamped_json_copy_without_polluting_stdout | — | standard | ⚪ Missing |
| tests.test_log_draft_cli.test_log_draft_save_writes_timestamped_markdown_copy | — | standard | ⚪ Missing |
| tests.test_log_draft_cli.test_log_draft_since_last_accept_filters_to_post_accept_evidence | — | standard | ⚪ Missing |
| tests.test_log_draft_cli.test_log_draft_snapshot_only_still_outputs_writable_draft | — | standard | ⚪ Missing |
| tests.test_cli_i18n.test_log_message_invalid_type_uses_friendly_zh_error_without_traceback | — | standard | ⚪ Missing |
| tests.test_cli_v2.test_log_message_keeps_json_first_line_and_prints_canonical_target | — | standard | ⚪ Missing |
| tests.test_log_write_from_draft.test_log_write_from_draft_path_policy | — | standard | ⚪ Missing |
| tests.test_log_write_from_draft.test_log_write_from_latest_draft_flag_writes_successfully | — | standard | ⚪ Missing |
| tests.test_log_write_from_draft.test_log_write_interactive_no_cancels_without_writing | — | standard | ⚪ Missing |
| tests.test_log_write_from_draft.test_log_write_interactive_yes_writes_diary | — | standard | ⚪ Missing |
| tests.test_log_write_from_draft.test_log_write_markdown_draft_maps_structured_quality_fields | — | standard | ⚪ Missing |
| tests.test_log_write_from_draft.test_log_write_markdown_fallback_uses_safe_excerpt_only | — | standard | ⚪ Missing |
| tests.test_log_write_from_draft.test_log_write_marker_failure_warns_without_rolling_back_diary | — | standard | ⚪ Missing |
| tests.test_log_draft.test_log_write_marker_round_trip_closes_since_last_log_boundary | — | standard | ⚪ Missing |
| tests.test_cli_i18n.test_log_write_non_interactive_requires_yes_uses_zh_i18n | — | standard | ⚪ Missing |
| tests.test_log_write_from_draft.test_log_write_non_interactive_without_yes_is_rejected | — | standard | ⚪ Missing |
| tests.test_log_write_from_draft.test_log_write_rejects_repo_external_absolute_path | — | standard | ⚪ Missing |
| tests.test_log_write_from_draft.test_log_write_requires_latest_draft_by_default | — | standard | ⚪ Missing |
| tests.test_log_write_from_draft.test_log_write_yes_writes_from_latest_json_and_updates_marker | — | standard | ⚪ Missing |
| tests.test_diary_workspace_paths.test_log_writes_only_canonical_path | — | standard | ⚪ Missing |
| tests.test_typescript_contract_presence.test_malformed_or_unsupported_ts_does_not_emit_contract_parse_error | — | standard | ⚪ Missing |
| tests.test_typescript_adapter_mvp.test_malformed_parse_does_not_poison_followup_file_parse | — | standard | ⚪ Missing |
| tests.test_typescript_contract_presence.test_medium_confidence_tsdoc_marks_non_contract_doc | — | standard | ⚪ Missing |
| tests.test_context_integrity.test_merge_generated_at_keeps_old_when_fingerprints_and_body_same | — | standard | ⚪ Missing |
| tests.test_doctor.test_merge_status_never_downgrades_fail | — | standard | ⚪ Missing |
| tests.test_context_integrity.test_metadata_has_no_absolute_paths | — | standard | ⚪ Missing |
| tests.test_min_count_one.test_min_count_one_includes_single_file_dir | — | standard | ⚪ Missing |
| tests.test_context_integrity.test_missing_file_handling_is_deterministic | — | standard | ⚪ Missing |
| tests.test_init_detector.test_mixed_stack_rules | — | standard | ⚪ Missing |
| tests.test_module_capsule.test_module_capsule_dir_keeps_nested_path | — | standard | ⚪ Missing |
| tests.test_cli_help_and_ux.test_module_help_lists_inspect_seal_stale_and_promote_skill | — | standard | ⚪ Missing |
| tests.test_cli_module_capsule_batch.test_module_inspect_and_single_seal_behavior_unchanged | — | standard | ⚪ Missing |
| tests.test_cli_module_capsule.test_module_inspect_is_recognized | — | standard | ⚪ Missing |
| tests.test_cli_module_skill.test_module_promote_skill_is_recognized | — | standard | ⚪ Missing |
| tests.test_cli_module_skill.test_module_promote_skill_legacy_exists_but_canonical_missing_fails | — | standard | ⚪ Missing |
| tests.test_cli_module_skill.test_module_promote_skill_missing_capsule | — | standard | ⚪ Missing |
| tests.test_cli_module_skill.test_module_promote_skill_stale_capsule | — | standard | ⚪ Missing |
| tests.test_cli_module_skill.test_module_promote_skill_up_to_date_generates_skill | — | standard | ⚪ Missing |
| tests.test_cli_module_capsule_batch.test_module_seal_all_discovers_indexed_modules_only_and_stable_order | — | standard | ⚪ Missing |
| tests.test_cli_module_capsule_batch.test_module_seal_all_none_friendly | — | standard | ⚪ Missing |
| tests.test_cli_module_capsule_batch.test_module_seal_all_write_creates_three_files_per_module | — | standard | ⚪ Missing |
| tests.test_cli_module_capsule_batch.test_module_seal_changed_and_all_args_are_recognized | — | standard | ⚪ Missing |
| tests.test_cli_module_capsule_batch.test_module_seal_changed_dedup_sort_and_windows_path_preview | — | standard | ⚪ Missing |
| tests.test_cli_module_capsule_batch.test_module_seal_changed_no_modules_friendly_and_no_write | — | standard | ⚪ Missing |
| tests.test_cli_module_capsule_batch.test_module_seal_changed_write_creates_three_files_per_module | — | standard | ⚪ Missing |
| tests.test_cli_module_capsule_batch.test_module_seal_modes_are_mutually_exclusive | — | standard | ⚪ Missing |
| tests.test_cli_help_and_ux.test_module_seal_modes_error_message_is_friendly_and_clear | — | standard | ⚪ Missing |
| tests.test_cli_module_capsule.test_module_seal_preview_is_recognized_and_no_write | — | standard | ⚪ Missing |
| tests.test_cli_module_capsule_batch.test_module_seal_single_write_dual_writes_when_export_enabled | — | standard | ⚪ Missing |
| tests.test_cli_module_capsule.test_module_seal_windows_style_path_normalizes_to_nested_dir | — | standard | ⚪ Missing |
| tests.test_cli_module_capsule.test_module_seal_write_creates_three_files | — | standard | ⚪ Missing |
| tests.test_cli_module_capsule_stale.test_module_stale_all_checks_all_modules_stable_order | — | standard | ⚪ Missing |
| tests.test_cli_module_capsule_stale.test_module_stale_args_are_recognized | — | standard | ⚪ Missing |
| tests.test_cli_module_capsule_stale.test_module_stale_changed_checks_each_module_and_windows_path | — | standard | ⚪ Missing |
| tests.test_cli_module_capsule_stale.test_module_stale_does_not_accept_write | — | standard | ⚪ Missing |
| tests.test_cli_module_capsule_stale.test_module_stale_modes_are_mutually_exclusive | — | standard | ⚪ Missing |
| tests.test_cli_help_and_ux.test_module_stale_modes_error_message_is_friendly_and_clear | — | standard | ⚪ Missing |
| tests.test_cli_module_capsule_stale.test_module_stale_single_fingerprint_missing | — | standard | ⚪ Missing |
| tests.test_cli_module_capsule_stale.test_module_stale_single_mismatch | — | standard | ⚪ Missing |
| tests.test_cli_module_capsule_stale.test_module_stale_single_missing_module_card | — | standard | ⚪ Missing |
| tests.test_cli_module_capsule_stale.test_module_stale_single_up_to_date | — | standard | ⚪ Missing |
| tests.test_cli_module_capsule_stale.test_module_stale_treats_legacy_existing_but_canonical_missing_as_stale | — | standard | ⚪ Missing |
| tests.test_cli_module_capsule_stale.test_module_stale_unknown_module_friendly | — | standard | ⚪ Missing |
| tests.test_diary_workspace_paths.test_monthly_rotation_writes_canonical_month_file | — | standard | ⚪ Missing |
| tests.test_drafting_json_parse.test_nested_brace_with_code_fence | — | standard | ⚪ Missing |
| tests.test_workspace_paths.test_new_config_read | — | standard | ⚪ Missing |
| tests.test_init_wizard.test_new_project_next_steps_do_not_suggest_immediate_checkpoint | — | standard | ⚪ Missing |
| tests.test_harbor_next.test_next_can_read_utf16_report | — | standard | ⚪ Missing |
| tests.test_typescript_next_guidance.test_next_explains_typescript_contract_gap | — | standard | ⚪ Missing |
| tests.test_typescript_next_guidance.test_next_explains_typescript_skipped_no_contract | — | standard | ⚪ Missing |
| tests.test_typescript_next_guidance.test_next_explains_typescript_unsupported_syntax_advisory | — | standard | ⚪ Missing |
| tests.test_harbor_next.test_next_json_items_include_blocking_and_status_is_ok_even_for_fail_report | — | standard | ⚪ Missing |
| tests.test_harbor_next.test_next_json_output_contract | — | standard | ⚪ Missing |
| tests.test_harbor_next.test_next_reads_checkpoint_report_and_groups_output | — | standard | ⚪ Missing |
| tests.test_harbor_next.test_next_unknown_category_graceful_degrade | — | standard | ⚪ Missing |
| tests.test_cli_docs_modes.test_no_changed_modules_prints_friendly_message | — | standard | ⚪ Missing |
| tests.test_python_adapter_compat.test_no_docstring_maps_to_empty_contract_sources | — | standard | ⚪ Missing |
| tests.test_module_capsule.test_no_records_is_friendly | — | standard | ⚪ Missing |
| tests.test_checkpoint_json_additive_compat.test_non_function_symbol_kind_does_not_enter_blocking_checkpoint_failures | — | standard | ⚪ Missing |
| tests.test_typescript_not_supported_boundaries.test_non_function_typescript_targets_do_not_enter_blocking_checkpoint | — | standard | ⚪ Missing |
| tests.test_init_wizard.test_non_tty_does_not_try_arrow_selector | — | standard | ⚪ Missing |
| tests.test_log_write_from_draft.test_normalize_cli_input_path_converts_repo_relative_windows_separators | — | standard | ⚪ Missing |
| tests.test_l2_paths.test_normalize_indexed_module_candidate_maps_repo_absolute_file_path | — | standard | ⚪ Missing |
| tests.test_module_capsule.test_normalize_module_path_supports_windows_and_posix | — | standard | ⚪ Missing |
| tests.test_module_skill.test_normalize_skill_slug_rules_are_stable | — | standard | ⚪ Missing |
| tests.test_typescript_adapter_mvp.test_parse_file_detects_export_async_function | — | standard | ⚪ Missing |
| tests.test_typescript_adapter_mvp.test_parse_file_detects_export_const_arrow_function | — | standard | ⚪ Missing |
| tests.test_typescript_adapter_mvp.test_parse_file_detects_export_const_async_arrow_function | — | standard | ⚪ Missing |
| tests.test_typescript_adapter_mvp.test_parse_file_detects_export_function | — | standard | ⚪ Missing |
| tests.test_typescript_adapter_mvp.test_parse_file_detects_exported_class_public_method | — | standard | ⚪ Missing |
| tests.test_typescript_adapter_mvp.test_parse_file_does_not_crash_on_unsupported_or_malformed_ts | — | standard | ⚪ Missing |
| tests.test_drafting_json_parse.test_parse_single_quotes_fallback | — | standard | ⚪ Missing |
| tests.test_drafting_json_parse.test_parse_with_code_fence | — | standard | ⚪ Missing |
| tests.test_drafting_json_parse.test_parse_with_noise_prefix_suffix | — | standard | ⚪ Missing |
| tests.test_context_integrity.test_parser_rejects_complex_yaml | — | standard | ⚪ Missing |
| tests.test_checkpoint_ci_guidance.test_possible_semantic_drift_guidance_is_conservative | — | standard | ⚪ Missing |
| tests.test_repair_guidance.test_possible_semantic_drift_requires_decision_and_is_conservative | — | standard | ⚪ Missing |
| tests.test_contract_presence.test_private_light_helper_without_docstring_is_skippable | — | standard | ⚪ Missing |
| tests.test_contract_impact.test_production_cli_path_remains_possible | — | standard | ⚪ Missing |
| tests.test_cli_help_and_ux.test_project_help_lists_structure_and_structure_help_lists_write | — | standard | ⚪ Missing |
| tests.test_workspace_gitignore_policy.test_project_structure_canonical_path_is_harbor_views | — | standard | ⚪ Missing |
| tests.test_workspace_paths.test_project_structure_docs_export_root_cannot_escape_repo_root | — | standard | ⚪ Missing |
| tests.test_cli_project_structure.test_project_structure_does_not_trigger_other_side_effect_paths | — | standard | ⚪ Missing |
| tests.test_cli_project_structure.test_project_structure_filesystem_fallback_generates_non_empty_key_areas_and_modules | — | standard | ⚪ Missing |
| tests.test_cli_project_structure.test_project_structure_no_index_is_friendly_and_not_crash_when_no_filesystem_fallback | — | standard | ⚪ Missing |
| tests.test_cli_help_and_ux.test_project_structure_preview_message_uses_resolved_canonical_path | — | standard | ⚪ Missing |
| tests.test_cli_project_structure.test_project_structure_preview_runs_and_does_not_write | — | standard | ⚪ Missing |
| tests.test_cli_project_structure.test_project_structure_repeat_write_keeps_generated_at_when_no_change | — | standard | ⚪ Missing |
| tests.test_cli_project_structure.test_project_structure_write_does_not_overwrite_existing_legacy_docs_when_export_disabled | — | standard | ⚪ Missing |
| tests.test_cli_project_structure.test_project_structure_write_dual_writes_when_docs_export_enabled | — | standard | ⚪ Missing |
| tests.test_cli_project_structure.test_project_structure_write_updates_canonical_path_by_default | — | standard | ⚪ Missing |
| tests.test_init_wizard.test_provider_fallback_accepts_name_deepseek | — | standard | ⚪ Missing |
| tests.test_init_wizard.test_provider_fallback_accepts_number_2 | — | standard | ⚪ Missing |
| tests.test_init_wizard.test_provider_invalid_input_shows_available_options | — | standard | ⚪ Missing |
| tests.test_contract_presence.test_public_without_docstring_is_contract_gap_required | — | standard | ⚪ Missing |
| tests.test_release_packaging.test_pyproject_declares_cli_runtime_dependencies | — | standard | ⚪ Missing |
| tests.test_release_packaging.test_pyproject_version_and_description_are_release_ready | Release packaging allows stable and pre-release (a/b/rc) ... | standard | ⚪ Missing |
| tests.test_init_wizard.test_pytest_env_does_not_try_arrow_selector | — | standard | ⚪ Missing |
| tests.test_python_adapter_compat.test_python_adapter_parse_file_behavior_unchanged | — | standard | ⚪ Missing |
| tests.test_typescript_not_supported_boundaries.test_python_audit_provider_behavior_unchanged | — | standard | ⚪ Missing |
| tests.test_checkpoint_json_additive_compat.test_python_checkpoint_json_keeps_legacy_fields_and_adds_identity_fields | — | standard | ⚪ Missing |
| tests.test_checkpoint_json_additive_compat.test_python_checkpoint_pass_fail_semantics_unchanged | — | standard | ⚪ Missing |
| tests.test_typescript_not_supported_boundaries.test_python_ddt_strict_and_latest_rules_unchanged | — | standard | ⚪ Missing |
| tests.test_python_ddt_regression.test_python_ddt_strict_forbids_latest_and_strict_version_stays_valid | — | standard | ⚪ Missing |
| tests.test_checkpoint_json_additive_compat.test_python_method_symbol_kind_and_func_id_stay_compatible | — | standard | ⚪ Missing |
| tests.test_init_detector.test_python_project_excludes_do_not_contain_py_globs | — | standard | ⚪ Missing |
| tests.test_python_audit_regression.test_python_semantic_audit_mismatch_mapping_unchanged | — | standard | ⚪ Missing |
| tests.test_python_audit_regression.test_python_semantic_audit_still_calls_provider_and_returns_ok | — | standard | ⚪ Missing |
| tests.test_drafting.test_raise_when_llm_not_configured | — | standard | ⚪ Missing |
| tests.test_project_structure.test_rank_key_file_prioritizes_entrypoints_and_impl_files | — | standard | ⚪ Missing |
| tests.test_cli_help_and_ux.test_readme_and_readme_en_include_key_new_command_phrases | — | standard | ⚪ Missing |
| tests.test_release_packaging.test_readme_contains_release_key_commands | — | standard | ⚪ Missing |
| tests.test_release_packaging.test_readme_en_contains_release_key_commands | — | standard | ⚪ Missing |
| tests.test_cli_init_output.test_real_harbor_init_writes_config_without_dangerous_py_excludes | — | standard | ⚪ Missing |
| tests.test_typescript_adapter_mvp.test_registry_default_python_only_and_typescript_unconfigured_disabled | — | standard | ⚪ Missing |
| tests.test_adapter_registry.test_registry_does_not_change_python_adapter_parse_file_behavior | — | standard | ⚪ Missing |
| tests.test_release_packaging.test_release_notes_include_unreleased_v130_track | Backward-compatible alias test name kept to avoid baselin... | standard | ⚪ Missing |
| tests.test_release_packaging.test_release_notes_include_v130_release_track | — | standard | ⚪ Missing |
| tests.test_repair_guidance.test_repair_guidance_has_no_llm_integration_symbols | — | standard | ⚪ Missing |
| tests.test_contract_impact.test_report_to_dict_is_deterministic_and_sanitized | — | standard | ⚪ Missing |
| tests.test_log_draft.test_reports_only_evidence_is_insufficient_and_does_not_build_writable_draft | — | standard | ⚪ Missing |
| tests.test_change_window_snapshot.test_retention_keeps_latest_fifty_snapshots | — | standard | ⚪ Missing |
| tests.test_decorator_engine.test_safe_adds_scope_without_breaking_indent | — | standard | ⚪ Missing |
| tests.test_decorator_engine.test_safe_does_not_duplicate_tag | — | standard | ⚪ Missing |
| tests.test_typescript_contract_presence.test_script_file_targets_are_not_required | — | standard | ⚪ Missing |
| tests.test_init_wizard.test_selector_fallback_does_not_repeat_selector_block | — | standard | ⚪ Missing |
| tests.test_init_wizard.test_selector_source_does_not_use_full_screen_dialog | — | standard | ⚪ Missing |
| tests.test_audit.test_semantic_guard_contract_gap_without_docstring | — | standard | ⚪ Missing |
| tests.test_audit.test_semantic_guard_mismatch_parsing | — | standard | ⚪ Missing |
| tests.test_semantic_audit_contract_gap.test_semantic_guard_missing_non_required_contract_skips_llm | — | standard | ⚪ Missing |
| tests.test_semantic_audit_contract_gap.test_semantic_guard_missing_required_contract_skips_llm | — | standard | ⚪ Missing |
| tests.test_audit.test_semantic_guard_ok | — | standard | ⚪ Missing |
| tests.test_audit.test_semantic_guard_skipped_no_contract_for_internal_helper | — | standard | ⚪ Missing |
| tests.test_adapter_basic.test_signature_hash_changes | — | standard | ⚪ Missing |
| tests.test_typescript_contract_presence.test_signature_only_public_function_remains_missing_required | — | standard | ⚪ Missing |
| tests.test_log_draft.test_since_last_accept_falls_back_when_accept_snapshot_is_missing | — | standard | ⚪ Missing |
| tests.test_log_draft.test_since_last_accept_filters_older_snapshots | — | standard | ⚪ Missing |
| tests.test_log_draft.test_since_last_log_invalid_marker_uses_explicit_uncertain_fallback_note | — | standard | ⚪ Missing |
| tests.test_log_draft.test_since_last_log_without_marker_falls_back_to_recent_snapshots | — | standard | ⚪ Missing |
| tests.test_workspace_paths.test_single_write_new_config_target | — | standard | ⚪ Missing |
| tests.test_doctor.test_skill_reference_check_legacy_existing_passes_when_export_enabled | — | standard | ⚪ Missing |
| tests.test_doctor.test_skill_reference_check_legacy_existing_warns_when_export_disabled | — | standard | ⚪ Missing |
| tests.test_doctor.test_skill_reference_check_passes_for_existing_canonical_reference | — | standard | ⚪ Missing |
| tests.test_doctor.test_skill_reference_check_skips_when_agents_skills_missing | — | standard | ⚪ Missing |
| tests.test_doctor.test_skill_reference_check_warns_when_capsule_missing | — | standard | ⚪ Missing |
| tests.test_change_window_snapshot.test_snapshot_does_not_store_file_content_or_diff_body | — | standard | ⚪ Missing |
| tests.test_log_draft.test_snapshot_only_evidence_still_builds_writable_draft | — | standard | ⚪ Missing |
| tests.test_context_integrity.test_source_fingerprint_is_deterministic | — | standard | ⚪ Missing |
| tests.test_release_packaging.test_source_of_truth_priority_and_conflict_docs_are_present | — | standard | ⚪ Missing |
| tests.test_cli_stale.test_stale_advisory_does_not_trigger_write_or_workflow_side_effects | — | standard | ⚪ Missing |
| tests.test_cli_stale.test_stale_all_scope_runs | — | standard | ⚪ Missing |
| tests.test_cli_stale.test_stale_changed_and_all_args_are_recognized | — | standard | ⚪ Missing |
| tests.test_cli_stale.test_stale_changed_checks_both_views | — | standard | ⚪ Missing |
| tests.test_cli_stale.test_stale_changed_windows_path_and_stable_order | — | standard | ⚪ Missing |
| tests.test_cli_stale.test_stale_ci_arg_is_recognized | — | standard | ⚪ Missing |
| tests.test_ci_mode.test_stale_ci_export_stale_is_advisory_only | — | standard | ⚪ Missing |
| tests.test_ci_mode.test_stale_ci_fail_on_canonical_l2_stale | — | standard | ⚪ Missing |
| tests.test_ci_mode.test_stale_ci_fail_on_module_capsule_stale | — | standard | ⚪ Missing |
| tests.test_ci_mode.test_stale_ci_json_single_object_and_no_abs_path | — | standard | ⚪ Missing |
| tests.test_ci_mode.test_stale_ci_pass_no_canonical_stale | — | standard | ⚪ Missing |
| tests.test_cli_stale.test_stale_default_is_changed_scope | — | standard | ⚪ Missing |
| tests.test_cli_help_and_ux.test_stale_help_lists_changed_all_module_and_format_flags | — | standard | ⚪ Missing |
| tests.test_stale.test_stale_json_contains_l2_readme_export_view_name | — | standard | ⚪ Missing |
| tests.test_cli_json_output.test_stale_json_output_has_required_fields_and_no_extra_text | — | standard | ⚪ Missing |
| tests.test_cli_json_output.test_stale_json_scope_for_module_and_deterministic_content | — | standard | ⚪ Missing |
| tests.test_cli_stale.test_stale_modes_are_mutually_exclusive | — | standard | ⚪ Missing |
| tests.test_cli_stale.test_stale_module_mode_runs | — | standard | ⚪ Missing |
| tests.test_cli_stale.test_stale_reports_all_up_to_date_message | — | standard | ⚪ Missing |
| tests.test_repair_guidance.test_stale_view_guidance_maps_context_refresh | — | standard | ⚪ Missing |
| tests.test_module_capsule_stale.test_stale_when_fingerprint_mismatch | — | standard | ⚪ Missing |
| tests.test_module_capsule_stale.test_stale_when_fingerprint_missing | — | standard | ⚪ Missing |
| tests.test_module_capsule_stale.test_stale_when_module_card_missing | — | standard | ⚪ Missing |
| tests.test_cli_v2.test_start_command_recognized | — | standard | ⚪ Missing |
| tests.test_cli_v2.test_status_alias_st | — | standard | ⚪ Missing |
| tests.test_cli_v2.test_status_skipped_no_contract_default_summary | — | standard | ⚪ Missing |
| tests.test_cli_v2.test_status_skipped_no_contract_verbose_lists_targets | — | standard | ⚪ Missing |
| tests.core.test_storage_migration.test_storage_migration_imports_json_to_sqlite | — | standard | ⚪ Missing |
| tests.test_ddt_version_baseline.test_strict_binding_missing_l3_version_still_fails | — | standard | ⚪ Missing |
| tests.test_ddt_version_baseline.test_strict_binding_reports_baseline_missing_advisory | — | standard | ⚪ Missing |
| tests.test_ddt_version_baseline.test_strict_binding_with_available_baseline_has_no_missing_baseline_advisory | — | standard | ⚪ Missing |
| tests.test_ddt_version_baseline.test_strict_binding_with_latest_still_fails | — | standard | ⚪ Missing |
| tests.test_contract_presence.test_strict_without_docstring_is_contract_gap_required | — | standard | ⚪ Missing |
| tests.test_sync_engine.test_sync_engine_contract_gap_for_required_target_without_docstring | — | standard | ⚪ Missing |
| tests.test_sync_engine.test_sync_engine_contract_parse_error_when_contract_presence_is_malformed | — | standard | ⚪ Missing |
| tests.test_sync_engine_registry_integration.test_sync_engine_default_registry_python_only | — | standard | ⚪ Missing |
| tests.test_sync_engine.test_sync_engine_drift_detection | — | standard | ⚪ Missing |
| tests.test_sync_engine_registry_integration.test_sync_engine_file_discovery_matches_python_only_when_ts_enabled | — | standard | ⚪ Missing |
| tests.test_sync_engine.test_sync_engine_skipped_no_contract_for_internal_helper_without_docstring | — | standard | ⚪ Missing |
| tests.test_typescript_adapter_mvp.test_target_id_rule_for_typescript_subject | — | standard | ⚪ Missing |
| tests.test_contract_subject_model.test_target_id_rule_is_stable_and_normalized | — | standard | ⚪ Missing |
| tests.test_python_adapter_compat.test_target_id_uses_python_file_symbol_qualified_name_rule | — | standard | ⚪ Missing |
| tests.test_contract_impact.test_tests_cli_snapshot_signal_remains_possible | — | standard | ⚪ Missing |
| tests.test_contract_impact.test_tests_ddt_binding_signal_remains_possible | — | standard | ⚪ Missing |
| tests.test_contract_impact.test_tests_generated_view_frontmatter_signal_remains_possible | — | standard | ⚪ Missing |
| tests.test_contract_impact.test_tests_helper_change_is_not_confirmed | — | standard | ⚪ Missing |
| tests.test_contract_impact.test_tests_helper_keyword_noise_stays_no_contract_impact | — | standard | ⚪ Missing |
| tests.test_contract_presence.test_to_dict_like_without_docstring_is_required | — | standard | ⚪ Missing |
| tests.test_contract_impact.test_to_dict_symbol_hits_cli_json_output | — | standard | ⚪ Missing |
| tests.test_typescript_checkpoint_ci.test_ts_disabled_keeps_typescript_out_of_checkpoint | — | standard | ⚪ Missing |
| tests.test_typescript_checkpoint_ci.test_ts_enabled_exported_function_without_jsdoc_becomes_contract_gap | — | standard | ⚪ Missing |
| tests.test_typescript_checkpoint_ci.test_ts_enabled_high_confidence_jsdoc_avoids_contract_gap | — | standard | ⚪ Missing |
| tests.test_typescript_checkpoint_ci.test_ts_enabled_internal_helper_without_jsdoc_becomes_skipped_advisory | — | standard | ⚪ Missing |
| tests.test_typescript_checkpoint_ci.test_ts_enabled_medium_block_comment_is_contract_gap | — | standard | ⚪ Missing |
| tests.test_typescript_checkpoint_ci.test_ts_enabled_unsupported_syntax_emits_non_blocking_advisory | — | standard | ⚪ Missing |
| tests.test_typescript_contract_presence.test_tsdoc_with_code_gap_is_not_attached_to_symbol | — | standard | ⚪ Missing |
| tests.test_typescript_not_supported_boundaries.test_typescript_adapter_discover_only_ts_and_excludes_js_family | — | standard | ⚪ Missing |
| tests.test_typescript_adapter_mvp.test_typescript_adapter_does_not_change_python_adapter_parse_file_behavior | — | standard | ⚪ Missing |
| tests.test_python_ddt_regression.test_typescript_binding_is_advisory_and_does_not_change_python_rules | — | standard | ⚪ Missing |
| tests.test_typescript_checkpoint_ci.test_typescript_checkpoint_categories_and_identity_fields_are_constrained | — | standard | ⚪ Missing |
| tests.test_checkpoint_json_additive_compat.test_typescript_contract_subject_json_has_task6a_ready_fields | — | standard | ⚪ Missing |
| tests.test_typescript_not_supported_boundaries.test_typescript_ddt_binding_is_advisory_not_supported | — | standard | ⚪ Missing |
| tests.test_typescript_checkpoint_ci.test_typescript_default_excluded_extensions_do_not_enter_checkpoint | — | standard | ⚪ Missing |
| tests.test_adapter_registry.test_typescript_enabled_in_config_but_not_implemented_does_not_crash | — | standard | ⚪ Missing |
| tests.test_index_builder_registry_integration.test_typescript_enabled_unavailable_does_not_affect_python_index | — | standard | ⚪ Missing |
| tests.test_sync_engine_registry_integration.test_typescript_enabled_unavailable_does_not_affect_python_status | — | standard | ⚪ Missing |
| tests.test_typescript_not_supported_boundaries.test_typescript_semantic_audit_is_skipped_without_contract_presence_or_ast | — | standard | ⚪ Missing |
| tests.test_typescript_not_supported_boundaries.test_typescript_unsupported_syntax_advisory_remains_non_blocking | — | standard | ⚪ Missing |
| tests.test_repair_guidance.test_unknown_checkpoint_category_graceful_degrade | — | standard | ⚪ Missing |
| tests.test_cli_module_capsule.test_unknown_module_does_not_crash_and_prints_friendly_message | — | standard | ⚪ Missing |
| tests.test_module_capsule_stale.test_unknown_module_is_friendly_stale | — | standard | ⚪ Missing |
| tests.test_module_capsule_stale.test_up_to_date_when_fingerprint_matches | — | standard | ⚪ Missing |
| tests.test_windows_abs_path_prefix.test_windows_abs_path_prefix | — | standard | ⚪ Missing |
| tests.test_workspace_paths.test_windows_posix_path_normalization | — | standard | ⚪ Missing |
| tests.test_init_wizard.test_wizard_language_prompt_comes_first | — | standard | ⚪ Missing |
| tests.test_cli_help_and_ux.test_workflow_help_exposes_start_checkpoint_finish_accept | — | standard | ⚪ Missing |
| tests.test_workspace_inspect.test_workspace_inspect_generated_views_count | — | standard | ⚪ Missing |
| tests.test_workspace_inspect.test_workspace_inspect_git_tracking_policy | — | standard | ⚪ Missing |
| tests.test_workspace_inspect.test_workspace_inspect_is_read_only_no_writes | — | standard | ⚪ Missing |
| tests.test_workspace_inspect.test_workspace_inspect_json_and_text_do_not_leak_absolute_paths | — | standard | ⚪ Missing |
| tests.test_workspace_inspect.test_workspace_inspect_legacy_detection_roles_and_severity | — | standard | ⚪ Missing |
| tests.test_workspace_inspect.test_workspace_inspect_reports_canonical_paths_repo_relative | — | standard | ⚪ Missing |
| tests.test_workspace_migrate.test_workspace_migrate_docs_export_plan_item_no_action | — | standard | ⚪ Missing |
| tests.test_workspace_migrate.test_workspace_migrate_dry_run_no_writes | — | standard | ⚪ Missing |
| tests.test_workspace_migrate.test_workspace_migrate_json_has_no_absolute_paths | — | standard | ⚪ Missing |
| tests.test_workspace_migrate.test_workspace_migrate_legacy_config_plan_item | — | standard | ⚪ Missing |
| tests.test_workspace_migrate.test_workspace_migrate_legacy_diary_plan_item_high_risk | — | standard | ⚪ Missing |
| tests.test_workspace_migrate.test_workspace_migrate_legacy_l2_metadata_plan_item | — | standard | ⚪ Missing |
| tests.test_workspace_migrate.test_workspace_migrate_module_readme_export_items | — | standard | ⚪ Missing |
| tests.test_diary_workspace_paths.test_workspace_outside_diary_paths_are_rejected | — | standard | ⚪ Missing |
| tests.test_workspace_i18n.test_workspace_text_i18n_zh | — | standard | ⚪ Missing |
| tests.test_config_update.test_write_config_and_update | — | standard | ⚪ Missing |
| tests.test_initializer.test_write_config_supports_language | — | standard | ⚪ Missing |
| tests.test_log_draft.test_write_diary_draft_output_writes_reports_and_rejects_diary_root | — | standard | ⚪ Missing |
| tests.test_contract_impact.test_write_function_hits_file_write_target_and_writes_files | — | standard | ⚪ Missing |
| tests.test_contract_presence.test_write_function_without_docstring_is_required | — | standard | ⚪ Missing |
| tests.test_log_draft.test_write_latest_diary_draft_cache_failure_is_warning_only | — | standard | ⚪ Missing |
| tests.test_log_draft.test_write_latest_diary_draft_cache_writes_markdown_and_json_wrapper | — | standard | ⚪ Missing |
| tests.test_module_capsule.test_write_module_capsule_rejects_export_root_outside_repo | — | standard | ⚪ Missing |
| tests.test_module_capsule.test_write_module_capsule_rejects_nested_parent_traversal_module_path | — | standard | ⚪ Missing |
| tests.test_module_capsule.test_write_module_capsule_rejects_parent_traversal_module_path | — | standard | ⚪ Missing |
| tests.test_module_capsule.test_write_module_capsule_writes_three_files | — | standard | ⚪ Missing |
| tests.test_module_capsule_stale.test_write_module_card_contains_frontmatter_fingerprint | — | standard | ⚪ Missing |
| tests.test_module_skill.test_write_module_skill_only_writes_skill_file | — | standard | ⚪ Missing |
| tests.test_workspace_paths.test_write_path_cannot_escape_repo_root | — | standard | ⚪ Missing |
| tests.test_project_structure.test_write_project_structure_returns_canonical_first | — | standard | ⚪ Missing |
| tests.test_change_window_snapshot.test_write_snapshot_creates_json_with_required_schema | — | standard | ⚪ Missing |
| tests.test_change_window_snapshot._FakeDDTValidator.validate | — | standard | ⚪ Missing |
| tests.test_index_builder.write_module | — | standard | ⚪ Missing |
| tests.test_sync_engine.write_module | — | standard | ⚪ Missing |
| tests.test_ddt_validate.write_test_file | — | standard | ⚪ Missing |

</details>

## Dependency (MVP)
- (TBD) 未来基于 import 简要分析模块依赖。

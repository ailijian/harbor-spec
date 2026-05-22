# Module: harbor/core

## Public API Summary
| Metric | Count |
|---|---:|
| Public by contract | 102 |
| Strict targets | 101 |
| Private-named but strict | 0 |
| Internal indexed | 591 |
| Strict targets missing DDT | 100 |
| Targets with DDT warnings | 0 |

## High-Risk Targets
| Function | File | Risk Focus | Scope | Strictness | Why |
|---|---|---|---|---|---|
| harbor.core.generated_verify.generated_verification_report_to_dict | harbor/core/generated_verify.py | JSON serialization | public | strict | JSON serialization, report serialization, generated verification |
| harbor.core.performance_baseline.runtime_performance_baseline_report_to_dict | harbor/core/performance_baseline.py | JSON serialization | public | strict | JSON serialization, report serialization, baseline state |
| harbor.core.generated_verify.GeneratedArtifactVerification.to_dict | harbor/core/generated_verify.py | JSON serialization | public | strict | JSON serialization, generated verification, generated context |
| harbor.core.generated_verify.GeneratedVerificationReport.to_dict | harbor/core/generated_verify.py | JSON serialization | public | strict | JSON serialization, generated verification, generated context |
| harbor.core.generated_verify.ModuleGeneratedVerification.to_dict | harbor/core/generated_verify.py | JSON serialization | public | strict | JSON serialization, generated verification, generated context |
| harbor.core.generated_verify.ProjectGeneratedVerification.to_dict | harbor/core/generated_verify.py | JSON serialization | public | strict | JSON serialization, generated verification, generated context |
| harbor.core.log_draft.write_diary_draft_output | harbor/core/log_draft.py | file write | public | strict | file write, diary persistence, log/change window |
| harbor.core.log_draft.write_diary_entry_from_draft | harbor/core/log_draft.py | file write | public | strict | file write, diary persistence, log/change window |
| harbor.core.log_draft.write_latest_diary_draft_cache | harbor/core/log_draft.py | file write | public | strict | file write, diary persistence, log/change window |
| harbor.core.workspace_inspect.workspace_inspect_report_to_dict | harbor/core/workspace_inspect.py | JSON serialization | unknown | unknown | JSON serialization, report serialization, workspace path |
| harbor.core.workspace_migrate.workspace_migrate_report_to_dict | harbor/core/workspace_migrate.py | JSON serialization | unknown | unknown | JSON serialization, report serialization, workspace path |
| harbor.core.contract_impact.contract_impact_report_to_dict | harbor/core/contract_impact.py | JSON serialization | public | strict | JSON serialization, report serialization, strict target |

### Contract / DDT Coverage Gaps
| Function | File | Scope | Strictness | DDT Status | Why |
|---|---|---|---|---|---|
| harbor.core.drafting.DiaryDrafter.__init__ | harbor/core/drafting.py | public | strict | ❌ Missing | Missing DDT, strict target, public surface |
| harbor.core.l2.L2Generator.__init__ | harbor/core/l2.py | public | strict | ❌ Missing | Missing DDT, strict target, public surface |
| harbor.core.index.IndexBuilder._iter_py_files | harbor/core/index.py | public | strict | ❌ Missing | Missing DDT, strict target, public surface |
| harbor.core.diary.DiaryManager.append_json_line | harbor/core/diary.py | public | strict | ❌ Missing | Missing DDT, strict target, public surface |
| harbor.core.init.Initializer.autodetect | harbor/core/init.py | public | strict | ❌ Missing | Missing DDT, strict target, public surface |
| harbor.core.index.IndexBuilder.build | harbor/core/index.py | public | strict | ❌ Missing | Missing DDT, strict target, public surface |
| harbor.core.audit.build_audit_prompt_context | harbor/core/audit.py | public | strict | ❌ Missing | Missing DDT, strict target, public surface |
| harbor.core.log_draft.build_diary_draft | harbor/core/log_draft.py | public | strict | ❌ Missing | Missing DDT, strict target, public surface |
| harbor.core.generated_verify.build_generated_verification_ci_result | harbor/core/generated_verify.py | public | strict | ❌ Missing | Missing DDT, strict target, public surface |
| harbor.core.generated_verify.build_generated_verification_report | harbor/core/generated_verify.py | public | strict | ❌ Missing | Missing DDT, strict target, public surface |

## Dependency Summary

**Outbound Dependencies**
- harbor/adapters (9 edges): harbor/adapters/base, harbor/adapters/python/compat, harbor/adapters/python/parser, ... (+6 more)
- harbor/utils (1 edges): harbor/utils/i18n

**Inbound Dependents**
- tests (2 edges): tests, tests/core
- harbor/cli (1 edges): harbor/cli

## Full Indexed Contracts
<details>
<summary>All indexed contracts</summary>

| Function | File | Scope | Strictness | DDT Status | Summary |
|---|---|---|---|---|---|
| harbor.core.audit.OpenAIProvider.__init__ | harbor/core/audit.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.console_output.CLIProgressReporter.__init__ | harbor/core/console_output.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.console_output._RichBatchProgress.__init__ | harbor/core/console_output.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.ddt.DDTScanner.__init__ | harbor/core/ddt.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.ddt.DDTValidator.__init__ | harbor/core/ddt.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.diary.DiaryManager.__init__ | harbor/core/diary.py | unknown | unknown | ⚪ Missing | 初始化 Diary 路径上下文（canonical 写入 + legacy 读取兼容）。 |
| harbor.core.drafting.DiaryDrafter.__init__ | harbor/core/drafting.py | public | strict | ❌ Missing | AI 辅助生成 Diary 草稿。 |
| harbor.core.git_utils.GitIgnoreMatcher.__init__ | harbor/core/git_utils.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.index.IndexBuilder.__init__ | harbor/core/index.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init.Initializer.__init__ | harbor/core/init.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init.ProjectDetector.__init__ | harbor/core/init.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init_wizard.InitWizard.__init__ | harbor/core/init_wizard.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.l2.L2Generator.__init__ | harbor/core/l2.py | public | strict | ❌ Missing | Initialize the L2 generator against a readonly index source. |
| harbor.core.storage.HarborDB.__init__ | harbor/core/storage.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.sync.SyncEngine.__init__ | harbor/core/sync.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.verification.VerificationTargetRef.__post_init__ | harbor/core/verification.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.ci._append_checkpoint_guidance_lines | harbor/core/ci.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init_wizard._append_missing_env_keys | harbor/core/init_wizard.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._append_text_value | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.storage.HarborDB._apply_pragmas | harbor/core/storage.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.project_structure._area_purpose | harbor/core/project_structure.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.context_integrity._as_repo_relative | harbor/core/context_integrity.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init_wizard.InitWizard._ask_advice_mode | harbor/core/init_wizard.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init_wizard.InitWizard._ask_language | harbor/core/init_wizard.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init_wizard.InitWizard._ask_project | harbor/core/init_wizard.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init_wizard.InitWizard._ask_yes_no | harbor/core/init_wizard.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.audit._audit_evidence_from_contract_source | harbor/core/audit.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.module_capsule._belongs_to_module | harbor/core/module_capsule.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.project_structure._belongs_to_module | harbor/core/project_structure.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._bucket_for_path | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.workspace._build_path | harbor/core/workspace.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.drafting.DiaryDrafter._build_prompt | harbor/core/drafting.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.l2._build_repo_import_graph | harbor/core/l2.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._build_risks | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.audit.SemanticGuard._build_subject_prompt | harbor/core/audit.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._build_suggested_diary_entry | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.generated_verify._build_summary | harbor/core/generated_verify.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._build_summary | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.readonly_index._build_transient_index | harbor/core/readonly_index.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.project_structure._build_transient_index_from_files | harbor/core/project_structure.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.verification._build_typescript_ddt_preview_report | harbor/core/verification.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._build_why | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.module_capsule._build_workflow_recommendations | harbor/core/module_capsule.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.generated_verify._cached_l2_body | harbor/core/generated_verify.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.project_structure._capsule_exists | harbor/core/project_structure.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.project_structure._capsule_export_exists | harbor/core/project_structure.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.workspace_inspect._check_git_ignored | harbor/core/workspace_inspect.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.ci._checkpoint_category_counts | harbor/core/ci.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.ci._checkpoint_category_priority | harbor/core/ci.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.ci._checkpoint_reason_for_entry | harbor/core/ci.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.ci._checkpoint_top_items | harbor/core/ci.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.ci._checkpoint_workflow_next_steps | harbor/core/ci.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init_prompt._choice_label | harbor/core/init_prompt.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._classify_affected_areas | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.workspace_inspect._classify_git_tracking | harbor/core/workspace_inspect.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.contract_impact._classify_tests_path | harbor/core/contract_impact.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.change_window._coerce_changed_files | harbor/core/change_window.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.change_window._coerce_mapping | harbor/core/change_window.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._coerce_validation_status | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.workspace_inspect._collect_advisory | harbor/core/workspace_inspect.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.ci._collect_checkpoint_next_steps | harbor/core/ci.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.project_structure._collect_fallback_files | harbor/core/project_structure.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.workspace_inspect._collect_generated_views | harbor/core/workspace_inspect.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.workspace_inspect._collect_git_tracking | harbor/core/workspace_inspect.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.l2.L2Generator._collect_integrity_inputs | harbor/core/l2.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.workspace_inspect._collect_legacy_paths | harbor/core/workspace_inspect.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.l2._collect_module_dependency_summary | harbor/core/l2.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.workspace_migrate._collect_module_readme_exports | harbor/core/workspace_migrate.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.ci._collect_next_steps | harbor/core/ci.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.doctor._collect_next_steps | harbor/core/doctor.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.sync.SyncEngine._collect_python_snapshot_items | harbor/core/sync.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.generated_verify._collect_repair_commands | harbor/core/generated_verify.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init.ProjectDetector._collect_typescript_entrypoints | harbor/core/init.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.verification._collect_typescript_preview_subjects | harbor/core/verification.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.audit._collect_typescript_preview_targets | harbor/core/audit.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.sync.SyncEngine._collect_typescript_snapshot_items | harbor/core/sync.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.audit._collect_typescript_subjects | harbor/core/audit.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.sync.SyncEngine._compare_snapshots | harbor/core/sync.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.generated_verify._compose_expected_canonical_l2_markdown | harbor/core/generated_verify.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.generated_verify._compose_expected_capsule_markdown | harbor/core/generated_verify.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.generated_verify._compose_expected_module_card_markdown | harbor/core/generated_verify.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.generated_verify._compose_expected_project_structure_markdown | harbor/core/generated_verify.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._compose_written_details | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.contract_impact._confidence_for_level | harbor/core/contract_impact.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.module_capsule._contracts_by_file | harbor/core/module_capsule.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.diary.DiaryManager._current_file_path | harbor/core/diary.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.ci._ddt_identity_defaults | harbor/core/ci.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.context_integrity._decode_scalar | harbor/core/context_integrity.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init.ProjectDetector._dedup | harbor/core/init.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._dedupe_changed_files | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.ci._dedupe_checkpoint_items | harbor/core/ci.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.verification._dedupe_preview_findings | harbor/core/verification.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.audit._dedupe_typescript_preview_findings | harbor/core/audit.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init_wizard._default_language | harbor/core/init_wizard.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.index_entry._default_name | harbor/core/index_entry.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init_wizard._default_project | harbor/core/init_wizard.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.l2._dependency_group | harbor/core/l2.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.ci._derive_checkpoint_identity | harbor/core/ci.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.ci._derive_qualified_name_and_symbol_kind | harbor/core/ci.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.generated_verify._derive_report_status | harbor/core/generated_verify.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._derive_validation_statuses | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.doctor._derived_view_detail_status | harbor/core/doctor.py | unknown | unknown | ⚪ Missing | 将内部 view status 归一化为可展示文本。 |
| harbor.core.init_prompt._detect_console_encoding | harbor/core/init_prompt.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init.ProjectDetector._detect_django | harbor/core/init.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init.ProjectDetector._detect_go | harbor/core/init.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init.ProjectDetector._detect_java | harbor/core/init.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init.ProjectDetector._detect_node | harbor/core/init.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init.ProjectDetector._detect_python_misc | harbor/core/init.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init.ProjectDetector._detect_typescript | harbor/core/init.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init.ProjectDetector._detect_workspace_markers | harbor/core/init.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.index._detect_workspace_root | harbor/core/index.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._determine_draft_status | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._discover_report_summaries | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.l2._display_strictness | harbor/core/l2.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.decorator.DecoratorEngine._docstring_node | harbor/core/decorator.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.audit._eligibility_message | harbor/core/audit.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init_wizard.InitWizard._emit_detected_summary | harbor/core/init_wizard.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.doctor._emit_doctor_phase | harbor/core/doctor.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init_wizard.InitWizard._emit_ide_guidance | harbor/core/init_wizard.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init_wizard.InitWizard._emit_next_steps | harbor/core/init_wizard.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init_wizard.InitWizard._emit_project_rules_guidance | harbor/core/init_wizard.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init_wizard.InitWizard._emit_typescript_guidance | harbor/core/init_wizard.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.storage.HarborDB._ensure_schema | harbor/core/storage.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.diary.DiaryManager._ensure_within_repo | harbor/core/diary.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.l2.L2Generator._ensure_within_root | harbor/core/l2.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.module_capsule._ensure_within_root | harbor/core/module_capsule.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.diary.DiaryManager._entry_dedupe_key | harbor/core/diary.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.audit._evaluate_python_audit_eligibility | harbor/core/audit.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.audit._evaluate_typescript_audit_eligibility | harbor/core/audit.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init.ProjectDetector._exclude_covers_root | harbor/core/init.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._extract_bullet_items | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.drafting.DiaryDrafter._extract_code_context | harbor/core/drafting.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._extract_first_safe_text_block | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.decorator.DecoratorEngine._extract_functions | harbor/core/decorator.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.l2._extract_import_tokens | harbor/core/l2.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.module_capsule._extract_import_tokens | harbor/core/module_capsule.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._extract_latest_git_head | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._extract_latest_snapshot_timestamp | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._extract_markdown_section | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._extract_markdown_summary_sections | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._extract_structured_fields_from_json_draft | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.project_structure._extract_toml_string_block | harbor/core/project_structure.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.index.IndexBuilder._file_hash | harbor/core/index.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init.ProjectDetector._filter_excludes | harbor/core/init.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.doctor._filter_safe_next_steps | harbor/core/doctor.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.contract_impact._finding_to_dict | harbor/core/contract_impact.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._format_area_list | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.generated_verify._format_artifact_lines | harbor/core/generated_verify.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.module_capsule._format_bullets | harbor/core/module_capsule.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._format_changed_files | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.l2._format_dependency_group_rows | harbor/core/l2.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.change_window._format_iso8601_utc | harbor/core/change_window.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._format_noop_changed_files | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._format_noop_reports | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._format_noop_snapshots | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._format_reports | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._format_snapshot_group | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._format_snapshot_line | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.change_window._format_snapshot_stamp | harbor/core/change_window.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.stale._format_view_lines | harbor/core/stale.py | unknown | unknown | ⚪ Missing | 格式化单个视图状态的文本行。 |
| harbor.core.diary.DiaryManager._from_dict | harbor/core/diary.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init.ProjectDetector._get_default_excludes | harbor/core/init.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.ci._get_optional_dict_list | harbor/core/ci.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.ci._get_optional_list | harbor/core/ci.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.ci._get_optional_text | harbor/core/ci.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.l2.L2Generator._get_repo_import_graph | harbor/core/l2.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.change_window._git_status_lines | harbor/core/change_window.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init_wizard._has_env_ignore | harbor/core/init_wizard.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.decorator.DecoratorEngine._has_scope_tag | harbor/core/decorator.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init.ProjectDetector._has_typescript_sources | harbor/core/init.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.index.IndexBuilder._index_entry | harbor/core/index.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.audit._ineligible_audit_result | harbor/core/audit.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.project_structure._infer_area | harbor/core/project_structure.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._infer_contract_impact | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.audit._infer_file_path_from_contract | harbor/core/audit.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.ci._is_blocking_checkpoint_target | harbor/core/ci.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.contract_impact._is_contract_asserting_test | harbor/core/contract_impact.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init.ProjectDetector._is_dangerous_python_exclude | harbor/core/init.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._is_diary_changed_file | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.contract_impact._is_docs_or_rules_path | harbor/core/contract_impact.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._is_env_or_secrets_path | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.decorator.DecoratorEngine._is_filtered_name | harbor/core/decorator.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.contract_impact._is_generated_view_module | harbor/core/contract_impact.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init_prompt._is_interactive | harbor/core/init_prompt.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.contract_impact._is_public_cli_path | harbor/core/contract_impact.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.contract_impact._is_test_path | harbor/core/contract_impact.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.contract_impact._is_to_dict_like | harbor/core/contract_impact.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init_wizard._is_tty | harbor/core/init_wizard.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.sync.SyncEngine._is_typescript_path | harbor/core/sync.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init.ProjectDetector._is_typescript_source_file | harbor/core/init.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.audit._is_typescript_target | harbor/core/audit.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._is_within | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.contract_impact._is_write_like | harbor/core/contract_impact.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.index.IndexBuilder._iter_code_roots | harbor/core/index.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.sync.SyncEngine._iter_code_roots | harbor/core/sync.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.index.IndexBuilder._iter_files_by_enabled_adapters | harbor/core/index.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.sync.SyncEngine._iter_files_by_enabled_adapters | harbor/core/sync.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.decorator.DecoratorEngine._iter_function_nodes | harbor/core/decorator.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init.ProjectDetector._iter_package_export_targets | harbor/core/init.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.ddt.DDTScanner._iter_py_files | harbor/core/ddt.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.index.IndexBuilder._iter_py_files | harbor/core/index.py | public | strict | ❌ Missing | 生成待扫描的 Python 文件列表（支持 Git 感知剪枝）。 |
| harbor.core.sync.SyncEngine._iter_py_files | harbor/core/sync.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.diary.DiaryManager._iter_read_dirs | harbor/core/diary.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.context_integrity._json_stable_hash | harbor/core/context_integrity.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.project_structure._key_files_display | harbor/core/project_structure.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.module_capsule._keyword_tokens | harbor/core/module_capsule.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.drafting.DiaryDrafter._kv_fallback_parse | harbor/core/drafting.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init_wizard.InitWizard._label_typescript_preset | harbor/core/init_wizard.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._latest_accept_snapshot | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.decorator.DecoratorEngine._leading_whitespace | harbor/core/decorator.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.index.IndexBuilder._load_cache | harbor/core/index.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.ddt.DDTScanner._load_config | harbor/core/ddt.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.index.IndexBuilder._load_config | harbor/core/index.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.sync.SyncEngine._load_config | harbor/core/sync.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.advice_config._load_config_advice | harbor/core/advice_config.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.readonly_index._load_existing_db_index | harbor/core/readonly_index.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.ddt.DDTValidator._load_index | harbor/core/ddt.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.l2.L2Generator._load_index | harbor/core/l2.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.module_capsule._load_index | harbor/core/module_capsule.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.project_structure._load_index | harbor/core/project_structure.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.ddt.DDTValidator._load_map | harbor/core/ddt.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.l2.L2Generator._load_meta | harbor/core/l2.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init.ProjectDetector._load_package_json | harbor/core/init.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.sync.SyncEngine._load_previous_snapshot_from_artifact | harbor/core/sync.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._load_report_summary | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init_wizard._load_template_text | harbor/core/init_wizard.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.index._load_worker_typescript_config | harbor/core/index.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.contract_presence._looks_like_contract_doc | harbor/core/contract_presence.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.context_integrity._looks_like_windows_absolute_path | harbor/core/context_integrity.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.l2._looks_like_windows_absolute_path | harbor/core/l2.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.project_structure._looks_like_windows_absolute_path | harbor/core/project_structure.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.verification._looks_like_windows_absolute_path | harbor/core/verification.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.workspace._looks_like_windows_absolute_path | harbor/core/workspace.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.verification._make_repo_relative_target_id | harbor/core/verification.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init_wizard._mask_key | harbor/core/init_wizard.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.contract_impact._max_level | harbor/core/contract_impact.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._merge_affected_area_mappings | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._merge_changed_files | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.doctor._merge_status | harbor/core/doctor.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.workspace_migrate._module_dir_has_python_files | harbor/core/workspace_migrate.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.module_capsule._module_profile | harbor/core/module_capsule.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.ci._module_qual_from_file_path | harbor/core/ci.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.decorator.DecoratorEngine._module_qual_from_path | harbor/core/decorator.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.module_capsule._module_specific_checklist_lines | harbor/core/module_capsule.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._non_diary_changed_files | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.generated_verify._normalize_body | harbor/core/generated_verify.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.context_integrity._normalize_body_for_compare | harbor/core/context_integrity.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._normalize_changed_file | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.ci._normalize_checkpoint_key_path | harbor/core/ci.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._normalize_cli_input_path | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | Normalize repo-relative CLI paths so Windows separators s... |
| harbor.core.log_draft._normalize_contract_impact | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.contract_presence._normalize_contract_path | harbor/core/contract_presence.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.baseline_artifact._normalize_contract_presence | harbor/core/baseline_artifact.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.diary.DiaryManager._normalize_for_hash | harbor/core/diary.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init.ProjectDetector._normalize_glob | harbor/core/init.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.baseline_artifact._normalize_hash | harbor/core/baseline_artifact.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.baseline_artifact._normalize_items | harbor/core/baseline_artifact.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.stale._normalize_l2_body_for_export_compare | harbor/core/stale.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.stale._normalize_l2_markdown_for_stale | harbor/core/stale.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.l2.L2Generator._normalize_meta_key | harbor/core/l2.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.advice_config._normalize_mode | harbor/core/advice_config.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.advice_config._normalize_mode_optional | harbor/core/advice_config.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.contract_impact._normalize_path | harbor/core/contract_impact.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.workspace._normalize_path_like | harbor/core/workspace.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.context_integrity._normalize_rel_path | harbor/core/context_integrity.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.module_capsule._normalize_rel_path | harbor/core/module_capsule.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.project_structure._normalize_rel_path | harbor/core/project_structure.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.sync.SyncEngine._normalize_repo_file_path | harbor/core/sync.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._normalize_report_status | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.audit._normalize_subject_source_path | harbor/core/audit.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.contract_impact._normalize_symbol | harbor/core/contract_impact.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.contract_impact._normalize_symbol_for_classification | harbor/core/contract_impact.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init_wizard.InitWizard._normalize_typescript_contract_strategy | harbor/core/init_wizard.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init_wizard.InitWizard._normalize_typescript_preset | harbor/core/init_wizard.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.context_integrity._normalized_source_content_for_fingerprint | harbor/core/context_integrity.py | unknown | unknown | ⚪ Missing | Return fingerprint input bytes with cross-platform text n... |
| harbor.core.context_integrity._now_iso | harbor/core/context_integrity.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init.ProjectDetector._package_has_exports | harbor/core/init.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._parse_affected_areas_section | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.audit._parse_audit_output | harbor/core/audit.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._parse_diary_draft_lines | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.doctor._parse_generated_frontmatter_safely | harbor/core/doctor.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.change_window._parse_git_status_line | harbor/core/change_window.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init.ProjectDetector._parse_gitignore | harbor/core/init.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._parse_markdown_draft_fields | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.verification._parse_preview_binding_for_validation | harbor/core/verification.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.ci._parse_target_id | harbor/core/ci.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.diary.DiaryManager._parse_ts | harbor/core/diary.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.verification._parse_typescript_ddt_preview_binding | harbor/core/verification.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._parse_validation_lines | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._pick_first_nonempty | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.storage.HarborDB._posix_rel | harbor/core/storage.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.verification._preview_finding | harbor/core/verification.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init_wizard.InitWizard._print | harbor/core/init_wizard.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.ci._push_status_failures | harbor/core/ci.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.performance_baseline._pushd | harbor/core/performance_baseline.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.sync._python_snapshot_item | harbor/core/sync.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.module_capsule._rank_debug_files | harbor/core/module_capsule.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.module_capsule._rank_tests | harbor/core/module_capsule.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._read_draft_source_file | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init_wizard._read_env_keys | harbor/core/init_wizard.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._read_last_log_marker | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._read_last_log_marker_timestamp | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._read_marker_value | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.l2.L2Generator._read_meta_file | harbor/core/l2.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.project_structure._read_project_metadata | harbor/core/project_structure.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._reject_diary_output_path | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init_prompt._render_inline_options | harbor/core/init_prompt.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.performance_baseline._render_metric_cell | harbor/core/performance_baseline.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.context_integrity._render_scalar | harbor/core/context_integrity.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.generated_verify._repo_display_path | harbor/core/generated_verify.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.l2._repo_relative_index_path | harbor/core/l2.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.baseline_artifact._require_bool | harbor/core/baseline_artifact.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.baseline_artifact._require_text | harbor/core/baseline_artifact.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._resolve_allowed_from_draft_path | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.baseline_artifact._resolve_artifact_path | harbor/core/baseline_artifact.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.diary.DiaryManager._resolve_author | harbor/core/diary.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.l2.L2Generator._resolve_canonical_readme_path | harbor/core/l2.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._resolve_cli_input_path | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._resolve_diary_draft_boundary | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.module_capsule._resolve_docs_export_modules_root | harbor/core/module_capsule.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.project_structure._resolve_docs_export_project_structure_path | harbor/core/project_structure.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.l2.L2Generator._resolve_export_readme_path | harbor/core/l2.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.l2._resolve_file_imports | harbor/core/l2.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.l2._resolve_import_token_to_module | harbor/core/l2.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.readonly_index._resolve_index_path | harbor/core/readonly_index.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._resolve_latest_draft_source | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.diary.DiaryManager._resolve_legacy_diary_dirs | harbor/core/diary.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.l2.L2Generator._resolve_meta_path | harbor/core/l2.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.module_capsule._resolve_module_target_dir | harbor/core/module_capsule.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._resolve_output_path | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.diary.DiaryManager._resolve_repo_root | harbor/core/diary.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.audit._resolve_subject_source_path | harbor/core/audit.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init_wizard.InitWizard._resolve_typescript_entrypoints | harbor/core/init_wizard.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init_wizard.InitWizard._resolve_typescript_language_config | harbor/core/init_wizard.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init.ProjectDetector._resolve_typescript_source_candidate | harbor/core/init.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.audit._resolve_typescript_subject_for_entry | harbor/core/audit.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.change_window._run_git | harbor/core/change_window.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init_prompt._safe_console_print | harbor/core/init_prompt.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._safe_excerpt | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.drafting.DiaryDrafter._safe_json_parse | harbor/core/drafting.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.l2.L2Generator._safe_module_subpath | harbor/core/l2.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.module_capsule._safe_module_subpath | harbor/core/module_capsule.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._safe_multiline_excerpt | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.l2._safe_read_text | harbor/core/l2.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.module_capsule._safe_read_text | harbor/core/module_capsule.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._sanitize_affected_areas | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.ci._sanitize_boundary_evidence_items | harbor/core/ci.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.ci._sanitize_checkpoint_contract_impact | harbor/core/ci.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.generated_verify._sanitize_details | harbor/core/generated_verify.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._sanitize_evidence | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.ci._sanitize_json_text | harbor/core/ci.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.contract_impact._sanitize_json_text | harbor/core/contract_impact.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.doctor._sanitize_json_text | harbor/core/doctor.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.stale._sanitize_json_text | harbor/core/stale.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._sanitize_markdown_text | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.l2.L2Generator._sanitize_meta_entries | harbor/core/l2.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.project_structure._sanitize_module | harbor/core/project_structure.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.stale._sanitize_module_for_json | harbor/core/stale.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.generated_verify._sanitize_rel_path | harbor/core/generated_verify.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._sanitize_risks | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.ci._sanitize_single_path | harbor/core/ci.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.contract_impact._sanitize_single_path | harbor/core/contract_impact.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.doctor._sanitize_single_path | harbor/core/doctor.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.stale._sanitize_single_path | harbor/core/stale.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.ci._sanitize_string_list | harbor/core/ci.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.ci._sanitize_summary | harbor/core/ci.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._sanitize_validation | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.index.IndexBuilder._save_cache | harbor/core/index.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.l2.L2Generator._save_meta | harbor/core/l2.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.module_capsule._score_debug_file | harbor/core/module_capsule.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.module_capsule._score_test_candidate | harbor/core/module_capsule.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._select_snapshots | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init_wizard.InitWizard._select_typescript_preset | harbor/core/init_wizard.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.audit._semantic_preview_finding_from_result | harbor/core/audit.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.project_structure._skill_exists | harbor/core/project_structure.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.audit._slice_source_excerpt | harbor/core/audit.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.change_window._snapshot_from_payload | harbor/core/change_window.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._snapshot_summary | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.module_capsule._sort_unique | harbor/core/module_capsule.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.contract_impact._sorted_findings | harbor/core/contract_impact.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.index_entry._source_confidence_summary | harbor/core/index_entry.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.index_entry._source_fingerprints | harbor/core/index_entry.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.index_entry._source_kinds | harbor/core/index_entry.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._split_list_values | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.module_capsule._stable_contract_rows | harbor/core/module_capsule.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.sync.SyncEngine._status_entry_from_snapshot_item | harbor/core/sync.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.doctor._status_text | harbor/core/doctor.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.doctor._status_to_json | harbor/core/doctor.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.l2._strictness_rank | harbor/core/l2.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.module_capsule._strictness_rank | harbor/core/module_capsule.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.path_normalization._strip_root_prefix | harbor/core/path_normalization.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.verification._strongest_contract_confidence | harbor/core/verification.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.audit._strongest_subject_confidence | harbor/core/audit.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.verification._subject_preview_metadata | harbor/core/verification.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.sync._subject_source_confidence_summary | harbor/core/sync.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.sync._subject_source_fingerprints | harbor/core/sync.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.sync._subject_source_kinds | harbor/core/sync.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.generated_verify._suggest_docs_refresh | harbor/core/generated_verify.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._summarize_affected_areas_for_details | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.module_capsule._summarize_strictness | harbor/core/module_capsule.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._summarize_validation_for_details | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.project_structure._supporting_area_purpose | harbor/core/project_structure.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.project_structure._table_cell | harbor/core/project_structure.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init_prompt._title_with_marker | harbor/core/init_prompt.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.advice_config._to_bool | harbor/core/advice_config.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.audit._to_bool | harbor/core/audit.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.verification._to_bool | harbor/core/verification.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.workspace._to_bool | harbor/core/workspace.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.workspace_inspect._to_display_path | harbor/core/workspace_inspect.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.workspace_migrate._to_display_path | harbor/core/workspace_migrate.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.project_structure._to_project_relative_path | harbor/core/project_structure.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.l2._to_repo_relative | harbor/core/l2.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft._to_repo_relative_display | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.drafting.DiaryDrafter._trim_segment | harbor/core/drafting.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.console_output._truthy_env | harbor/core/console_output.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init_prompt._try_arrow_select | harbor/core/init_prompt.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.audit._typescript_ineligibility_hint | harbor/core/audit.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.doctor._unique | harbor/core/doctor.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init_wizard._update_managed_block | harbor/core/init_wizard.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.diary.DiaryManager._utc_now_iso | harbor/core/diary.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.baseline_artifact._validate_artifact | harbor/core/baseline_artifact.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.verification._validate_preview_binding_against_subject | harbor/core/verification.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.workspace._validate_within_repo | harbor/core/workspace.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.module_capsule._workflow_file_matches | harbor/core/module_capsule.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.module_capsule._workflow_group_specs | harbor/core/module_capsule.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.module_capsule._workflow_test_matches | harbor/core/module_capsule.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init_wizard._write_file_with_policy | harbor/core/init_wizard.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.context_integrity._yaml_quote | harbor/core/context_integrity.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.project_structure._yes_no | harbor/core/project_structure.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.index.IndexBuilder.adapter | harbor/core/index.py | unknown | unknown | ⚪ Missing | Backward-compatible adapter accessor without instance har... |
| harbor.core.sync.SyncEngine.adapter | harbor/core/sync.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.diary.DiaryManager.append_json_line | harbor/core/diary.py | public | strict | ❌ Missing | Append one structured JSON line to canonical diary storage. |
| harbor.core.decorator.DecoratorEngine.apply | harbor/core/decorator.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.audit.SemanticGuard.audit | harbor/core/audit.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.audit.SemanticGuard.audit_subject | harbor/core/audit.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init.Initializer.autodetect | harbor/core/init.py | public | strict | ❌ Missing | 高级启发式自动探测。 |
| harbor.core.console_output.CLIProgressReporter.batch | harbor/core/console_output.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.index.IndexBuilder.build | harbor/core/index.py | public | strict | ❌ Missing | 构建或增量更新 L3 索引到缓存。 |
| harbor.core.audit.build_audit_prompt_context | harbor/core/audit.py | public | strict | ❌ Missing | Build the unified prompt context consumed by semantic-aud... |
| harbor.core.baseline_artifact.build_checkpoint_baseline_artifact | harbor/core/baseline_artifact.py | unknown | unknown | ⚪ Missing | Build the accepted checkpoint baseline artifact payload. |
| harbor.core.ci.build_checkpoint_ci_result | harbor/core/ci.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.console_output.build_cli_progress | harbor/core/console_output.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.context_integrity.build_context_integrity_metadata | harbor/core/context_integrity.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.contract_impact.build_contract_impact_report | harbor/core/contract_impact.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft.build_diary_draft | harbor/core/log_draft.py | public | strict | ❌ Missing | Build a deterministic diary draft from existing change-wi... |
| harbor.core.ci.build_doctor_ci_result | harbor/core/ci.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.doctor.build_doctor_report | harbor/core/doctor.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.generated_verify.build_generated_verification_ci_result | harbor/core/generated_verify.py | public | strict | ❌ Missing | Build the public CI gate result for verify-generated. |
| harbor.core.generated_verify.build_generated_verification_report | harbor/core/generated_verify.py | public | strict | ❌ Missing | Verify tracked generated context by recomputing expected ... |
| harbor.core.log_draft.build_log_write_preview | harbor/core/log_draft.py | public | strict | ❌ Missing | Build summary-level preview data for interactive `harbor ... |
| harbor.core.module_capsule.build_module_card_frontmatter | harbor/core/module_capsule.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.audit.SemanticGuard.build_prompt | harbor/core/audit.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.audit.SemanticGuard.build_prompt_from_context | harbor/core/audit.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.audit.build_python_audit_subject | harbor/core/audit.py | public | strict | ❌ Missing | Adapt the existing Python semantic-audit path to the unif... |
| harbor.core.performance_baseline.build_runtime_baseline_observation | harbor/core/performance_baseline.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.performance_baseline.build_runtime_performance_baseline_report | harbor/core/performance_baseline.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft.build_saved_diary_draft_output_path | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | Build a timestamped safe reports path for `harbor log dra... |
| harbor.core.ci.build_stale_ci_result | harbor/core/ci.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.audit.build_typescript_audit_subject | harbor/core/audit.py | public | strict | ❌ Missing | Adapt one TypeScript `ContractSubject` into the unified a... |
| harbor.core.audit.build_typescript_semantic_audit_preview | harbor/core/audit.py | public | strict | ❌ Missing | Build the additive TypeScript semantic-audit preview report. |
| harbor.core.workspace_inspect.build_workspace_inspect_report | harbor/core/workspace_inspect.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.workspace_migrate.build_workspace_migrate_dry_run_report | harbor/core/workspace_migrate.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.workspace.build_workspace_paths | harbor/core/workspace.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft.build_written_diary_entry | harbor/core/log_draft.py | public | strict | ❌ Missing | Build one structured written diary entry payload from an ... |
| harbor.core.l2.L2Generator.canonical_readme_path | harbor/core/l2.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.change_window.change_window_dir | harbor/core/change_window.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.module_skill.check_capsule_ready_for_skill | harbor/core/module_skill.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.stale.check_l2_readme_export_stale | harbor/core/stale.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.stale.check_l2_readme_stale | harbor/core/stale.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.module_capsule.check_module_capsule_stale | harbor/core/module_capsule.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.stale.check_module_derived_views_stale | harbor/core/stale.py | public | strict | ❌ Missing | Check one module's derived-view stale status against fres... |
| harbor.core.sync.SyncEngine.check_status | harbor/core/sync.py | public | strict | ✅ Valid | 对比缓存索引与当前代码，输出 Harbor 上下文状态。 |
| harbor.core.ci.checkpoint_ci_result_to_dict | harbor/core/ci.py | public | strict | ❌ Missing | 将 CheckpointCIResult 序列化为 `checkpoint --ci` 公开 CI JSON pa... |
| harbor.core.ci.checkpoint_ci_summary_to_dict | harbor/core/ci.py | public | strict | ❌ Missing | 将 CheckpointCIResult 序列化为 `checkpoint --ci --format json ... |
| harbor.core.ci.ci_result_to_dict | harbor/core/ci.py | public | strict | ❌ Missing | 将通用 CIResult 序列化为 checkpoint 之外的公开 CI JSON payload。 |
| harbor.core.contract_impact.classify_contract_impact_for_docstring_diff | harbor/core/contract_impact.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.contract_impact.classify_contract_impact_for_file_path | harbor/core/contract_impact.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.contract_impact.classify_contract_impact_for_function_change | harbor/core/contract_impact.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.contract_impact.classify_contract_impact_from_status_record | harbor/core/contract_impact.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.project_structure.classify_project_area | harbor/core/project_structure.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.l2.L2Generator.collect_all_indexed_modules | harbor/core/l2.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.l2.collect_all_indexed_modules | harbor/core/l2.py | public | strict | ❌ Missing | Collect normalized module paths from readonly index records. |
| harbor.core.changed_scope.collect_changed_modules_from_status | harbor/core/changed_scope.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.changed_scope.collect_changed_paths_from_status | harbor/core/changed_scope.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.sync.SyncEngine.collect_current_snapshot | harbor/core/sync.py | unknown | unknown | ⚪ Missing | Collect the current comparable checkpoint snapshot from s... |
| harbor.core.change_window.collect_git_workspace_state | harbor/core/change_window.py | unknown | unknown | ⚪ Missing | Collect lightweight git metadata for change-window snapsh... |
| harbor.core.module_capsule.collect_module_context | harbor/core/module_capsule.py | public | strict | ❌ Missing | Collect readonly context records used to render one modul... |
| harbor.core.l2.collect_modules_from_paths | harbor/core/l2.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.project_structure.collect_project_structure_context | harbor/core/project_structure.py | public | strict | ❌ Missing | Collect the canonical project-structure context from inde... |
| harbor.core.project_structure.collect_project_structure_integrity_inputs | harbor/core/project_structure.py | public | strict | ❌ Missing | Collect deterministic integrity inputs for project-struct... |
| harbor.core.performance_baseline.collect_runtime_baseline_context_metrics | harbor/core/performance_baseline.py | public | standard | ⚪ Missing | Collect repository-wide context counts for performance ba... |
| harbor.core.context_integrity.compose_markdown_with_frontmatter | harbor/core/context_integrity.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.utils.compute_body_hash | harbor/core/utils.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.context_integrity.compute_contract_fingerprint | harbor/core/context_integrity.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.context_integrity.compute_generator_fingerprint | harbor/core/context_integrity.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.l2.L2Generator.compute_meta_hash | harbor/core/l2.py | public | strict | ❌ Missing | Hash L2 body content using the canonical `_meta.json` nor... |
| harbor.core.module_capsule.compute_module_fingerprint | harbor/core/module_capsule.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.context_integrity.compute_source_fingerprint | harbor/core/context_integrity.py | unknown | unknown | ⚪ Missing | Compute a deterministic generated-context source fingerpr... |
| harbor.core.init_prompt.confirm | harbor/core/init_prompt.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.context_integrity.content_without_generated_at_for_compare | harbor/core/context_integrity.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.contract_impact.contract_impact_report_to_dict | harbor/core/contract_impact.py | public | strict | ❌ Missing | Serialize contract-impact analysis into stable JSON output. |
| harbor.core.index_entry.contract_subject_to_index_entry | harbor/core/index_entry.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.audit.TypeScriptSemanticAuditPreviewFinding.dedupe_key | harbor/core/audit.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.ci.CheckpointCIItem.dedupe_key | harbor/core/ci.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.verification.TypeScriptDDTPreviewFinding.dedupe_key | harbor/core/verification.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.utils.derive_adopted_roots | harbor/core/utils.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init.ProjectDetector.detect | harbor/core/init.py | public | strict | ❌ Missing | 启发式探测技术栈并生成配置建议。 |
| harbor.core.init.Initializer.detect_code_roots | harbor/core/init.py | public | strict | ❌ Missing | 智能探测项目代码根目录。 |
| harbor.core.console_output.detect_console_encoding | harbor/core/console_output.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.changed_scope.detect_generator_integrity_changes | harbor/core/changed_scope.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.module_capsule.detect_tests_for_module | harbor/core/module_capsule.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init.Initializer.detect_typescript_hints | harbor/core/init.py | unknown | unknown | ⚪ Missing | Detect TypeScript onboarding hints for `harbor init`. |
| harbor.core.init.ProjectDetector.detect_typescript_hints | harbor/core/init.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.utils.discover_indexable_files | harbor/core/utils.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.advice_config.AdviceSettings.enabled | harbor/core/advice_config.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.audit.evaluate_audit_eligibility | harbor/core/audit.py | public | strict | ❌ Missing | Evaluate whether a subject may enter semantic audit. |
| harbor.core.contract_presence.evaluate_contract_presence | harbor/core/contract_presence.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.changed_scope.expand_modules_with_indexed_parents | harbor/core/changed_scope.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.diary.DiaryManager.export_markdown | harbor/core/diary.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.context_integrity.extract_integrity_fingerprints | harbor/core/context_integrity.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.utils.find_function_node | harbor/core/utils.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.ci.format_checkpoint_ci_result | harbor/core/ci.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.ci.format_checkpoint_workflow_summary | harbor/core/ci.py | public | strict | ❌ Missing | Render the default `harbor checkpoint` text output in a s... |
| harbor.core.ci.format_ci_result | harbor/core/ci.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.contract_impact.format_contract_impact_report | harbor/core/contract_impact.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.doctor.format_doctor_report | harbor/core/doctor.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.generated_verify.format_generated_verification_report | harbor/core/generated_verify.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.performance_baseline.format_runtime_performance_baseline_report | harbor/core/performance_baseline.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.stale.format_stale_summary | harbor/core/stale.py | unknown | unknown | ⚪ Missing | 将 stale 检查结果渲染为 CLI 文本摘要。 |
| harbor.core.workspace_inspect.format_workspace_inspect_report | harbor/core/workspace_inspect.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.workspace_migrate.format_workspace_migrate_report | harbor/core/workspace_migrate.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.verification.VerificationBinding.from_legacy_ddt_binding | harbor/core/verification.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.git_utils.GitIgnoreMatcher.from_root | harbor/core/git_utils.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.index_entry.function_contract_to_index_entry | harbor/core/index_entry.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.l2.L2Generator.generate | harbor/core/l2.py | public | strict | ❌ Missing | 生成指定模块的 L2 README Markdown 文本。 |
| harbor.core.module_capsule.generate_debug_playbook | harbor/core/module_capsule.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.drafting.DiaryDrafter.generate_draft | harbor/core/drafting.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.module_capsule.generate_module_card | harbor/core/module_capsule.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.module_skill.generate_module_skill | harbor/core/module_skill.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.project_structure.generate_project_structure_markdown | harbor/core/project_structure.py | public | strict | ❌ Missing | Render a deterministic Markdown view from project-structu... |
| harbor.core.module_capsule.generate_review_checklist | harbor/core/module_capsule.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.generated_verify.generated_verification_report_to_dict | harbor/core/generated_verify.py | public | strict | ❌ Missing | Serialize the verify-generated domain report to the publi... |
| harbor.core.repair_guidance.generic_conservative_guidance | harbor/core/repair_guidance.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.storage.HarborDB.get_all_files | harbor/core/storage.py | public | strict | ❌ Missing | 列出所有已索引文件及其 mtime。 |
| harbor.core.storage.HarborDB.get_file | harbor/core/storage.py | public | strict | ❌ Missing | 查询单文件记录。 |
| harbor.core.storage.HarborDB.get_file_entries | harbor/core/storage.py | public | strict | ❌ Missing | 查询指定文件的所有条目。 |
| harbor.core.change_window.get_latest_change_window | harbor/core/change_window.py | unknown | unknown | ⚪ Missing | Return the newest readable snapshot, optionally filtered ... |
| harbor.core.repair_guidance.guidance_for_checkpoint_category | harbor/core/repair_guidance.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.repair_guidance.guidance_for_doctor_item | harbor/core/repair_guidance.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.repair_guidance.guidance_for_stale_item | harbor/core/repair_guidance.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.index_entry.index_entry_to_cache_item | harbor/core/index_entry.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.audit.LLMProvider.infer | harbor/core/audit.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.audit.MockProvider.infer | harbor/core/audit.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.audit.OpenAIProvider.infer | harbor/core/audit.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.l2.infer_module_from_path | harbor/core/l2.py | unknown | unknown | ⚪ Missing | 从文件路径推断模块目录（统一为 POSIX 风格）。 |
| harbor.core.console_output.is_ci_environment | harbor/core/console_output.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.contract_presence.is_contract_required | harbor/core/contract_presence.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.index.IndexBuilder.iter_build | harbor/core/index.py | public | strict | ❌ Missing | 以生成器方式构建索引，逐文件产出进度事件。 |
| harbor.core.utils.iter_project_files | harbor/core/utils.py | public | strict | ❌ Missing | 生成待扫描的 Python 文件列表（统一剪枝逻辑）。 |
| harbor.core.change_window.list_change_windows | harbor/core/change_window.py | unknown | unknown | ⚪ Missing | List readable change-window snapshots from newest to oldest. |
| harbor.core.diary.DiaryManager.load_active | harbor/core/diary.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.baseline_artifact.load_checkpoint_baseline_artifact | harbor/core/baseline_artifact.py | unknown | unknown | ⚪ Missing | Load and validate the accepted checkpoint baseline artifa... |
| harbor.core.readonly_index.load_readonly_index | harbor/core/readonly_index.py | public | strict | ❌ Missing | Load a read-only Harbor index snapshot for analysis paths. |
| harbor.core.verification.load_typescript_ddt_preview_sidecar | harbor/core/verification.py | public | strict | ❌ Missing | Load the TypeScript DDT preview sidecar only when preview... |
| harbor.core.workspace.load_workspace_config | harbor/core/workspace.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.workspace.load_workspace_paths | harbor/core/workspace.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.diary.DiaryManager.log | harbor/core/diary.py | public | strict | ❌ Missing | 写入一条 DiaryEntry 到当月 JSONL。 |
| harbor.core.path_normalization.looks_like_absolute_path | harbor/core/path_normalization.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.git_utils.GitIgnoreMatcher.match_dir | harbor/core/git_utils.py | public | strict | ❌ Missing | 判断相对路径目录是否被忽略（用于剪枝）。 |
| harbor.core.git_utils.GitIgnoreMatcher.match_file | harbor/core/git_utils.py | public | strict | ❌ Missing | 判断相对路径文件是否被忽略。 |
| harbor.core.context_integrity.merge_generated_at | harbor/core/context_integrity.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.storage.HarborDB.migrate_from_json | harbor/core/storage.py | public | strict | ❌ Missing | 从旧版 JSON 索引迁移到 SQLite。 |
| harbor.core.module_capsule.module_capsule_dir | harbor/core/module_capsule.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.baseline_artifact.normalize_baseline_item_path | harbor/core/baseline_artifact.py | unknown | unknown | ⚪ Missing | Normalize one baseline item path into repo-relative POSIX... |
| harbor.core.changed_scope.normalize_changed_path | harbor/core/changed_scope.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.l2.normalize_indexed_module_candidate | harbor/core/l2.py | unknown | unknown | ⚪ Missing | 将索引记录路径归一化为模块候选，优先映射 repo 内绝对路径。 |
| harbor.core.module_capsule.normalize_module_path | harbor/core/module_capsule.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.path_normalization.normalize_path_separators | harbor/core/path_normalization.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.verification.normalize_repo_relative_path | harbor/core/verification.py | public | strict | ❌ Missing | Normalize one repo-local path into stable POSIX-style rel... |
| harbor.core.module_skill.normalize_skill_slug | harbor/core/module_skill.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.context_integrity.parse_frontmatter | harbor/core/context_integrity.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.workspace.parse_workspace_export_options | harbor/core/workspace.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.console_output.CLIProgressReporter.phase | harbor/core/console_output.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.decorator.DecoratorEngine.preview | harbor/core/decorator.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.module_capsule.preview_module_capsule | harbor/core/module_capsule.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.verification.VerificationTargetRef.primary_anchor | harbor/core/verification.py | unknown | unknown | ⚪ Missing | Return the preferred stable anchor for verification bindi... |
| harbor.core.index.process_file_worker | harbor/core/index.py | public | strict | ❌ Missing | 并行 Worker：解析并计算单文件条目。 |
| harbor.core.change_window.prune_change_windows | harbor/core/change_window.py | unknown | unknown | ⚪ Missing | Delete change-window snapshots older than the newest `lim... |
| harbor.core.storage.HarborDB.purge_missing | harbor/core/storage.py | public | strict | ❌ Missing | 删除 DB 中存在但磁盘已缺失的文件记录。 |
| harbor.core.project_structure.rank_key_file | harbor/core/project_structure.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.generated_verify.re_match_absolute_path | harbor/core/generated_verify.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.module_capsule.read_capsule_fingerprint | harbor/core/module_capsule.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft.render_diary_draft_markdown | harbor/core/log_draft.py | public | strict | ❌ Missing | Render a stable markdown diary draft from the JSON payload. |
| harbor.core.context_integrity.render_frontmatter | harbor/core/context_integrity.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.path_normalization.repo_relative_path | harbor/core/path_normalization.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.advice_config.resolve_advice_settings | harbor/core/advice_config.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.utils.resolve_code_roots | harbor/core/utils.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft.resolve_draft_source | harbor/core/log_draft.py | unknown | unknown | ⚪ Missing | Resolve and parse one authorized draft source for `harbor... |
| harbor.core.module_capsule.resolve_module_capsule_paths | harbor/core/module_capsule.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.audit.resolve_provider | harbor/core/audit.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.verification.resolve_repo_local_file | harbor/core/verification.py | public | strict | ❌ Missing | Resolve a repo-local file path under the repository trust... |
| harbor.core.verification.resolve_typescript_ddt_preview_config | harbor/core/verification.py | public | strict | ❌ Missing | Resolve additive TypeScript DDT preview config with safe ... |
| harbor.core.audit.resolve_typescript_semantic_audit_preview_config | harbor/core/audit.py | public | strict | ❌ Missing | Resolve additive TypeScript semantic-audit preview config. |
| harbor.core.workspace.resolve_workspace_config_path | harbor/core/workspace.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init_wizard.InitWizard.run | harbor/core/init_wizard.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.doctor.run_config_index_check | harbor/core/doctor.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.doctor.run_ddt_fast_check | harbor/core/doctor.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.doctor.run_derived_views_check | harbor/core/doctor.py | unknown | unknown | ⚪ Missing | 检查模块派生视图状态并汇总为 Doctor 结果。 |
| harbor.core.doctor.run_skill_reference_check | harbor/core/doctor.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.doctor.run_workspace_status_check | harbor/core/doctor.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.performance_baseline.runtime_performance_baseline_report_to_dict | harbor/core/performance_baseline.py | public | strict | ❌ Missing | Serialize the runtime baseline report into the public JSO... |
| harbor.core.console_output.safe_console_print | harbor/core/console_output.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.path_normalization.sanitize_path_for_display | harbor/core/path_normalization.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.workspace_inspect.sanitize_text | harbor/core/workspace_inspect.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.workspace_migrate.sanitize_text | harbor/core/workspace_migrate.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.decorator.DecoratorEngine.scan | harbor/core/decorator.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.ddt.DDTScanner.scan_tests | harbor/core/ddt.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.init_prompt.select_one | harbor/core/init_prompt.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.log_draft.serialize_diary_draft | harbor/core/log_draft.py | public | strict | ❌ Missing | Serialize a diary draft payload as markdown or stable JSON. |
| harbor.core.console_output.should_render_progress | harbor/core/console_output.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.module_skill.skill_dir_for_module | harbor/core/module_skill.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.audit.TypeScriptSemanticAuditPreviewFinding.sort_key | harbor/core/audit.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.verification.TypeScriptDDTPreviewFinding.sort_key | harbor/core/verification.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.context_integrity.split_frontmatter | harbor/core/context_integrity.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.stale.stale_report_to_dict | harbor/core/stale.py | unknown | unknown | ⚪ Missing | 将 stale 检查结果序列化为 machine-readable JSON 对象。 |
| harbor.core.console_output.CLIProgressReporter.status | harbor/core/console_output.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.context_integrity.strip_frontmatter | harbor/core/context_integrity.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.audit.AuditEligibility.to_dict | harbor/core/audit.py | public | strict | ❌ Missing | Serialize one eligibility evaluation into a stable dictio... |
| harbor.core.audit.AuditEvidence.to_dict | harbor/core/audit.py | public | strict | ❌ Missing | Serialize one audit evidence row into a stable dictionary. |
| harbor.core.audit.AuditPromptContext.to_dict | harbor/core/audit.py | public | strict | ❌ Missing | Serialize one prompt context into a stable dictionary. |
| harbor.core.audit.AuditSubject.to_dict | harbor/core/audit.py | public | strict | ❌ Missing | Serialize one audit subject into a stable dictionary. |
| harbor.core.audit.TypeScriptSemanticAuditPreviewConfig.to_dict | harbor/core/audit.py | public | strict | ❌ Missing | Serialize normalized TypeScript semantic-audit preview co... |
| harbor.core.audit.TypeScriptSemanticAuditPreviewFinding.to_dict | harbor/core/audit.py | public | strict | ❌ Missing | Serialize one TypeScript semantic-audit preview finding. |
| harbor.core.audit.TypeScriptSemanticAuditPreviewReport.to_dict | harbor/core/audit.py | public | strict | ❌ Missing | Serialize the TypeScript semantic-audit preview report. |
| harbor.core.change_window.ChangeWindowSnapshot.to_dict | harbor/core/change_window.py | public | strict | ❌ Missing | Serialize the current snapshot into a JSON-friendly chang... |
| harbor.core.ci.CIFailure.to_dict | harbor/core/ci.py | public | strict | ❌ Missing | 将通用 CI failure/advisory 项序列化为 machine-readable JSON-compa... |
| harbor.core.ci.CheckpointCIItem.to_dict | harbor/core/ci.py | public | strict | ❌ Missing | 将 checkpoint CI failure/advisory 项序列化为 machine-readable J... |
| harbor.core.doctor.DoctorCheckResult.to_dict | harbor/core/doctor.py | public | strict | ❌ Missing | Serialize one doctor check result into stable JSON output. |
| harbor.core.doctor.DoctorReport.to_dict | harbor/core/doctor.py | public | strict | ❌ Missing | Serialize the aggregated doctor report into stable JSON o... |
| harbor.core.generated_verify.GeneratedArtifactVerification.to_dict | harbor/core/generated_verify.py | public | strict | ❌ Missing | Serialize one verified artifact row to a stable JSON-comp... |
| harbor.core.generated_verify.GeneratedVerificationReport.to_dict | harbor/core/generated_verify.py | public | strict | ❌ Missing | Serialize the verify-generated domain report via the publ... |
| harbor.core.generated_verify.ModuleGeneratedVerification.to_dict | harbor/core/generated_verify.py | public | strict | ❌ Missing | Serialize one module verification group to a stable JSON-... |
| harbor.core.generated_verify.ProjectGeneratedVerification.to_dict | harbor/core/generated_verify.py | public | strict | ❌ Missing | Serialize project-level verification rows to a stable JSO... |
| harbor.core.performance_baseline.RuntimeBaselineContextMetrics.to_dict | harbor/core/performance_baseline.py | public | strict | ❌ Missing | Serialize baseline context counts into a stable JSON-comp... |
| harbor.core.performance_baseline.RuntimeBaselineObservation.to_dict | harbor/core/performance_baseline.py | public | strict | ❌ Missing | Serialize one runtime observation into stable JSON output. |
| harbor.core.performance_baseline.RuntimeHotspotAssessment.to_dict | harbor/core/performance_baseline.py | public | strict | ❌ Missing | Serialize one hotspot assessment into a stable JSON-compa... |
| harbor.core.performance_baseline.RuntimeMatrixEntry.to_dict | harbor/core/performance_baseline.py | public | strict | ❌ Missing | Serialize one runtime command-matrix row into a stable ma... |
| harbor.core.performance_baseline.RuntimePerformanceBaselineReport.to_dict | harbor/core/performance_baseline.py | public | strict | ❌ Missing | Serialize the runtime baseline report into stable JSON ou... |
| harbor.core.repair_guidance.RepairGuidance.to_dict | harbor/core/repair_guidance.py | public | strict | ❌ Missing | Serialize deterministic repair guidance into a JSON-compa... |
| harbor.core.stale.ModuleStaleSummary.to_dict | harbor/core/stale.py | public | strict | ❌ Missing | Serialize one module stale summary into stable JSON output. |
| harbor.core.stale.ViewStaleResult.to_dict | harbor/core/stale.py | public | strict | ❌ Missing | Serialize one stale-view result into a stable JSON-safe s... |
| harbor.core.verification.TypeScriptDDTPreviewConfig.to_dict | harbor/core/verification.py | public | strict | ❌ Missing | Serialize normalized preview config into a stable diction... |
| harbor.core.verification.TypeScriptDDTPreviewFinding.to_dict | harbor/core/verification.py | public | strict | ❌ Missing | Serialize one TypeScript DDT preview finding into a stabl... |
| harbor.core.verification.TypeScriptDDTPreviewReport.to_dict | harbor/core/verification.py | public | strict | ❌ Missing | Serialize the preview validator report into a stable dict... |
| harbor.core.verification.TypeScriptDDTPreviewSidecar.to_dict | harbor/core/verification.py | public | strict | ❌ Missing | Serialize parsed preview sidecar data into a stable dicti... |
| harbor.core.verification.VerificationBinding.to_dict | harbor/core/verification.py | public | strict | ❌ Missing | Serialize verification binding metadata into a stable dic... |
| harbor.core.verification.VerificationTargetRef.to_dict | harbor/core/verification.py | public | strict | ❌ Missing | Serialize verification target identity into a stable dict... |
| harbor.core.verification.VerificationTestAsset.to_dict | harbor/core/verification.py | public | strict | ❌ Missing | Serialize verification test asset metadata into a stable ... |
| harbor.core.workspace_inspect.WorkspaceGeneratedViewsStatus.to_dict | harbor/core/workspace_inspect.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.workspace_inspect.WorkspaceGitTrackingStatus.to_dict | harbor/core/workspace_inspect.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.workspace_inspect.WorkspaceLegacyPathStatus.to_dict | harbor/core/workspace_inspect.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.workspace_migrate.WorkspaceMigrationPlanItem.to_dict | harbor/core/workspace_migrate.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.diary.DiaryEntry.to_json | harbor/core/diary.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.audit.TypeScriptSemanticAuditPreviewReport.to_summary_dict | harbor/core/audit.py | public | strict | ❌ Missing | Serialize the compact preview summary without finding rows. |
| harbor.core.verification.TypeScriptDDTPreviewReport.to_summary_dict | harbor/core/verification.py | public | strict | ❌ Missing | Serialize the lightweight preview summary without full fi... |
| harbor.core.ddt.DDTBinding.to_verification_binding | harbor/core/ddt.py | public | strict | ❌ Missing | Convert the legacy Python-first DDT binding into a langua... |
| harbor.core.storage.HarborDB.transaction | harbor/core/storage.py | public | strict | ❌ Missing | 事务上下文管理器（单文件原子写入）。 |
| harbor.core.console_output._NoOpBatchProgress.update | harbor/core/console_output.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.console_output._RichBatchProgress.update | harbor/core/console_output.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.storage.HarborDB.upsert_entry | harbor/core/storage.py | public | strict | ❌ Missing | 插入或更新函数条目。 |
| harbor.core.storage.HarborDB.upsert_file | harbor/core/storage.py | public | strict | ❌ Missing | 插入或更新文件记录。 |
| harbor.core.ddt.DDTValidator.validate | harbor/core/ddt.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.verification.validate_typescript_ddt_preview | harbor/core/verification.py | public | strict | ❌ Missing | Validate TypeScript DDT preview bindings in advisory-only... |
| harbor.core.generated_verify.verify_canonical_l2_readme | harbor/core/generated_verify.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.generated_verify.verify_export_l2_readme | harbor/core/generated_verify.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.generated_verify.verify_l2_meta | harbor/core/generated_verify.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.generated_verify.verify_module_capsule | harbor/core/generated_verify.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.generated_verify.verify_module_generated | harbor/core/generated_verify.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.generated_verify.verify_project_structure | harbor/core/generated_verify.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.workspace_inspect.workspace_inspect_report_to_dict | harbor/core/workspace_inspect.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.workspace_migrate.workspace_migrate_report_to_dict | harbor/core/workspace_migrate.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.l2.L2Generator.write | harbor/core/l2.py | public | strict | ❌ Missing | Write the canonical L2 README and synchronized metadata f... |
| harbor.core.change_window.write_change_window_snapshot | harbor/core/change_window.py | public | strict | ❌ Missing | Write one change-window snapshot under `.harbor/state/cha... |
| harbor.core.baseline_artifact.write_checkpoint_baseline_artifact | harbor/core/baseline_artifact.py | unknown | unknown | ⚪ Missing | Validate and write the accepted checkpoint baseline artif... |
| harbor.core.init.Initializer.write_config | harbor/core/init.py | public | strict | ❌ Missing | 写入 `.harbor/config/harbor.yaml`。 |
| harbor.core.log_draft.write_diary_draft_output | harbor/core/log_draft.py | public | strict | ❌ Missing | Write a rendered diary draft to a safe non-diary path ins... |
| harbor.core.log_draft.write_diary_entry_from_draft | harbor/core/log_draft.py | public | strict | ❌ Missing | Write one structured diary entry from an approved draft s... |
| harbor.core.log_draft.write_last_log_marker | harbor/core/log_draft.py | public | strict | ❌ Missing | Best-effort update of `.harbor/state/log/last_log_marker.... |
| harbor.core.log_draft.write_latest_diary_draft_cache | harbor/core/log_draft.py | public | strict | ❌ Missing | Best-effort write of latest diary draft runtime cache und... |
| harbor.core.module_capsule.write_module_capsule | harbor/core/module_capsule.py | public | strict | ❌ Missing | Write the canonical Module Capsule views for one module. |
| harbor.core.module_skill.write_module_skill | harbor/core/module_skill.py | unknown | unknown | ⚪ Missing | — |
| harbor.core.project_structure.write_project_structure | harbor/core/project_structure.py | public | strict | ❌ Missing | Write the canonical project-structure view and optional e... |
| harbor.core.workspace.write_workspace_config | harbor/core/workspace.py | public | strict | ❌ Missing | Write the canonical Harbor workspace config file. |

</details>
# Module: harbor

## Public API
| Function | Summary | Strictness | DDT Status |
|---|---|---|---|
| harbor.core.drafting.DiaryDrafter.__init__ | AI 辅助生成 Diary 草稿。 | strict | ❌ Missing |
| harbor.core.l2.L2Generator.__init__ | Initialize the L2 generator against a readonly index source. | strict | ❌ Missing |
| harbor.core.index.IndexBuilder._iter_py_files | 生成待扫描的 Python 文件列表（支持 Git 感知剪枝）。 | strict | ❌ Missing |
| harbor.core.diary.DiaryManager.append_json_line | Append one structured JSON line to canonical diary storage. | strict | ❌ Missing |
| harbor.core.init.Initializer.autodetect | 高级启发式自动探测。 | strict | ❌ Missing |
| harbor.core.index.IndexBuilder.build | 构建或增量更新 L3 索引到缓存。 | strict | ❌ Missing |
| harbor.core.log_draft.build_diary_draft | Build a deterministic diary draft from existing change-wi... | strict | ❌ Missing |
| harbor.core.log_draft.build_log_write_preview | Build summary-level preview data for interactive `harbor ... | strict | ❌ Missing |
| harbor.core.log_draft.build_written_diary_entry | Build one structured written diary entry payload from an ... | strict | ❌ Missing |
| harbor.core.stale.check_module_derived_views_stale | Check one module's derived-view stale status against fres... | strict | ❌ Missing |
| harbor.core.sync.SyncEngine.check_status | 对比缓存索引与当前代码，输出 Harbor 上下文状态。 | strict | ✅ Valid |
| harbor.core.ci.checkpoint_ci_result_to_dict | 将 CheckpointCIResult 序列化为 `checkpoint --ci` 公开 CI JSON pa... | strict | ❌ Missing |
| harbor.core.ci.ci_result_to_dict | 将通用 CIResult 序列化为 checkpoint 之外的公开 CI JSON payload。 | strict | ❌ Missing |
| harbor.core.l2.collect_all_indexed_modules | Collect normalized module paths from readonly index records. | strict | ❌ Missing |
| harbor.core.module_capsule.collect_module_context | Collect readonly context records used to render one modul... | strict | ❌ Missing |
| harbor.core.project_structure.collect_project_structure_context | Collect the canonical project-structure context from inde... | strict | ❌ Missing |
| harbor.core.contract_impact.contract_impact_report_to_dict | Serialize contract-impact analysis into stable JSON output. | strict | ❌ Missing |
| harbor.core.init.ProjectDetector.detect | 启发式探测技术栈并生成配置建议。 | strict | ❌ Missing |
| harbor.core.init.Initializer.detect_code_roots | 智能探测项目代码根目录。 | strict | ❌ Missing |
| harbor.utils.formatting.format_size | 将字节数转换为人类可读的 KB/MB 字符串。 | strict | ✅ Valid |
| harbor.core.l2.L2Generator.generate | 生成指定模块的 L2 README Markdown 文本。 | strict | ❌ Missing |
| harbor.core.project_structure.generate_project_structure_markdown | Render a deterministic Markdown view from project-structu... | strict | ❌ Missing |
| harbor.core.storage.HarborDB.get_all_files | 列出所有已索引文件及其 mtime。 | strict | ❌ Missing |
| harbor.core.storage.HarborDB.get_file | 查询单文件记录。 | strict | ❌ Missing |
| harbor.core.storage.HarborDB.get_file_entries | 查询指定文件的所有条目。 | strict | ❌ Missing |
| harbor.utils.i18n.get_lang | 解析当前语言。 | standard | ⚪ Missing |
| harbor.core.index.IndexBuilder.iter_build | 以生成器方式构建索引，逐文件产出进度事件。 | strict | ❌ Missing |
| harbor.core.utils.iter_project_files | 生成待扫描的 Python 文件列表（统一剪枝逻辑）。 | strict | ❌ Missing |
| harbor.core.readonly_index.load_readonly_index | Load a read-only Harbor index snapshot for analysis paths. | strict | ❌ Missing |
| harbor.core.diary.DiaryManager.log | 写入一条 DiaryEntry 到当月 JSONL。 | strict | ❌ Missing |
| harbor.cli.main.main | Harbor CLI entrypoint and public command dispatch contract. | strict | ❌ Missing |
| harbor.core.git_utils.GitIgnoreMatcher.match_dir | 判断相对路径目录是否被忽略（用于剪枝）。 | strict | ❌ Missing |
| harbor.core.git_utils.GitIgnoreMatcher.match_file | 判断相对路径文件是否被忽略。 | strict | ❌ Missing |
| harbor.core.storage.HarborDB.migrate_from_json | 从旧版 JSON 索引迁移到 SQLite。 | strict | ❌ Missing |
| harbor.adapters.python.parser.PythonAdapter.parse_file | 解析并提取指定 Python 文件中的函数/方法契约元数据。 | strict | ❌ Missing |
| harbor.core.index.process_file_worker | 并行 Worker：解析并计算单文件条目。 | strict | ❌ Missing |
| harbor.core.storage.HarborDB.purge_missing | 删除 DB 中存在但磁盘已缺失的文件记录。 | strict | ❌ Missing |
| harbor.core.log_draft.render_diary_draft_markdown | Render a stable markdown diary draft from the JSON payload. | strict | ❌ Missing |
| harbor.core.log_draft.serialize_diary_draft | Serialize a diary draft payload as markdown or stable JSON. | strict | ❌ Missing |
| harbor.utils.i18n.t | 根据当前语言返回文案。 | standard | ⚪ Missing |
| harbor.adapters.base.ContractSource.to_dict | Serialize contract source into a JSON-friendly dictionary. | strict | ❌ Missing |
| harbor.adapters.base.ContractSubject.to_dict | Serialize contract subject into a JSON-friendly dictionary. | strict | ❌ Missing |
| harbor.core.change_window.ChangeWindowSnapshot.to_dict | Serialize the current snapshot into a JSON-friendly chang... | strict | ❌ Missing |
| harbor.core.ci.CIFailure.to_dict | 将通用 CI failure/advisory 项序列化为 machine-readable JSON-compa... | strict | ❌ Missing |
| harbor.core.ci.CheckpointCIItem.to_dict | 将 checkpoint CI failure/advisory 项序列化为 machine-readable J... | strict | ❌ Missing |
| harbor.core.doctor.DoctorCheckResult.to_dict | Serialize one doctor check result into stable JSON output. | strict | ❌ Missing |
| harbor.core.doctor.DoctorReport.to_dict | Serialize the aggregated doctor report into stable JSON o... | strict | ❌ Missing |
| harbor.core.repair_guidance.RepairGuidance.to_dict | Serialize deterministic repair guidance into a JSON-compa... | strict | ❌ Missing |
| harbor.core.stale.ModuleStaleSummary.to_dict | Serialize one module stale summary into stable JSON output. | strict | ❌ Missing |
| harbor.core.stale.ViewStaleResult.to_dict | Serialize one stale-view result into a stable JSON-safe s... | strict | ❌ Missing |
| harbor.core.storage.HarborDB.transaction | 事务上下文管理器（单文件原子写入）。 | strict | ❌ Missing |
| harbor.core.storage.HarborDB.upsert_entry | 插入或更新函数条目。 | strict | ❌ Missing |
| harbor.core.storage.HarborDB.upsert_file | 插入或更新文件记录。 | strict | ❌ Missing |
| harbor.core.change_window.write_change_window_snapshot | Write one change-window snapshot under `.harbor/state/cha... | strict | ❌ Missing |
| harbor.core.init.Initializer.write_config | 写入 `.harbor/config/harbor.yaml`。 | strict | ❌ Missing |
| harbor.core.log_draft.write_diary_draft_output | Write a rendered diary draft to a safe non-diary path ins... | strict | ❌ Missing |
| harbor.core.log_draft.write_diary_entry_from_draft | Write one structured diary entry from an approved draft s... | strict | ❌ Missing |
| harbor.core.log_draft.write_last_log_marker | Best-effort update of `.harbor/state/log/last_log_marker.... | strict | ❌ Missing |
| harbor.core.log_draft.write_latest_diary_draft_cache | Best-effort write of latest diary draft runtime cache und... | strict | ❌ Missing |
| harbor.core.module_capsule.write_module_capsule | Write the canonical Module Capsule views for one module. | strict | ❌ Missing |
| harbor.core.project_structure.write_project_structure | Write the canonical project-structure view and optional e... | strict | ❌ Missing |
| harbor.core.workspace.write_workspace_config | Write the canonical Harbor workspace config file. | strict | ❌ Missing |

## Internal Details (optional)
<details>
<summary>Internal functions</summary>

| Function | Summary | Strictness | DDT Status |
|---|---|---|---|
| harbor.adapters.registry.AdapterRegistry.__init__ | — | standard | ⚪ Missing |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser.__init__ | — | standard | ⚪ Missing |
| harbor.core.audit.OpenAIProvider.__init__ | — | standard | ⚪ Missing |
| harbor.core.ddt.DDTScanner.__init__ | — | standard | ⚪ Missing |
| harbor.core.ddt.DDTValidator.__init__ | — | standard | ⚪ Missing |
| harbor.core.diary.DiaryManager.__init__ | 初始化 Diary 路径上下文（canonical 写入 + legacy 读取兼容）。 | standard | ⚪ Missing |
| harbor.core.git_utils.GitIgnoreMatcher.__init__ | — | standard | ⚪ Missing |
| harbor.core.index.IndexBuilder.__init__ | — | standard | ⚪ Missing |
| harbor.core.init.Initializer.__init__ | — | standard | ⚪ Missing |
| harbor.core.init.ProjectDetector.__init__ | — | standard | ⚪ Missing |
| harbor.core.init_wizard.InitWizard.__init__ | — | standard | ⚪ Missing |
| harbor.core.storage.HarborDB.__init__ | — | standard | ⚪ Missing |
| harbor.core.sync.SyncEngine.__init__ | — | standard | ⚪ Missing |
| harbor.adapters.base.ContractSource.__post_init__ | — | standard | ⚪ Missing |
| harbor.core.ci._append_checkpoint_guidance_lines | — | standard | ⚪ Missing |
| harbor.core.init_wizard._append_missing_env_keys | — | standard | ⚪ Missing |
| harbor.core.log_draft._append_text_value | — | standard | ⚪ Missing |
| harbor.core.storage.HarborDB._apply_pragmas | — | standard | ⚪ Missing |
| harbor.core.project_structure._area_purpose | — | standard | ⚪ Missing |
| harbor.core.context_integrity._as_repo_relative | — | standard | ⚪ Missing |
| harbor.core.init_wizard.InitWizard._ask_advice_mode | — | standard | ⚪ Missing |
| harbor.core.init_wizard.InitWizard._ask_language | — | standard | ⚪ Missing |
| harbor.core.init_wizard.InitWizard._ask_project | — | standard | ⚪ Missing |
| harbor.core.init_wizard.InitWizard._ask_yes_no | — | standard | ⚪ Missing |
| harbor.core.module_capsule._belongs_to_module | — | standard | ⚪ Missing |
| harbor.core.project_structure._belongs_to_module | — | standard | ⚪ Missing |
| harbor.core.log_draft._bucket_for_path | — | standard | ⚪ Missing |
| harbor.core.workspace._build_path | — | standard | ⚪ Missing |
| harbor.core.drafting.DiaryDrafter._build_prompt | — | standard | ⚪ Missing |
| harbor.core.log_draft._build_risks | — | standard | ⚪ Missing |
| harbor.core.log_draft._build_suggested_diary_entry | — | standard | ⚪ Missing |
| harbor.core.log_draft._build_summary | — | standard | ⚪ Missing |
| harbor.core.readonly_index._build_transient_index | — | standard | ⚪ Missing |
| harbor.core.project_structure._build_transient_index_from_files | — | standard | ⚪ Missing |
| harbor.core.log_draft._build_why | — | standard | ⚪ Missing |
| harbor.core.project_structure._capsule_exists | — | standard | ⚪ Missing |
| harbor.core.workspace_inspect._check_git_ignored | — | standard | ⚪ Missing |
| harbor.core.ci._checkpoint_reason_for_entry | — | standard | ⚪ Missing |
| harbor.core.init_prompt._choice_label | — | standard | ⚪ Missing |
| harbor.core.log_draft._classify_affected_areas | — | standard | ⚪ Missing |
| harbor.adapters.typescript.jsdoc._classify_comment | — | standard | ⚪ Missing |
| harbor.core.workspace_inspect._classify_git_tracking | — | standard | ⚪ Missing |
| harbor.core.contract_impact._classify_tests_path | — | standard | ⚪ Missing |
| harbor.core.change_window._coerce_changed_files | — | standard | ⚪ Missing |
| harbor.core.change_window._coerce_mapping | — | standard | ⚪ Missing |
| harbor.core.log_draft._coerce_validation_status | — | standard | ⚪ Missing |
| harbor.core.workspace_inspect._collect_advisory | — | standard | ⚪ Missing |
| harbor.core.ci._collect_checkpoint_next_steps | — | standard | ⚪ Missing |
| harbor.adapters.typescript.adapter._collect_contract_sources | — | standard | ⚪ Missing |
| harbor.core.project_structure._collect_fallback_files | — | standard | ⚪ Missing |
| harbor.adapters.typescript.adapter.TypeScriptAdapter._collect_file | — | standard | ⚪ Missing |
| harbor.core.workspace_inspect._collect_generated_views | — | standard | ⚪ Missing |
| harbor.core.workspace_inspect._collect_git_tracking | — | standard | ⚪ Missing |
| harbor.core.l2.L2Generator._collect_integrity_inputs | — | standard | ⚪ Missing |
| harbor.core.workspace_inspect._collect_legacy_paths | — | standard | ⚪ Missing |
| harbor.core.workspace_migrate._collect_module_readme_exports | — | standard | ⚪ Missing |
| harbor.core.ci._collect_next_steps | — | standard | ⚪ Missing |
| harbor.core.doctor._collect_next_steps | — | standard | ⚪ Missing |
| harbor.core.sync.SyncEngine._collect_python_snapshot_items | — | standard | ⚪ Missing |
| harbor.core.sync.SyncEngine._collect_typescript_snapshot_items | — | standard | ⚪ Missing |
| harbor.core.sync.SyncEngine._compare_snapshots | — | standard | ⚪ Missing |
| harbor.core.log_draft._compose_written_details | — | standard | ⚪ Missing |
| harbor.core.contract_impact._confidence_for_level | — | standard | ⚪ Missing |
| harbor.cli.main._configure_redirected_windows_stdio | Backward-compatible wrapper for the Windows CLI-wide stdi... | standard | ⚪ Missing |
| harbor.cli.main._configure_windows_stdio | Apply a Windows CLI-wide UTF-8-first stdio strategy when ... | standard | ⚪ Missing |
| harbor.adapters.python.parser.PythonAdapter._contract_area | 提取契约区文本（Args/Returns/Raises + @harbor.* tags）。找不到则返回空串。 | standard | ⚪ Missing |
| harbor.adapters.python.parser.PythonAdapter._contract_from_function | 根据函数节点生成契约元数据。 | standard | ⚪ Missing |
| harbor.adapters.typescript.adapter._contract_hash_for_sources | — | standard | ⚪ Missing |
| harbor.core.diary.DiaryManager._current_file_path | — | standard | ⚪ Missing |
| harbor.core.ci._ddt_identity_defaults | — | standard | ⚪ Missing |
| harbor.core.context_integrity._decode_scalar | — | standard | ⚪ Missing |
| harbor.core.init.ProjectDetector._dedup | — | standard | ⚪ Missing |
| harbor.core.log_draft._dedupe_changed_files | — | standard | ⚪ Missing |
| harbor.core.ci._dedupe_checkpoint_items | — | standard | ⚪ Missing |
| harbor.core.init_wizard._default_language | — | standard | ⚪ Missing |
| harbor.core.index_entry._default_name | — | standard | ⚪ Missing |
| harbor.core.init_wizard._default_project | — | standard | ⚪ Missing |
| harbor.core.ci._derive_checkpoint_identity | — | standard | ⚪ Missing |
| harbor.core.ci._derive_qualified_name_and_symbol_kind | — | standard | ⚪ Missing |
| harbor.core.log_draft._derive_validation_statuses | — | standard | ⚪ Missing |
| harbor.core.doctor._derived_view_detail_status | 将内部 view status 归一化为可展示文本。 | standard | ⚪ Missing |
| harbor.core.init_prompt._detect_console_encoding | — | standard | ⚪ Missing |
| harbor.core.init.ProjectDetector._detect_django | — | standard | ⚪ Missing |
| harbor.core.init.ProjectDetector._detect_go | — | standard | ⚪ Missing |
| harbor.core.init.ProjectDetector._detect_java | — | standard | ⚪ Missing |
| harbor.core.init.ProjectDetector._detect_node | — | standard | ⚪ Missing |
| harbor.core.init.ProjectDetector._detect_python_misc | — | standard | ⚪ Missing |
| harbor.core.log_draft._determine_draft_status | — | standard | ⚪ Missing |
| harbor.core.log_draft._discover_report_summaries | — | standard | ⚪ Missing |
| harbor.adapters.python.parser.PythonAdapter._docstring_hashes | 计算 Docstring 的 raw/contract 双哈希。 | standard | ⚪ Missing |
| harbor.core.decorator.DecoratorEngine._docstring_node | — | standard | ⚪ Missing |
| harbor.core.init_wizard.InitWizard._emit_detected_summary | — | standard | ⚪ Missing |
| harbor.core.init_wizard.InitWizard._emit_ide_guidance | — | standard | ⚪ Missing |
| harbor.cli.main._emit_json_stdout | Write one JSON object to stdout with an ASCII-safe fallba... | standard | ⚪ Missing |
| harbor.core.init_wizard.InitWizard._emit_next_steps | — | standard | ⚪ Missing |
| harbor.core.init_wizard.InitWizard._emit_project_rules_guidance | — | standard | ⚪ Missing |
| harbor.core.storage.HarborDB._ensure_schema | — | standard | ⚪ Missing |
| harbor.core.diary.DiaryManager._ensure_within_repo | — | standard | ⚪ Missing |
| harbor.core.l2.L2Generator._ensure_within_root | — | standard | ⚪ Missing |
| harbor.core.module_capsule._ensure_within_root | — | standard | ⚪ Missing |
| harbor.core.diary.DiaryManager._entry_dedupe_key | — | standard | ⚪ Missing |
| harbor.core.init.ProjectDetector._exclude_covers_root | — | standard | ⚪ Missing |
| harbor.adapters.typescript.parser._extract_arrow_body | — | standard | ⚪ Missing |
| harbor.core.log_draft._extract_bullet_items | — | standard | ⚪ Missing |
| harbor.core.drafting.DiaryDrafter._extract_code_context | — | standard | ⚪ Missing |
| harbor.core.log_draft._extract_first_safe_text_block | — | standard | ⚪ Missing |
| harbor.adapters.python.parser.PythonAdapter._extract_functions | 提取顶层函数与类方法的契约元数据。 | standard | ⚪ Missing |
| harbor.core.decorator.DecoratorEngine._extract_functions | — | standard | ⚪ Missing |
| harbor.core.log_draft._extract_latest_git_head | — | standard | ⚪ Missing |
| harbor.core.log_draft._extract_latest_snapshot_timestamp | — | standard | ⚪ Missing |
| harbor.core.log_draft._extract_markdown_section | — | standard | ⚪ Missing |
| harbor.core.log_draft._extract_markdown_summary_sections | — | standard | ⚪ Missing |
| harbor.core.log_draft._extract_structured_fields_from_json_draft | — | standard | ⚪ Missing |
| harbor.core.project_structure._extract_toml_string_block | — | standard | ⚪ Missing |
| harbor.core.index.IndexBuilder._file_hash | — | standard | ⚪ Missing |
| harbor.core.init.ProjectDetector._filter_excludes | — | standard | ⚪ Missing |
| harbor.core.doctor._filter_safe_next_steps | — | standard | ⚪ Missing |
| harbor.adapters.typescript.jsdoc._find_block_comment_start | — | standard | ⚪ Missing |
| harbor.adapters.typescript.parser._find_matching | — | standard | ⚪ Missing |
| harbor.core.contract_impact._finding_to_dict | — | standard | ⚪ Missing |
| harbor.core.log_draft._format_area_list | — | standard | ⚪ Missing |
| harbor.core.log_draft._format_changed_files | — | standard | ⚪ Missing |
| harbor.core.change_window._format_iso8601_utc | — | standard | ⚪ Missing |
| harbor.core.log_draft._format_noop_changed_files | — | standard | ⚪ Missing |
| harbor.core.log_draft._format_noop_reports | — | standard | ⚪ Missing |
| harbor.core.log_draft._format_noop_snapshots | — | standard | ⚪ Missing |
| harbor.core.log_draft._format_reports | — | standard | ⚪ Missing |
| harbor.core.log_draft._format_snapshot_group | — | standard | ⚪ Missing |
| harbor.core.log_draft._format_snapshot_line | — | standard | ⚪ Missing |
| harbor.core.change_window._format_snapshot_stamp | — | standard | ⚪ Missing |
| harbor.core.stale._format_view_lines | 格式化单个视图状态的文本行。 | standard | ⚪ Missing |
| harbor.core.diary.DiaryManager._from_dict | — | standard | ⚪ Missing |
| harbor.core.init.ProjectDetector._get_default_excludes | — | standard | ⚪ Missing |
| harbor.core.ci._get_optional_list | — | standard | ⚪ Missing |
| harbor.core.ci._get_optional_text | — | standard | ⚪ Missing |
| harbor.core.change_window._git_status_lines | — | standard | ⚪ Missing |
| harbor.core.init_wizard._has_env_ignore | — | standard | ⚪ Missing |
| harbor.core.decorator.DecoratorEngine._has_scope_tag | — | standard | ⚪ Missing |
| harbor.core.index.IndexBuilder._index_entry | — | standard | ⚪ Missing |
| harbor.core.project_structure._infer_area | — | standard | ⚪ Missing |
| harbor.core.log_draft._infer_contract_impact | — | standard | ⚪ Missing |
| harbor.core.audit._infer_file_path_from_contract | — | standard | ⚪ Missing |
| harbor.core.ci._is_blocking_checkpoint_target | — | standard | ⚪ Missing |
| harbor.core.contract_impact._is_contract_asserting_test | — | standard | ⚪ Missing |
| harbor.adapters.typescript.adapter._is_contract_required | — | standard | ⚪ Missing |
| harbor.core.init.ProjectDetector._is_dangerous_python_exclude | — | standard | ⚪ Missing |
| harbor.core.log_draft._is_diary_changed_file | — | standard | ⚪ Missing |
| harbor.core.contract_impact._is_docs_or_rules_path | — | standard | ⚪ Missing |
| harbor.core.log_draft._is_env_or_secrets_path | — | standard | ⚪ Missing |
| harbor.core.decorator.DecoratorEngine._is_filtered_name | — | standard | ⚪ Missing |
| harbor.core.contract_impact._is_generated_view_module | — | standard | ⚪ Missing |
| harbor.adapters.typescript.jsdoc._is_high_confidence_tag | — | standard | ⚪ Missing |
| harbor.core.init_prompt._is_interactive | — | standard | ⚪ Missing |
| harbor.cli.main._is_log_write_interactive | — | standard | ⚪ Missing |
| harbor.core.contract_impact._is_public_cli_path | — | standard | ⚪ Missing |
| harbor.cli.main._is_pure_json_output_argv | Detect pure JSON stdout routes from raw argv without chan... | standard | ⚪ Missing |
| harbor.adapters.typescript.adapter._is_script_file | — | standard | ⚪ Missing |
| harbor.adapters.typescript.adapter._is_test_file | — | standard | ⚪ Missing |
| harbor.core.contract_impact._is_test_path | — | standard | ⚪ Missing |
| harbor.core.contract_impact._is_to_dict_like | — | standard | ⚪ Missing |
| harbor.core.init_wizard._is_tty | — | standard | ⚪ Missing |
| harbor.core.sync.SyncEngine._is_typescript_path | — | standard | ⚪ Missing |
| harbor.core.audit._is_typescript_target | — | standard | ⚪ Missing |
| harbor.cli.main._is_utf8_compatible_stdio_encoding | — | standard | ⚪ Missing |
| harbor.core.log_draft._is_within | — | standard | ⚪ Missing |
| harbor.core.contract_impact._is_write_like | — | standard | ⚪ Missing |
| harbor.core.index.IndexBuilder._iter_code_roots | — | standard | ⚪ Missing |
| harbor.core.sync.SyncEngine._iter_code_roots | — | standard | ⚪ Missing |
| harbor.core.index.IndexBuilder._iter_files_by_enabled_adapters | — | standard | ⚪ Missing |
| harbor.core.sync.SyncEngine._iter_files_by_enabled_adapters | — | standard | ⚪ Missing |
| harbor.core.decorator.DecoratorEngine._iter_function_nodes | — | standard | ⚪ Missing |
| harbor.core.ddt.DDTScanner._iter_py_files | — | standard | ⚪ Missing |
| harbor.core.sync.SyncEngine._iter_py_files | — | standard | ⚪ Missing |
| harbor.core.diary.DiaryManager._iter_read_dirs | — | standard | ⚪ Missing |
| harbor.core.context_integrity._json_stable_hash | — | standard | ⚪ Missing |
| harbor.core.project_structure._key_files_display | — | standard | ⚪ Missing |
| harbor.core.drafting.DiaryDrafter._kv_fallback_parse | — | standard | ⚪ Missing |
| harbor.core.log_draft._latest_accept_snapshot | — | standard | ⚪ Missing |
| harbor.core.decorator.DecoratorEngine._leading_whitespace | — | standard | ⚪ Missing |
| harbor.core.index.IndexBuilder._load_cache | — | standard | ⚪ Missing |
| harbor.core.ddt.DDTScanner._load_config | — | standard | ⚪ Missing |
| harbor.core.index.IndexBuilder._load_config | — | standard | ⚪ Missing |
| harbor.core.sync.SyncEngine._load_config | — | standard | ⚪ Missing |
| harbor.core.advice_config._load_config_advice | — | standard | ⚪ Missing |
| harbor.core.readonly_index._load_existing_db_index | — | standard | ⚪ Missing |
| harbor.core.ddt.DDTValidator._load_index | — | standard | ⚪ Missing |
| harbor.core.l2.L2Generator._load_index | — | standard | ⚪ Missing |
| harbor.core.module_capsule._load_index | — | standard | ⚪ Missing |
| harbor.core.project_structure._load_index | — | standard | ⚪ Missing |
| harbor.core.ddt.DDTValidator._load_map | — | standard | ⚪ Missing |
| harbor.core.l2.L2Generator._load_meta | — | standard | ⚪ Missing |
| harbor.core.sync.SyncEngine._load_previous_snapshot_from_artifact | — | standard | ⚪ Missing |
| harbor.core.log_draft._load_report_summary | — | standard | ⚪ Missing |
| harbor.core.init_wizard._load_template_text | — | standard | ⚪ Missing |
| harbor.core.contract_presence._looks_like_contract_doc | — | standard | ⚪ Missing |
| harbor.core.context_integrity._looks_like_windows_absolute_path | — | standard | ⚪ Missing |
| harbor.core.l2._looks_like_windows_absolute_path | — | standard | ⚪ Missing |
| harbor.core.project_structure._looks_like_windows_absolute_path | — | standard | ⚪ Missing |
| harbor.core.workspace._looks_like_windows_absolute_path | — | standard | ⚪ Missing |
| harbor.core.init_wizard._mask_key | — | standard | ⚪ Missing |
| harbor.core.contract_impact._max_level | — | standard | ⚪ Missing |
| harbor.core.log_draft._merge_affected_area_mappings | — | standard | ⚪ Missing |
| harbor.core.log_draft._merge_changed_files | — | standard | ⚪ Missing |
| harbor.core.doctor._merge_status | — | standard | ⚪ Missing |
| harbor.core.workspace_migrate._module_dir_has_python_files | — | standard | ⚪ Missing |
| harbor.core.ci._module_qual_from_file_path | — | standard | ⚪ Missing |
| harbor.adapters.python.parser.PythonAdapter._module_qual_from_path | 根据文件路径生成模块限定名（点分格式）。 | standard | ⚪ Missing |
| harbor.core.decorator.DecoratorEngine._module_qual_from_path | — | standard | ⚪ Missing |
| harbor.core.log_draft._non_diary_changed_files | — | standard | ⚪ Missing |
| harbor.core.context_integrity._normalize_body_for_compare | — | standard | ⚪ Missing |
| harbor.core.log_draft._normalize_changed_file | — | standard | ⚪ Missing |
| harbor.core.ci._normalize_checkpoint_key_path | — | standard | ⚪ Missing |
| harbor.core.log_draft._normalize_cli_input_path | Normalize repo-relative CLI paths so Windows separators s... | standard | ⚪ Missing |
| harbor.core.log_draft._normalize_contract_impact | — | standard | ⚪ Missing |
| harbor.core.baseline_artifact._normalize_contract_presence | — | standard | ⚪ Missing |
| harbor.core.diary.DiaryManager._normalize_for_hash | — | standard | ⚪ Missing |
| harbor.core.init.ProjectDetector._normalize_glob | — | standard | ⚪ Missing |
| harbor.core.baseline_artifact._normalize_hash | — | standard | ⚪ Missing |
| harbor.core.baseline_artifact._normalize_items | — | standard | ⚪ Missing |
| harbor.core.stale._normalize_l2_body_for_export_compare | — | standard | ⚪ Missing |
| harbor.core.stale._normalize_l2_markdown_for_stale | — | standard | ⚪ Missing |
| harbor.core.advice_config._normalize_mode | — | standard | ⚪ Missing |
| harbor.core.advice_config._normalize_mode_optional | — | standard | ⚪ Missing |
| harbor.core.contract_impact._normalize_path | — | standard | ⚪ Missing |
| harbor.core.workspace._normalize_path_like | — | standard | ⚪ Missing |
| harbor.adapters.python.compat._normalize_posix_path | — | standard | ⚪ Missing |
| harbor.core.context_integrity._normalize_rel_path | — | standard | ⚪ Missing |
| harbor.core.module_capsule._normalize_rel_path | — | standard | ⚪ Missing |
| harbor.core.project_structure._normalize_rel_path | — | standard | ⚪ Missing |
| harbor.core.sync.SyncEngine._normalize_repo_file_path | — | standard | ⚪ Missing |
| harbor.core.log_draft._normalize_report_status | — | standard | ⚪ Missing |
| harbor.core.contract_impact._normalize_symbol | — | standard | ⚪ Missing |
| harbor.core.contract_impact._normalize_symbol_for_classification | — | standard | ⚪ Missing |
| harbor.cli.main._normalize_windows_stdio_encoding_name | — | standard | ⚪ Missing |
| harbor.core.context_integrity._now_iso | — | standard | ⚪ Missing |
| harbor.core.log_draft._parse_affected_areas_section | — | standard | ⚪ Missing |
| harbor.core.log_draft._parse_diary_draft_lines | — | standard | ⚪ Missing |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_export_arrow_functions | — | standard | ⚪ Missing |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_export_class_methods | — | standard | ⚪ Missing |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_export_default_classes | — | standard | ⚪ Missing |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_export_default_functions | — | standard | ⚪ Missing |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_export_functions | — | standard | ⚪ Missing |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_export_interfaces | — | standard | ⚪ Missing |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_export_types | — | standard | ⚪ Missing |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_export_zod_schemas | — | standard | ⚪ Missing |
| harbor.core.doctor._parse_generated_frontmatter_safely | — | standard | ⚪ Missing |
| harbor.core.change_window._parse_git_status_line | — | standard | ⚪ Missing |
| harbor.core.init.ProjectDetector._parse_gitignore | — | standard | ⚪ Missing |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_internal_arrow_functions | — | standard | ⚪ Missing |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_internal_functions | — | standard | ⚪ Missing |
| harbor.core.log_draft._parse_markdown_draft_fields | — | standard | ⚪ Missing |
| harbor.adapters.python.parser.PythonAdapter._parse_tags | 从 Docstring 提取 @harbor.* 标签。 | standard | ⚪ Missing |
| harbor.core.ci._parse_target_id | — | standard | ⚪ Missing |
| harbor.core.diary.DiaryManager._parse_ts | — | standard | ⚪ Missing |
| harbor.core.log_draft._parse_validation_lines | — | standard | ⚪ Missing |
| harbor.core.log_draft._pick_first_nonempty | — | standard | ⚪ Missing |
| harbor.core.storage.HarborDB._posix_rel | — | standard | ⚪ Missing |
| harbor.core.init_wizard.InitWizard._print | — | standard | ⚪ Missing |
| harbor.core.ci._push_status_failures | — | standard | ⚪ Missing |
| harbor.core.log_draft._read_draft_source_file | — | standard | ⚪ Missing |
| harbor.adapters.registry.AdapterRegistry._read_enabled_flag | — | standard | ⚪ Missing |
| harbor.core.init_wizard._read_env_keys | — | standard | ⚪ Missing |
| harbor.adapters.registry.AdapterRegistry._read_languages_config | — | standard | ⚪ Missing |
| harbor.core.log_draft._read_last_log_marker | — | standard | ⚪ Missing |
| harbor.core.log_draft._read_last_log_marker_timestamp | — | standard | ⚪ Missing |
| harbor.core.log_draft._read_marker_value | — | standard | ⚪ Missing |
| harbor.core.l2.L2Generator._read_meta_file | — | standard | ⚪ Missing |
| harbor.core.project_structure._read_project_metadata | — | standard | ⚪ Missing |
| harbor.core.log_draft._reject_diary_output_path | — | standard | ⚪ Missing |
| harbor.core.init_prompt._render_inline_options | — | standard | ⚪ Missing |
| harbor.core.context_integrity._render_scalar | — | standard | ⚪ Missing |
| harbor.core.l2._repo_relative_index_path | — | standard | ⚪ Missing |
| harbor.core.baseline_artifact._require_bool | — | standard | ⚪ Missing |
| harbor.core.baseline_artifact._require_text | — | standard | ⚪ Missing |
| harbor.core.log_draft._resolve_allowed_from_draft_path | — | standard | ⚪ Missing |
| harbor.core.baseline_artifact._resolve_artifact_path | — | standard | ⚪ Missing |
| harbor.core.diary.DiaryManager._resolve_author | — | standard | ⚪ Missing |
| harbor.core.l2.L2Generator._resolve_canonical_readme_path | — | standard | ⚪ Missing |
| harbor.core.log_draft._resolve_cli_input_path | — | standard | ⚪ Missing |
| harbor.adapters.typescript.adapter._resolve_contract_presence | — | standard | ⚪ Missing |
| harbor.core.log_draft._resolve_diary_draft_boundary | — | standard | ⚪ Missing |
| harbor.core.module_capsule._resolve_docs_export_modules_root | — | standard | ⚪ Missing |
| harbor.core.project_structure._resolve_docs_export_project_structure_path | — | standard | ⚪ Missing |
| harbor.core.l2.L2Generator._resolve_export_readme_path | — | standard | ⚪ Missing |
| harbor.core.readonly_index._resolve_index_path | — | standard | ⚪ Missing |
| harbor.core.log_draft._resolve_latest_draft_source | — | standard | ⚪ Missing |
| harbor.core.diary.DiaryManager._resolve_legacy_diary_dirs | — | standard | ⚪ Missing |
| harbor.core.l2.L2Generator._resolve_meta_path | — | standard | ⚪ Missing |
| harbor.core.module_capsule._resolve_module_target_dir | — | standard | ⚪ Missing |
| harbor.core.log_draft._resolve_output_path | — | standard | ⚪ Missing |
| harbor.core.diary.DiaryManager._resolve_repo_root | — | standard | ⚪ Missing |
| harbor.cli.main._resolve_windows_explicit_stdio_config | — | standard | ⚪ Missing |
| harbor.cli.main._resolve_windows_redirected_stdio_encoding | Backward-compatible access to the resolved Windows stdio ... | standard | ⚪ Missing |
| harbor.cli.main._resolve_windows_stdio_target | Resolve the preferred Windows stdio strategy for one CLI ... | standard | ⚪ Missing |
| harbor.core.change_window._run_git | — | standard | ⚪ Missing |
| harbor.core.init_prompt._safe_console_print | — | standard | ⚪ Missing |
| harbor.core.log_draft._safe_excerpt | — | standard | ⚪ Missing |
| harbor.core.drafting.DiaryDrafter._safe_json_parse | — | standard | ⚪ Missing |
| harbor.core.l2.L2Generator._safe_module_subpath | — | standard | ⚪ Missing |
| harbor.core.module_capsule._safe_module_subpath | — | standard | ⚪ Missing |
| harbor.core.log_draft._safe_multiline_excerpt | — | standard | ⚪ Missing |
| harbor.core.log_draft._sanitize_affected_areas | — | standard | ⚪ Missing |
| harbor.core.ci._sanitize_checkpoint_contract_impact | — | standard | ⚪ Missing |
| harbor.core.log_draft._sanitize_evidence | — | standard | ⚪ Missing |
| harbor.core.ci._sanitize_json_text | — | standard | ⚪ Missing |
| harbor.core.contract_impact._sanitize_json_text | — | standard | ⚪ Missing |
| harbor.core.doctor._sanitize_json_text | — | standard | ⚪ Missing |
| harbor.core.stale._sanitize_json_text | — | standard | ⚪ Missing |
| harbor.core.log_draft._sanitize_markdown_text | — | standard | ⚪ Missing |
| harbor.core.project_structure._sanitize_module | — | standard | ⚪ Missing |
| harbor.core.stale._sanitize_module_for_json | — | standard | ⚪ Missing |
| harbor.core.log_draft._sanitize_risks | — | standard | ⚪ Missing |
| harbor.core.ci._sanitize_single_path | — | standard | ⚪ Missing |
| harbor.core.contract_impact._sanitize_single_path | — | standard | ⚪ Missing |
| harbor.core.doctor._sanitize_single_path | — | standard | ⚪ Missing |
| harbor.core.stale._sanitize_single_path | — | standard | ⚪ Missing |
| harbor.core.ci._sanitize_string_list | — | standard | ⚪ Missing |
| harbor.core.ci._sanitize_summary | — | standard | ⚪ Missing |
| harbor.core.log_draft._sanitize_validation | — | standard | ⚪ Missing |
| harbor.core.index.IndexBuilder._save_cache | — | standard | ⚪ Missing |
| harbor.core.l2.L2Generator._save_meta | — | standard | ⚪ Missing |
| harbor.core.log_draft._select_snapshots | — | standard | ⚪ Missing |
| harbor.adapters.python.parser.PythonAdapter._signature_hash | 计算函数签名的稳定哈希。 | standard | ⚪ Missing |
| harbor.core.project_structure._skill_exists | — | standard | ⚪ Missing |
| harbor.adapters.typescript.parser._skip_ws | — | standard | ⚪ Missing |
| harbor.core.change_window._snapshot_from_payload | — | standard | ⚪ Missing |
| harbor.core.log_draft._snapshot_summary | — | standard | ⚪ Missing |
| harbor.core.module_capsule._sort_unique | — | standard | ⚪ Missing |
| harbor.core.contract_impact._sorted_findings | — | standard | ⚪ Missing |
| harbor.core.index_entry._source_confidence_summary | — | standard | ⚪ Missing |
| harbor.core.index_entry._source_fingerprints | — | standard | ⚪ Missing |
| harbor.core.index_entry._source_kinds | — | standard | ⚪ Missing |
| harbor.core.log_draft._split_list_values | — | standard | ⚪ Missing |
| harbor.core.module_capsule._stable_contract_rows | — | standard | ⚪ Missing |
| harbor.core.sync.SyncEngine._status_entry_from_snapshot_item | — | standard | ⚪ Missing |
| harbor.core.doctor._status_text | — | standard | ⚪ Missing |
| harbor.core.doctor._status_to_json | — | standard | ⚪ Missing |
| harbor.core.module_capsule._strictness_rank | — | standard | ⚪ Missing |
| harbor.core.path_normalization._strip_root_prefix | — | standard | ⚪ Missing |
| harbor.core.sync._subject_source_confidence_summary | — | standard | ⚪ Missing |
| harbor.core.sync._subject_source_fingerprints | — | standard | ⚪ Missing |
| harbor.core.sync._subject_source_kinds | — | standard | ⚪ Missing |
| harbor.core.log_draft._summarize_affected_areas_for_details | — | standard | ⚪ Missing |
| harbor.core.module_capsule._summarize_strictness | — | standard | ⚪ Missing |
| harbor.core.log_draft._summarize_validation_for_details | — | standard | ⚪ Missing |
| harbor.core.project_structure._supporting_area_purpose | — | standard | ⚪ Missing |
| harbor.core.project_structure._table_cell | — | standard | ⚪ Missing |
| harbor.core.init_prompt._title_with_marker | — | standard | ⚪ Missing |
| harbor.core.advice_config._to_bool | — | standard | ⚪ Missing |
| harbor.core.workspace._to_bool | — | standard | ⚪ Missing |
| harbor.core.workspace_inspect._to_display_path | — | standard | ⚪ Missing |
| harbor.core.workspace_migrate._to_display_path | — | standard | ⚪ Missing |
| harbor.adapters.typescript.parser._to_lineno | — | standard | ⚪ Missing |
| harbor.adapters.typescript.adapter._to_posix_path | — | standard | ⚪ Missing |
| harbor.core.project_structure._to_project_relative_path | — | standard | ⚪ Missing |
| harbor.core.l2._to_repo_relative | — | standard | ⚪ Missing |
| harbor.core.log_draft._to_repo_relative_display | — | standard | ⚪ Missing |
| harbor.core.drafting.DiaryDrafter._trim_segment | — | standard | ⚪ Missing |
| harbor.core.init_prompt._try_arrow_select | — | standard | ⚪ Missing |
| harbor.core.doctor._unique | — | standard | ⚪ Missing |
| harbor.core.init_wizard._update_managed_block | — | standard | ⚪ Missing |
| harbor.core.diary.DiaryManager._utc_now_iso | — | standard | ⚪ Missing |
| harbor.core.baseline_artifact._validate_artifact | — | standard | ⚪ Missing |
| harbor.core.workspace._validate_within_repo | — | standard | ⚪ Missing |
| harbor.core.init_wizard._write_file_with_policy | — | standard | ⚪ Missing |
| harbor.core.context_integrity._yaml_quote | — | standard | ⚪ Missing |
| harbor.core.project_structure._yes_no | — | standard | ⚪ Missing |
| harbor.core.index.IndexBuilder.adapter | Backward-compatible adapter accessor without instance har... | standard | ⚪ Missing |
| harbor.core.sync.SyncEngine.adapter | — | standard | ⚪ Missing |
| harbor.core.decorator.DecoratorEngine.apply | — | standard | ⚪ Missing |
| harbor.core.audit.SemanticGuard.audit | — | standard | ⚪ Missing |
| harbor.core.baseline_artifact.build_checkpoint_baseline_artifact | Build the accepted checkpoint baseline artifact payload. | standard | ⚪ Missing |
| harbor.core.ci.build_checkpoint_ci_result | — | standard | ⚪ Missing |
| harbor.core.context_integrity.build_context_integrity_metadata | — | standard | ⚪ Missing |
| harbor.core.contract_impact.build_contract_impact_report | — | standard | ⚪ Missing |
| harbor.core.ci.build_doctor_ci_result | — | standard | ⚪ Missing |
| harbor.core.doctor.build_doctor_report | — | standard | ⚪ Missing |
| harbor.core.module_capsule.build_module_card_frontmatter | — | standard | ⚪ Missing |
| harbor.core.audit.SemanticGuard.build_prompt | — | standard | ⚪ Missing |
| harbor.core.log_draft.build_saved_diary_draft_output_path | Build a timestamped safe reports path for `harbor log dra... | standard | ⚪ Missing |
| harbor.core.ci.build_stale_ci_result | — | standard | ⚪ Missing |
| harbor.core.workspace_inspect.build_workspace_inspect_report | — | standard | ⚪ Missing |
| harbor.core.workspace_migrate.build_workspace_migrate_dry_run_report | — | standard | ⚪ Missing |
| harbor.core.workspace.build_workspace_paths | — | standard | ⚪ Missing |
| harbor.core.l2.L2Generator.canonical_readme_path | — | standard | ⚪ Missing |
| harbor.core.change_window.change_window_dir | — | standard | ⚪ Missing |
| harbor.core.module_skill.check_capsule_ready_for_skill | — | standard | ⚪ Missing |
| harbor.core.stale.check_l2_readme_export_stale | — | standard | ⚪ Missing |
| harbor.core.stale.check_l2_readme_stale | — | standard | ⚪ Missing |
| harbor.core.module_capsule.check_module_capsule_stale | — | standard | ⚪ Missing |
| harbor.core.contract_impact.classify_contract_impact_for_docstring_diff | — | standard | ⚪ Missing |
| harbor.core.contract_impact.classify_contract_impact_for_file_path | — | standard | ⚪ Missing |
| harbor.core.contract_impact.classify_contract_impact_for_function_change | — | standard | ⚪ Missing |
| harbor.core.contract_impact.classify_contract_impact_from_status_record | — | standard | ⚪ Missing |
| harbor.core.project_structure.classify_project_area | — | standard | ⚪ Missing |
| harbor.core.l2.L2Generator.collect_all_indexed_modules | — | standard | ⚪ Missing |
| harbor.core.changed_scope.collect_changed_modules_from_status | — | standard | ⚪ Missing |
| harbor.core.changed_scope.collect_changed_paths_from_status | — | standard | ⚪ Missing |
| harbor.core.sync.SyncEngine.collect_current_snapshot | Collect the current comparable checkpoint snapshot from s... | standard | ⚪ Missing |
| harbor.core.change_window.collect_git_workspace_state | Collect lightweight git metadata for change-window snapsh... | standard | ⚪ Missing |
| harbor.core.l2.collect_modules_from_paths | — | standard | ⚪ Missing |
| harbor.core.context_integrity.compose_markdown_with_frontmatter | — | standard | ⚪ Missing |
| harbor.core.utils.compute_body_hash | — | standard | ⚪ Missing |
| harbor.core.context_integrity.compute_contract_fingerprint | — | standard | ⚪ Missing |
| harbor.adapters.base.ContractSource.compute_fingerprint | — | standard | ⚪ Missing |
| harbor.core.context_integrity.compute_generator_fingerprint | — | standard | ⚪ Missing |
| harbor.core.l2.L2Generator.compute_meta_hash | — | standard | ⚪ Missing |
| harbor.core.module_capsule.compute_module_fingerprint | — | standard | ⚪ Missing |
| harbor.core.context_integrity.compute_source_fingerprint | — | standard | ⚪ Missing |
| harbor.core.init_prompt.confirm | — | standard | ⚪ Missing |
| harbor.core.context_integrity.content_without_generated_at_for_compare | — | standard | ⚪ Missing |
| harbor.core.index_entry.contract_subject_to_index_entry | — | standard | ⚪ Missing |
| harbor.core.ci.CheckpointCIItem.dedupe_key | — | standard | ⚪ Missing |
| harbor.adapters.registry.AdapterRegistry.default | — | standard | ⚪ Missing |
| harbor.core.utils.derive_adopted_roots | — | standard | ⚪ Missing |
| harbor.core.console_output.detect_console_encoding | — | standard | ⚪ Missing |
| harbor.core.changed_scope.detect_generator_integrity_changes | — | standard | ⚪ Missing |
| harbor.core.module_capsule.detect_tests_for_module | — | standard | ⚪ Missing |
| harbor.adapters.base.LanguageAdapter.discover_files | — | standard | ⚪ Missing |
| harbor.adapters.typescript.adapter.TypeScriptAdapter.discover_files | — | standard | ⚪ Missing |
| harbor.core.utils.discover_indexable_files | — | standard | ⚪ Missing |
| harbor.core.advice_config.AdviceSettings.enabled | — | standard | ⚪ Missing |
| harbor.core.contract_presence.evaluate_contract_presence | — | standard | ⚪ Missing |
| harbor.core.changed_scope.expand_modules_with_indexed_parents | — | standard | ⚪ Missing |
| harbor.core.diary.DiaryManager.export_markdown | — | standard | ⚪ Missing |
| harbor.adapters.typescript.jsdoc.extract_adjacent_tsdoc | — | standard | ⚪ Missing |
| harbor.core.context_integrity.extract_integrity_fingerprints | — | standard | ⚪ Missing |
| harbor.core.utils.find_function_node | — | standard | ⚪ Missing |
| harbor.core.ci.format_checkpoint_ci_result | — | standard | ⚪ Missing |
| harbor.core.ci.format_ci_result | — | standard | ⚪ Missing |
| harbor.core.contract_impact.format_contract_impact_report | — | standard | ⚪ Missing |
| harbor.core.doctor.format_doctor_report | — | standard | ⚪ Missing |
| harbor.core.stale.format_stale_summary | 将 stale 检查结果渲染为 CLI 文本摘要。 | standard | ⚪ Missing |
| harbor.core.workspace_inspect.format_workspace_inspect_report | — | standard | ⚪ Missing |
| harbor.core.workspace_migrate.format_workspace_migrate_report | — | standard | ⚪ Missing |
| harbor.adapters.registry.AdapterRegistry.from_config | — | standard | ⚪ Missing |
| harbor.core.git_utils.GitIgnoreMatcher.from_root | — | standard | ⚪ Missing |
| harbor.core.index_entry.function_contract_to_index_entry | — | standard | ⚪ Missing |
| harbor.adapters.python.compat.function_contract_to_subject | — | standard | ⚪ Missing |
| harbor.core.module_capsule.generate_debug_playbook | — | standard | ⚪ Missing |
| harbor.core.drafting.DiaryDrafter.generate_draft | — | standard | ⚪ Missing |
| harbor.core.module_capsule.generate_module_card | — | standard | ⚪ Missing |
| harbor.core.module_skill.generate_module_skill | — | standard | ⚪ Missing |
| harbor.core.module_capsule.generate_review_checklist | — | standard | ⚪ Missing |
| harbor.core.repair_guidance.generic_conservative_guidance | — | standard | ⚪ Missing |
| harbor.adapters.registry.AdapterRegistry.get_adapter | — | standard | ⚪ Missing |
| harbor.adapters.registry.AdapterRegistry.get_adapters | — | standard | ⚪ Missing |
| harbor.adapters.registry.AdapterRegistry.get_enabled_languages | — | standard | ⚪ Missing |
| harbor.core.change_window.get_latest_change_window | Return the newest readable snapshot, optionally filtered ... | standard | ⚪ Missing |
| harbor.core.repair_guidance.guidance_for_checkpoint_category | — | standard | ⚪ Missing |
| harbor.core.repair_guidance.guidance_for_doctor_item | — | standard | ⚪ Missing |
| harbor.core.repair_guidance.guidance_for_stale_item | — | standard | ⚪ Missing |
| harbor.test_utils.harbor_ddt_target | — | standard | ⚪ Missing |
| harbor.core.index_entry.index_entry_to_cache_item | — | standard | ⚪ Missing |
| harbor.core.audit.LLMProvider.infer | — | standard | ⚪ Missing |
| harbor.core.audit.MockProvider.infer | — | standard | ⚪ Missing |
| harbor.core.audit.OpenAIProvider.infer | — | standard | ⚪ Missing |
| harbor.core.l2.infer_module_from_path | 从文件路径推断模块目录（统一为 POSIX 风格）。 | standard | ⚪ Missing |
| harbor.core.contract_presence.is_contract_required | — | standard | ⚪ Missing |
| harbor.adapters.registry.AdapterRegistry.is_enabled | — | standard | ⚪ Missing |
| harbor.core.change_window.list_change_windows | List readable change-window snapshots from newest to oldest. | standard | ⚪ Missing |
| harbor.core.diary.DiaryManager.load_active | — | standard | ⚪ Missing |
| harbor.core.baseline_artifact.load_checkpoint_baseline_artifact | Load and validate the accepted checkpoint baseline artifa... | standard | ⚪ Missing |
| harbor.core.workspace.load_workspace_config | — | standard | ⚪ Missing |
| harbor.core.workspace.load_workspace_paths | — | standard | ⚪ Missing |
| harbor.core.path_normalization.looks_like_absolute_path | — | standard | ⚪ Missing |
| harbor.adapters.base.ContractSubject.make_target_id | — | standard | ⚪ Missing |
| harbor.core.context_integrity.merge_generated_at | — | standard | ⚪ Missing |
| harbor.core.module_capsule.module_capsule_dir | — | standard | ⚪ Missing |
| harbor.core.baseline_artifact.normalize_baseline_item_path | Normalize one baseline item path into repo-relative POSIX... | standard | ⚪ Missing |
| harbor.core.changed_scope.normalize_changed_path | — | standard | ⚪ Missing |
| harbor.core.l2.normalize_indexed_module_candidate | 将索引记录路径归一化为模块候选，优先映射 repo 内绝对路径。 | standard | ⚪ Missing |
| harbor.core.module_capsule.normalize_module_path | — | standard | ⚪ Missing |
| harbor.core.path_normalization.normalize_path_separators | — | standard | ⚪ Missing |
| harbor.core.module_skill.normalize_skill_slug | — | standard | ⚪ Missing |
| harbor.adapters.typescript.hashing.normalize_text | — | standard | ⚪ Missing |
| harbor.adapters.typescript.hashing.normalized_sha256 | — | standard | ⚪ Missing |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser.parse | — | standard | ⚪ Missing |
| harbor.adapters.base.LanguageAdapter.parse_file | — | standard | ⚪ Missing |
| harbor.adapters.typescript.adapter.TypeScriptAdapter.parse_file | — | standard | ⚪ Missing |
| harbor.core.context_integrity.parse_frontmatter | — | standard | ⚪ Missing |
| harbor.core.workspace.parse_workspace_export_options | — | standard | ⚪ Missing |
| harbor.core.decorator.DecoratorEngine.preview | — | standard | ⚪ Missing |
| harbor.core.module_capsule.preview_module_capsule | — | standard | ⚪ Missing |
| harbor.core.change_window.prune_change_windows | Delete change-window snapshots older than the newest `lim... | standard | ⚪ Missing |
| harbor.core.project_structure.rank_key_file | — | standard | ⚪ Missing |
| harbor.core.module_capsule.read_capsule_fingerprint | — | standard | ⚪ Missing |
| harbor.core.context_integrity.render_frontmatter | — | standard | ⚪ Missing |
| harbor.core.path_normalization.repo_relative_path | — | standard | ⚪ Missing |
| harbor.core.advice_config.resolve_advice_settings | — | standard | ⚪ Missing |
| harbor.core.utils.resolve_code_roots | — | standard | ⚪ Missing |
| harbor.core.log_draft.resolve_draft_source | Resolve and parse one authorized draft source for `harbor... | standard | ⚪ Missing |
| harbor.core.module_capsule.resolve_module_capsule_paths | — | standard | ⚪ Missing |
| harbor.core.audit.resolve_provider | — | standard | ⚪ Missing |
| harbor.core.workspace.resolve_workspace_config_path | — | standard | ⚪ Missing |
| harbor.core.init_wizard.InitWizard.run | — | standard | ⚪ Missing |
| harbor.core.doctor.run_config_index_check | — | standard | ⚪ Missing |
| harbor.core.doctor.run_ddt_fast_check | — | standard | ⚪ Missing |
| harbor.core.doctor.run_derived_views_check | 检查模块派生视图状态并汇总为 Doctor 结果。 | standard | ⚪ Missing |
| harbor.core.doctor.run_skill_reference_check | — | standard | ⚪ Missing |
| harbor.core.doctor.run_workspace_status_check | — | standard | ⚪ Missing |
| harbor.core.console_output.safe_console_print | — | standard | ⚪ Missing |
| harbor.core.path_normalization.sanitize_path_for_display | — | standard | ⚪ Missing |
| harbor.core.workspace_inspect.sanitize_text | — | standard | ⚪ Missing |
| harbor.core.workspace_migrate.sanitize_text | — | standard | ⚪ Missing |
| harbor.core.decorator.DecoratorEngine.scan | — | standard | ⚪ Missing |
| harbor.core.ddt.DDTScanner.scan_tests | — | standard | ⚪ Missing |
| harbor.core.init_prompt.select_one | — | standard | ⚪ Missing |
| harbor.adapters.typescript.hashing.sha256_text | — | standard | ⚪ Missing |
| harbor.core.module_skill.skill_dir_for_module | — | standard | ⚪ Missing |
| harbor.core.context_integrity.split_frontmatter | — | standard | ⚪ Missing |
| harbor.core.stale.stale_report_to_dict | 将 stale 检查结果序列化为 machine-readable JSON 对象。 | standard | ⚪ Missing |
| harbor.core.context_integrity.strip_frontmatter | — | standard | ⚪ Missing |
| harbor.core.workspace_inspect.WorkspaceGeneratedViewsStatus.to_dict | — | standard | ⚪ Missing |
| harbor.core.workspace_inspect.WorkspaceGitTrackingStatus.to_dict | — | standard | ⚪ Missing |
| harbor.core.workspace_inspect.WorkspaceLegacyPathStatus.to_dict | — | standard | ⚪ Missing |
| harbor.core.workspace_migrate.WorkspaceMigrationPlanItem.to_dict | — | standard | ⚪ Missing |
| harbor.core.diary.DiaryEntry.to_json | — | standard | ⚪ Missing |
| harbor.core.ddt.DDTValidator.validate | — | standard | ⚪ Missing |
| harbor.core.workspace_inspect.workspace_inspect_report_to_dict | — | standard | ⚪ Missing |
| harbor.core.workspace_migrate.workspace_migrate_report_to_dict | — | standard | ⚪ Missing |
| harbor.core.l2.L2Generator.write | — | standard | ⚪ Missing |
| harbor.core.baseline_artifact.write_checkpoint_baseline_artifact | Validate and write the accepted checkpoint baseline artif... | standard | ⚪ Missing |
| harbor.core.module_skill.write_module_skill | — | standard | ⚪ Missing |

</details>

## Dependency (MVP)
- (TBD) 未来基于 import 简要分析模块依赖。
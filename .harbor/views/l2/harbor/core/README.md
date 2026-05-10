---
generated_by: "harbor-spec"
harbor_version: "1.3.0"
view_type: "l2_readme"
module: "harbor/core"
generated_at: "2026-05-10T14:41:02Z"
generation_command: "harbor docs --module harbor/core --write"
stale_policy: "advisory"
source_path_count: 28
source_paths_truncated: false
source_paths:
  - "harbor/core/__init__.py"
  - "harbor/core/audit.py"
  - "harbor/core/ci.py"
  - "harbor/core/context_integrity.py"
  - "harbor/core/contract_impact.py"
  - "harbor/core/contract_presence.py"
  - "harbor/core/ddt.py"
  - "harbor/core/decorator.py"
  - "harbor/core/diary.py"
  - "harbor/core/doctor.py"
  - "harbor/core/drafting.py"
  - "harbor/core/git_utils.py"
  - "harbor/core/index.py"
  - "harbor/core/init.py"
  - "harbor/core/init_prompt.py"
  - "harbor/core/init_wizard.py"
  - "harbor/core/l2.py"
  - "harbor/core/module_capsule.py"
  - "harbor/core/module_skill.py"
  - "harbor/core/project_structure.py"
  - "harbor/core/stale.py"
  - "harbor/core/storage.py"
  - "harbor/core/sync.py"
  - "harbor/core/t_decorate.py"
  - "harbor/core/utils.py"
  - "harbor/core/workspace.py"
  - "harbor/core/workspace_inspect.py"
  - "harbor/core/workspace_migrate.py"
source_fingerprint: "sha256:b11804536c79ba91281e7e5cf3e638db7a2266d6ca342174a4f3e839afaef3e3"
contract_fingerprint: "sha256:c58b0a66e3a070a4f99e67b92c10e0f0dd5748ac4a7d9262dd575d6bd589c7d0"
generator_fingerprint: "sha256:6b9304b870db7c5ff618b75f674235d81f2106e80a504eab0a1e1823ea26ed51"
---

# Module: harbor/core

## Public API
| Function | Summary | Strictness | DDT Status |
|---|---|---|---|
| harbor.core.drafting.DiaryDrafter.__init__ | AI 辅助生成 Diary 草稿。 | strict | ❌ Missing |
| harbor.core.index.IndexBuilder._iter_py_files | 生成待扫描的 Python 文件列表（支持 Git 感知剪枝）。 | strict | ❌ Missing |
| harbor.core.init.Initializer.autodetect | 高级启发式自动探测。 | strict | ❌ Missing |
| harbor.core.index.IndexBuilder.build | 构建或增量更新 L3 索引到缓存。 | strict | ❌ Missing |
| harbor.core.sync.SyncEngine.check_status | 对比缓存索引与当前代码，输出 Harbor 上下文状态。 | strict | ✅ Valid |
| harbor.core.ci.checkpoint_ci_result_to_dict | — | strict | ❌ Missing |
| harbor.core.ci.ci_result_to_dict | — | strict | ❌ Missing |
| harbor.core.init.ProjectDetector.detect | 启发式探测技术栈并生成配置建议。 | strict | ❌ Missing |
| harbor.core.init.Initializer.detect_code_roots | 智能探测项目代码根目录。 | strict | ❌ Missing |
| harbor.core.l2.L2Generator.generate | 生成指定模块的 L2 README Markdown 文本。 | strict | ❌ Missing |
| harbor.core.storage.HarborDB.get_all_files | 列出所有已索引文件及其 mtime。 | strict | ❌ Missing |
| harbor.core.storage.HarborDB.get_file | 查询单文件记录。 | strict | ❌ Missing |
| harbor.core.storage.HarborDB.get_file_entries | 查询指定文件的所有条目。 | strict | ❌ Missing |
| harbor.core.index.IndexBuilder.iter_build | 以生成器方式构建索引，逐文件产出进度事件。 | strict | ❌ Missing |
| harbor.core.utils.iter_project_files | 生成待扫描的 Python 文件列表（统一剪枝逻辑）。 | strict | ❌ Missing |
| harbor.core.diary.DiaryManager.log | 写入一条 DiaryEntry 到当月 JSONL。 | strict | ❌ Missing |
| harbor.core.git_utils.GitIgnoreMatcher.match_dir | 判断相对路径目录是否被忽略（用于剪枝）。 | strict | ❌ Missing |
| harbor.core.git_utils.GitIgnoreMatcher.match_file | 判断相对路径文件是否被忽略。 | strict | ❌ Missing |
| harbor.core.storage.HarborDB.migrate_from_json | 从旧版 JSON 索引迁移到 SQLite。 | strict | ❌ Missing |
| harbor.core.index.process_file_worker | 并行 Worker：解析并计算单文件条目。 | strict | ❌ Missing |
| harbor.core.storage.HarborDB.purge_missing | 删除 DB 中存在但磁盘已缺失的文件记录。 | strict | ❌ Missing |
| harbor.core.ci.CIFailure.to_dict | — | strict | ❌ Missing |
| harbor.core.ci.CheckpointCIItem.to_dict | — | strict | ❌ Missing |
| harbor.core.storage.HarborDB.transaction | 事务上下文管理器（单文件原子写入）。 | strict | ❌ Missing |
| harbor.core.storage.HarborDB.upsert_entry | 插入或更新函数条目。 | strict | ❌ Missing |
| harbor.core.storage.HarborDB.upsert_file | 插入或更新文件记录。 | strict | ❌ Missing |
| harbor.core.init.Initializer.write_config | 写入 `.harbor/config/harbor.yaml`。 | strict | ❌ Missing |

## Internal Details (optional)
<details>
<summary>Internal functions</summary>

| Function | Summary | Strictness | DDT Status |
|---|---|---|---|
| harbor.core.ddt.DDTScanner.__init__ | — | standard | ⚪ Missing |
| harbor.core.ddt.DDTValidator.__init__ | — | standard | ⚪ Missing |
| harbor.core.index.IndexBuilder.__init__ | — | standard | ⚪ Missing |
| harbor.core.audit.OpenAIProvider.__init__ | — | standard | ⚪ Missing |
| harbor.core.init.ProjectDetector.__init__ | — | standard | ⚪ Missing |
| harbor.core.init.Initializer.__init__ | — | standard | ⚪ Missing |
| harbor.core.sync.SyncEngine.__init__ | — | standard | ⚪ Missing |
| harbor.core.git_utils.GitIgnoreMatcher.__init__ | — | standard | ⚪ Missing |
| harbor.core.diary.DiaryManager.__init__ | 初始化 Diary 路径上下文（canonical 写入 + legacy 读取兼容）。 | standard | ⚪ Missing |
| harbor.core.storage.HarborDB.__init__ | — | standard | ⚪ Missing |
| harbor.core.l2.L2Generator.__init__ | — | standard | ⚪ Missing |
| harbor.core.init_wizard.InitWizard.__init__ | — | standard | ⚪ Missing |
| harbor.core.init_wizard._append_missing_env_keys | — | standard | ⚪ Missing |
| harbor.core.storage.HarborDB._apply_pragmas | — | standard | ⚪ Missing |
| harbor.core.project_structure._area_purpose | — | standard | ⚪ Missing |
| harbor.core.context_integrity._as_repo_relative | — | standard | ⚪ Missing |
| harbor.core.init_wizard.InitWizard._ask_language | — | standard | ⚪ Missing |
| harbor.core.init_wizard.InitWizard._ask_project | — | standard | ⚪ Missing |
| harbor.core.init_wizard.InitWizard._ask_yes_no | — | standard | ⚪ Missing |
| harbor.core.project_structure._belongs_to_module | — | standard | ⚪ Missing |
| harbor.core.module_capsule._belongs_to_module | — | standard | ⚪ Missing |
| harbor.core.workspace._build_path | — | standard | ⚪ Missing |
| harbor.core.drafting.DiaryDrafter._build_prompt | — | standard | ⚪ Missing |
| harbor.core.project_structure._build_transient_index_from_files | — | standard | ⚪ Missing |
| harbor.core.project_structure._capsule_exists | — | standard | ⚪ Missing |
| harbor.core.workspace_inspect._check_git_ignored | — | standard | ⚪ Missing |
| harbor.core.init_prompt._choice_label | — | standard | ⚪ Missing |
| harbor.core.workspace_inspect._classify_git_tracking | — | standard | ⚪ Missing |
| harbor.core.contract_impact._classify_tests_path | — | standard | ⚪ Missing |
| harbor.core.workspace_inspect._collect_advisory | — | standard | ⚪ Missing |
| harbor.core.ci._collect_checkpoint_next_steps | — | standard | ⚪ Missing |
| harbor.core.project_structure._collect_fallback_files | — | standard | ⚪ Missing |
| harbor.core.workspace_inspect._collect_generated_views | — | standard | ⚪ Missing |
| harbor.core.workspace_inspect._collect_git_tracking | — | standard | ⚪ Missing |
| harbor.core.l2.L2Generator._collect_integrity_inputs | — | standard | ⚪ Missing |
| harbor.core.workspace_inspect._collect_legacy_paths | — | standard | ⚪ Missing |
| harbor.core.workspace_migrate._collect_module_readme_exports | — | standard | ⚪ Missing |
| harbor.core.doctor._collect_next_steps | — | standard | ⚪ Missing |
| harbor.core.ci._collect_next_steps | — | standard | ⚪ Missing |
| harbor.core.contract_impact._confidence_for_level | — | standard | ⚪ Missing |
| harbor.core.diary.DiaryManager._current_file_path | — | standard | ⚪ Missing |
| harbor.core.context_integrity._decode_scalar | — | standard | ⚪ Missing |
| harbor.core.init.ProjectDetector._dedup | — | standard | ⚪ Missing |
| harbor.core.ci._dedupe_checkpoint_items | — | standard | ⚪ Missing |
| harbor.core.init_wizard._default_language | — | standard | ⚪ Missing |
| harbor.core.init_wizard._default_project | — | standard | ⚪ Missing |
| harbor.core.doctor._derived_view_detail_status | 将内部 view status 归一化为可展示文本。 | standard | ⚪ Missing |
| harbor.core.init.ProjectDetector._detect_django | — | standard | ⚪ Missing |
| harbor.core.init.ProjectDetector._detect_go | — | standard | ⚪ Missing |
| harbor.core.init.ProjectDetector._detect_java | — | standard | ⚪ Missing |
| harbor.core.init.ProjectDetector._detect_node | — | standard | ⚪ Missing |
| harbor.core.init.ProjectDetector._detect_python_misc | — | standard | ⚪ Missing |
| harbor.core.decorator.DecoratorEngine._docstring_node | — | standard | ⚪ Missing |
| harbor.core.init_wizard.InitWizard._emit_detected_summary | — | standard | ⚪ Missing |
| harbor.core.init_wizard.InitWizard._emit_ide_guidance | — | standard | ⚪ Missing |
| harbor.core.init_wizard.InitWizard._emit_next_steps | — | standard | ⚪ Missing |
| harbor.core.init_wizard.InitWizard._emit_project_rules_guidance | — | standard | ⚪ Missing |
| harbor.core.storage.HarborDB._ensure_schema | — | standard | ⚪ Missing |
| harbor.core.diary.DiaryManager._ensure_within_repo | — | standard | ⚪ Missing |
| harbor.core.module_capsule._ensure_within_root | — | standard | ⚪ Missing |
| harbor.core.l2.L2Generator._ensure_within_root | — | standard | ⚪ Missing |
| harbor.core.diary.DiaryManager._entry_dedupe_key | — | standard | ⚪ Missing |
| harbor.core.init.ProjectDetector._exclude_covers_root | — | standard | ⚪ Missing |
| harbor.core.drafting.DiaryDrafter._extract_code_context | — | standard | ⚪ Missing |
| harbor.core.decorator.DecoratorEngine._extract_functions | — | standard | ⚪ Missing |
| harbor.core.project_structure._extract_toml_string_block | — | standard | ⚪ Missing |
| harbor.core.index.IndexBuilder._file_hash | — | standard | ⚪ Missing |
| harbor.core.init.ProjectDetector._filter_excludes | — | standard | ⚪ Missing |
| harbor.core.doctor._filter_safe_next_steps | — | standard | ⚪ Missing |
| harbor.core.contract_impact._finding_to_dict | — | standard | ⚪ Missing |
| harbor.core.stale._format_view_lines | 格式化单个视图状态的文本行。 | standard | ⚪ Missing |
| harbor.core.diary.DiaryManager._from_dict | — | standard | ⚪ Missing |
| harbor.core.init.ProjectDetector._get_default_excludes | — | standard | ⚪ Missing |
| harbor.core.init_wizard._has_env_ignore | — | standard | ⚪ Missing |
| harbor.core.decorator.DecoratorEngine._has_scope_tag | — | standard | ⚪ Missing |
| harbor.core.index.IndexBuilder._index_entry | — | standard | ⚪ Missing |
| harbor.core.project_structure._infer_area | — | standard | ⚪ Missing |
| harbor.core.audit._infer_file_path_from_contract | — | standard | ⚪ Missing |
| harbor.core.contract_impact._is_contract_asserting_test | — | standard | ⚪ Missing |
| harbor.core.init.ProjectDetector._is_dangerous_python_exclude | — | standard | ⚪ Missing |
| harbor.core.contract_impact._is_docs_or_rules_path | — | standard | ⚪ Missing |
| harbor.core.decorator.DecoratorEngine._is_filtered_name | — | standard | ⚪ Missing |
| harbor.core.contract_impact._is_generated_view_module | — | standard | ⚪ Missing |
| harbor.core.init_prompt._is_interactive | — | standard | ⚪ Missing |
| harbor.core.contract_impact._is_public_cli_path | — | standard | ⚪ Missing |
| harbor.core.contract_impact._is_test_path | — | standard | ⚪ Missing |
| harbor.core.contract_impact._is_to_dict_like | — | standard | ⚪ Missing |
| harbor.core.init_wizard._is_tty | — | standard | ⚪ Missing |
| harbor.core.contract_impact._is_write_like | — | standard | ⚪ Missing |
| harbor.core.decorator.DecoratorEngine._iter_function_nodes | — | standard | ⚪ Missing |
| harbor.core.ddt.DDTScanner._iter_py_files | — | standard | ⚪ Missing |
| harbor.core.sync.SyncEngine._iter_py_files | — | standard | ⚪ Missing |
| harbor.core.diary.DiaryManager._iter_read_dirs | — | standard | ⚪ Missing |
| harbor.core.context_integrity._json_stable_hash | — | standard | ⚪ Missing |
| harbor.core.project_structure._key_files_display | — | standard | ⚪ Missing |
| harbor.core.drafting.DiaryDrafter._kv_fallback_parse | — | standard | ⚪ Missing |
| harbor.core.decorator.DecoratorEngine._leading_whitespace | — | standard | ⚪ Missing |
| harbor.core.index.IndexBuilder._load_cache | — | standard | ⚪ Missing |
| harbor.core.ddt.DDTScanner._load_config | — | standard | ⚪ Missing |
| harbor.core.index.IndexBuilder._load_config | — | standard | ⚪ Missing |
| harbor.core.sync.SyncEngine._load_config | — | standard | ⚪ Missing |
| harbor.core.ddt.DDTValidator._load_index | — | standard | ⚪ Missing |
| harbor.core.project_structure._load_index | — | standard | ⚪ Missing |
| harbor.core.module_capsule._load_index | — | standard | ⚪ Missing |
| harbor.core.l2.L2Generator._load_index | — | standard | ⚪ Missing |
| harbor.core.ddt.DDTValidator._load_map | — | standard | ⚪ Missing |
| harbor.core.l2.L2Generator._load_meta | — | standard | ⚪ Missing |
| harbor.core.init_wizard._load_template_text | — | standard | ⚪ Missing |
| harbor.core.contract_presence._looks_like_contract_doc | — | standard | ⚪ Missing |
| harbor.core.init_wizard._mask_key | — | standard | ⚪ Missing |
| harbor.core.contract_impact._max_level | — | standard | ⚪ Missing |
| harbor.core.doctor._merge_status | — | standard | ⚪ Missing |
| harbor.core.workspace_migrate._module_dir_has_python_files | — | standard | ⚪ Missing |
| harbor.core.decorator.DecoratorEngine._module_qual_from_path | — | standard | ⚪ Missing |
| harbor.core.context_integrity._normalize_body_for_compare | — | standard | ⚪ Missing |
| harbor.core.ci._normalize_checkpoint_key_path | — | standard | ⚪ Missing |
| harbor.core.diary.DiaryManager._normalize_for_hash | — | standard | ⚪ Missing |
| harbor.core.init.ProjectDetector._normalize_glob | — | standard | ⚪ Missing |
| harbor.core.stale._normalize_l2_body_for_export_compare | — | standard | ⚪ Missing |
| harbor.core.stale._normalize_l2_markdown_for_stale | — | standard | ⚪ Missing |
| harbor.core.contract_impact._normalize_path | — | standard | ⚪ Missing |
| harbor.core.workspace._normalize_path_like | — | standard | ⚪ Missing |
| harbor.core.project_structure._normalize_rel_path | — | standard | ⚪ Missing |
| harbor.core.module_capsule._normalize_rel_path | — | standard | ⚪ Missing |
| harbor.core.context_integrity._normalize_rel_path | — | standard | ⚪ Missing |
| harbor.core.contract_impact._normalize_symbol | — | standard | ⚪ Missing |
| harbor.core.contract_impact._normalize_symbol_for_classification | — | standard | ⚪ Missing |
| harbor.core.context_integrity._now_iso | — | standard | ⚪ Missing |
| harbor.core.doctor._parse_generated_frontmatter_safely | — | standard | ⚪ Missing |
| harbor.core.init.ProjectDetector._parse_gitignore | — | standard | ⚪ Missing |
| harbor.core.diary.DiaryManager._parse_ts | — | standard | ⚪ Missing |
| harbor.core.storage.HarborDB._posix_rel | — | standard | ⚪ Missing |
| harbor.core.ci._push_status_failures | — | standard | ⚪ Missing |
| harbor.core.init_wizard._read_env_keys | — | standard | ⚪ Missing |
| harbor.core.l2.L2Generator._read_meta_file | — | standard | ⚪ Missing |
| harbor.core.project_structure._read_project_metadata | — | standard | ⚪ Missing |
| harbor.core.init_prompt._render_inline_options | — | standard | ⚪ Missing |
| harbor.core.context_integrity._render_scalar | — | standard | ⚪ Missing |
| harbor.core.diary.DiaryManager._resolve_author | — | standard | ⚪ Missing |
| harbor.core.l2.L2Generator._resolve_canonical_readme_path | — | standard | ⚪ Missing |
| harbor.core.diary.DiaryManager._resolve_diary_dir | — | standard | ⚪ Missing |
| harbor.core.module_capsule._resolve_docs_export_modules_root | — | standard | ⚪ Missing |
| harbor.core.project_structure._resolve_docs_export_project_structure_path | — | standard | ⚪ Missing |
| harbor.core.l2.L2Generator._resolve_export_readme_path | — | standard | ⚪ Missing |
| harbor.core.diary.DiaryManager._resolve_legacy_diary_dirs | — | standard | ⚪ Missing |
| harbor.core.l2.L2Generator._resolve_meta_path | — | standard | ⚪ Missing |
| harbor.core.module_capsule._resolve_module_target_dir | — | standard | ⚪ Missing |
| harbor.core.diary.DiaryManager._resolve_repo_root | — | standard | ⚪ Missing |
| harbor.core.drafting.DiaryDrafter._safe_json_parse | — | standard | ⚪ Missing |
| harbor.core.module_capsule._safe_module_subpath | — | standard | ⚪ Missing |
| harbor.core.l2.L2Generator._safe_module_subpath | — | standard | ⚪ Missing |
| harbor.core.ci._sanitize_checkpoint_contract_impact | — | standard | ⚪ Missing |
| harbor.core.doctor._sanitize_json_text | — | standard | ⚪ Missing |
| harbor.core.stale._sanitize_json_text | — | standard | ⚪ Missing |
| harbor.core.ci._sanitize_json_text | — | standard | ⚪ Missing |
| harbor.core.contract_impact._sanitize_json_text | — | standard | ⚪ Missing |
| harbor.core.project_structure._sanitize_module | — | standard | ⚪ Missing |
| harbor.core.stale._sanitize_module_for_json | — | standard | ⚪ Missing |
| harbor.core.doctor._sanitize_single_path | — | standard | ⚪ Missing |
| harbor.core.stale._sanitize_single_path | — | standard | ⚪ Missing |
| harbor.core.ci._sanitize_single_path | — | standard | ⚪ Missing |
| harbor.core.contract_impact._sanitize_single_path | — | standard | ⚪ Missing |
| harbor.core.ci._sanitize_summary | — | standard | ⚪ Missing |
| harbor.core.index.IndexBuilder._save_cache | — | standard | ⚪ Missing |
| harbor.core.l2.L2Generator._save_meta | — | standard | ⚪ Missing |
| harbor.core.project_structure._skill_exists | — | standard | ⚪ Missing |
| harbor.core.module_capsule._sort_unique | — | standard | ⚪ Missing |
| harbor.core.contract_impact._sorted_findings | — | standard | ⚪ Missing |
| harbor.core.module_capsule._stable_contract_rows | — | standard | ⚪ Missing |
| harbor.core.doctor._status_text | — | standard | ⚪ Missing |
| harbor.core.doctor._status_to_json | — | standard | ⚪ Missing |
| harbor.core.module_capsule._strictness_rank | — | standard | ⚪ Missing |
| harbor.core.module_capsule._summarize_strictness | — | standard | ⚪ Missing |
| harbor.core.project_structure._supporting_area_purpose | — | standard | ⚪ Missing |
| harbor.core.project_structure._table_cell | — | standard | ⚪ Missing |
| harbor.core.init_prompt._title_with_marker | — | standard | ⚪ Missing |
| harbor.core.workspace._to_bool | — | standard | ⚪ Missing |
| harbor.core.workspace_migrate._to_display_path | — | standard | ⚪ Missing |
| harbor.core.workspace_inspect._to_display_path | — | standard | ⚪ Missing |
| harbor.core.project_structure._to_project_relative_path | — | standard | ⚪ Missing |
| harbor.core.l2._to_repo_relative | — | standard | ⚪ Missing |
| harbor.core.drafting.DiaryDrafter._trim_segment | — | standard | ⚪ Missing |
| harbor.core.init_prompt._try_arrow_select | — | standard | ⚪ Missing |
| harbor.core.doctor._unique | — | standard | ⚪ Missing |
| harbor.core.init_wizard._update_managed_block | — | standard | ⚪ Missing |
| harbor.core.diary.DiaryManager._utc_now_iso | — | standard | ⚪ Missing |
| harbor.core.workspace._validate_within_repo | — | standard | ⚪ Missing |
| harbor.core.init_wizard._write_file_with_policy | — | standard | ⚪ Missing |
| harbor.core.context_integrity._yaml_quote | — | standard | ⚪ Missing |
| harbor.core.project_structure._yes_no | — | standard | ⚪ Missing |
| harbor.core.decorator.DecoratorEngine.apply | — | standard | ⚪ Missing |
| harbor.core.audit.SemanticGuard.audit | — | standard | ⚪ Missing |
| harbor.core.ci.build_checkpoint_ci_result | — | standard | ⚪ Missing |
| harbor.core.context_integrity.build_context_integrity_metadata | — | standard | ⚪ Missing |
| harbor.core.contract_impact.build_contract_impact_report | — | standard | ⚪ Missing |
| harbor.core.ci.build_doctor_ci_result | — | standard | ⚪ Missing |
| harbor.core.doctor.build_doctor_report | — | standard | ⚪ Missing |
| harbor.core.module_capsule.build_module_card_frontmatter | — | standard | ⚪ Missing |
| harbor.core.audit.SemanticGuard.build_prompt | — | standard | ⚪ Missing |
| harbor.core.ci.build_stale_ci_result | — | standard | ⚪ Missing |
| harbor.core.workspace_inspect.build_workspace_inspect_report | — | standard | ⚪ Missing |
| harbor.core.workspace_migrate.build_workspace_migrate_dry_run_report | — | standard | ⚪ Missing |
| harbor.core.workspace.build_workspace_paths | — | standard | ⚪ Missing |
| harbor.core.l2.L2Generator.canonical_readme_path | — | standard | ⚪ Missing |
| harbor.core.module_skill.check_capsule_ready_for_skill | — | standard | ⚪ Missing |
| harbor.core.stale.check_l2_readme_export_stale | — | standard | ⚪ Missing |
| harbor.core.stale.check_l2_readme_stale | — | standard | ⚪ Missing |
| harbor.core.module_capsule.check_module_capsule_stale | — | standard | ⚪ Missing |
| harbor.core.stale.check_module_derived_views_stale | 检查单模块的 L2 / L2 export / Capsule 三类视图状态。 | standard | ⚪ Missing |
| harbor.core.contract_impact.classify_contract_impact_for_docstring_diff | — | standard | ⚪ Missing |
| harbor.core.contract_impact.classify_contract_impact_for_file_path | — | standard | ⚪ Missing |
| harbor.core.contract_impact.classify_contract_impact_for_function_change | — | standard | ⚪ Missing |
| harbor.core.contract_impact.classify_contract_impact_from_status_record | — | standard | ⚪ Missing |
| harbor.core.project_structure.classify_project_area | — | standard | ⚪ Missing |
| harbor.core.l2.collect_all_indexed_modules | — | standard | ⚪ Missing |
| harbor.core.l2.L2Generator.collect_all_indexed_modules | — | standard | ⚪ Missing |
| harbor.core.module_capsule.collect_module_context | — | standard | ⚪ Missing |
| harbor.core.l2.collect_modules_from_paths | — | standard | ⚪ Missing |
| harbor.core.project_structure.collect_project_structure_context | — | standard | ⚪ Missing |
| harbor.core.context_integrity.compose_markdown_with_frontmatter | — | standard | ⚪ Missing |
| harbor.core.utils.compute_body_hash | — | standard | ⚪ Missing |
| harbor.core.context_integrity.compute_contract_fingerprint | — | standard | ⚪ Missing |
| harbor.core.context_integrity.compute_generator_fingerprint | — | standard | ⚪ Missing |
| harbor.core.l2.L2Generator.compute_meta_hash | — | standard | ⚪ Missing |
| harbor.core.module_capsule.compute_module_fingerprint | — | standard | ⚪ Missing |
| harbor.core.context_integrity.compute_source_fingerprint | — | standard | ⚪ Missing |
| harbor.core.init_prompt.confirm | — | standard | ⚪ Missing |
| harbor.core.context_integrity.content_without_generated_at_for_compare | — | standard | ⚪ Missing |
| harbor.core.contract_impact.contract_impact_report_to_dict | — | standard | ⚪ Missing |
| harbor.core.ci.CheckpointCIItem.dedupe_key | — | standard | ⚪ Missing |
| harbor.core.utils.derive_adopted_roots | — | standard | ⚪ Missing |
| harbor.core.module_capsule.detect_tests_for_module | — | standard | ⚪ Missing |
| harbor.core.contract_presence.evaluate_contract_presence | — | standard | ⚪ Missing |
| harbor.core.diary.DiaryManager.export_markdown | — | standard | ⚪ Missing |
| harbor.core.context_integrity.extract_integrity_fingerprints | — | standard | ⚪ Missing |
| harbor.core.utils.find_function_node | — | standard | ⚪ Missing |
| harbor.core.ci.format_checkpoint_ci_result | — | standard | ⚪ Missing |
| harbor.core.ci.format_ci_result | — | standard | ⚪ Missing |
| harbor.core.contract_impact.format_contract_impact_report | — | standard | ⚪ Missing |
| harbor.core.doctor.format_doctor_report | — | standard | ⚪ Missing |
| harbor.core.stale.format_stale_summary | 将 stale 检查结果渲染为 CLI 文本摘要。 | standard | ⚪ Missing |
| harbor.core.workspace_inspect.format_workspace_inspect_report | — | standard | ⚪ Missing |
| harbor.core.workspace_migrate.format_workspace_migrate_report | — | standard | ⚪ Missing |
| harbor.core.git_utils.GitIgnoreMatcher.from_root | — | standard | ⚪ Missing |
| harbor.core.module_capsule.generate_debug_playbook | — | standard | ⚪ Missing |
| harbor.core.drafting.DiaryDrafter.generate_draft | — | standard | ⚪ Missing |
| harbor.core.module_capsule.generate_module_card | — | standard | ⚪ Missing |
| harbor.core.module_skill.generate_module_skill | — | standard | ⚪ Missing |
| harbor.core.project_structure.generate_project_structure_markdown | — | standard | ⚪ Missing |
| harbor.core.module_capsule.generate_review_checklist | — | standard | ⚪ Missing |
| harbor.core.audit.LLMProvider.infer | — | standard | ⚪ Missing |
| harbor.core.audit.MockProvider.infer | — | standard | ⚪ Missing |
| harbor.core.audit.OpenAIProvider.infer | — | standard | ⚪ Missing |
| harbor.core.l2.infer_module_from_path | 从文件路径推断模块目录（统一为 POSIX 风格）。 | standard | ⚪ Missing |
| harbor.core.contract_presence.is_contract_required | — | standard | ⚪ Missing |
| harbor.core.diary.DiaryManager.load_active | — | standard | ⚪ Missing |
| harbor.core.workspace.load_workspace_config | — | standard | ⚪ Missing |
| harbor.core.workspace.load_workspace_paths | — | standard | ⚪ Missing |
| harbor.core.context_integrity.merge_generated_at | — | standard | ⚪ Missing |
| harbor.core.module_capsule.module_capsule_dir | — | standard | ⚪ Missing |
| harbor.core.l2.normalize_indexed_module_candidate | 将索引记录路径归一化为模块候选，优先映射 repo 内绝对路径。 | standard | ⚪ Missing |
| harbor.core.module_capsule.normalize_module_path | — | standard | ⚪ Missing |
| harbor.core.module_skill.normalize_skill_slug | — | standard | ⚪ Missing |
| harbor.core.context_integrity.parse_frontmatter | — | standard | ⚪ Missing |
| harbor.core.workspace.parse_workspace_export_options | — | standard | ⚪ Missing |
| harbor.core.decorator.DecoratorEngine.preview | — | standard | ⚪ Missing |
| harbor.core.module_capsule.preview_module_capsule | — | standard | ⚪ Missing |
| harbor.core.project_structure.rank_key_file | — | standard | ⚪ Missing |
| harbor.core.module_capsule.read_capsule_fingerprint | — | standard | ⚪ Missing |
| harbor.core.context_integrity.render_frontmatter | — | standard | ⚪ Missing |
| harbor.core.module_capsule.resolve_module_capsule_paths | — | standard | ⚪ Missing |
| harbor.core.audit.resolve_provider | — | standard | ⚪ Missing |
| harbor.core.workspace.resolve_workspace_config_path | — | standard | ⚪ Missing |
| harbor.core.init_wizard.InitWizard.run | — | standard | ⚪ Missing |
| harbor.core.doctor.run_config_index_check | — | standard | ⚪ Missing |
| harbor.core.doctor.run_ddt_fast_check | — | standard | ⚪ Missing |
| harbor.core.doctor.run_derived_views_check | 检查模块派生视图状态并汇总为 Doctor 结果。 | standard | ⚪ Missing |
| harbor.core.doctor.run_skill_reference_check | — | standard | ⚪ Missing |
| harbor.core.doctor.run_workspace_status_check | — | standard | ⚪ Missing |
| harbor.core.workspace_migrate.sanitize_text | — | standard | ⚪ Missing |
| harbor.core.workspace_inspect.sanitize_text | — | standard | ⚪ Missing |
| harbor.core.decorator.DecoratorEngine.scan | — | standard | ⚪ Missing |
| harbor.core.ddt.DDTScanner.scan_tests | — | standard | ⚪ Missing |
| harbor.core.init_prompt.select_one | — | standard | ⚪ Missing |
| harbor.core.module_skill.skill_dir_for_module | — | standard | ⚪ Missing |
| harbor.core.context_integrity.split_frontmatter | — | standard | ⚪ Missing |
| harbor.core.stale.stale_report_to_dict | 将 stale 检查结果序列化为 machine-readable JSON 对象。 | standard | ⚪ Missing |
| harbor.core.context_integrity.strip_frontmatter | — | standard | ⚪ Missing |
| harbor.core.doctor.DoctorCheckResult.to_dict | — | standard | ⚪ Missing |
| harbor.core.doctor.DoctorReport.to_dict | — | standard | ⚪ Missing |
| harbor.core.stale.ViewStaleResult.to_dict | — | standard | ⚪ Missing |
| harbor.core.stale.ModuleStaleSummary.to_dict | 将模块视图状态摘要序列化为稳定 JSON 结构。 | standard | ⚪ Missing |
| harbor.core.workspace_migrate.WorkspaceMigrationPlanItem.to_dict | — | standard | ⚪ Missing |
| harbor.core.workspace_inspect.WorkspaceLegacyPathStatus.to_dict | — | standard | ⚪ Missing |
| harbor.core.workspace_inspect.WorkspaceGitTrackingStatus.to_dict | — | standard | ⚪ Missing |
| harbor.core.workspace_inspect.WorkspaceGeneratedViewsStatus.to_dict | — | standard | ⚪ Missing |
| harbor.core.diary.DiaryEntry.to_json | — | standard | ⚪ Missing |
| harbor.core.ddt.DDTValidator.validate | — | standard | ⚪ Missing |
| harbor.core.workspace_inspect.workspace_inspect_report_to_dict | — | standard | ⚪ Missing |
| harbor.core.workspace_migrate.workspace_migrate_report_to_dict | — | standard | ⚪ Missing |
| harbor.core.l2.L2Generator.write | — | standard | ⚪ Missing |
| harbor.core.module_capsule.write_module_capsule | — | standard | ⚪ Missing |
| harbor.core.module_skill.write_module_skill | — | standard | ⚪ Missing |
| harbor.core.project_structure.write_project_structure | — | standard | ⚪ Missing |
| harbor.core.workspace.write_workspace_config | — | standard | ⚪ Missing |

</details>

## Dependency (MVP)
- (TBD) 未来基于 import 简要分析模块依赖。

---
harbor_capsule_version: 1
module: harbor/core
fingerprint: b9f87e92f9b87430ca758bc3d8249976c9b86d36f1dcaa863235fcde8064aa2e
source_files:
- harbor/core/__init__.py
- harbor/core/audit.py
- harbor/core/ddt.py
- harbor/core/decorator.py
- harbor/core/diary.py
- harbor/core/doctor.py
- harbor/core/drafting.py
- harbor/core/git_utils.py
- harbor/core/index.py
- harbor/core/init.py
- harbor/core/l2.py
- harbor/core/module_capsule.py
- harbor/core/module_skill.py
- harbor/core/project_structure.py
- harbor/core/stale.py
- harbor/core/storage.py
- harbor/core/sync.py
- harbor/core/t_decorate.py
- harbor/core/utils.py
- harbor/core/workspace.py
contracts:
- harbor.core.audit.LLMProvider.infer
- harbor.core.audit.MockProvider.infer
- harbor.core.audit.OpenAIProvider.__init__
- harbor.core.audit.OpenAIProvider.infer
- harbor.core.audit.SemanticGuard.audit
- harbor.core.audit.SemanticGuard.build_prompt
- harbor.core.audit.resolve_provider
- harbor.core.ddt.DDTScanner.__init__
- harbor.core.ddt.DDTScanner._iter_py_files
- harbor.core.ddt.DDTScanner._load_config
- harbor.core.ddt.DDTScanner.scan_tests
- harbor.core.ddt.DDTValidator.__init__
- harbor.core.ddt.DDTValidator._load_index
- harbor.core.ddt.DDTValidator._load_map
- harbor.core.ddt.DDTValidator.validate
- harbor.core.decorator.DecoratorEngine._docstring_node
- harbor.core.decorator.DecoratorEngine._extract_functions
- harbor.core.decorator.DecoratorEngine._has_scope_tag
- harbor.core.decorator.DecoratorEngine._is_filtered_name
- harbor.core.decorator.DecoratorEngine._iter_function_nodes
- harbor.core.decorator.DecoratorEngine._leading_whitespace
- harbor.core.decorator.DecoratorEngine._module_qual_from_path
- harbor.core.decorator.DecoratorEngine.apply
- harbor.core.decorator.DecoratorEngine.preview
- harbor.core.decorator.DecoratorEngine.scan
- harbor.core.diary.DiaryEntry.to_json
- harbor.core.diary.DiaryManager.__init__
- harbor.core.diary.DiaryManager._current_file_path
- harbor.core.diary.DiaryManager._from_dict
- harbor.core.diary.DiaryManager._parse_ts
- harbor.core.diary.DiaryManager._resolve_author
- harbor.core.diary.DiaryManager._resolve_diary_dir
- harbor.core.diary.DiaryManager._utc_now_iso
- harbor.core.diary.DiaryManager.export_markdown
- harbor.core.diary.DiaryManager.load_active
- harbor.core.diary.DiaryManager.log
- harbor.core.doctor.DoctorCheckResult.to_dict
- harbor.core.doctor.DoctorReport.to_dict
- harbor.core.doctor._collect_next_steps
- harbor.core.doctor._derived_view_detail_status
- harbor.core.doctor._sanitize_json_text
- harbor.core.doctor._sanitize_single_path
- harbor.core.doctor._status_text
- harbor.core.doctor._status_to_json
- harbor.core.doctor._unique
- harbor.core.doctor.build_doctor_report
- harbor.core.doctor.format_doctor_report
- harbor.core.doctor.run_config_index_check
- harbor.core.doctor.run_ddt_fast_check
- harbor.core.doctor.run_derived_views_check
- harbor.core.doctor.run_skill_reference_check
- harbor.core.doctor.run_workspace_status_check
- harbor.core.drafting.DiaryDrafter.__init__
- harbor.core.drafting.DiaryDrafter._build_prompt
- harbor.core.drafting.DiaryDrafter._extract_code_context
- harbor.core.drafting.DiaryDrafter._kv_fallback_parse
- harbor.core.drafting.DiaryDrafter._safe_json_parse
- harbor.core.drafting.DiaryDrafter._trim_segment
- harbor.core.drafting.DiaryDrafter.generate_draft
- harbor.core.git_utils.GitIgnoreMatcher.__init__
- harbor.core.git_utils.GitIgnoreMatcher.from_root
- harbor.core.git_utils.GitIgnoreMatcher.match_dir
- harbor.core.git_utils.GitIgnoreMatcher.match_file
- harbor.core.index.IndexBuilder.__init__
- harbor.core.index.IndexBuilder._file_hash
- harbor.core.index.IndexBuilder._index_entry
- harbor.core.index.IndexBuilder._iter_py_files
- harbor.core.index.IndexBuilder._load_cache
- harbor.core.index.IndexBuilder._load_config
- harbor.core.index.IndexBuilder._save_cache
- harbor.core.index.IndexBuilder.build
- harbor.core.index.IndexBuilder.iter_build
- harbor.core.index.process_file_worker
- harbor.core.init.Initializer.__init__
- harbor.core.init.Initializer.autodetect
- harbor.core.init.Initializer.detect_code_roots
- harbor.core.init.Initializer.write_config
- harbor.core.init.ProjectDetector.__init__
- harbor.core.init.ProjectDetector._dedup
- harbor.core.init.ProjectDetector._detect_django
- harbor.core.init.ProjectDetector._detect_go
- harbor.core.init.ProjectDetector._detect_java
- harbor.core.init.ProjectDetector._detect_node
- harbor.core.init.ProjectDetector._detect_python_misc
- harbor.core.init.ProjectDetector._get_default_excludes
- harbor.core.init.ProjectDetector._parse_gitignore
- harbor.core.init.ProjectDetector.detect
- harbor.core.l2.L2Generator.__init__
- harbor.core.l2.L2Generator._ensure_within_root
- harbor.core.l2.L2Generator._load_index
- harbor.core.l2.L2Generator._load_meta
- harbor.core.l2.L2Generator._read_meta_file
- harbor.core.l2.L2Generator._resolve_canonical_readme_path
- harbor.core.l2.L2Generator._resolve_export_readme_path
- harbor.core.l2.L2Generator._resolve_meta_path
- harbor.core.l2.L2Generator._safe_module_subpath
- harbor.core.l2.L2Generator._save_meta
- harbor.core.l2.L2Generator.canonical_readme_path
- harbor.core.l2.L2Generator.collect_all_indexed_modules
- harbor.core.l2.L2Generator.compute_meta_hash
- harbor.core.l2.L2Generator.generate
- harbor.core.l2.L2Generator.write
- harbor.core.l2.collect_all_indexed_modules
- harbor.core.l2.collect_modules_from_paths
- harbor.core.l2.infer_module_from_path
- harbor.core.l2.normalize_indexed_module_candidate
- harbor.core.module_capsule._belongs_to_module
- harbor.core.module_capsule._ensure_within_root
- harbor.core.module_capsule._load_index
- harbor.core.module_capsule._normalize_rel_path
- harbor.core.module_capsule._resolve_docs_export_modules_root
- harbor.core.module_capsule._resolve_module_target_dir
- harbor.core.module_capsule._safe_module_subpath
- harbor.core.module_capsule._sort_unique
- harbor.core.module_capsule._stable_contract_rows
- harbor.core.module_capsule._strictness_rank
- harbor.core.module_capsule._summarize_strictness
- harbor.core.module_capsule.build_module_card_frontmatter
- harbor.core.module_capsule.check_module_capsule_stale
- harbor.core.module_capsule.collect_module_context
- harbor.core.module_capsule.compute_module_fingerprint
- harbor.core.module_capsule.detect_tests_for_module
- harbor.core.module_capsule.generate_debug_playbook
- harbor.core.module_capsule.generate_module_card
- harbor.core.module_capsule.generate_review_checklist
- harbor.core.module_capsule.module_capsule_dir
- harbor.core.module_capsule.normalize_module_path
- harbor.core.module_capsule.preview_module_capsule
- harbor.core.module_capsule.read_capsule_fingerprint
- harbor.core.module_capsule.resolve_module_capsule_paths
- harbor.core.module_capsule.write_module_capsule
- harbor.core.module_skill.check_capsule_ready_for_skill
- harbor.core.module_skill.generate_module_skill
- harbor.core.module_skill.normalize_skill_slug
- harbor.core.module_skill.skill_dir_for_module
- harbor.core.module_skill.write_module_skill
- harbor.core.project_structure._area_purpose
- harbor.core.project_structure._belongs_to_module
- harbor.core.project_structure._build_transient_index_from_files
- harbor.core.project_structure._capsule_exists
- harbor.core.project_structure._collect_fallback_files
- harbor.core.project_structure._extract_toml_string_block
- harbor.core.project_structure._infer_area
- harbor.core.project_structure._key_files_display
- harbor.core.project_structure._load_index
- harbor.core.project_structure._normalize_rel_path
- harbor.core.project_structure._read_project_metadata
- harbor.core.project_structure._resolve_docs_export_project_structure_path
- harbor.core.project_structure._sanitize_module
- harbor.core.project_structure._skill_exists
- harbor.core.project_structure._supporting_area_purpose
- harbor.core.project_structure._table_cell
- harbor.core.project_structure._to_project_relative_path
- harbor.core.project_structure._yes_no
- harbor.core.project_structure.classify_project_area
- harbor.core.project_structure.collect_project_structure_context
- harbor.core.project_structure.generate_project_structure_markdown
- harbor.core.project_structure.rank_key_file
- harbor.core.project_structure.write_project_structure
- harbor.core.stale.ModuleStaleSummary.to_dict
- harbor.core.stale.ViewStaleResult.to_dict
- harbor.core.stale._format_view_lines
- harbor.core.stale._normalize_l2_markdown_for_stale
- harbor.core.stale._sanitize_json_text
- harbor.core.stale._sanitize_module_for_json
- harbor.core.stale._sanitize_single_path
- harbor.core.stale.check_l2_readme_stale
- harbor.core.stale.check_module_derived_views_stale
- harbor.core.stale.format_stale_summary
- harbor.core.stale.stale_report_to_dict
- harbor.core.storage.HarborDB.__init__
- harbor.core.storage.HarborDB._apply_pragmas
- harbor.core.storage.HarborDB._ensure_schema
- harbor.core.storage.HarborDB._posix_rel
- harbor.core.storage.HarborDB.get_all_files
- harbor.core.storage.HarborDB.get_file
- harbor.core.storage.HarborDB.get_file_entries
- harbor.core.storage.HarborDB.migrate_from_json
- harbor.core.storage.HarborDB.purge_missing
- harbor.core.storage.HarborDB.transaction
- harbor.core.storage.HarborDB.upsert_entry
- harbor.core.storage.HarborDB.upsert_file
- harbor.core.sync.SyncEngine.__init__
- harbor.core.sync.SyncEngine._iter_py_files
- harbor.core.sync.SyncEngine._load_config
- harbor.core.sync.SyncEngine.check_status
- harbor.core.utils.compute_body_hash
- harbor.core.utils.derive_adopted_roots
- harbor.core.utils.find_function_node
- harbor.core.utils.iter_project_files
- harbor.core.workspace._build_path
- harbor.core.workspace._normalize_path_like
- harbor.core.workspace._to_bool
- harbor.core.workspace._validate_within_repo
- harbor.core.workspace.build_workspace_paths
- harbor.core.workspace.load_workspace_config
- harbor.core.workspace.load_workspace_paths
- harbor.core.workspace.parse_workspace_export_options
- harbor.core.workspace.resolve_workspace_config_path
- harbor.core.workspace.write_workspace_config
---

# Module Card: harbor/core

> This file is generated by Harbor-spec.
> It is a derived maintenance view, not a source of truth.

## Responsibility

This module appears to cover code under:

```text
harbor/core
```

If this summary is too generic, update the underlying contracts or module documentation rather than treating this file as the source of truth.

## Key Files

```text
harbor/core/__init__.py
harbor/core/audit.py
harbor/core/ddt.py
harbor/core/decorator.py
harbor/core/diary.py
harbor/core/doctor.py
harbor/core/drafting.py
harbor/core/git_utils.py
harbor/core/index.py
harbor/core/init.py
harbor/core/l2.py
harbor/core/module_capsule.py
harbor/core/module_skill.py
harbor/core/project_structure.py
harbor/core/stale.py
harbor/core/storage.py
harbor/core/sync.py
harbor/core/t_decorate.py
harbor/core/utils.py
harbor/core/workspace.py
```

## Public / Indexed Contracts

| Symbol | File | Scope | Strictness |
| ------ | ---- | ----- | ---------- |
| harbor.core.audit.LLMProvider.infer | harbor/core/audit.py | unknown | standard |
| harbor.core.audit.MockProvider.infer | harbor/core/audit.py | unknown | standard |
| harbor.core.audit.OpenAIProvider.__init__ | harbor/core/audit.py | unknown | standard |
| harbor.core.audit.OpenAIProvider.infer | harbor/core/audit.py | unknown | standard |
| harbor.core.audit.SemanticGuard.audit | harbor/core/audit.py | unknown | standard |
| harbor.core.audit.SemanticGuard.build_prompt | harbor/core/audit.py | unknown | standard |
| harbor.core.audit.resolve_provider | harbor/core/audit.py | unknown | standard |
| harbor.core.ddt.DDTScanner.__init__ | harbor/core/ddt.py | unknown | standard |
| harbor.core.ddt.DDTScanner._iter_py_files | harbor/core/ddt.py | unknown | standard |
| harbor.core.ddt.DDTScanner._load_config | harbor/core/ddt.py | unknown | standard |
| harbor.core.ddt.DDTScanner.scan_tests | harbor/core/ddt.py | unknown | standard |
| harbor.core.ddt.DDTValidator.__init__ | harbor/core/ddt.py | unknown | standard |
| harbor.core.ddt.DDTValidator._load_index | harbor/core/ddt.py | unknown | standard |
| harbor.core.ddt.DDTValidator._load_map | harbor/core/ddt.py | unknown | standard |
| harbor.core.ddt.DDTValidator.validate | harbor/core/ddt.py | unknown | standard |
| harbor.core.decorator.DecoratorEngine._docstring_node | harbor/core/decorator.py | unknown | standard |
| harbor.core.decorator.DecoratorEngine._extract_functions | harbor/core/decorator.py | unknown | standard |
| harbor.core.decorator.DecoratorEngine._has_scope_tag | harbor/core/decorator.py | unknown | standard |
| harbor.core.decorator.DecoratorEngine._is_filtered_name | harbor/core/decorator.py | unknown | standard |
| harbor.core.decorator.DecoratorEngine._iter_function_nodes | harbor/core/decorator.py | unknown | standard |
| harbor.core.decorator.DecoratorEngine._leading_whitespace | harbor/core/decorator.py | unknown | standard |
| harbor.core.decorator.DecoratorEngine._module_qual_from_path | harbor/core/decorator.py | unknown | standard |
| harbor.core.decorator.DecoratorEngine.apply | harbor/core/decorator.py | unknown | standard |
| harbor.core.decorator.DecoratorEngine.preview | harbor/core/decorator.py | unknown | standard |
| harbor.core.decorator.DecoratorEngine.scan | harbor/core/decorator.py | unknown | standard |
| harbor.core.diary.DiaryEntry.to_json | harbor/core/diary.py | unknown | standard |
| harbor.core.diary.DiaryManager.__init__ | harbor/core/diary.py | unknown | standard |
| harbor.core.diary.DiaryManager._current_file_path | harbor/core/diary.py | unknown | standard |
| harbor.core.diary.DiaryManager._from_dict | harbor/core/diary.py | unknown | standard |
| harbor.core.diary.DiaryManager._parse_ts | harbor/core/diary.py | unknown | standard |
| harbor.core.diary.DiaryManager._resolve_author | harbor/core/diary.py | unknown | standard |
| harbor.core.diary.DiaryManager._resolve_diary_dir | harbor/core/diary.py | unknown | standard |
| harbor.core.diary.DiaryManager._utc_now_iso | harbor/core/diary.py | unknown | standard |
| harbor.core.diary.DiaryManager.export_markdown | harbor/core/diary.py | unknown | standard |
| harbor.core.diary.DiaryManager.load_active | harbor/core/diary.py | unknown | standard |
| harbor.core.diary.DiaryManager.log | harbor/core/diary.py | public | strict |
| harbor.core.doctor.DoctorCheckResult.to_dict | harbor/core/doctor.py | unknown | standard |
| harbor.core.doctor.DoctorReport.to_dict | harbor/core/doctor.py | unknown | standard |
| harbor.core.doctor._collect_next_steps | harbor/core/doctor.py | unknown | standard |
| harbor.core.doctor._derived_view_detail_status | harbor/core/doctor.py | unknown | standard |
| harbor.core.doctor._sanitize_json_text | harbor/core/doctor.py | unknown | standard |
| harbor.core.doctor._sanitize_single_path | harbor/core/doctor.py | unknown | standard |
| harbor.core.doctor._status_text | harbor/core/doctor.py | unknown | standard |
| harbor.core.doctor._status_to_json | harbor/core/doctor.py | unknown | standard |
| harbor.core.doctor._unique | harbor/core/doctor.py | unknown | standard |
| harbor.core.doctor.build_doctor_report | harbor/core/doctor.py | unknown | standard |
| harbor.core.doctor.format_doctor_report | harbor/core/doctor.py | unknown | standard |
| harbor.core.doctor.run_config_index_check | harbor/core/doctor.py | unknown | standard |
| harbor.core.doctor.run_ddt_fast_check | harbor/core/doctor.py | unknown | standard |
| harbor.core.doctor.run_derived_views_check | harbor/core/doctor.py | unknown | standard |
| harbor.core.doctor.run_skill_reference_check | harbor/core/doctor.py | unknown | standard |
| harbor.core.doctor.run_workspace_status_check | harbor/core/doctor.py | unknown | standard |
| harbor.core.drafting.DiaryDrafter.__init__ | harbor/core/drafting.py | public | strict |
| harbor.core.drafting.DiaryDrafter._build_prompt | harbor/core/drafting.py | unknown | standard |
| harbor.core.drafting.DiaryDrafter._extract_code_context | harbor/core/drafting.py | unknown | standard |
| harbor.core.drafting.DiaryDrafter._kv_fallback_parse | harbor/core/drafting.py | unknown | standard |
| harbor.core.drafting.DiaryDrafter._safe_json_parse | harbor/core/drafting.py | unknown | standard |
| harbor.core.drafting.DiaryDrafter._trim_segment | harbor/core/drafting.py | unknown | standard |
| harbor.core.drafting.DiaryDrafter.generate_draft | harbor/core/drafting.py | unknown | standard |
| harbor.core.git_utils.GitIgnoreMatcher.__init__ | harbor/core/git_utils.py | unknown | standard |
| harbor.core.git_utils.GitIgnoreMatcher.from_root | harbor/core/git_utils.py | unknown | standard |
| harbor.core.git_utils.GitIgnoreMatcher.match_dir | harbor/core/git_utils.py | public | strict |
| harbor.core.git_utils.GitIgnoreMatcher.match_file | harbor/core/git_utils.py | public | strict |
| harbor.core.index.IndexBuilder.__init__ | harbor/core/index.py | unknown | standard |
| harbor.core.index.IndexBuilder._file_hash | harbor/core/index.py | unknown | standard |
| harbor.core.index.IndexBuilder._index_entry | harbor/core/index.py | unknown | standard |
| harbor.core.index.IndexBuilder._iter_py_files | harbor/core/index.py | public | strict |
| harbor.core.index.IndexBuilder._load_cache | harbor/core/index.py | unknown | standard |
| harbor.core.index.IndexBuilder._load_config | harbor/core/index.py | unknown | standard |
| harbor.core.index.IndexBuilder._save_cache | harbor/core/index.py | unknown | standard |
| harbor.core.index.IndexBuilder.build | harbor/core/index.py | public | strict |
| harbor.core.index.IndexBuilder.iter_build | harbor/core/index.py | public | strict |
| harbor.core.index.process_file_worker | harbor/core/index.py | public | strict |
| harbor.core.init.Initializer.__init__ | harbor/core/init.py | unknown | standard |
| harbor.core.init.Initializer.autodetect | harbor/core/init.py | public | strict |
| harbor.core.init.Initializer.detect_code_roots | harbor/core/init.py | public | strict |
| harbor.core.init.Initializer.write_config | harbor/core/init.py | public | strict |
| harbor.core.init.ProjectDetector.__init__ | harbor/core/init.py | unknown | standard |
| harbor.core.init.ProjectDetector._dedup | harbor/core/init.py | unknown | standard |
| harbor.core.init.ProjectDetector._detect_django | harbor/core/init.py | unknown | standard |
| harbor.core.init.ProjectDetector._detect_go | harbor/core/init.py | unknown | standard |
| harbor.core.init.ProjectDetector._detect_java | harbor/core/init.py | unknown | standard |
| harbor.core.init.ProjectDetector._detect_node | harbor/core/init.py | unknown | standard |
| harbor.core.init.ProjectDetector._detect_python_misc | harbor/core/init.py | unknown | standard |
| harbor.core.init.ProjectDetector._get_default_excludes | harbor/core/init.py | unknown | standard |
| harbor.core.init.ProjectDetector._parse_gitignore | harbor/core/init.py | unknown | standard |
| harbor.core.init.ProjectDetector.detect | harbor/core/init.py | public | strict |
| harbor.core.l2.L2Generator.__init__ | harbor/core/l2.py | unknown | standard |
| harbor.core.l2.L2Generator._ensure_within_root | harbor/core/l2.py | unknown | standard |
| harbor.core.l2.L2Generator._load_index | harbor/core/l2.py | unknown | standard |
| harbor.core.l2.L2Generator._load_meta | harbor/core/l2.py | unknown | standard |
| harbor.core.l2.L2Generator._read_meta_file | harbor/core/l2.py | unknown | standard |
| harbor.core.l2.L2Generator._resolve_canonical_readme_path | harbor/core/l2.py | unknown | standard |
| harbor.core.l2.L2Generator._resolve_export_readme_path | harbor/core/l2.py | unknown | standard |
| harbor.core.l2.L2Generator._resolve_meta_path | harbor/core/l2.py | unknown | standard |
| harbor.core.l2.L2Generator._safe_module_subpath | harbor/core/l2.py | unknown | standard |
| harbor.core.l2.L2Generator._save_meta | harbor/core/l2.py | unknown | standard |
| harbor.core.l2.L2Generator.canonical_readme_path | harbor/core/l2.py | unknown | standard |
| harbor.core.l2.L2Generator.collect_all_indexed_modules | harbor/core/l2.py | unknown | standard |
| harbor.core.l2.L2Generator.compute_meta_hash | harbor/core/l2.py | unknown | standard |
| harbor.core.l2.L2Generator.generate | harbor/core/l2.py | public | strict |
| harbor.core.l2.L2Generator.write | harbor/core/l2.py | unknown | standard |
| harbor.core.l2.collect_all_indexed_modules | harbor/core/l2.py | unknown | standard |
| harbor.core.l2.collect_modules_from_paths | harbor/core/l2.py | unknown | standard |
| harbor.core.l2.infer_module_from_path | harbor/core/l2.py | unknown | standard |
| harbor.core.l2.normalize_indexed_module_candidate | harbor/core/l2.py | unknown | standard |
| harbor.core.module_capsule._belongs_to_module | harbor/core/module_capsule.py | unknown | standard |
| harbor.core.module_capsule._ensure_within_root | harbor/core/module_capsule.py | unknown | standard |
| harbor.core.module_capsule._load_index | harbor/core/module_capsule.py | unknown | standard |
| harbor.core.module_capsule._normalize_rel_path | harbor/core/module_capsule.py | unknown | standard |
| harbor.core.module_capsule._resolve_docs_export_modules_root | harbor/core/module_capsule.py | unknown | standard |
| harbor.core.module_capsule._resolve_module_target_dir | harbor/core/module_capsule.py | unknown | standard |
| harbor.core.module_capsule._safe_module_subpath | harbor/core/module_capsule.py | unknown | standard |
| harbor.core.module_capsule._sort_unique | harbor/core/module_capsule.py | unknown | standard |
| harbor.core.module_capsule._stable_contract_rows | harbor/core/module_capsule.py | unknown | standard |
| harbor.core.module_capsule._strictness_rank | harbor/core/module_capsule.py | unknown | standard |
| harbor.core.module_capsule._summarize_strictness | harbor/core/module_capsule.py | unknown | standard |
| harbor.core.module_capsule.build_module_card_frontmatter | harbor/core/module_capsule.py | unknown | standard |
| harbor.core.module_capsule.check_module_capsule_stale | harbor/core/module_capsule.py | unknown | standard |
| harbor.core.module_capsule.collect_module_context | harbor/core/module_capsule.py | unknown | standard |
| harbor.core.module_capsule.compute_module_fingerprint | harbor/core/module_capsule.py | unknown | standard |
| harbor.core.module_capsule.detect_tests_for_module | harbor/core/module_capsule.py | unknown | standard |
| harbor.core.module_capsule.generate_debug_playbook | harbor/core/module_capsule.py | unknown | standard |
| harbor.core.module_capsule.generate_module_card | harbor/core/module_capsule.py | unknown | standard |
| harbor.core.module_capsule.generate_review_checklist | harbor/core/module_capsule.py | unknown | standard |
| harbor.core.module_capsule.module_capsule_dir | harbor/core/module_capsule.py | unknown | standard |
| harbor.core.module_capsule.normalize_module_path | harbor/core/module_capsule.py | unknown | standard |
| harbor.core.module_capsule.preview_module_capsule | harbor/core/module_capsule.py | unknown | standard |
| harbor.core.module_capsule.read_capsule_fingerprint | harbor/core/module_capsule.py | unknown | standard |
| harbor.core.module_capsule.resolve_module_capsule_paths | harbor/core/module_capsule.py | unknown | standard |
| harbor.core.module_capsule.write_module_capsule | harbor/core/module_capsule.py | unknown | standard |
| harbor.core.module_skill.check_capsule_ready_for_skill | harbor/core/module_skill.py | unknown | standard |
| harbor.core.module_skill.generate_module_skill | harbor/core/module_skill.py | unknown | standard |
| harbor.core.module_skill.normalize_skill_slug | harbor/core/module_skill.py | unknown | standard |
| harbor.core.module_skill.skill_dir_for_module | harbor/core/module_skill.py | unknown | standard |
| harbor.core.module_skill.write_module_skill | harbor/core/module_skill.py | unknown | standard |
| harbor.core.project_structure._area_purpose | harbor/core/project_structure.py | unknown | standard |
| harbor.core.project_structure._belongs_to_module | harbor/core/project_structure.py | unknown | standard |
| harbor.core.project_structure._build_transient_index_from_files | harbor/core/project_structure.py | unknown | standard |
| harbor.core.project_structure._capsule_exists | harbor/core/project_structure.py | unknown | standard |
| harbor.core.project_structure._collect_fallback_files | harbor/core/project_structure.py | unknown | standard |
| harbor.core.project_structure._extract_toml_string_block | harbor/core/project_structure.py | unknown | standard |
| harbor.core.project_structure._infer_area | harbor/core/project_structure.py | unknown | standard |
| harbor.core.project_structure._key_files_display | harbor/core/project_structure.py | unknown | standard |
| harbor.core.project_structure._load_index | harbor/core/project_structure.py | unknown | standard |
| harbor.core.project_structure._normalize_rel_path | harbor/core/project_structure.py | unknown | standard |
| harbor.core.project_structure._read_project_metadata | harbor/core/project_structure.py | unknown | standard |
| harbor.core.project_structure._resolve_docs_export_project_structure_path | harbor/core/project_structure.py | unknown | standard |
| harbor.core.project_structure._sanitize_module | harbor/core/project_structure.py | unknown | standard |
| harbor.core.project_structure._skill_exists | harbor/core/project_structure.py | unknown | standard |
| harbor.core.project_structure._supporting_area_purpose | harbor/core/project_structure.py | unknown | standard |
| harbor.core.project_structure._table_cell | harbor/core/project_structure.py | unknown | standard |
| harbor.core.project_structure._to_project_relative_path | harbor/core/project_structure.py | unknown | standard |
| harbor.core.project_structure._yes_no | harbor/core/project_structure.py | unknown | standard |
| harbor.core.project_structure.classify_project_area | harbor/core/project_structure.py | unknown | standard |
| harbor.core.project_structure.collect_project_structure_context | harbor/core/project_structure.py | unknown | standard |
| harbor.core.project_structure.generate_project_structure_markdown | harbor/core/project_structure.py | unknown | standard |
| harbor.core.project_structure.rank_key_file | harbor/core/project_structure.py | unknown | standard |
| harbor.core.project_structure.write_project_structure | harbor/core/project_structure.py | unknown | standard |
| harbor.core.stale.ModuleStaleSummary.to_dict | harbor/core/stale.py | unknown | standard |
| harbor.core.stale.ViewStaleResult.to_dict | harbor/core/stale.py | unknown | standard |
| harbor.core.stale._format_view_lines | harbor/core/stale.py | unknown | standard |
| harbor.core.stale._normalize_l2_markdown_for_stale | harbor/core/stale.py | unknown | standard |
| harbor.core.stale._sanitize_json_text | harbor/core/stale.py | unknown | standard |
| harbor.core.stale._sanitize_module_for_json | harbor/core/stale.py | unknown | standard |
| harbor.core.stale._sanitize_single_path | harbor/core/stale.py | unknown | standard |
| harbor.core.stale.check_l2_readme_stale | harbor/core/stale.py | unknown | standard |
| harbor.core.stale.check_module_derived_views_stale | harbor/core/stale.py | unknown | standard |
| harbor.core.stale.format_stale_summary | harbor/core/stale.py | unknown | standard |
| harbor.core.stale.stale_report_to_dict | harbor/core/stale.py | unknown | standard |
| harbor.core.storage.HarborDB.__init__ | harbor/core/storage.py | unknown | standard |
| harbor.core.storage.HarborDB._apply_pragmas | harbor/core/storage.py | unknown | standard |
| harbor.core.storage.HarborDB._ensure_schema | harbor/core/storage.py | unknown | standard |
| harbor.core.storage.HarborDB._posix_rel | harbor/core/storage.py | unknown | standard |
| harbor.core.storage.HarborDB.get_all_files | harbor/core/storage.py | public | strict |
| harbor.core.storage.HarborDB.get_file | harbor/core/storage.py | public | strict |
| harbor.core.storage.HarborDB.get_file_entries | harbor/core/storage.py | public | strict |
| harbor.core.storage.HarborDB.migrate_from_json | harbor/core/storage.py | public | strict |
| harbor.core.storage.HarborDB.purge_missing | harbor/core/storage.py | public | strict |
| harbor.core.storage.HarborDB.transaction | harbor/core/storage.py | public | strict |
| harbor.core.storage.HarborDB.upsert_entry | harbor/core/storage.py | public | strict |
| harbor.core.storage.HarborDB.upsert_file | harbor/core/storage.py | public | strict |
| harbor.core.sync.SyncEngine.__init__ | harbor/core/sync.py | unknown | standard |
| harbor.core.sync.SyncEngine._iter_py_files | harbor/core/sync.py | unknown | standard |
| harbor.core.sync.SyncEngine._load_config | harbor/core/sync.py | unknown | standard |
| harbor.core.sync.SyncEngine.check_status | harbor/core/sync.py | public | strict |
| harbor.core.utils.compute_body_hash | harbor/core/utils.py | unknown | standard |
| harbor.core.utils.derive_adopted_roots | harbor/core/utils.py | unknown | standard |
| harbor.core.utils.find_function_node | harbor/core/utils.py | unknown | standard |
| harbor.core.utils.iter_project_files | harbor/core/utils.py | public | strict |
| harbor.core.workspace._build_path | harbor/core/workspace.py | unknown | standard |
| harbor.core.workspace._normalize_path_like | harbor/core/workspace.py | unknown | standard |
| harbor.core.workspace._to_bool | harbor/core/workspace.py | unknown | standard |
| harbor.core.workspace._validate_within_repo | harbor/core/workspace.py | unknown | standard |
| harbor.core.workspace.build_workspace_paths | harbor/core/workspace.py | unknown | standard |
| harbor.core.workspace.load_workspace_config | harbor/core/workspace.py | unknown | standard |
| harbor.core.workspace.load_workspace_paths | harbor/core/workspace.py | unknown | standard |
| harbor.core.workspace.parse_workspace_export_options | harbor/core/workspace.py | unknown | standard |
| harbor.core.workspace.resolve_workspace_config_path | harbor/core/workspace.py | unknown | standard |
| harbor.core.workspace.write_workspace_config | harbor/core/workspace.py | unknown | standard |

## Tests

```text
tests/core/test_index_sync_sqlite.py
tests/core/test_storage_migration.py
tests/test_audit.py
tests/test_cli_doctor.py
tests/test_cli_finish_sync_context.py
tests/test_cli_init_output.py
tests/test_cli_module_capsule.py
tests/test_cli_module_capsule_batch.py
tests/test_cli_module_capsule_stale.py
tests/test_cli_module_skill.py
tests/test_cli_project_structure.py
tests/test_cli_stale.py
tests/test_ddt_validate.py
tests/test_decorator_engine.py
tests/test_doctor.py
tests/test_drafting.py
tests/test_drafting_json_parse.py
tests/test_index_builder.py
tests/test_index_builder_bad_syntax.py
tests/test_index_progress.py
tests/test_init_detector.py
tests/test_initializer.py
tests/test_l2_paths.py
tests/test_module_capsule.py
tests/test_module_capsule_stale.py
tests/test_module_skill.py
tests/test_project_structure.py
tests/test_stale.py
tests/test_sync_engine.py
tests/test_utils_format.py
tests/test_workspace_gitignore_policy.py
tests/test_workspace_paths.py
```

## Review Focus

* Check Contract Impact before changing public behavior.
* Check schema/type drift if this module exposes data structures.
* Check DDT/test coverage for strict targets.
* Check Runtime Safety if this module writes files, changes data, or touches external systems.

## Debug Entry Points

Start with:

```text
harbor/core/__init__.py
harbor/core/audit.py
```

## Related Views

```text
L2 README:
  harbor/core/README.md

Capsule files:
  .harbor/views/modules/harbor/core/review-checklist.md
  .harbor/views/modules/harbor/core/debug-playbook.md

Optional docs export (if enabled):
  docs/harbor/modules/harbor/core/review-checklist.md
  docs/harbor/modules/harbor/core/debug-playbook.md
```

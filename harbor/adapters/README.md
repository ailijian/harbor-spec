# Module: harbor/adapters

## Public API Summary
| Metric | Count |
|---|---:|
| Public by contract | 4 |
| Strict targets | 4 |
| Private-named but strict | 0 |
| Internal indexed | 107 |
| Strict targets missing DDT | 4 |
| Targets with DDT warnings | 0 |

## High-Risk Targets
| Function | File | Scope | Strictness | DDT Status | Why |
|---|---|---|---|---|---|
| harbor.adapters.base.ContractSource.to_dict | harbor/adapters/base.py | public | strict | ❌ Missing | strict, public, missing DDT |
| harbor.adapters.base.ContractSubject.to_dict | harbor/adapters/base.py | public | strict | ❌ Missing | strict, public, missing DDT |
| harbor.adapters.typescript.public_boundary.PublicBoundaryEvidence.to_dict | harbor/adapters/typescript/public_boundary.py | public | strict | ❌ Missing | strict, public, missing DDT |
| harbor.adapters.python.parser.PythonAdapter.parse_file | harbor/adapters/python/parser.py | public | strict | ❌ Missing | strict, public, missing DDT |
| harbor.adapters.typescript.resolution._build_re_export_reason | harbor/adapters/typescript/resolution.py | unknown | None | ⚪ Missing | export path |
| harbor.adapters.typescript.resolution.TypeScriptBoundaryResolver._build_re_export_rules | harbor/adapters/typescript/resolution.py | unknown | None | ⚪ Missing | export path |
| harbor.adapters.typescript.resolution._coerce_export_target | harbor/adapters/typescript/resolution.py | unknown | None | ⚪ Missing | export path |
| harbor.adapters.typescript.resolution._initial_export_names | harbor/adapters/typescript/resolution.py | unknown | None | ⚪ Missing | export path |
| harbor.adapters.typescript.resolution._load_package_exports | harbor/adapters/typescript/resolution.py | unknown | None | ⚪ Missing | export path |
| harbor.adapters.typescript.resolution._map_package_export_to_source | harbor/adapters/typescript/resolution.py | unknown | None | ⚪ Missing | export path |
| harbor.adapters.typescript.resolution._normalize_exports_block | harbor/adapters/typescript/resolution.py | unknown | None | ⚪ Missing | export path |
| harbor.adapters.typescript.resolution.TypeScriptBoundaryResolver._package_export_evidence | harbor/adapters/typescript/resolution.py | unknown | None | ⚪ Missing | export path |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_export_arrow_functions | harbor/adapters/typescript/parser.py | unknown | None | ⚪ Missing | export path |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_export_class_methods | harbor/adapters/typescript/parser.py | unknown | None | ⚪ Missing | export path |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_export_default_classes | harbor/adapters/typescript/parser.py | unknown | None | ⚪ Missing | export path |

## Full Indexed Contracts
<details>
<summary>All indexed contracts</summary>

| Function | File | Scope | Strictness | DDT Status | Summary |
|---|---|---|---|---|---|
| harbor.adapters.registry.AdapterRegistry.__init__ | harbor/adapters/registry.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.adapter.TypeScriptAdapter.__init__ | harbor/adapters/typescript/adapter.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser.__init__ | harbor/adapters/typescript/parser.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.resolution.TypeScriptBoundaryResolver.__init__ | harbor/adapters/typescript/resolution.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.base.ContractSource.__post_init__ | harbor/adapters/base.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary._boundary_evidence_kinds | harbor/adapters/typescript/public_boundary.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._build_re_export_reason | harbor/adapters/typescript/resolution.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.resolution.TypeScriptBoundaryResolver._build_re_export_rules | harbor/adapters/typescript/resolution.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.jsdoc._classify_comment | harbor/adapters/typescript/jsdoc.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._coerce_export_target | harbor/adapters/typescript/resolution.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary._coerce_public_boundary_evidence | harbor/adapters/typescript/public_boundary.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.adapter._collect_contract_sources | harbor/adapters/typescript/adapter.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.adapter.TypeScriptAdapter._collect_file | harbor/adapters/typescript/adapter.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary._confidence_score | harbor/adapters/typescript/public_boundary.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary._confidence_sort_key | harbor/adapters/typescript/public_boundary.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.resolution.TypeScriptBoundaryResolver._configured_entrypoint_evidence | harbor/adapters/typescript/resolution.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.resolution.TypeScriptBoundaryResolver._context_for | harbor/adapters/typescript/resolution.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.python.parser.PythonAdapter._contract_area | harbor/adapters/python/parser.py | internal | standard | ⚪ Missing | 提取 Harbor 契约区文本（标准段落 + `@harbor.*` tags）。找不到则返回空串。 |
| harbor.adapters.python.parser.PythonAdapter._contract_from_function | harbor/adapters/python/parser.py | internal | standard | ⚪ Missing | 根据函数节点生成契约元数据。 |
| harbor.adapters.typescript.adapter._contract_hash_for_sources | harbor/adapters/typescript/adapter.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._dedupe_paths | harbor/adapters/typescript/resolution.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._default_source_mapping | harbor/adapters/typescript/resolution.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.python.parser.PythonAdapter._docstring_hashes | harbor/adapters/python/parser.py | internal | standard | ⚪ Missing | 计算 Docstring 的 raw/contract 双哈希。 |
| harbor.adapters.typescript.parser._extract_arrow_body | harbor/adapters/typescript/parser.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.python.parser.PythonAdapter._extract_functions | harbor/adapters/python/parser.py | internal | standard | ⚪ Missing | 提取顶层函数与类方法的契约元数据。 |
| harbor.adapters.typescript.resolution._extract_wildcard | harbor/adapters/typescript/resolution.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.jsdoc._find_block_comment_start | harbor/adapters/typescript/jsdoc.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._find_first_parent_file | harbor/adapters/typescript/resolution.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.parser._find_matching | harbor/adapters/typescript/parser.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._find_package_root | harbor/adapters/typescript/resolution.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._initial_export_names | harbor/adapters/typescript/resolution.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.adapter._is_contract_required | harbor/adapters/typescript/adapter.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.jsdoc._is_high_confidence_tag | harbor/adapters/typescript/jsdoc.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.adapter._is_script_file | harbor/adapters/typescript/adapter.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.adapter._is_test_file | harbor/adapters/typescript/adapter.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._iter_project_typescript_files | harbor/adapters/typescript/resolution.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._load_package_exports | harbor/adapters/typescript/resolution.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._load_tsconfig_paths | harbor/adapters/typescript/resolution.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._map_package_export_to_source | harbor/adapters/typescript/resolution.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._match_source_mapping | harbor/adapters/typescript/resolution.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._module_candidates | harbor/adapters/typescript/resolution.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.python.parser.PythonAdapter._module_qual_from_path | harbor/adapters/python/parser.py | internal | standard | ⚪ Missing | 根据文件路径生成模块限定名（点分格式）。 |
| harbor.adapters.typescript.public_boundary._normalize_boundary_confidence | harbor/adapters/typescript/public_boundary.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._normalize_exports_block | harbor/adapters/typescript/resolution.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.python.compat._normalize_posix_path | harbor/adapters/python/compat.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary._optional_text | harbor/adapters/typescript/public_boundary.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.resolution.TypeScriptBoundaryResolver._package_export_evidence | harbor/adapters/typescript/resolution.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_export_arrow_functions | harbor/adapters/typescript/parser.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_export_class_methods | harbor/adapters/typescript/parser.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_export_default_classes | harbor/adapters/typescript/parser.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_export_default_functions | harbor/adapters/typescript/parser.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_export_functions | harbor/adapters/typescript/parser.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_export_interfaces | harbor/adapters/typescript/parser.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_export_types | harbor/adapters/typescript/parser.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_export_zod_schemas | harbor/adapters/typescript/parser.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_internal_arrow_functions | harbor/adapters/typescript/parser.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_internal_functions | harbor/adapters/typescript/parser.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._parse_named_specifier | harbor/adapters/typescript/resolution.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.python.parser.PythonAdapter._parse_tags | harbor/adapters/python/parser.py | internal | standard | ⚪ Missing | 从 Docstring 提取 @harbor.* 标签。 |
| harbor.adapters.typescript.public_boundary._preferred_reason_kinds | harbor/adapters/typescript/public_boundary.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.registry.AdapterRegistry._read_enabled_flag | harbor/adapters/registry.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.registry.AdapterRegistry._read_language_config | harbor/adapters/registry.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.registry.AdapterRegistry._read_languages_config | harbor/adapters/registry.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary._resolve_boundary_confidence | harbor/adapters/typescript/public_boundary.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary._resolve_boundary_reason | harbor/adapters/typescript/public_boundary.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary._resolve_boundary_state | harbor/adapters/typescript/public_boundary.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.adapter._resolve_contract_presence | harbor/adapters/typescript/adapter.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._resolve_entrypoint_path | harbor/adapters/typescript/resolution.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._resolve_module_specifier | harbor/adapters/typescript/resolution.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary._select_preferred_reason_item | harbor/adapters/typescript/public_boundary.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.python.parser.PythonAdapter._signature_hash | harbor/adapters/python/parser.py | internal | standard | ⚪ Missing | 计算函数签名的稳定哈希。 |
| harbor.adapters.typescript.parser._skip_ws | harbor/adapters/typescript/parser.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._split_named_specifiers | harbor/adapters/typescript/resolution.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary._to_bool | harbor/adapters/typescript/public_boundary.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.parser._to_lineno | harbor/adapters/typescript/parser.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._to_lineno | harbor/adapters/typescript/resolution.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.adapter._to_posix_path | harbor/adapters/typescript/adapter.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.resolution.TypeScriptBoundaryResolver._trace_re_export_chain | harbor/adapters/typescript/resolution.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._tsconfig_path_candidates | harbor/adapters/typescript/resolution.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary.build_public_boundary_metadata | harbor/adapters/typescript/public_boundary.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.resolution.TypeScriptBoundaryResolver.collect_evidence | harbor/adapters/typescript/resolution.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.base.ContractSource.compute_fingerprint | harbor/adapters/base.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary.PublicBoundaryEvidence.dedupe_key | harbor/adapters/typescript/public_boundary.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.registry.AdapterRegistry.default | harbor/adapters/registry.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.base.LanguageAdapter.discover_files | harbor/adapters/base.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.adapter.TypeScriptAdapter.discover_files | harbor/adapters/typescript/adapter.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.jsdoc.extract_adjacent_tsdoc | harbor/adapters/typescript/jsdoc.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.registry.AdapterRegistry.from_config | harbor/adapters/registry.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.python.compat.function_contract_to_subject | harbor/adapters/python/compat.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.registry.AdapterRegistry.get_adapter | harbor/adapters/registry.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.registry.AdapterRegistry.get_adapters | harbor/adapters/registry.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.registry.AdapterRegistry.get_enabled_languages | harbor/adapters/registry.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary.initial_public_boundary_evidence_for_symbol | harbor/adapters/typescript/public_boundary.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.registry.AdapterRegistry.is_enabled | harbor/adapters/registry.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.base.ContractSubject.make_target_id | harbor/adapters/base.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary.normalize_contract_required_strategy | harbor/adapters/typescript/public_boundary.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary.normalize_public_boundary_evidence_items | harbor/adapters/typescript/public_boundary.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary.normalize_public_boundary_preset_mode | harbor/adapters/typescript/public_boundary.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.hashing.normalize_text | harbor/adapters/typescript/hashing.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary.normalize_typescript_governance_config | harbor/adapters/typescript/public_boundary.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.hashing.normalized_sha256 | harbor/adapters/typescript/hashing.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser.parse | harbor/adapters/typescript/parser.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.base.LanguageAdapter.parse_file | harbor/adapters/base.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.python.parser.PythonAdapter.parse_file | harbor/adapters/python/parser.py | public | strict | ❌ Missing | 解析并提取指定 Python 文件中的函数/方法契约元数据。 |
| harbor.adapters.typescript.adapter.TypeScriptAdapter.parse_file | harbor/adapters/typescript/adapter.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.resolution.ReExportRule.propagate | harbor/adapters/typescript/resolution.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.hashing.sha256_text | harbor/adapters/typescript/hashing.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary.PublicBoundaryEvidence.sort_key | harbor/adapters/typescript/public_boundary.py | unknown | None | ⚪ Missing | — |
| harbor.adapters.base.ContractSource.to_dict | harbor/adapters/base.py | public | strict | ❌ Missing | Serialize contract source into a JSON-friendly dictionary. |
| harbor.adapters.base.ContractSubject.to_dict | harbor/adapters/base.py | public | strict | ❌ Missing | Serialize contract subject into a JSON-friendly dictionary. |
| harbor.adapters.typescript.public_boundary.PublicBoundaryEvidence.to_dict | harbor/adapters/typescript/public_boundary.py | public | strict | ❌ Missing | Serialize one public-boundary evidence item into stable J... |

</details>

## Dependency Summary

**Outbound Dependencies**
- None detected from repo-local Python imports.

**Inbound Dependents**
- harbor/core
- tests
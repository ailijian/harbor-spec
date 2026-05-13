# Module: harbor/adapters

## Public API
| Function | Summary | Strictness | DDT Status |
|---|---|---|---|
| harbor.adapters.python.parser.PythonAdapter.parse_file | 解析并提取指定 Python 文件中的函数/方法契约元数据。 | strict | ❌ Missing |
| harbor.adapters.base.ContractSource.to_dict | Serialize contract source into a JSON-friendly dictionary. | strict | ❌ Missing |
| harbor.adapters.base.ContractSubject.to_dict | Serialize contract subject into a JSON-friendly dictionary. | strict | ❌ Missing |

## Internal Details (optional)
<details>
<summary>Internal functions</summary>

| Function | Summary | Strictness | DDT Status |
|---|---|---|---|
| harbor.adapters.registry.AdapterRegistry.__init__ | — | standard | ⚪ Missing |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser.__init__ | — | standard | ⚪ Missing |
| harbor.adapters.base.ContractSource.__post_init__ | — | standard | ⚪ Missing |
| harbor.adapters.typescript.jsdoc._classify_comment | — | standard | ⚪ Missing |
| harbor.adapters.typescript.adapter._collect_contract_sources | — | standard | ⚪ Missing |
| harbor.adapters.typescript.adapter.TypeScriptAdapter._collect_file | — | standard | ⚪ Missing |
| harbor.adapters.python.parser.PythonAdapter._contract_area | 提取契约区文本（Args/Returns/Raises + @harbor.* tags）。找不到则返回空串。 | standard | ⚪ Missing |
| harbor.adapters.python.parser.PythonAdapter._contract_from_function | 根据函数节点生成契约元数据。 | standard | ⚪ Missing |
| harbor.adapters.typescript.adapter._contract_hash_for_sources | — | standard | ⚪ Missing |
| harbor.adapters.python.parser.PythonAdapter._docstring_hashes | 计算 Docstring 的 raw/contract 双哈希。 | standard | ⚪ Missing |
| harbor.adapters.typescript.parser._extract_arrow_body | — | standard | ⚪ Missing |
| harbor.adapters.python.parser.PythonAdapter._extract_functions | 提取顶层函数与类方法的契约元数据。 | standard | ⚪ Missing |
| harbor.adapters.typescript.jsdoc._find_block_comment_start | — | standard | ⚪ Missing |
| harbor.adapters.typescript.parser._find_matching | — | standard | ⚪ Missing |
| harbor.adapters.typescript.adapter._is_contract_required | — | standard | ⚪ Missing |
| harbor.adapters.typescript.jsdoc._is_high_confidence_tag | — | standard | ⚪ Missing |
| harbor.adapters.typescript.adapter._is_script_file | — | standard | ⚪ Missing |
| harbor.adapters.typescript.adapter._is_test_file | — | standard | ⚪ Missing |
| harbor.adapters.python.parser.PythonAdapter._module_qual_from_path | 根据文件路径生成模块限定名（点分格式）。 | standard | ⚪ Missing |
| harbor.adapters.python.compat._normalize_posix_path | — | standard | ⚪ Missing |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_export_arrow_functions | — | standard | ⚪ Missing |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_export_class_methods | — | standard | ⚪ Missing |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_export_default_classes | — | standard | ⚪ Missing |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_export_default_functions | — | standard | ⚪ Missing |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_export_functions | — | standard | ⚪ Missing |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_export_interfaces | — | standard | ⚪ Missing |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_export_types | — | standard | ⚪ Missing |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_export_zod_schemas | — | standard | ⚪ Missing |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_internal_arrow_functions | — | standard | ⚪ Missing |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_internal_functions | — | standard | ⚪ Missing |
| harbor.adapters.python.parser.PythonAdapter._parse_tags | 从 Docstring 提取 @harbor.* 标签。 | standard | ⚪ Missing |
| harbor.adapters.registry.AdapterRegistry._read_enabled_flag | — | standard | ⚪ Missing |
| harbor.adapters.registry.AdapterRegistry._read_languages_config | — | standard | ⚪ Missing |
| harbor.adapters.typescript.adapter._resolve_contract_presence | — | standard | ⚪ Missing |
| harbor.adapters.python.parser.PythonAdapter._signature_hash | 计算函数签名的稳定哈希。 | standard | ⚪ Missing |
| harbor.adapters.typescript.parser._skip_ws | — | standard | ⚪ Missing |
| harbor.adapters.typescript.parser._to_lineno | — | standard | ⚪ Missing |
| harbor.adapters.typescript.adapter._to_posix_path | — | standard | ⚪ Missing |
| harbor.adapters.base.ContractSource.compute_fingerprint | — | standard | ⚪ Missing |
| harbor.adapters.registry.AdapterRegistry.default | — | standard | ⚪ Missing |
| harbor.adapters.base.LanguageAdapter.discover_files | — | standard | ⚪ Missing |
| harbor.adapters.typescript.adapter.TypeScriptAdapter.discover_files | — | standard | ⚪ Missing |
| harbor.adapters.typescript.jsdoc.extract_adjacent_tsdoc | — | standard | ⚪ Missing |
| harbor.adapters.registry.AdapterRegistry.from_config | — | standard | ⚪ Missing |
| harbor.adapters.python.compat.function_contract_to_subject | — | standard | ⚪ Missing |
| harbor.adapters.registry.AdapterRegistry.get_adapter | — | standard | ⚪ Missing |
| harbor.adapters.registry.AdapterRegistry.get_adapters | — | standard | ⚪ Missing |
| harbor.adapters.registry.AdapterRegistry.get_enabled_languages | — | standard | ⚪ Missing |
| harbor.adapters.registry.AdapterRegistry.is_enabled | — | standard | ⚪ Missing |
| harbor.adapters.base.ContractSubject.make_target_id | — | standard | ⚪ Missing |
| harbor.adapters.typescript.hashing.normalize_text | — | standard | ⚪ Missing |
| harbor.adapters.typescript.hashing.normalized_sha256 | — | standard | ⚪ Missing |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser.parse | — | standard | ⚪ Missing |
| harbor.adapters.base.LanguageAdapter.parse_file | — | standard | ⚪ Missing |
| harbor.adapters.typescript.adapter.TypeScriptAdapter.parse_file | — | standard | ⚪ Missing |
| harbor.adapters.typescript.hashing.sha256_text | — | standard | ⚪ Missing |

</details>

## Dependency (MVP)
- (TBD) 未来基于 import 简要分析模块依赖。
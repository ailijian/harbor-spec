---
generated_by: "harbor-spec"
harbor_version: "1.4.5"
view_type: "l2_readme"
module: "harbor/adapters/typescript"
generated_at: "2026-05-22T09:07:07Z"
generation_command: "harbor docs --module harbor/adapters/typescript --write"
stale_policy: "advisory"
source_path_count: 8
source_paths_truncated: false
source_paths_omitted_count: 0
source_paths:
  - "harbor/adapters/typescript/__init__.py"
  - "harbor/adapters/typescript/adapter.py"
  - "harbor/adapters/typescript/hashing.py"
  - "harbor/adapters/typescript/jsdoc.py"
  - "harbor/adapters/typescript/parser.py"
  - "harbor/adapters/typescript/public_boundary.py"
  - "harbor/adapters/typescript/resolution.py"
  - "harbor/adapters/typescript/symbols.py"
source_fingerprint: "sha256:91cfd04c76c47b37c15481c1675c814d85cf52cd999d2c18cfec01c146b02e64"
contract_fingerprint: "sha256:3e3cb0d7cf2e3f0f081930a94d30d60c0786a9102e476ac9afeb258d760d128a"
generator_fingerprint: "sha256:68b2aca4bf5c13c668bc92889e1a0784af297a9177096fc08553e55bd0e7e9ee"
---

# Module: harbor/adapters/typescript

## Public API Summary
| Metric | Count |
|---|---:|
| Public by contract | 1 |
| Strict targets | 1 |
| Private-named but strict | 0 |
| Internal indexed | 83 |
| Strict targets missing DDT | 1 |
| Targets with DDT warnings | 0 |

## High-Risk Targets
| Function | File | Risk Focus | Scope | Strictness | Why |
|---|---|---|---|---|---|
| harbor.adapters.typescript.public_boundary.PublicBoundaryEvidence.to_dict | harbor/adapters/typescript/public_boundary.py | JSON serialization | public | strict | JSON serialization, strict target, public surface |
| harbor.adapters.typescript.resolution._build_re_export_reason | harbor/adapters/typescript/resolution.py | export/output path | unknown | unknown | export/output path |
| harbor.adapters.typescript.resolution.TypeScriptBoundaryResolver._build_re_export_rules | harbor/adapters/typescript/resolution.py | export/output path | unknown | unknown | export/output path |
| harbor.adapters.typescript.resolution._coerce_export_target | harbor/adapters/typescript/resolution.py | export/output path | unknown | unknown | export/output path |
| harbor.adapters.typescript.resolution._initial_export_names | harbor/adapters/typescript/resolution.py | export/output path | unknown | unknown | export/output path |
| harbor.adapters.typescript.resolution._load_package_exports | harbor/adapters/typescript/resolution.py | export/output path | unknown | unknown | export/output path |
| harbor.adapters.typescript.resolution._map_package_export_to_source | harbor/adapters/typescript/resolution.py | export/output path | unknown | unknown | export/output path |
| harbor.adapters.typescript.resolution._normalize_exports_block | harbor/adapters/typescript/resolution.py | export/output path | unknown | unknown | export/output path |
| harbor.adapters.typescript.resolution.TypeScriptBoundaryResolver._package_export_evidence | harbor/adapters/typescript/resolution.py | export/output path | unknown | unknown | export/output path |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_export_arrow_functions | harbor/adapters/typescript/parser.py | export/output path | unknown | unknown | export/output path |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_export_class_methods | harbor/adapters/typescript/parser.py | export/output path | unknown | unknown | export/output path |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_export_default_classes | harbor/adapters/typescript/parser.py | export/output path | unknown | unknown | export/output path |

### Contract / DDT Coverage Gaps
| Function | File | Scope | Strictness | DDT Status | Why |
|---|---|---|---|---|---|
| harbor.adapters.typescript.public_boundary.PublicBoundaryEvidence.to_dict | harbor/adapters/typescript/public_boundary.py | public | strict | ❌ Missing | Missing DDT, strict target, public surface |

## Dependency Summary

**Outbound Dependencies**
- harbor/adapters (1 edges): harbor/adapters/base

**Inbound Dependents**
- harbor/adapters (1 edges): harbor/adapters
- harbor/core (1 edges): harbor/core
- tests (1 edges): tests

## Full Indexed Contracts
<details>
<summary>All indexed contracts</summary>

| Function | File | Scope | Strictness | DDT Status | Summary |
|---|---|---|---|---|---|
| harbor.adapters.typescript.adapter.TypeScriptAdapter.__init__ | harbor/adapters/typescript/adapter.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser.__init__ | harbor/adapters/typescript/parser.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.resolution.TypeScriptBoundaryResolver.__init__ | harbor/adapters/typescript/resolution.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary._boundary_evidence_kinds | harbor/adapters/typescript/public_boundary.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._build_re_export_reason | harbor/adapters/typescript/resolution.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.resolution.TypeScriptBoundaryResolver._build_re_export_rules | harbor/adapters/typescript/resolution.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.jsdoc._classify_comment | harbor/adapters/typescript/jsdoc.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._coerce_export_target | harbor/adapters/typescript/resolution.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary._coerce_public_boundary_evidence | harbor/adapters/typescript/public_boundary.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.adapter._collect_contract_sources | harbor/adapters/typescript/adapter.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.adapter.TypeScriptAdapter._collect_file | harbor/adapters/typescript/adapter.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary._confidence_score | harbor/adapters/typescript/public_boundary.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary._confidence_sort_key | harbor/adapters/typescript/public_boundary.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.resolution.TypeScriptBoundaryResolver._configured_entrypoint_evidence | harbor/adapters/typescript/resolution.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.resolution.TypeScriptBoundaryResolver._context_for | harbor/adapters/typescript/resolution.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.adapter._contract_hash_for_sources | harbor/adapters/typescript/adapter.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._dedupe_paths | harbor/adapters/typescript/resolution.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._default_source_mapping | harbor/adapters/typescript/resolution.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.parser._extract_arrow_body | harbor/adapters/typescript/parser.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._extract_wildcard | harbor/adapters/typescript/resolution.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.jsdoc._find_block_comment_start | harbor/adapters/typescript/jsdoc.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._find_first_parent_file | harbor/adapters/typescript/resolution.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.parser._find_matching | harbor/adapters/typescript/parser.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._find_package_root | harbor/adapters/typescript/resolution.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._initial_export_names | harbor/adapters/typescript/resolution.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.adapter._is_contract_required | harbor/adapters/typescript/adapter.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.jsdoc._is_high_confidence_tag | harbor/adapters/typescript/jsdoc.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.adapter._is_script_file | harbor/adapters/typescript/adapter.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.adapter._is_test_file | harbor/adapters/typescript/adapter.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._iter_project_typescript_files | harbor/adapters/typescript/resolution.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._load_package_exports | harbor/adapters/typescript/resolution.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._load_tsconfig_paths | harbor/adapters/typescript/resolution.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._map_package_export_to_source | harbor/adapters/typescript/resolution.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._match_source_mapping | harbor/adapters/typescript/resolution.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._module_candidates | harbor/adapters/typescript/resolution.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary._normalize_boundary_confidence | harbor/adapters/typescript/public_boundary.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._normalize_exports_block | harbor/adapters/typescript/resolution.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary._optional_text | harbor/adapters/typescript/public_boundary.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.resolution.TypeScriptBoundaryResolver._package_export_evidence | harbor/adapters/typescript/resolution.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_export_arrow_functions | harbor/adapters/typescript/parser.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_export_class_methods | harbor/adapters/typescript/parser.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_export_default_classes | harbor/adapters/typescript/parser.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_export_default_functions | harbor/adapters/typescript/parser.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_export_functions | harbor/adapters/typescript/parser.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_export_interfaces | harbor/adapters/typescript/parser.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_export_types | harbor/adapters/typescript/parser.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_export_zod_schemas | harbor/adapters/typescript/parser.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_internal_arrow_functions | harbor/adapters/typescript/parser.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser._parse_internal_functions | harbor/adapters/typescript/parser.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._parse_named_specifier | harbor/adapters/typescript/resolution.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary._preferred_reason_kinds | harbor/adapters/typescript/public_boundary.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary._resolve_boundary_confidence | harbor/adapters/typescript/public_boundary.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary._resolve_boundary_reason | harbor/adapters/typescript/public_boundary.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary._resolve_boundary_state | harbor/adapters/typescript/public_boundary.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.adapter._resolve_contract_presence | harbor/adapters/typescript/adapter.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._resolve_entrypoint_path | harbor/adapters/typescript/resolution.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._resolve_module_specifier | harbor/adapters/typescript/resolution.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary._select_preferred_reason_item | harbor/adapters/typescript/public_boundary.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.parser._skip_ws | harbor/adapters/typescript/parser.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._split_named_specifiers | harbor/adapters/typescript/resolution.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary._to_bool | harbor/adapters/typescript/public_boundary.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.parser._to_lineno | harbor/adapters/typescript/parser.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._to_lineno | harbor/adapters/typescript/resolution.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.adapter._to_posix_path | harbor/adapters/typescript/adapter.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.resolution.TypeScriptBoundaryResolver._trace_re_export_chain | harbor/adapters/typescript/resolution.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.resolution._tsconfig_path_candidates | harbor/adapters/typescript/resolution.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary.build_public_boundary_metadata | harbor/adapters/typescript/public_boundary.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.resolution.TypeScriptBoundaryResolver.collect_evidence | harbor/adapters/typescript/resolution.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary.PublicBoundaryEvidence.dedupe_key | harbor/adapters/typescript/public_boundary.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.adapter.TypeScriptAdapter.discover_files | harbor/adapters/typescript/adapter.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.jsdoc.extract_adjacent_tsdoc | harbor/adapters/typescript/jsdoc.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary.initial_public_boundary_evidence_for_symbol | harbor/adapters/typescript/public_boundary.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary.normalize_contract_required_strategy | harbor/adapters/typescript/public_boundary.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary.normalize_public_boundary_evidence_items | harbor/adapters/typescript/public_boundary.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary.normalize_public_boundary_preset_mode | harbor/adapters/typescript/public_boundary.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.hashing.normalize_text | harbor/adapters/typescript/hashing.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary.normalize_typescript_governance_config | harbor/adapters/typescript/public_boundary.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.hashing.normalized_sha256 | harbor/adapters/typescript/hashing.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.parser.TypeScriptLightweightParser.parse | harbor/adapters/typescript/parser.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.adapter.TypeScriptAdapter.parse_file | harbor/adapters/typescript/adapter.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.resolution.ReExportRule.propagate | harbor/adapters/typescript/resolution.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.hashing.sha256_text | harbor/adapters/typescript/hashing.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary.PublicBoundaryEvidence.sort_key | harbor/adapters/typescript/public_boundary.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.typescript.public_boundary.PublicBoundaryEvidence.to_dict | harbor/adapters/typescript/public_boundary.py | public | strict | ❌ Missing | Serialize one public-boundary evidence item into stable J... |

</details>

---
generated_by: "harbor-spec"
harbor_version: "1.4.5"
view_type: "l2_readme"
module: "harbor/adapters/python"
generated_at: "2026-05-22T09:07:06Z"
generation_command: "harbor docs --module harbor/adapters/python --write"
stale_policy: "advisory"
source_path_count: 3
source_paths_truncated: false
source_paths_omitted_count: 0
source_paths:
  - "harbor/adapters/python/__init__.py"
  - "harbor/adapters/python/compat.py"
  - "harbor/adapters/python/parser.py"
source_fingerprint: "sha256:bd7cc0652e5fa35029e33fbae3acf5d6b824ad752c4747ed0754e41e2a26b962"
contract_fingerprint: "sha256:1b6c3d3b0bc1af1e4449b75f903247c8791b5f35f42330028c4176009a0a76c4"
generator_fingerprint: "sha256:68b2aca4bf5c13c668bc92889e1a0784af297a9177096fc08553e55bd0e7e9ee"
---

# Module: harbor/adapters/python

## Public API Summary
| Metric | Count |
|---|---:|
| Public by contract | 1 |
| Strict targets | 1 |
| Private-named but strict | 0 |
| Internal indexed | 9 |
| Strict targets missing DDT | 1 |
| Targets with DDT warnings | 0 |

## High-Risk Targets
| Function | File | Risk Focus | Scope | Strictness | Why |
|---|---|---|---|---|---|
| harbor.adapters.python.parser.PythonAdapter.parse_file | harbor/adapters/python/parser.py | strict target | public | strict | strict target, public surface |
| harbor.adapters.python.parser.PythonAdapter._module_qual_from_path | harbor/adapters/python/parser.py | path normalization | internal | standard | path normalization |
| harbor.adapters.python.compat._normalize_posix_path | harbor/adapters/python/compat.py | path normalization | unknown | unknown | path normalization |

### Contract / DDT Coverage Gaps
| Function | File | Scope | Strictness | DDT Status | Why |
|---|---|---|---|---|---|
| harbor.adapters.python.parser.PythonAdapter.parse_file | harbor/adapters/python/parser.py | public | strict | ❌ Missing | Missing DDT, strict target, public surface |

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
| harbor.adapters.python.parser.PythonAdapter._contract_area | harbor/adapters/python/parser.py | internal | standard | ⚪ Missing | 提取 Harbor 契约区文本（标准段落 + `@harbor.*` tags）。找不到则返回空串。 |
| harbor.adapters.python.parser.PythonAdapter._contract_from_function | harbor/adapters/python/parser.py | internal | standard | ⚪ Missing | 根据函数节点生成契约元数据。 |
| harbor.adapters.python.parser.PythonAdapter._docstring_hashes | harbor/adapters/python/parser.py | internal | standard | ⚪ Missing | 计算 Docstring 的 raw/contract 双哈希。 |
| harbor.adapters.python.parser.PythonAdapter._extract_functions | harbor/adapters/python/parser.py | internal | standard | ⚪ Missing | 提取顶层函数与类方法的契约元数据。 |
| harbor.adapters.python.parser.PythonAdapter._module_qual_from_path | harbor/adapters/python/parser.py | internal | standard | ⚪ Missing | 根据文件路径生成模块限定名（点分格式）。 |
| harbor.adapters.python.compat._normalize_posix_path | harbor/adapters/python/compat.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.python.parser.PythonAdapter._parse_tags | harbor/adapters/python/parser.py | internal | standard | ⚪ Missing | 从 Docstring 提取 @harbor.* 标签。 |
| harbor.adapters.python.parser.PythonAdapter._signature_hash | harbor/adapters/python/parser.py | internal | standard | ⚪ Missing | 计算函数签名的稳定哈希。 |
| harbor.adapters.python.compat.function_contract_to_subject | harbor/adapters/python/compat.py | unknown | unknown | ⚪ Missing | — |
| harbor.adapters.python.parser.PythonAdapter.parse_file | harbor/adapters/python/parser.py | public | strict | ❌ Missing | 解析并提取指定 Python 文件中的函数/方法契约元数据。 |

</details>

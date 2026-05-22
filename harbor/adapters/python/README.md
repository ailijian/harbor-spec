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
---
generated_by: "harbor-spec"
harbor_version: "1.4.1"
view_type: "l2_readme"
module: "harbor/adapters/python"
generated_at: "2026-05-12T15:21:01Z"
generation_command: "harbor docs --module harbor/adapters/python --write"
stale_policy: "advisory"
source_path_count: 3
source_paths_truncated: false
source_paths:
  - "harbor/adapters/python/__init__.py"
  - "harbor/adapters/python/compat.py"
  - "harbor/adapters/python/parser.py"
source_fingerprint: "sha256:81cdd3c9b7f3cf968e7bc17cebd7bd88d79ba29b3e4020915311a8b3c46b3206"
contract_fingerprint: "sha256:16c86881dc538b205d2db0b2bc0a8ed6acc8304e8c109ca4f324f005e8112ec3"
generator_fingerprint: "sha256:49c406651f0550ace951edd5aae0f6a03ed8d94240c13ad846bb5e6a31da5ae5"
---

# Module: harbor/adapters/python

## Public API
| Function | Summary | Strictness | DDT Status |
|---|---|---|---|
| harbor.adapters.python.parser.PythonAdapter.parse_file | 解析并提取指定 Python 文件中的函数/方法契约元数据。 | strict | ❌ Missing |

## Internal Details (optional)
<details>
<summary>Internal functions</summary>

| Function | Summary | Strictness | DDT Status |
|---|---|---|---|
| harbor.adapters.python.parser.PythonAdapter._contract_area | 提取契约区文本（Args/Returns/Raises + @harbor.* tags）。找不到则返回空串。 | standard | ⚪ Missing |
| harbor.adapters.python.parser.PythonAdapter._contract_from_function | 根据函数节点生成契约元数据。 | standard | ⚪ Missing |
| harbor.adapters.python.parser.PythonAdapter._docstring_hashes | 计算 Docstring 的 raw/contract 双哈希。 | standard | ⚪ Missing |
| harbor.adapters.python.parser.PythonAdapter._extract_functions | 提取顶层函数与类方法的契约元数据。 | standard | ⚪ Missing |
| harbor.adapters.python.parser.PythonAdapter._module_qual_from_path | 根据文件路径生成模块限定名（点分格式）。 | standard | ⚪ Missing |
| harbor.adapters.python.compat._normalize_posix_path | — | standard | ⚪ Missing |
| harbor.adapters.python.parser.PythonAdapter._parse_tags | 从 Docstring 提取 @harbor.* 标签。 | standard | ⚪ Missing |
| harbor.adapters.python.parser.PythonAdapter._signature_hash | 计算函数签名的稳定哈希。 | standard | ⚪ Missing |
| harbor.adapters.python.compat.function_contract_to_subject | — | standard | ⚪ Missing |

</details>

## Dependency (MVP)
- (TBD) 未来基于 import 简要分析模块依赖。

---
generated_by: "harbor-spec"
harbor_version: "1.4.5"
view_type: "l2_readme"
module: "harbor/adapters/python"
generated_at: "2026-05-22T07:09:03Z"
generation_command: "harbor docs --module harbor/adapters/python --write"
stale_policy: "advisory"
source_path_count: 3
source_paths_truncated: false
source_paths:
  - "harbor/adapters/python/__init__.py"
  - "harbor/adapters/python/compat.py"
  - "harbor/adapters/python/parser.py"
source_fingerprint: "sha256:bd7cc0652e5fa35029e33fbae3acf5d6b824ad752c4747ed0754e41e2a26b962"
contract_fingerprint: "sha256:1b6c3d3b0bc1af1e4449b75f903247c8791b5f35f42330028c4176009a0a76c4"
generator_fingerprint: "sha256:68b2aca4bf5c13c668bc92889e1a0784af297a9177096fc08553e55bd0e7e9ee"
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
| harbor.adapters.python.parser.PythonAdapter._contract_area | 提取 Harbor 契约区文本（标准段落 + `@harbor.*` tags）。找不到则返回空串。 | standard | ⚪ Missing |
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

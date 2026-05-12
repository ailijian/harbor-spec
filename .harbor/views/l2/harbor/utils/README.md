---
generated_by: "harbor-spec"
harbor_version: "1.4.1"
view_type: "l2_readme"
module: "harbor/utils"
generated_at: "2026-05-12T15:21:05Z"
generation_command: "harbor docs --module harbor/utils --write"
stale_policy: "advisory"
source_path_count: 3
source_paths_truncated: false
source_paths:
  - "harbor/utils/__init__.py"
  - "harbor/utils/formatting.py"
  - "harbor/utils/i18n.py"
source_fingerprint: "sha256:9928e5105f74dba56d9359798faa51b4b71df7300ca98ba105f1f6211609ce77"
contract_fingerprint: "sha256:885d2ce9187f1f00625f908557d61bb1becce82dd1922e18e33a7a9b2420383c"
generator_fingerprint: "sha256:49c406651f0550ace951edd5aae0f6a03ed8d94240c13ad846bb5e6a31da5ae5"
---

# Module: harbor/utils

## Public API
| Function | Summary | Strictness | DDT Status |
|---|---|---|---|
| harbor.utils.formatting.format_size | 将字节数转换为人类可读的 KB/MB 字符串。 | strict | ✅ Valid |
| harbor.utils.i18n.get_lang | 解析当前语言。 | standard | ⚪ Missing |
| harbor.utils.i18n.t | 根据当前语言返回文案。 | standard | ⚪ Missing |


## Dependency (MVP)
- (TBD) 未来基于 import 简要分析模块依赖。

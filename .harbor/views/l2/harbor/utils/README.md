---
generated_by: "harbor-spec"
harbor_version: "1.4.2.2"
view_type: "l2_readme"
module: "harbor/utils"
generated_at: "2026-05-15T06:15:40Z"
generation_command: "harbor docs --module harbor/utils --write"
stale_policy: "advisory"
source_path_count: 3
source_paths_truncated: false
source_paths:
  - "harbor/utils/__init__.py"
  - "harbor/utils/formatting.py"
  - "harbor/utils/i18n.py"
source_fingerprint: "sha256:e4f1eec91e5b76d1c8c531ec945541d206f89f244bf8f083343eb1d3ef8f93a0"
contract_fingerprint: "sha256:885d2ce9187f1f00625f908557d61bb1becce82dd1922e18e33a7a9b2420383c"
generator_fingerprint: "sha256:c1ce3559ca9ff43a479363bee03ab606ee1922fae51c1c59776a9cee111bb553"
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

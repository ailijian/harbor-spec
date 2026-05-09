---
generated_by: "harbor-spec"
harbor_version: "1.3.0"
view_type: "l2_readme"
module: "harbor/utils"
generated_at: "2026-05-09T14:42:41Z"
generation_command: "harbor docs --module harbor/utils --write"
stale_policy: "advisory"
source_path_count: 3
source_paths_truncated: false
source_paths:
  - "harbor/utils/__init__.py"
  - "harbor/utils/formatting.py"
  - "harbor/utils/i18n.py"
source_fingerprint: "sha256:dc4e0f67590b11ce503090b466f7aa6d4383167ac90c8b8fbb6f2263a96714fb"
contract_fingerprint: "sha256:885d2ce9187f1f00625f908557d61bb1becce82dd1922e18e33a7a9b2420383c"
generator_fingerprint: "sha256:6b9304b870db7c5ff618b75f674235d81f2106e80a504eab0a1e1823ea26ed51"
---

# Module: harbor/utils

## Public API
| Function | Summary | Strictness | DDT Status |
|---|---|---|---|
| harbor.utils.formatting.format_size | 将字节数转换为人类可读的 KB/MB 字符串。 | strict | ✅ Valid |
| harbor.utils.i18n.get_lang | 解析当前语言。 | standard | ⚪ Missing |
| harbor.utils.i18n.t | — | standard | ⚪ Missing |


## Dependency (MVP)
- (TBD) 未来基于 import 简要分析模块依赖。

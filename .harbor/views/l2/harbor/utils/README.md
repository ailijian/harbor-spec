---
generated_by: "harbor-spec"
harbor_version: "1.4.5"
view_type: "l2_readme"
module: "harbor/utils"
generated_at: "2026-05-22T09:07:15Z"
generation_command: "harbor docs --module harbor/utils --write"
stale_policy: "advisory"
source_path_count: 3
source_paths_truncated: false
source_paths_omitted_count: 0
source_paths:
  - "harbor/utils/__init__.py"
  - "harbor/utils/formatting.py"
  - "harbor/utils/i18n.py"
source_fingerprint: "sha256:c9f9e2225a3519d07a8b60e11edd6d6f663db4eb0835f6f97487b1ff64d37729"
contract_fingerprint: "sha256:885d2ce9187f1f00625f908557d61bb1becce82dd1922e18e33a7a9b2420383c"
generator_fingerprint: "sha256:68b2aca4bf5c13c668bc92889e1a0784af297a9177096fc08553e55bd0e7e9ee"
---

# Module: harbor/utils

## Public API Summary
| Metric | Count |
|---|---:|
| Public by contract | 3 |
| Strict targets | 1 |
| Private-named but strict | 0 |
| Internal indexed | 0 |
| Strict targets missing DDT | 0 |
| Targets with DDT warnings | 0 |

## High-Risk Targets
| Function | File | Risk Focus | Scope | Strictness | Why |
|---|---|---|---|---|---|
| harbor.utils.formatting.format_size | harbor/utils/formatting.py | strict target | public | strict | strict target, public surface |
| harbor.utils.i18n.get_lang | harbor/utils/i18n.py | public surface | public | standard | public surface |
| harbor.utils.i18n.t | harbor/utils/i18n.py | public surface | public | standard | public surface |

### Contract / DDT Coverage Gaps
| Function | File | Scope | Strictness | DDT Status | Why |
|---|---|---|---|---|---|
| harbor.utils.formatting.format_size | harbor/utils/formatting.py | public | strict | ✅ Valid | strict target, public surface |
| harbor.utils.i18n.get_lang | harbor/utils/i18n.py | public | standard | ⚪ Missing | public surface |
| harbor.utils.i18n.t | harbor/utils/i18n.py | public | standard | ⚪ Missing | public surface |

## Dependency Summary

**Outbound Dependencies**
- None detected from repo-local Python imports.

**Inbound Dependents**
- harbor/cli (1 edges): harbor/cli
- harbor/core (1 edges): harbor/core
- tests (1 edges): tests

## Full Indexed Contracts
<details>
<summary>All indexed contracts</summary>

| Function | File | Scope | Strictness | DDT Status | Summary |
|---|---|---|---|---|---|
| harbor.utils.formatting.format_size | harbor/utils/formatting.py | public | strict | ✅ Valid | 将字节数转换为人类可读的 KB/MB 字符串。 |
| harbor.utils.i18n.get_lang | harbor/utils/i18n.py | public | standard | ⚪ Missing | 解析当前语言。 |
| harbor.utils.i18n.t | harbor/utils/i18n.py | public | standard | ⚪ Missing | 根据当前语言返回文案。 |

</details>

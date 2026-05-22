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
| Function | File | Scope | Strictness | DDT Status | Why |
|---|---|---|---|---|---|
| harbor.utils.formatting.format_size | harbor/utils/formatting.py | public | strict | ✅ Valid | strict, public |
| harbor.utils.i18n.get_lang | harbor/utils/i18n.py | public | standard | ⚪ Missing | public |
| harbor.utils.i18n.t | harbor/utils/i18n.py | public | standard | ⚪ Missing | public |

## Full Indexed Contracts
<details>
<summary>All indexed contracts</summary>

| Function | File | Scope | Strictness | DDT Status | Summary |
|---|---|---|---|---|---|
| harbor.utils.formatting.format_size | harbor/utils/formatting.py | public | strict | ✅ Valid | 将字节数转换为人类可读的 KB/MB 字符串。 |
| harbor.utils.i18n.get_lang | harbor/utils/i18n.py | public | standard | ⚪ Missing | 解析当前语言。 |
| harbor.utils.i18n.t | harbor/utils/i18n.py | public | standard | ⚪ Missing | 根据当前语言返回文案。 |

</details>

## Dependency Summary

**Outbound Dependencies**
- None detected from repo-local Python imports.

**Inbound Dependents**
- harbor/cli
- harbor/core
- tests
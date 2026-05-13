# Module: harbor/cli

## Public API
| Function | Summary | Strictness | DDT Status |
|---|---|---|---|
| harbor.cli.main.main | Harbor CLI entrypoint and public command dispatch contract. | strict | ❌ Missing |

## Internal Details (optional)
<details>
<summary>Internal functions</summary>

| Function | Summary | Strictness | DDT Status |
|---|---|---|---|
| harbor.cli.main._configure_redirected_windows_stdio | Force UTF-8 on redirected Windows stdio for localized CLI... | standard | ⚪ Missing |
| harbor.cli.main._is_log_write_interactive | — | standard | ⚪ Missing |

</details>

## Dependency (MVP)
- (TBD) 未来基于 import 简要分析模块依赖。
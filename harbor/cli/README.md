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
| harbor.cli.main._configure_redirected_windows_stdio | Use a caller-compatible encoding for redirected Windows l... | standard | ⚪ Missing |
| harbor.cli.main._is_log_write_interactive | — | standard | ⚪ Missing |
| harbor.cli.main._resolve_windows_redirected_stdio_encoding | Choose a Windows redirected stdio encoding that matches t... | standard | ⚪ Missing |

</details>

## Dependency (MVP)
- (TBD) 未来基于 import 简要分析模块依赖。
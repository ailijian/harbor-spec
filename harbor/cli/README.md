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
| harbor.cli.main._configure_redirected_windows_stdio | Backward-compatible wrapper for the Windows CLI-wide stdi... | standard | ⚪ Missing |
| harbor.cli.main._configure_windows_stdio | Apply a Windows CLI-wide UTF-8-first stdio strategy when ... | standard | ⚪ Missing |
| harbor.cli.main._emit_json_stdout | Write one JSON object to stdout with an ASCII-safe fallba... | standard | ⚪ Missing |
| harbor.cli.main._is_log_write_interactive | — | standard | ⚪ Missing |
| harbor.cli.main._is_pure_json_output_argv | Detect pure JSON stdout routes from raw argv without chan... | standard | ⚪ Missing |
| harbor.cli.main._is_utf8_compatible_stdio_encoding | — | standard | ⚪ Missing |
| harbor.cli.main._normalize_windows_stdio_encoding_name | — | standard | ⚪ Missing |
| harbor.cli.main._resolve_windows_explicit_stdio_config | — | standard | ⚪ Missing |
| harbor.cli.main._resolve_windows_redirected_stdio_encoding | Backward-compatible access to the resolved Windows stdio ... | standard | ⚪ Missing |
| harbor.cli.main._resolve_windows_stdio_target | Resolve the preferred Windows stdio strategy for one CLI ... | standard | ⚪ Missing |

</details>

## Dependency (MVP)
- (TBD) 未来基于 import 简要分析模块依赖。
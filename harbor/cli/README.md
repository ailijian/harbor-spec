# Module: harbor/cli

## Public API Summary
| Metric | Count |
|---|---:|
| Public by contract | 1 |
| Strict targets | 1 |
| Private-named but strict | 0 |
| Internal indexed | 11 |
| Strict targets missing DDT | 1 |
| Targets with DDT warnings | 0 |

## High-Risk Targets
| Function | File | Scope | Strictness | DDT Status | Why |
|---|---|---|---|---|---|
| harbor.cli.main.main | harbor/cli/main.py | public | strict | ❌ Missing | strict, public, missing DDT |
| harbor.cli.main._is_log_write_interactive | harbor/cli/main.py | unknown | None | ⚪ Missing | file-write path, entrypoint |
| harbor.cli.main._emit_json_stdout | harbor/cli/main.py | unknown | None | ⚪ Missing | json/output, entrypoint |
| harbor.cli.main._is_pure_json_output_argv | harbor/cli/main.py | unknown | None | ⚪ Missing | json/output, entrypoint |
| harbor.cli.main._configure_redirected_windows_stdio | harbor/cli/main.py | unknown | None | ⚪ Missing | entrypoint |
| harbor.cli.main._configure_windows_stdio | harbor/cli/main.py | unknown | None | ⚪ Missing | entrypoint |
| harbor.cli.main._is_utf8_compatible_stdio_encoding | harbor/cli/main.py | unknown | None | ⚪ Missing | entrypoint |
| harbor.cli.main._make_progress | harbor/cli/main.py | unknown | None | ⚪ Missing | entrypoint |
| harbor.cli.main._normalize_windows_stdio_encoding_name | harbor/cli/main.py | unknown | None | ⚪ Missing | entrypoint |
| harbor.cli.main._resolve_windows_explicit_stdio_config | harbor/cli/main.py | unknown | None | ⚪ Missing | entrypoint |
| harbor.cli.main._resolve_windows_redirected_stdio_encoding | harbor/cli/main.py | unknown | None | ⚪ Missing | entrypoint |
| harbor.cli.main._resolve_windows_stdio_target | harbor/cli/main.py | unknown | None | ⚪ Missing | entrypoint |

## Full Indexed Contracts
<details>
<summary>All indexed contracts</summary>

| Function | File | Scope | Strictness | DDT Status | Summary |
|---|---|---|---|---|---|
| harbor.cli.main._configure_redirected_windows_stdio | harbor/cli/main.py | unknown | None | ⚪ Missing | Backward-compatible wrapper for the Windows CLI-wide stdi... |
| harbor.cli.main._configure_windows_stdio | harbor/cli/main.py | unknown | None | ⚪ Missing | Apply a Windows CLI-wide UTF-8-first stdio strategy when ... |
| harbor.cli.main._emit_json_stdout | harbor/cli/main.py | unknown | None | ⚪ Missing | Write one JSON object to stdout with an ASCII-safe fallba... |
| harbor.cli.main._is_log_write_interactive | harbor/cli/main.py | unknown | None | ⚪ Missing | — |
| harbor.cli.main._is_pure_json_output_argv | harbor/cli/main.py | unknown | None | ⚪ Missing | Detect pure JSON stdout routes from raw argv without chan... |
| harbor.cli.main._is_utf8_compatible_stdio_encoding | harbor/cli/main.py | unknown | None | ⚪ Missing | — |
| harbor.cli.main._make_progress | harbor/cli/main.py | unknown | None | ⚪ Missing | — |
| harbor.cli.main._normalize_windows_stdio_encoding_name | harbor/cli/main.py | unknown | None | ⚪ Missing | — |
| harbor.cli.main._resolve_windows_explicit_stdio_config | harbor/cli/main.py | unknown | None | ⚪ Missing | — |
| harbor.cli.main._resolve_windows_redirected_stdio_encoding | harbor/cli/main.py | unknown | None | ⚪ Missing | Backward-compatible access to the resolved Windows stdio ... |
| harbor.cli.main._resolve_windows_stdio_target | harbor/cli/main.py | unknown | None | ⚪ Missing | Resolve the preferred Windows stdio strategy for one CLI ... |
| harbor.cli.main.main | harbor/cli/main.py | public | strict | ❌ Missing | Harbor CLI entrypoint and public command dispatch contract. |

</details>

## Dependency Summary

**Outbound Dependencies**
- harbor/core/advice_config
- harbor/core/audit
- harbor/core/baseline_artifact
- harbor/core/change_window
- harbor/core/changed_scope
- harbor/core/ci
- harbor/core/console_output
- harbor/core/contract_impact

**Inbound Dependents**
- tests
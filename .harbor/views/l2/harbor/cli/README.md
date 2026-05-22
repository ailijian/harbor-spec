---
generated_by: "harbor-spec"
harbor_version: "1.4.6"
view_type: "l2_readme"
module: "harbor/cli"
generated_at: "2026-05-22T11:34:12Z"
generation_command: "harbor docs --module harbor/cli --write"
stale_policy: "advisory"
source_path_count: 2
source_paths_truncated: false
source_paths_omitted_count: 0
source_paths:
  - "harbor/cli/__init__.py"
  - "harbor/cli/main.py"
source_fingerprint: "sha256:d4f8bce0ebf11073ba3367b7075474719195ea79b09dcbd17d40ea3734181db1"
contract_fingerprint: "sha256:7e5eed90fae8cc818731770b38232454db53a5e08f136b0ade914b62216ba801"
generator_fingerprint: "sha256:88b0a0a6f104b36d6894cfa15ca2a67be8b338d182c5681279c2d0ecb2a59486"
---

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
| Function | File | Risk Focus | Scope | Strictness | Why |
|---|---|---|---|---|---|
| harbor.cli.main._is_log_write_interactive | harbor/cli/main.py | file write | unknown | unknown | file write, CLI behavior, entrypoint |
| harbor.cli.main._emit_json_stdout | harbor/cli/main.py | JSON output | unknown | unknown | JSON output, CLI behavior, entrypoint |
| harbor.cli.main._is_pure_json_output_argv | harbor/cli/main.py | JSON output | unknown | unknown | JSON output, CLI behavior, entrypoint |
| harbor.cli.main.main | harbor/cli/main.py | CLI behavior | public | strict | CLI behavior, entrypoint, strict target |
| harbor.cli.main._configure_redirected_windows_stdio | harbor/cli/main.py | CLI behavior | unknown | unknown | CLI behavior, entrypoint |
| harbor.cli.main._configure_windows_stdio | harbor/cli/main.py | CLI behavior | unknown | unknown | CLI behavior, entrypoint |
| harbor.cli.main._is_utf8_compatible_stdio_encoding | harbor/cli/main.py | CLI behavior | unknown | unknown | CLI behavior, entrypoint |
| harbor.cli.main._make_progress | harbor/cli/main.py | CLI behavior | unknown | unknown | CLI behavior, entrypoint |
| harbor.cli.main._normalize_windows_stdio_encoding_name | harbor/cli/main.py | CLI behavior | unknown | unknown | CLI behavior, entrypoint |
| harbor.cli.main._resolve_windows_explicit_stdio_config | harbor/cli/main.py | CLI behavior | unknown | unknown | CLI behavior, entrypoint |
| harbor.cli.main._resolve_windows_redirected_stdio_encoding | harbor/cli/main.py | CLI behavior | unknown | unknown | CLI behavior, entrypoint |
| harbor.cli.main._resolve_windows_stdio_target | harbor/cli/main.py | CLI behavior | unknown | unknown | CLI behavior, entrypoint |

### Contract / DDT Coverage Gaps
| Function | File | Scope | Strictness | DDT Status | Why |
|---|---|---|---|---|---|
| harbor.cli.main.main | harbor/cli/main.py | public | strict | ❌ Missing | Missing DDT, strict target, public surface |

## Dependency Summary

**Outbound Dependencies**
- harbor/core (29 edges): harbor/core/advice_config, harbor/core/audit, harbor/core/baseline_artifact, ... (+26 more)
- harbor/utils (1 edges): harbor/utils/i18n

**Inbound Dependents**
- tests (1 edges): tests

## Full Indexed Contracts
<details>
<summary>All indexed contracts</summary>

| Function | File | Scope | Strictness | DDT Status | Summary |
|---|---|---|---|---|---|
| harbor.cli.main._configure_redirected_windows_stdio | harbor/cli/main.py | unknown | unknown | ⚪ Missing | Backward-compatible wrapper for the Windows CLI-wide stdi... |
| harbor.cli.main._configure_windows_stdio | harbor/cli/main.py | unknown | unknown | ⚪ Missing | Apply a Windows CLI-wide UTF-8-first stdio strategy when ... |
| harbor.cli.main._emit_json_stdout | harbor/cli/main.py | unknown | unknown | ⚪ Missing | Write one JSON object to stdout with an ASCII-safe fallba... |
| harbor.cli.main._is_log_write_interactive | harbor/cli/main.py | unknown | unknown | ⚪ Missing | — |
| harbor.cli.main._is_pure_json_output_argv | harbor/cli/main.py | unknown | unknown | ⚪ Missing | Detect pure JSON stdout routes from raw argv without chan... |
| harbor.cli.main._is_utf8_compatible_stdio_encoding | harbor/cli/main.py | unknown | unknown | ⚪ Missing | — |
| harbor.cli.main._make_progress | harbor/cli/main.py | unknown | unknown | ⚪ Missing | — |
| harbor.cli.main._normalize_windows_stdio_encoding_name | harbor/cli/main.py | unknown | unknown | ⚪ Missing | — |
| harbor.cli.main._resolve_windows_explicit_stdio_config | harbor/cli/main.py | unknown | unknown | ⚪ Missing | — |
| harbor.cli.main._resolve_windows_redirected_stdio_encoding | harbor/cli/main.py | unknown | unknown | ⚪ Missing | Backward-compatible access to the resolved Windows stdio ... |
| harbor.cli.main._resolve_windows_stdio_target | harbor/cli/main.py | unknown | unknown | ⚪ Missing | Resolve the preferred Windows stdio strategy for one CLI ... |
| harbor.cli.main.main | harbor/cli/main.py | public | strict | ❌ Missing | Harbor CLI entrypoint and public command dispatch contract. |

</details>

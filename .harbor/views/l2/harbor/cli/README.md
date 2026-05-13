---
generated_by: "harbor-spec"
harbor_version: "1.4.1"
view_type: "l2_readme"
module: "harbor/cli"
generated_at: "2026-05-13T13:47:49Z"
generation_command: "harbor docs --module harbor/cli --write"
stale_policy: "advisory"
source_path_count: 2
source_paths_truncated: false
source_paths:
  - "harbor/cli/__init__.py"
  - "harbor/cli/main.py"
source_fingerprint: "sha256:1d2898a67d352a1d0adc0d0d450e7e862fcd5c196a1a7cb0140a87bebd76937f"
contract_fingerprint: "sha256:3bcf3c7820d5344ef1a4ea31e7530a72e819dbd10d0baa4900e51b5657d91754"
generator_fingerprint: "sha256:49c406651f0550ace951edd5aae0f6a03ed8d94240c13ad846bb5e6a31da5ae5"
---

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

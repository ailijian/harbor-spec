---
generated_by: "harbor-spec"
harbor_version: "1.4.1"
view_type: "l2_readme"
module: "harbor/cli"
generated_at: "2026-05-13T06:48:15Z"
generation_command: "harbor docs --module harbor/cli --write"
stale_policy: "advisory"
source_path_count: 2
source_paths_truncated: false
source_paths:
  - "harbor/cli/__init__.py"
  - "harbor/cli/main.py"
source_fingerprint: "sha256:a4594ba210e525316c6b13f391be97867e6125d65d9984050d98c84566918464"
contract_fingerprint: "sha256:bc7df7f57c499867ae0d87d5229891e5a5f48993ff267725be5f471edf07f919"
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
| harbor.cli.main._configure_redirected_windows_stdio | Force UTF-8 on redirected Windows stdio for localized CLI... | standard | ⚪ Missing |
| harbor.cli.main._is_log_write_interactive | — | standard | ⚪ Missing |

</details>

## Dependency (MVP)
- (TBD) 未来基于 import 简要分析模块依赖。

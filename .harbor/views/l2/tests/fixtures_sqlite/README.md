---
generated_by: "harbor-spec"
harbor_version: "1.4.5"
view_type: "l2_readme"
module: "tests/fixtures_sqlite"
generated_at: "2026-05-22T08:22:14Z"
generation_command: "harbor docs --module tests/fixtures_sqlite --write"
stale_policy: "advisory"
source_path_count: 1
source_paths_truncated: false
source_paths:
  - "tests/fixtures_sqlite/sample.py"
source_fingerprint: "sha256:4366e71d00d3548af0c9334a2541193888a12981225580bbd4470ac2065d9fc2"
contract_fingerprint: "sha256:6297e41a589efd86eb34a56f81c76bcaf2266209e98a8a393bf6ce58f01f9f51"
generator_fingerprint: "sha256:68b2aca4bf5c13c668bc92889e1a0784af297a9177096fc08553e55bd0e7e9ee"
---

# Module: tests/fixtures_sqlite

## Public API Summary
| Metric | Count |
|---|---:|
| Public by contract | 1 |
| Strict targets | 1 |
| Private-named but strict | 0 |
| Internal indexed | 0 |
| Strict targets missing DDT | 1 |
| Targets with DDT warnings | 0 |

## High-Risk Targets
| Function | File | Scope | Strictness | DDT Status | Why |
|---|---|---|---|---|---|
| tests.fixtures_sqlite.sample.func1 | tests/fixtures_sqlite/sample.py | public | strict | ❌ Missing | strict, public, missing DDT |

## Full Indexed Contracts
<details>
<summary>All indexed contracts</summary>

| Function | File | Scope | Strictness | DDT Status | Summary |
|---|---|---|---|---|---|
| tests.fixtures_sqlite.sample.func1 | tests/fixtures_sqlite/sample.py | public | strict | ❌ Missing | 测试函数。 |

</details>

## Dependency Summary

**Outbound Dependencies**
- None detected from repo-local Python imports.

**Inbound Dependents**
- None detected from repo-local Python imports.

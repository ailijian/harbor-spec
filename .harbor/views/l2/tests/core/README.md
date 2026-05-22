---
generated_by: "harbor-spec"
harbor_version: "1.4.5"
view_type: "l2_readme"
module: "tests/core"
generated_at: "2026-05-22T08:22:13Z"
generation_command: "harbor docs --module tests/core --write"
stale_policy: "advisory"
source_path_count: 2
source_paths_truncated: false
source_paths:
  - "tests/core/test_index_sync_sqlite.py"
  - "tests/core/test_storage_migration.py"
source_fingerprint: "sha256:5b1b43fea42acddb24983634659bc86ce9c5032ee2ffd08ad1d76316ec9b1da4"
contract_fingerprint: "sha256:fbb4e933d96b1acbd25c9f813730ef3993e64c0f0ac3240442f0285c989d9eb1"
generator_fingerprint: "sha256:68b2aca4bf5c13c668bc92889e1a0784af297a9177096fc08553e55bd0e7e9ee"
---

# Module: tests/core

## Public API Summary
| Metric | Count |
|---|---:|
| Public by contract | 0 |
| Strict targets | 0 |
| Private-named but strict | 0 |
| Internal indexed | 3 |
| Strict targets missing DDT | 0 |
| Targets with DDT warnings | 0 |

## High-Risk Targets
| Function | File | Scope | Strictness | DDT Status | Why |
|---|---|---|---|---|---|
| tests.core.test_storage_migration.test_storage_migration_imports_json_to_sqlite | tests/core/test_storage_migration.py | unknown | None | ⚪ Missing | json/output |
| tests.core.test_index_sync_sqlite.test_index_and_sync_detects_body_drift | tests/core/test_index_sync_sqlite.py | unknown | None | ⚪ Missing | indexed target |
| tests.core.test_storage_migration.test_storage_migration_preserves_additive_typescript_meta | tests/core/test_storage_migration.py | unknown | None | ⚪ Missing | indexed target |

## Full Indexed Contracts
<details>
<summary>All indexed contracts</summary>

| Function | File | Scope | Strictness | DDT Status | Summary |
|---|---|---|---|---|---|
| tests.core.test_index_sync_sqlite.test_index_and_sync_detects_body_drift | tests/core/test_index_sync_sqlite.py | unknown | None | ⚪ Missing | — |
| tests.core.test_storage_migration.test_storage_migration_imports_json_to_sqlite | tests/core/test_storage_migration.py | unknown | None | ⚪ Missing | — |
| tests.core.test_storage_migration.test_storage_migration_preserves_additive_typescript_meta | tests/core/test_storage_migration.py | unknown | None | ⚪ Missing | — |

</details>

## Dependency Summary

**Outbound Dependencies**
- harbor/core/index
- harbor/core/storage
- harbor/core/sync

**Inbound Dependents**
- None detected from repo-local Python imports.

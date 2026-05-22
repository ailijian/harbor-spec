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
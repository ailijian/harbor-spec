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
| Function | File | Risk Focus | Scope | Strictness | Why |
|---|---|---|---|---|---|
| tests.fixtures_sqlite.sample.func1 | tests/fixtures_sqlite/sample.py | strict target | public | strict | strict target, public surface |

### Contract / DDT Coverage Gaps
| Function | File | Scope | Strictness | DDT Status | Why |
|---|---|---|---|---|---|
| tests.fixtures_sqlite.sample.func1 | tests/fixtures_sqlite/sample.py | public | strict | ❌ Missing | Missing DDT, strict target, public surface |

## Dependency Summary

**Outbound Dependencies**
- None detected from repo-local Python imports.

**Inbound Dependents**
- None detected from repo-local Python imports.

## Full Indexed Contracts
<details>
<summary>All indexed contracts</summary>

| Function | File | Scope | Strictness | DDT Status | Summary |
|---|---|---|---|---|---|
| tests.fixtures_sqlite.sample.func1 | tests/fixtures_sqlite/sample.py | public | strict | ❌ Missing | 测试函数。 |

</details>
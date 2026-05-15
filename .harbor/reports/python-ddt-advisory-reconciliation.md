# Python DDT Advisory Reconciliation Report

Date: `2026-05-15`
Scope: `Task 2` + `Task 3` closeout for Python DDT advisory reconciliation

## Summary

- Source evidence:
  - `.harbor/reports/checkpoint-full.json`
  - `.harbor/reports/task-b-post-refresh-checkpoint.json`
  - direct local scan via `DDTScanner().scan_tests()`
- Observed advisory bindings: `5`
- Unique `func_id`: `2`
- Advisory category: `ddt_version_baseline_missing`
- Shared cause:
  - strict Python DDT bindings are structurally valid;
  - the repository has an accepted checkpoint baseline artifact;
  - the repository does not have a repo-owned `l3_version` baseline source such as `.harbor/cache/l3_hash_map.json`;
  - `accepted-checkpoint.json` stores body / contract comparison data, but not DDT version baseline metadata.
- Why these items are not blockers:
  - Harbor rules classify `ddt_version_baseline_missing` as advisory / non-blocking.
  - no evidence currently shows a Python DDT rule violation such as `strategy="latest"` on a strict target.
  - no evidence currently shows a confirmed contract/body mismatch for the bound Python targets themselves.
- Low-risk closeout completed in this task:
  - replaced the vague release-note wording that only repeated `ddt_advisory=5`;
  - added this formal adjudication report;
  - added regression tests so future release text keeps the adjudicated narrative.

## Adjudication Legend

- `RESOLVE_NOW`: can be fixed now without changing governance semantics or weakening DDT coverage.
- `ACCEPTED_BACKLOG`: known and understood; not blocking now; should be revisited only when the repo introduces a trustworthy DDT version-baseline source.
- `NEEDS_FOLLOW_UP`: evidence or ownership is still incomplete and needs further product or design work before acceptance.

## Item 1

- Test binding: `tests/test_sync_engine.py::test_sync_engine_drift_detection`
- `func_id`: `harbor.core.sync.SyncEngine.check_status`
- Category: `ddt_version_baseline_missing`
- Cause:
  - strict binding uses explicit `l3_version=1`;
  - validator cannot find version-baseline metadata for this `func_id`;
  - validator therefore cannot tell whether `l3_version` should remain `1` or be upgraded.
- Why not blocker:
  - rule status is advisory by design;
  - binding is structurally valid and does not use `strategy="latest"`.
- Low-risk fixable now: `no`
- Why not low-risk now:
  - auto-deriving a version baseline from `accepted-checkpoint.json` would introduce new governance semantics;
  - removing the binding would reduce explicit DDT coverage on a strict core target.
- Decision: `ACCEPTED_BACKLOG`
- Future handling condition:
  - revisit when Harbor has a repo-owned, reviewable DDT version-baseline source or an explicit accept-time materialization path for `l3_version` metadata.

## Item 2

- Test binding: `tests/test_utils_format.py::test_format_size_bytes`
- `func_id`: `harbor.utils.formatting.format_size`
- Category: `ddt_version_baseline_missing`
- Cause:
  - strict binding uses explicit `l3_version=1`;
  - validator cannot find version-baseline metadata for this `func_id`.
- Why not blocker:
  - rule status is advisory by design;
  - binding is structurally valid and does not use `strategy="latest"`.
- Low-risk fixable now: `no`
- Why not low-risk now:
  - deleting or downgrading the binding would weaken contract-linked coverage instead of fixing the missing baseline source.
- Decision: `ACCEPTED_BACKLOG`
- Future handling condition:
  - same as Item 1.

## Item 3

- Test binding: `tests/test_utils_format.py::test_format_size_kb`
- `func_id`: `harbor.utils.formatting.format_size`
- Category: `ddt_version_baseline_missing`
- Cause:
  - same underlying baseline-source gap as Item 2.
- Why not blocker:
  - advisory by rule;
  - explicit strict binding remains valid.
- Low-risk fixable now: `no`
- Why not low-risk now:
  - the missing artifact is baseline metadata, not an incorrect test assertion.
- Decision: `ACCEPTED_BACKLOG`
- Future handling condition:
  - same as Item 1.

## Item 4

- Test binding: `tests/test_utils_format.py::test_format_size_mb`
- `func_id`: `harbor.utils.formatting.format_size`
- Category: `ddt_version_baseline_missing`
- Cause:
  - same underlying baseline-source gap as Item 2.
- Why not blocker:
  - advisory by rule;
  - explicit strict binding remains valid.
- Low-risk fixable now: `no`
- Why not low-risk now:
  - the repo currently lacks a trustworthy place to persist reviewed DDT version baselines.
- Decision: `ACCEPTED_BACKLOG`
- Future handling condition:
  - same as Item 1.

## Item 5

- Test binding: `tests/test_utils_format.py::test_format_size_negative_raises`
- `func_id`: `harbor.utils.formatting.format_size`
- Category: `ddt_version_baseline_missing`
- Cause:
  - same underlying baseline-source gap as Item 2.
- Why not blocker:
  - advisory by rule;
  - explicit strict binding remains valid.
- Low-risk fixable now: `no`
- Why not low-risk now:
  - replacing this with an unbound test would only hide the advisory, not establish a reviewed version baseline.
- Decision: `ACCEPTED_BACKLOG`
- Future handling condition:
  - same as Item 1.

## Consolidated Verdict

- `RESOLVE_NOW`: `0`
- `ACCEPTED_BACKLOG`: `5`
- `NEEDS_FOLLOW_UP`: `0`
- Unique underlying baseline gaps:
  - `harbor.core.sync.SyncEngine.check_status`
  - `harbor.utils.formatting.format_size`

## Recommended Next Trigger

- Re-open this report only when one of the following becomes true:
  - Harbor adds a repo-owned DDT version-baseline artifact or accepted source of truth;
  - `harbor accept` gains an explicit, reviewable way to persist `l3_version` baseline metadata;
  - one of the bound Python contracts actually changes and needs a reviewed `l3_version` bump.

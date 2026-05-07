# Workspace Layout Phase 2E Verification

Date: 2026-05-07
Phase: 2E-A (Diary canonical path migration)

## canonical diary path
- Canonical write path: `.harbor/diary/YYYY-MM.jsonl`
- Verified by unit tests and `harbor log -m` runtime output.

## legacy read compatibility
- Legacy read path remains: `specs/diary/YYYY-MM.jsonl`
- `DiaryManager.load_active()` keeps reading legacy files in two-month window.
- Legacy files are read-only in this phase; no deletion/migration performed.

## dual-read merge result
- Canonical + legacy records are merged for `load_active()`.
- Dedupe uses stable normalized JSON hash; field order differences are deduped.
- Covered by `tests/test_diary_workspace_paths.py::test_dual_read_merge_with_stable_normalized_hash_dedupe`.

## write target
- New writes only target canonical `.harbor/diary/YYYY-MM.jsonl`.
- `specs/diary` is not used as write target.
- `harbor log` output keeps first line as entry JSON, then prints canonical write target/path policy.

## tests
- `pytest tests/test_diary_workspace_paths.py` -> 7 passed
- `pytest tests/test_workspace_paths.py` -> 9 passed
- `pytest tests/test_cli_v2.py` -> 13 passed
- `pytest tests/test_cli_docs_modes.py` -> 18 passed
- `pytest tests/test_stale.py tests/test_doctor.py` -> 25 passed
- `pytest` -> 252 passed

## command verification
- `harbor log -m "Phase 2E-A verification" --type chore --importance normal --visibility repo` -> passed
  - Output confirms canonical write target `.harbor/diary/2026-05.jsonl`.
- `harbor finish --sync-context` -> passed
  - Refresh completed for changed L2 README and module capsules.
- `harbor doctor` -> passed (WARN only, advisory)
- `harbor stale` -> passed (all up to date)

## remaining warnings
- `harbor doctor` reports existing workspace-state WARN (changed records present).
- `harbor doctor` reports existing legacy metadata advisory:
  - `.harbor/l2_meta.json` detected (read-compatible only).
- No new Phase 2E-A diary-specific doctor advisory added in this phase.


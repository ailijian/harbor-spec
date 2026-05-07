# Workspace Layout Phase 2F-E Release Freeze Checklist

Date: 2026-05-08
Scope: Final pre-freeze verification-only pack (no new features, no migrate write path)

## Test result

- `pytest` executed: **280 passed**.
- Command: `pytest`

## JSON smoke result

- `harbor workspace inspect --format json`
  - exit code: 0
  - single JSON object: yes
  - absolute path leak (Windows/user/temp): no
  - `writes_files=false`
- `harbor workspace migrate --dry-run --format json`
  - exit code: 0
  - single JSON object: yes
  - absolute path leak (Windows/user/temp): no
  - `writes_files=false`
- `harbor doctor --format json`
  - exit code: 0
  - single JSON object: yes
  - absolute path leak (Windows/user/temp): no
  - `writes_files=false`
- `harbor stale --format json`
  - exit code: 0
  - single JSON object: yes
  - absolute path leak (Windows/user/temp): no
  - `writes_files=false`

## Dry-run no-write result

- `harbor workspace migrate --dry-run --format json` remains read-only.
- Reported `mode=dry_run`, and `writes_files=false`.
- No copy/move/delete/config update side effects observed from command output.

## WARN baseline accepted

- `harbor doctor --format json` status: `warn` (advisory baseline).
- Accepted WARN categories in current freeze baseline:
  - workspace changed/untracked state warning
  - legacy metadata advisory (`.harbor/l2_meta.json`)
  - legacy diary advisory (`specs/diary/*.jsonl`)
- No FAIL/blocker reported by doctor/stale in this run.

## Legacy retained list

- `.harbor/config.yaml` (legacy read-compatible config)
- `.harbor/l2_meta.json` (legacy read-compatible metadata)
- `specs/diary/**` (legacy read-compatible diary path)
- `docs/harbor/**` (optional docs export path)

## Canonical workspace paths

- `.harbor/` as canonical Harbor workspace
- `.harbor/config/harbor.yaml` as canonical config
- `.harbor/views/project-structure.md` as canonical project structure view
- `.harbor/views/modules/<module>/` as canonical module capsule view
- `.harbor/views/l2/<module>/README.md` as canonical L2 README view
- `.harbor/views/l2/_meta.json` as canonical L2 metadata
- `.harbor/diary/YYYY-MM.jsonl` as canonical diary path

## Files recommended for inclusion

- `.harbor/reports/dogfooding/workspace-layout-release-hardening.md`
- `.harbor/reports/dogfooding/workspace-layout-release-freeze-checklist.md`
- `README.md`
- `README.en.md`
- `RELEASE.md`
- `docs/design/harbor-workspace-layout-v1.md`
- `docs/design/harbor-workspace-layout-v1.en.md`

## Files recommended for exclusion

- `.harbor/cache/**`
- `.harbor/state/**`
- `.harbor/exports/**`
- `.pytest_cache/**`
- `**/__pycache__/**`
- `harbor_spec.egg-info/**`
- temporary build/output files (`dist/**`, local temp artifacts)

## Not implemented

- `harbor workspace migrate --write`
- automatic legacy cleanup
- automatic diary migration

## Manual release actions

- review diff
- decide whether to include optional `.agents/skills/harbor-debug-harbor-core/SKILL.md`
- `git add`
- `git commit`
- `git tag`
- publish

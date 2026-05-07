# Workspace Layout Release Hardening (Phase 2F-C)

## Scope

- Phase 2F-C is verification and release hardening only.
- No new command was added.
- `harbor workspace migrate --write` is not implemented in this phase.
- No legacy file was copied/moved/deleted by this verification.

## Validation Commands

- `pytest`
  - Result: `280 passed`
  - Exit code: `0`
- `harbor workspace inspect`
  - Result: success; read-only advisory report printed.
  - Exit code: `0`
- `harbor workspace inspect --format json`
  - Result: single JSON object; `command=workspace_inspect`; `writes_files=false`.
  - Exit code: `0`
- `harbor workspace migrate --dry-run`
  - Result: success; dry-run plan printed; `writes_files=false`.
  - Exit code: `0`
- `harbor workspace migrate --dry-run --format json`
  - Result: single JSON object; `command=workspace_migrate`; `mode=dry_run`; `writes_files=false`.
  - Exit code: `0`
- `harbor doctor`
  - Result: success; advisory WARN exists (derived views + legacy advisory).
  - Exit code: `0`
- `harbor doctor --format json`
  - Result: single JSON object; `command=doctor`; `writes_files=false`; status `warn`.
  - Exit code: `0`
- `harbor stale`
  - Result: success; stale warnings reported for changed modules.
  - Exit code: `0`
- `harbor stale --format json`
  - Result: single JSON object; `command=stale`; `writes_files=false`; status `warn`.
  - Exit code: `0`
- `harbor docs --module harbor/core --write`
  - Result: updated canonical L2 README and module README export for `harbor/core`.
  - Exit code: `0`
- `harbor docs --all --write`
  - Result: updated indexed modules’ canonical L2 README + module README exports.
  - Exit code: `0`
- `harbor module seal harbor/core --write`
  - Result: updated canonical capsule files under `.harbor/views/modules/harbor/core/`.
  - Exit code: `0`
- `harbor module stale harbor/core`
  - Result: up-to-date.
  - Exit code: `0`
- `harbor log -m "Workspace layout release hardening verification" --type chore --importance normal --visibility repo`
  - Result: diary entry appended to `.harbor/diary/2026-05.jsonl`.
  - Exit code: `0`
- `harbor finish --sync-context`
  - Result: changed-module L2 + module capsule synced; stale check run; no `accept` executed.
  - Exit code: `0`

## JSON Contract Smoke

Script-based checks were executed for:

- `harbor workspace inspect --format json`
- `harbor workspace migrate --dry-run --format json`
- `harbor doctor --format json`
- `harbor stale --format json`

Results (all four commands):

- `json.loads`: pass
- stdout single JSON object only: pass
- no Windows absolute path leak: pass
- no user/temp absolute path leak: pass
- top-level keys present: pass

Top-level keys snapshot:

- inspect: `advisory`, `advisory_summary`, `canonical_paths`, `command`, `config`, `generated_views`, `git_tracking`, `legacy_paths`, `writes_files`
- migrate: `advisory`, `command`, `mode`, `next_steps`, `plan_items`, `summary`, `writes_files`
- doctor: `advisory`, `checks`, `command`, `scope`, `status`, `summary`, `writes_files`
- stale: `advisory`, `command`, `modules`, `scope`, `status`, `summary`, `writes_files`

## Dry-run No-write Verification

Before and after running both commands:

- `harbor workspace migrate --dry-run`
- `harbor workspace migrate --dry-run --format json`

fingerprints were compared for:

- `.harbor/config/harbor.yaml`
- `.harbor/views/project-structure.md`
- `.harbor/views/l2/_meta.json`
- `.harbor/diary/*.jsonl`
- `specs/diary/*.jsonl`
- `.harbor/l2_meta.json`
- `docs/harbor/**`
- module README exports (`harbor/**/README.md`, `tests/**/README.md`)

Verification result:

- file hashes unchanged: pass
- no new file created by dry-run commands: pass
- no file deleted by dry-run commands: pass
- legacy files retained and untouched by dry-run commands: pass

## Documentation Consistency Review

Reviewed files:

- `README.md`
- `README.en.md`
- `RELEASE.md`
- `docs/design/harbor-workspace-layout-v1.md`
- `docs/design/harbor-workspace-layout-v1.en.md`

Actions:

- Added explicit statement that `harbor workspace migrate --write` is not implemented in current phase.
- Added Phase 2F-C constraints to both design docs.
- Added release-hardening wording in `RELEASE.md` to keep canonical/export/legacy semantics aligned.

Consistency status:

- `.harbor/` as canonical workspace: confirmed
- `docs/design/` as human-authored design docs: confirmed
- `docs/harbor/` as optional export (non-canonical): confirmed
- `.agents/skills/` as external integration export target: confirmed
- `specs/diary/` and `.harbor/l2_meta.json` as legacy read-compatible only: confirmed
- module README as export targets, not canonical: confirmed
- inspect and migrate dry-run read-only semantics: confirmed

## Working Tree Classification

Observed modified tracked files from this run include:

- `.harbor/diary/2026-05.jsonl`
- `.harbor/views/l2/_meta.json`
- `.harbor/views/l2/**/README.md`
- `.harbor/views/modules/harbor/cli/module-card.md`
- `.harbor/views/modules/harbor/core/module-card.md`
- `harbor/**/README.md`
- `tests/**/README.md`

Classification:

- Include (release/repo):
  - `.harbor/config/harbor.yaml` (policy baseline, unchanged in this run but include-class)
  - `.harbor/views/project-structure.md` (canonical, unchanged in this run but include-class)
  - `.harbor/views/modules/**`
  - `.harbor/views/l2/**`
  - `.harbor/diary/**`
  - `.harbor/reports/dogfooding/**` (includes this report)
  - `docs/design/**`
  - `README.md`, `README.en.md`, `RELEASE.md`
  - source/tests changes when present
- Optional include:
  - `.agents/skills/harbor-debug-harbor-core/SKILL.md`
- Exclude (do not include):
  - `.harbor/cache/**`
  - `.harbor/state/**`
  - `.harbor/exports/**`
  - `.pytest_cache/**`
  - `__pycache__/**`
  - `harbor_spec.egg-info/**`
  - temporary files
- Legacy retained (do not auto-clean):
  - `.harbor/config.yaml`
  - `.harbor/l2_meta.json`
  - `specs/diary/**`
  - `docs/harbor/**`
- Module README exports:
  - `harbor/core/README.md`
  - `harbor/cli/README.md`
  - `harbor/utils/README.md`
  - `tests/**/README.md`
  - these are export targets, not canonical storage
- Unexpected:
  - none from executed Phase 2F-C command set
  - pre-existing ignored/untracked noise exists in workspace and should be triaged separately

## Known Warnings

- `harbor doctor` and `harbor stale` report advisory WARN for stale derived views in changed scope (expected in active working tree).
- legacy advisory remains for `.harbor/l2_meta.json` and `specs/diary` (expected, read-compatible only).
- `git status --short --ignored` shows additional ignored artifacts (`.env`, caches, egg-info, docs/harbor, etc.); these are outside this phase’s write intent.

## Runtime Safety

- Files written by this phase:
  - `.harbor/views/l2/**`
  - `.harbor/views/modules/**`
  - `.harbor/diary/2026-05.jsonl`
  - module README export targets
  - this report and release/docs wording updates
- Workspace outside writes: not observed.
- High-risk operations: none executed.
- Dependency installation: none.
- Prohibited actions not executed:
  - `harbor workspace migrate --write`
  - file deletion/migration of legacy paths
  - `harbor accept`
  - `git add` / `commit` / `tag` / `push`

## Not Implemented List

- `harbor workspace migrate --write`
- any new migration/write command beyond existing CLI
- automatic legacy cleanup/migration

## Release Recommendation

- Recommendation: **continue hardening**
- Rationale:
  - verification commands succeeded and dry-run no-write contract holds.
  - JSON contract smoke is stable.
  - documentation wording is aligned for canonical/export/legacy semantics.
  - active working tree still contains advisory WARN/stale items; freeze is possible only if the team accepts current advisory state as baseline.

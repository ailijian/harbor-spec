# Harbor Workspace Layout V1

> Status: Draft  
> Target version: v1.3.1+  
> Design goal: unify all Harbor-owned files under a clear, structured, maintainable workspace layout.

---

## 0. Purpose

This document defines the recommended workspace layout for `harbor-spec`.

The goal is to make every Harbor-generated or Harbor-managed file easy to understand, locate, version, ignore, regenerate, and consume by AI coding agents.

`docs/design/` is the human-authored design documentation directory and should remain Git-trackable by default.

Harbor should not scatter its artifacts across unrelated directories such as:

```text
docs/harbor/
specs/diary/
.harbor/
.agents/skills/
```

Instead, Harbor should use a unified canonical workspace:

```text
.harbor/
```

Human-readable design documents, such as this file, should remain under:

```text
docs/design/
```

This creates a clear boundary:

```text
.harbor/      = Harbor runtime workspace and managed assets
docs/design/ = human-readable architecture and design documents
```

---

## 1. Core Decision

Harbor adopts a **Harbor-only canonical workspace model**.

### Canonical Harbor workspace

```text
.harbor/
```

All Harbor-owned runtime assets, generated views, policies, reports, diary records, exports, integrations, state, and cache should live under `.harbor/`.

### Human design documents

```text
docs/design/
```

Human-authored design documents should remain outside `.harbor/` so they are not confused with generated Harbor artifacts.

### External tool outputs

External AI tool files, such as Codex skills or Claude skills, may still be exported to tool-specific directories:

```text
.agents/skills/
.claude/skills/
.cursor/rules/
```

But these are **export targets**, not canonical Harbor storage.

---

## 2. Design Principles

### 2.1 Harbor-owned files should be easy to locate

A user should be able to answer:

```text
Where does Harbor store its files?
```

with:

```text
.harbor/
```

---

### 2.2 Generated views are not source of truth

Files such as:

```text
project-structure.md
module-card.md
review-checklist.md
debug-playbook.md
```

are generated or derived views.

They are useful for humans and AI agents, but they are not the source of truth.

The source of truth remains:

```text
source code
contracts
schemas
tests
Harbor policy
Harbor diary
```

---

### 2.3 Human design documents should stay human-readable

Design documents should not be hidden inside `.harbor/`.

Examples:

```text
docs/design/harbor-workspace-layout-v1.md
docs/design/context-routing-v1.md
docs/design/contract-graph-v1.md
```

These documents explain Harbor itself. They are not Harbor runtime artifacts.

---

### 2.4 External tool directories are integration targets

Directories such as:

```text
.agents/skills/
.claude/skills/
.cursor/rules/
```

belong to external AI tools.

Harbor may export files into them, but Harbor should not treat them as the canonical source.

Canonical Harbor-owned integration data should live under:

```text
.harbor/integrations/
```

or:

```text
.harbor/exports/
```

---

### 2.5 State and cache should not be mixed with versioned knowledge

Harbor should distinguish between:

```text
versioned knowledge
local state
cache
generated views
external exports
```

These should not all live in the same flat directory.

---

## 3. Recommended Top-level Layout

The recommended Harbor workspace layout is:

```text
.harbor/
  config/
  policy/
  state/
  views/
  diary/
  reports/
  exports/
  integrations/
  cache/
```

Each directory has a distinct purpose.

---

## 4. Directory Specification

## 4.1 `.harbor/config/`

### Purpose

Project-level Harbor configuration.

This directory contains configuration that tells Harbor how to behave in this repository.

### Suggested files

```text
.harbor/config/
  harbor.yaml
```

### Example

```yaml
version: 1

paths:
  source:
    - harbor/
  tests:
    - tests/
  docs:
    - docs/
  exclude:
    - .git/
    - .venv/
    - node_modules/
    - __pycache__/

views:
  root: .harbor/views
  export_docs: false

diary:
  root: .harbor/diary

reports:
  root: .harbor/reports

state:
  root: .harbor/state

cache:
  root: .harbor/cache
```

### Git strategy

Recommended:

```text
track in Git
```

Reason:

Configuration defines project behavior and should be shared across contributors.

---

## 4.2 `.harbor/policy/`

### Purpose

Machine-readable Harbor policies.

This directory stores policy files that define how Harbor interprets contracts, safety, DDT, modules, and strictness.

### Suggested files

```text
.harbor/policy/
  contract.yaml
  safety.yaml
  ddt.yaml
  modules.yaml
```

### File responsibilities

| File            | Purpose                                  |
| --------------- | ---------------------------------------- |
| `contract.yaml` | Strictness, contract scope, L3 behavior  |
| `safety.yaml`   | Runtime safety rules: allow / ask / deny |
| `ddt.yaml`      | Docstring-driven testing strategy        |
| `modules.yaml`  | Optional explicit module mapping         |

### Example: `contract.yaml`

```yaml
version: 1

strictness:
  strict:
    - harbor/cli/**
    - harbor/core/**
  standard:
    - harbor/utils/**
  light:
    - tests/**
```

### Example: `safety.yaml`

```yaml
version: 1

rules:
  deny:
    - pattern: ".env"
      action: "read_or_write"
      reason: "Never read or modify secrets."

  ask:
    - pattern: "migrations/**"
      action: "write"
      reason: "Migration changes require explicit confirmation."

  allow:
    - pattern: "README.md"
      action: "write"
```

### Git strategy

Recommended:

```text
track in Git
```

Reason:

Policies are shared governance rules and should be visible to both humans and AI agents.

---

## 4.3 `.harbor/state/`

### Purpose

Local Harbor state.

This directory stores machine state that can usually be regenerated or is specific to a working copy.

### Suggested files

```text
.harbor/state/
  index.sqlite
  baseline.json
  lock.json
  scan-state.json
```

### Characteristics

```text
machine-readable
local
regenerable
not intended for manual editing
```

### Git strategy

Recommended default:

```text
ignore in Git
```

Reason:

State files may be local, large, frequently changing, or environment-specific.

### `.gitignore`

```gitignore
.harbor/state/
```

---

## 4.4 `.harbor/views/`

### Purpose

Canonical generated Harbor views.

This directory stores generated project and module views that are used by humans and AI agents.

### Suggested layout

```text
.harbor/views/
  project-structure.md

  l2/
    harbor/core/README.md
    harbor/utils/README.md

  modules/
    harbor/core/
      module-card.md
      review-checklist.md
      debug-playbook.md

    harbor/cli/
      module-card.md
      review-checklist.md
      debug-playbook.md
```

### View types

| View                             | Purpose                           |
| -------------------------------- | --------------------------------- |
| `project-structure.md`           | Project-level structure map       |
| `l2/**/README.md`                | Module-level contract anchor view |
| `modules/**/module-card.md`      | Module maintenance context        |
| `modules/**/review-checklist.md` | Review guide                      |
| `modules/**/debug-playbook.md`   | Debug guide                       |

### Important rule

These files are derived views.

They should contain a warning:

```text
Generated by Harbor-spec.
This is a derived view, not a source of truth.
```

### Git strategy

Recommended default:

```text
track by project choice
```

For open-source projects, tracking `.harbor/views/` may be valuable because it lets humans and AI tools inspect project structure without regenerating views.

For internal projects, teams may choose to ignore views and regenerate them locally.

### Suggested config

```yaml
views:
  track_in_git: true
```

---

## 4.5 `.harbor/diary/`

### Purpose

Harbor evolution memory (canonical write path).

Legacy read-compatible path:

```text
specs/diary/
```

### Suggested layout

```text
.harbor/diary/
  2026-05.jsonl
  2026-06.jsonl
```

### Diary records should capture

```text
contract changes
architecture decisions
bugfix reasons
incident notes
migration decisions
important refactors
```

### Example record

```json
{
  "type": "feature",
  "importance": "high",
  "visibility": "repo",
  "module": "harbor/core",
  "summary": "Add Project Structure View",
  "reason": "Help AI agents understand project structure before reading source files.",
  "changes": [
    "Added project-structure.md generated view",
    "Separated Code Modules from Supporting Areas"
  ],
  "ref": ""
}
```

### Git strategy

Recommended:

```text
track in Git
```

Reason:

Diary files preserve project decision memory and are valuable for future AI agents and maintainers.

---

## 4.6 `.harbor/reports/`

### Purpose

Harbor-generated reports and validation artifacts.

This directory stores reports that are not runtime state but are still useful as evidence or history.

### Suggested layout

```text
.harbor/reports/
  dogfooding/
    v1.3.0-rc-validation.md
    v1.3.0-rc-issues.md
    v1.3.0-rc-command-log.md
    v1.3.0-release-freeze-checklist.md

  releases/
    v1.3.0-validation.md

  audits/
    semantic-audit-2026-05.md
```

### Report categories

| Directory     | Purpose                                    |
| ------------- | ------------------------------------------ |
| `dogfooding/` | RC validation, test evidence, UX findings  |
| `releases/`   | Release validation and freeze notes        |
| `audits/`     | Semantic audit or governance audit reports |

### Git strategy

Recommended:

```text
track important reports
ignore temporary reports
```

For example:

```gitignore
.harbor/reports/tmp/
.harbor/reports/local/
```

But keep release and dogfooding reports when they are part of project history.

---

## 4.7 `.harbor/exports/`

### Purpose

Export staging area.

This directory contains generated files intended to be copied or synced to external locations.

### Suggested layout

```text
.harbor/exports/
  docs/
    project-structure.md
    modules/

  skills/
    codex/
    claude/
```

### Example use cases

```text
export Harbor views to docs/harbor/
export Harbor skills to .agents/skills/
export Claude skills to .claude/skills/
```

### Git strategy

Recommended:

```text
ignore by default
```

Reason:

Exports are usually derived from canonical Harbor assets.

---

## 4.8 `.harbor/integrations/`

### Purpose

Canonical integration metadata.

This directory stores integration-specific configuration or generated plans for external AI coding tools.

### Suggested layout

```text
.harbor/integrations/
  codex/
    skills.yaml

  claude/
    skills.yaml

  cursor/
    rules.yaml

  trae/
    skills.yaml
```

### Important distinction

External directories are output targets:

```text
.agents/skills/
.claude/skills/
.cursor/rules/
```

Harbor integration metadata should live in:

```text
.harbor/integrations/
```

### Git strategy

Recommended:

```text
track integration config
ignore generated export outputs
```

---

## 4.9 `.harbor/cache/`

### Purpose

Temporary cache.

### Suggested layout

```text
.harbor/cache/
  scan/
  llm/
  temp/
```

### Git strategy

Recommended:

```text
ignore in Git
```

### `.gitignore`

```gitignore
.harbor/cache/
```

---

## 5. Canonical vs Exported Files

Harbor should distinguish between canonical files and exported files.

## 5.1 Canonical files

Canonical Harbor assets live under:

```text
.harbor/
```

Examples:

```text
.harbor/config/harbor.yaml
.harbor/policy/contract.yaml
.harbor/views/project-structure.md
.harbor/views/modules/harbor/core/module-card.md
.harbor/diary/2026-05.jsonl
```

## 5.2 Exported files

Exported files may be placed outside `.harbor/` for compatibility with humans or tools.

Examples:

```text
docs/harbor/project-structure.md
docs/harbor/modules/harbor/core/module-card.md
.agents/skills/harbor-debug-harbor-core/SKILL.md
.claude/skills/harbor-debug-harbor-core/SKILL.md
```

These files should be considered export targets.

They should not become the source of truth.

---

## 6. Relationship with Existing Paths

## 6.1 `docs/harbor/`

Current role:

```text
generated views and Harbor documentation
```

Future role:

```text
optional human-readable export target
```

Recommended:

```text
canonical: .harbor/views/
optional export: docs/harbor/
```

## 6.2 `specs/diary/`

Current role:

```text
Harbor diary / evolution memory
```

Future role:

```text
legacy read-compatible path (not a canonical write target)
```

Recommended strategy:

```text
write:
  .harbor/diary/YYYY-MM.jsonl

read:
  .harbor/diary/YYYY-MM.jsonl
  + specs/diary/YYYY-MM.jsonl
```

## 6.3 `.agents/skills/`

Current role:

```text
generated skill entrypoints
```

Future role:

```text
external tool export target
```

Canonical skill generation metadata should live under:

```text
.harbor/integrations/
```

or:

```text
.harbor/exports/skills/
```

## 6.4 `.harbor/`

Current role:

```text
mixed config/state/policy
```

Future role:

```text
canonical Harbor workspace
```

---

## 7. Git Tracking Strategy

Recommended default:

```text
Track:
  .harbor/config/
  .harbor/policy/
  .harbor/diary/
  selected .harbor/views/
  selected .harbor/reports/

Ignore:
  .harbor/state/
  .harbor/cache/
  .harbor/exports/
  local reports
```

Suggested `.gitignore`:

```gitignore
# Harbor local state and cache
.harbor/state/
.harbor/cache/

# Harbor export staging
.harbor/exports/

# Local-only reports
.harbor/reports/tmp/
.harbor/reports/local/
```

Phase 2B.5 enforcement for `harbor-spec`:

```text
Do not use broad `.harbor/` ignore.
`.harbor/views/project-structure.md` must remain Git-trackable.
`docs/harbor` is an optional export target, not canonical storage.
```

If a project wants to ignore all generated views:

```gitignore
.harbor/views/
```

If a project wants to track generated views:

```gitignore
# do not ignore .harbor/views
```

---

## 8. Recommended Default Tracking Policy

For harbor-spec itself, recommended tracking is:

| Path                                 |                   Track? | Reason                        |
| ------------------------------------ | -----------------------: | ----------------------------- |
| `.harbor/config/`                    |                      yes | shared project config         |
| `.harbor/policy/`                    |                      yes | shared governance             |
| `.harbor/state/`                     |                       no | local runtime state           |
| `.harbor/cache/`                     |                       no | local cache                   |
| `.harbor/views/project-structure.md` |                      yes | useful for AI context loading |
| `.harbor/views/modules/`             |                 optional | useful but generated          |
| `.harbor/diary/`                     |                      yes | project memory                |
| `.harbor/reports/dogfooding/`        | yes for release evidence | validation history            |
| `.harbor/exports/`                   |                       no | derived export staging        |
| `.agents/skills/`                    |                 optional | external tool output          |

---

## 9. Command Behavior Implications

The workspace layout affects existing commands.

## 9.1 Project Structure

Current:

```text
docs/harbor/project-structure.md
```

Future canonical target:

```text
.harbor/views/project-structure.md
```

Optional export target:

```text
docs/harbor/project-structure.md
```

Suggested future commands:

```powershell
harbor project structure
harbor project structure --write
harbor views export --target docs
```

## 9.2 Module Capsule

Current:

```text
docs/harbor/modules/<module>/
```

Future canonical target:

```text
.harbor/views/modules/<module>/
```

Optional export target:

```text
docs/harbor/modules/<module>/
```

## 9.3 L2 README

Current:

```text
<module>/README.md
```

Future canonical target:

```text
.harbor/views/l2/<module>/README.md
```

Optional export target:

```text
<module>/README.md
```

This is a sensitive compatibility area because many users expect module README files to live next to source modules.

L2 metadata canonical target:

```text
.harbor/views/l2/_meta.json
```

Legacy compatibility:

```text
.harbor/l2_meta.json (read-compatible only, no longer a write target)
```

Therefore, L2 README should support configurable output:

```yaml
l2:
  canonical_root: .harbor/views/l2
  export:
    module_readme:
      enabled: true
```

## 9.4 Diary

Current:

```text
specs/diary/YYYY-MM.jsonl
```

Future:

```text
.harbor/diary/YYYY-MM.jsonl
```

Migration policy:

```text
canonical single-write: write only to .harbor/diary/YYYY-MM.jsonl
legacy dual-read: continue reading specs/diary/YYYY-MM.jsonl
dedupe when merging canonical + legacy records
no automatic migration or deletion of legacy diary files
```

## 9.5 Skill Promotion

Current output:

```text
.agents/skills/harbor-debug-<module-slug>/SKILL.md
```

Future behavior:

```text
canonical metadata: .harbor/integrations/codex/skills.yaml
export target: .agents/skills/
```

Skill files may still be generated directly to `.agents/skills/` for compatibility, but Harbor should document that `.agents/skills/` is an export target.

---

## 10. Backward Compatibility

Harbor should not break existing repositories immediately.

## 10.1 v1.3.x compatibility

Keep current output paths supported:

```text
docs/harbor/project-structure.md
docs/harbor/modules/
specs/diary/
.agents/skills/
```

Add new configuration support gradually.

## 10.2 v1.3.1 proposed behavior

Introduce:

```text
.harbor/config/harbor.yaml
```

with configurable roots:

```yaml
workspace:
  root: .harbor

views:
  canonical_root: .harbor/views
  export_docs_root: docs/harbor
  export_docs_enabled: false

diary:
  root: .harbor/diary

reports:
  root: .harbor/reports
```

Do not force migration automatically.

## 10.3 v1.4 proposed behavior

Add migration tooling:

```powershell
harbor workspace inspect
harbor workspace migrate --dry-run
harbor workspace migrate --write
```

Phase 2F-A (Workspace Inspect MVP) constraints:

```text
harbor workspace inspect is a read-only advisory command
it reports canonical paths / legacy paths / Git tracking / generated views / advisory
it does not run workspace migrate
it does not delete legacy files
it does not modify any write behavior
```

Phase 2F-B (Workspace Migrate Dry-run MVP) constraints:

```text
add harbor workspace migrate --dry-run (with --format text/json)
the command only generates a migration plan and does not execute migration
no file copy
no file move
no file delete
no config update
no .gitignore update
no diary migration
if --dry-run is missing, return an error that only --dry-run is supported in this version
```

## 10.4 v2.0 possible behavior

Make `.harbor/views/` the default canonical location.

Keep export commands for legacy paths.

---

## 11. Migration Strategy

## 11.1 Phase 1: Design only

Create:

```text
docs/design/harbor-workspace-layout-v1.md
```

No code changes.

## 11.2 Phase 2: Config support

Add:

```text
.harbor/config/harbor.yaml
```

Support configurable roots for:

```text
views
diary
reports
exports
state
cache
```

### Phase 2A (Scoped Foundation)

Phase 2A is intentionally limited to path infrastructure only:

```text
Workspace config loader
Path resolver
Path write safety checks
```

Implementation boundaries for Phase 2A:

```text
No command behavior changed.
No generated view path changed yet.
No migration command introduced.
```

This means existing commands can keep current write targets during Phase 2A, while new workspace path primitives are prepared for later phases.

## 11.3 Phase 3: Dual-write optional support

Allow commands to write canonical `.harbor/views` and optionally export to legacy locations.

Example:

```yaml
views:
  canonical_root: .harbor/views
  export_docs_enabled: true
  export_docs_root: docs/harbor
```

## 11.4 Phase 4: Migration command

Add:

```powershell
harbor workspace migrate --dry-run
harbor workspace migrate --write
```

The migration command should:

```text
show planned moves
avoid deletion by default
preserve old files unless explicitly confirmed
create backups or migration report
```

## 11.5 Phase 5: Default switch

After compatibility period, switch defaults to:

```text
.harbor/views/
.harbor/diary/
.harbor/reports/
```

---

## 12. Proposed `.harbor/config/harbor.yaml`

```yaml
version: 1

workspace:
  root: .harbor

config:
  root: .harbor/config

policy:
  root: .harbor/policy

state:
  root: .harbor/state
  git: ignore

cache:
  root: .harbor/cache
  git: ignore

views:
  canonical_root: .harbor/views
  git: track
  export:
    docs:
      enabled: false
      root: docs/harbor

l2:
  canonical_root: .harbor/views/l2
  export:
    module_readme:
      enabled: true

modules:
  capsule_root: .harbor/views/modules

diary:
  root: .harbor/diary
  git: track

reports:
  root: .harbor/reports
  git: track_selected

integrations:
  root: .harbor/integrations
  exports:
    codex_skills:
      enabled: true
      root: .agents/skills
    claude_skills:
      enabled: false
      root: .claude/skills
```

---

## 13. Tooling Implications

## 13.1 `harbor doctor`

Doctor should eventually check:

```text
config root exists
policy root exists
state root is ignored
cache root is ignored
views root exists
diary root exists if enabled
reports root exists if enabled
exports are consistent
```

## 13.2 `harbor stale`

Stale should check canonical views first:

```text
.harbor/views/
```

Then optionally check exported views if export is enabled.

Phase 2D-B implementation status:

```text
canonical L2 freshness is determined only by .harbor/views/l2/<module>/README.md
module README export is reported as a separate advisory view named l2_readme_export
when canonical is unavailable, export is unknown/skipped and out-of-sync comparison is skipped
disabled export must be explicitly represented as disabled and must not count as warn
legacy .harbor/l2_meta.json advisory appears only in harbor doctor (not in stale)
doctor may WARN on export mismatch / legacy metadata, but should not FAIL because of them
legacy diary advisory (`specs/diary/*.jsonl`) appears only in harbor doctor (not in stale text/json)
this diary advisory is workspace layout / project memory guidance, not derived-view freshness
advisory appears only when `*.jsonl` exists under `specs/diary`; empty directory does not trigger it; multiple files still emit one advisory set
doctor remains read-only for legacy diary: canonical path is `.harbor/diary`, new writes go only to `.harbor/diary`
no automatic migration, deletion, or writes to `specs/diary`
```

## 13.3 `harbor finish --sync-context`

Future behavior:

```text
write canonical views under .harbor/views
optionally export to docs/harbor or module README paths
```

## 13.4 `harbor project structure --write`

Future behavior:

```text
write .harbor/views/project-structure.md
```

Optional:

```text
export docs/harbor/project-structure.md
```

Phase 2B implementation status:

```text
canonical write default: enabled
docs export default: disabled (opt-in via views.export.docs.enabled=true)
preview mode: still read-only (no file writes)
```

## 13.5 `harbor module seal --write`

Future behavior:

```text
write .harbor/views/modules/<module>/
```

Optional:

```text
export docs/harbor/modules/<module>/
```

Phase 2C implementation status:

```text
canonical write default: enabled (.harbor/views/modules/<module>/)
docs export default: disabled (opt-in via views.export.docs.enabled=true)
stale checks use canonical module-card by default
promote-skill references canonical capsule paths by default
legacy docs capsule files are not auto-deleted or overwritten
```

---

## 14. Source of Truth Rules

Harbor should maintain the following invariants:

### Invariant 1

```text
Generated views are not source of truth.
```

### Invariant 2

```text
.harbor/state and .harbor/cache are local and should not be manually edited.
```

### Invariant 3

```text
.harbor/config and .harbor/policy are shared project configuration.
```

### Invariant 4

```text
.harbor/diary is project memory and should normally be versioned.
```

### Invariant 5

```text
External tool files are export targets, not canonical Harbor storage.
```

### Invariant 6

```text
Human design docs live under docs/design, not .harbor.
```

---

## 15. Recommended Initial `.gitignore`

```gitignore
# Harbor local state
.harbor/state/
.harbor/cache/

# Harbor export staging
.harbor/exports/

# Optional local-only reports
.harbor/reports/tmp/
.harbor/reports/local/
```

Do not ignore all of `.harbor/` by default.

That would hide useful shared Harbor governance assets such as:

```text
.harbor/config/
.harbor/policy/
.harbor/diary/
selected .harbor/views/
```

---

## 16. Recommended v1.3.1 Implementation Plan

## Step 1: Add layout design document

```text
docs/design/harbor-workspace-layout-v1.md
```

No runtime behavior change.

## Step 2: Add config loader support

Introduce:

```text
.harbor/config/harbor.yaml
```

Support reading workspace roots.

## Step 3: Add path resolver

Create a central path resolver:

```python
HarborWorkspacePaths
```

Responsible for:

```text
views_root
modules_view_root
project_structure_path
diary_root
reports_root
state_root
cache_root
exports_root
```

## Step 4: Migrate project structure write path behind config

Allow:

```yaml
views:
  canonical_root: .harbor/views
```

while preserving current default for compatibility.

Phase 2B landing update:

```text
`harbor project structure --write` now defaults to canonical
.harbor/views/project-structure.md
and can optionally export to docs/harbor/project-structure.md
```

## Step 5: Migrate module capsule paths behind config

Move hardcoded paths behind `HarborWorkspacePaths`.

## Step 6: Migrate diary paths

Support:

```text
.harbor/diary/
```

while reading legacy:

```text
specs/diary/
```

if present.

## Step 7: Add workspace inspect

Add read-only command:

```powershell
harbor workspace inspect
```

It should show:

```text
current configured roots
which paths exist
which paths are tracked or ignored
legacy paths detected
migration suggestions
```

Phase 2F-A implementation note:

```text
inspect only reports and advises
no migration/deletion/write side effects
workspace migrate remains a future phase
```

## Step 8: Add dry-run migration

Add:

```powershell
harbor workspace migrate --dry-run
```

No writes by default.

---

## 17. Non-goals for V1

This layout design does not require immediate implementation of:

```text
automatic migration
deleting legacy files
changing all defaults immediately
CI integration
multi-tool export sync
project-map.json
context plan
contract graph
```

---

## 18. Open Questions

### 18.1 Should `.harbor/views/` be tracked by default?

Recommended:

```text
yes for harbor-spec itself
configurable for users
```

### 18.2 Should L2 README remain beside modules?

Recommended:

```text
support as export target
do not treat as canonical storage
```

### 18.3 Should dogfooding reports be tracked?

Recommended:

```text
yes for release validation reports
no for temporary local reports
```

### 18.4 Should `.agents/skills/` be tracked?

Recommended:

```text
optional
```

If tracked, document it as an external integration export.

---

## 19. Summary

Harbor should adopt a unified workspace model:

```text
.harbor/ = canonical Harbor workspace
docs/design/ = human-authored design documents
docs/harbor/ = optional published docs export
.agents/.claude/.cursor = external tool export targets
```

The recommended layout is:

```text
.harbor/
  config/
  policy/
  state/
  views/
  diary/
  reports/
  exports/
  integrations/
  cache/
```

This layout gives Harbor a clear, scalable foundation for:

```text
project structure views
module capsules
diary memory
dogfooding reports
tool integrations
future context planning
future contract graph
future CI integration
```

The most important principle is:

```text
Harbor should own its workspace.
Generated context should be structured, discoverable, and clearly separated from both human design docs and external tool exports.
```

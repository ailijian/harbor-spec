---
name: harbor-workspace-migration-plan
description: Use when inspecting Harbor workspace layout, planning workspace cleanup, validating .harbor/ canonical workspace health, reviewing managed files, running workspace inspect, or previewing read-only workspace migration plans with migrate --dry-run.
---

# Harbor Workspace Migration Plan Skill

Version: Harbor-spec v1.3.0  
Purpose: Workspace diagnostics and read-only migration planning workflow for Harbor-managed repositories

---

## 1. Purpose

Use this skill when the task involves Harbor workspace layout, workspace diagnostics, managed files, migration planning, cleanup planning, or canonical workspace validation.

Harbor-spec v1.3.0 uses `.harbor/` as the canonical workspace.

This skill helps AI agents inspect workspace state safely and produce migration or cleanup plans without performing destructive actions.

This skill is an on-demand workflow entrypoint.

It is not source of truth.

It must follow:

```text
AGENTS.md
.harbor/policy.yaml
.harbor/safety.yaml
.harbor/rules/agent-policy.md
.harbor/rules/runtime-safety.md
.harbor/rules/diary-rules.md
.harbor/rules/project-rules.md, if present
```

Core principle:

```text
Workspace changes must be visible, planned, read-only first, reversible when possible, and never silently destructive.
```

---

## 2. When to Use

Use this skill when the task involves:

```text
Harbor workspace layout
.harbor/ canonical workspace validation
.harbor/rules/**
.harbor/views/**
.harbor/diary/**
.harbor/reports/**
.harbor/cache/**
.harbor/state/**
.harbor/exports/**
.agents/skills/**
AGENTS.md managed block
workspace inspect
workspace migration dry-run
workspace cleanup planning
managed file markers
managed block markers
init state review
upgrade planning
release workspace validation
future migrate --write design discussion
```

Typical triggers:

```text
user asks whether workspace is healthy
user asks to inspect Harbor workspace
user asks to clean up Harbor workspace
user asks to preview migration plan
user asks whether files are managed by Harbor
doctor reports workspace warning
init produced unexpected files
rules / views / diary layout changed
workspace dry-run output needs interpretation
release requires workspace sanity check
```

Do not use this skill for ordinary coding tasks unless workspace layout is involved.

---

## 3. Boundary With AGENTS.md, Project Rules, and Other Skills

### 3.1 AGENTS.md

`AGENTS.md` is the lightweight cross-tool entrypoint.

Use it for:

```text
global role
workspace boundaries
default workflow
instruction priority
context loading order
completion expectations
```

Do not duplicate all AGENTS rules inside this skill.

---

### 3.2 Project Rules

Project-specific rules live in:

```text
.harbor/rules/project-rules.md
```

Use Project Rules for:

```text
project-specific workspace conventions
project-specific protected paths
verified workspace commands
local release or init conventions
local skill routing
```

If this skill conflicts with Project Rules, inspect `.harbor/policy.yaml` and `.harbor/safety.yaml`.

Machine policy wins over Markdown rules.

---

### 3.3 Machine Policy

Machine-readable policy lives in:

```text
.harbor/policy.yaml
.harbor/safety.yaml
```

These files may define:

```text
protected workspace paths
managed file behavior
generated context policy
runtime safety decisions
strictness policy
```

If Markdown rules conflict with machine policy, prefer machine policy.

---

### 3.4 Related Skills

Use related skills when needed:

```text
harbor-safety-preflight
  Use before any workspace write, cleanup, deletion, batch move, .harbor/*.yaml modification, or generated skill modification.

harbor-context-refresh
  Use when workspace diagnostics show .harbor/views/** should be regenerated.

harbor-code-review
  Use when reviewing a diff that changes workspace behavior.

harbor-contract-change
  Use when workspace behavior, CLI output, JSON output, or file write contract changes.

harbor-ddt-diary
  Use when workspace migration planning requires DDT updates or Diary Draft.
```

This skill may route to these skills, but should not replace them.

---

## 4. Canonical Workspace

Harbor-spec v1.3.0 canonical workspace:

```text
.harbor/
  config/
    harbor.yaml

  rules/
    glossary.md
    agent-policy.md
    contract-rules.md
    ddt-rules.md
    runtime-safety.md
    diary-rules.md
    project-rules-guide.md
    project-rules.md

  views/
    project-structure.md

    l2/
      _meta.json
      <module>/
        README.md

    modules/
      <module>/
        module-card.md
        review-checklist.md
        debug-playbook.md

  diary/
    YYYY-MM.jsonl

  reports/

  cache/

  state/

  exports/
```

Meaning:

```text
.harbor/config/
  Harbor configuration.

.harbor/rules/
  static Harbor rule docs.

.harbor/views/
  generated context views.

.harbor/diary/
  structured decision memory.

.harbor/reports/
  validation, audit, migration, and dogfooding reports.

.harbor/cache/
  local runtime cache; not source of truth.

.harbor/state/
  local runtime state; not source of truth.

.harbor/exports/
  optional export area.
```

---

## 5. Source-of-Truth Boundary

Treat these as source of truth:

```text
source code
tests
schemas
type definitions
configuration
public CLI behavior
public JSON output
human-authored project docs
.harbor/diary/**
.harbor/policy.yaml
.harbor/safety.yaml
```

Treat these as Harbor rule references:

```text
.harbor/rules/**
```

Treat these as generated context:

```text
.harbor/views/**
```

Treat these as external workflow exports:

```text
.agents/skills/**
```

Treat these as runtime artifacts:

```text
.harbor/cache/**
.harbor/state/**
```

Rules:

```text
Do not treat generated views as primary source of behavior.
Do not treat skills as source of truth.
Do not treat cache or state as source of truth.
Do not let workspace diagnostics override source code, tests, schemas, policy, or diary.
```

---

## 6. Runtime Safety Boundary

Workspace operations can be risky.

Use `harbor-safety-preflight` before:

```text
deleting workspace files
batch-moving workspace files
modifying .harbor/*.yaml
modifying .harbor/rules/**
modifying .harbor/diary/**
modifying .agents/skills/**
overwriting AGENTS.md or managed blocks
running broad cleanup
performing any workspace write migration
```

Read-only diagnostics are usually safe:

```text
harbor workspace inspect
harbor workspace inspect --format json
harbor workspace migrate --dry-run
harbor workspace migrate --dry-run --format json
```

But do not claim results unless commands actually ran.

---

## 7. Important Boundary: Dry-run Only

In Harbor-spec v1.3.0:

```text
harbor workspace migrate --dry-run
```

is a read-only planning and diagnostics command.

It must not:

```text
write files
move files
delete files
rewrite files
modify AGENTS.md
modify .harbor/**
modify .agents/skills/**
append diary entries
change baseline
```

Do not assume this command exists:

```powershell
harbor workspace migrate --write
```

Future workspace write migration must require:

```text
dry-run plan
per-item confirmation
backup
rollback
idempotency
conflict detection
managed block detection
diary merge / dedupe strategy
migration report
failure recovery
no partial silent migration
```

---

## 8. Step 1: Identify Workspace Task Type

Classify the task as one or more of:

```text
workspace inspect
workspace health review
workspace migration dry-run
workspace cleanup planning
managed file review
managed block review
init state review
rules layout review
views layout review
diary layout review
skill export review
cache / state review
reports review
workspace contract review
release workspace validation
future write migration design
unknown
```

If task type is unclear, inspect the user request and workspace files before recommending write actions.

Do not assume cleanup is safe.

---

## 9. Step 2: Identify Affected Workspace Areas

Identify which areas are involved:

```text
.harbor/config/**
.harbor/rules/**
.harbor/views/**
.harbor/diary/**
.harbor/reports/**
.harbor/cache/**
.harbor/state/**
.harbor/exports/**
.agents/skills/**
AGENTS.md
.harbor/policy.yaml
.harbor/safety.yaml
```

Classify each area:

```text
configuration
rule docs
generated context
decision memory
reports
runtime cache
runtime state
external skill export
agent entrypoint
machine policy
```

Use this classification to decide safety and validation requirements.

---

## 10. Step 3: Choose Diagnostic Commands

For basic workspace state:

```powershell
harbor workspace inspect
```

For machine-readable workspace state:

```powershell
harbor workspace inspect --format json
```

For read-only migration or cleanup planning:

```powershell
harbor workspace migrate --dry-run
```

For machine-readable dry-run plan:

```powershell
harbor workspace migrate --dry-run --format json
```

For generated context health:

```powershell
harbor stale
harbor stale --format json
```

For overall Harbor health:

```powershell
harbor doctor
harbor doctor --format json
```

Do not run commands unless appropriate to the user request and available environment.

Do not invent command output.

---

## 11. Step 4: Inspect Workspace State

When inspecting workspace state, look for:

```text
whether .harbor/ exists
whether .harbor/config/ exists
whether .harbor/rules/ exists
whether .harbor/views/ exists
whether .harbor/diary/ exists
whether .harbor/reports/ exists
whether .harbor/cache/ exists
whether .harbor/state/ exists
whether .harbor/policy.yaml exists
whether .harbor/safety.yaml exists
whether AGENTS.md exists
whether Harbor managed block exists in AGENTS.md
whether .agents/skills/** exists
whether expected skills exist
whether generated views are present
whether generated views appear stale
whether cache/state are being treated as source of truth
```

Do not read secrets while inspecting workspace.

Do not modify files during inspection.

---

## 12. Step 5: Interpret Workspace Inspect

When interpreting `harbor workspace inspect`, classify findings as:

```text
PASS
WARN
FAIL
SKIP
```

Guidance:

```text
PASS:
  Workspace state supports normal Harbor workflow.

WARN:
  Workspace is usable, but has incomplete generated context, missing optional files, or cleanup suggestions.

FAIL:
  Workspace state blocks Harbor workflow or violates canonical layout.

SKIP:
  Check could not run due to missing prerequisites or unavailable command.
```

Examples:

```text
PASS:
  .harbor/rules exists and AGENTS.md routes to it.

WARN:
  .harbor/views is missing before first context generation.

FAIL:
  .harbor/safety.yaml missing when safety policy is required by project profile.

SKIP:
  Git is unavailable, so changed-module detection cannot run.
```

---

## 13. Step 6: Interpret Migration Dry-run

When interpreting `harbor workspace migrate --dry-run`, verify:

```text
it is read-only
it reports planned actions
it reports write intent as false or equivalent
it does not perform moves
it does not delete files
it does not modify AGENTS.md
it does not modify .harbor/**
it does not modify .agents/skills/**
```

Classify plan items as:

```text
KEEP
CREATE
UPDATE_MANAGED
COPY
MOVE
MERGE
DEDUP
DELETE
IGNORE_CACHE
IGNORE_STATE
MANUAL_REVIEW
SKIP
```

Meaning:

```text
KEEP:
  Leave as is.

CREATE:
  Would create a missing managed file or directory in a future write mode.

UPDATE_MANAGED:
  Would update a managed file or managed block in a future write mode.

COPY:
  Would copy content without removing original in a future write mode.

MOVE:
  Would move content in a future write mode; requires confirmation and rollback.

MERGE:
  Would merge records or content; requires conflict handling.

DEDUP:
  Would remove duplicates; requires review.

DELETE:
  Would delete files; requires explicit confirmation and backup.

IGNORE_CACHE:
  Cache should not be migrated as source of truth.

IGNORE_STATE:
  Runtime state should not be migrated as source of truth.

MANUAL_REVIEW:
  Human review needed.

SKIP:
  No action.
```

In v1.3.0, dry-run should only report these actions, not execute them.

---

## 14. Step 7: Managed File Review

A Harbor-managed file may contain a marker such as:

```markdown
<!-- harbor-spec:managed version=1.3.0 kind=rule -->
```

Managed files can be updated by Harbor-aware workflows, but still require caution.

Review:

```text
is the file clearly managed?
does the marker match expected version?
does the file contain user-authored content outside managed areas?
would update overwrite user content?
does update require confirmation?
```

Do not overwrite user-authored files unless:

```text
file is clearly managed
or the user explicitly confirms overwrite
```

---

## 15. Step 8: Managed Block Review

A Harbor-managed block may look like:

```markdown
<!-- harbor-spec:start version=1.3.0 -->
...
<!-- harbor-spec:end -->
```

Managed blocks allow Harbor to update a section without overwriting the whole file.

Use managed blocks for user-owned files such as:

```text
AGENTS.md
README.md, if ever needed
tool-specific rule adapters
```

Review:

```text
does the block exist?
does the block have matching start and end markers?
is there exactly one Harbor block unless intentionally multiple?
is the block version current?
would an update affect content outside the block?
```

Do not replace entire user files when a managed block update is sufficient.

---

## 16. Step 9: Cache and State Handling

Runtime cache:

```text
.harbor/cache/**
```

Runtime state:

```text
.harbor/state/**
```

Rules:

```text
cache is not source of truth
state is not source of truth
do not migrate cache as project truth
do not use cache/state to override rules, views, diary, tests, or code
do not delete cache/state without confirmation if deletion is requested
```

Cleaning cache/state can be useful, but file deletion still requires safety preflight.

Prefer:

```powershell
Get-ChildItem -Path .\.harbor\cache -Recurse
Remove-Item .\.harbor\cache -Recurse -WhatIf
```

before any deletion.

---

## 17. Step 10: Rules and Policy Handling

Rule docs:

```text
.harbor/rules/**
```

Machine policy:

```text
.harbor/policy.yaml
.harbor/safety.yaml
```

Rules:

```text
Markdown rule docs explain behavior.
YAML policy controls machine-readable behavior.
If Markdown conflicts with YAML, prefer YAML.
Changing YAML policy is high risk.
Changing rule docs may affect AI agent behavior.
```

Use safety preflight before modifying:

```text
.harbor/policy.yaml
.harbor/safety.yaml
```

Use caution before broad modifications to:

```text
.harbor/rules/**
```

---

## 18. Step 11: Generated Context Handling

Generated context:

```text
.harbor/views/**
```

Rules:

```text
generated context is not source of truth
generated context should be refreshed through Harbor commands
do not manually edit generated views as project truth
if generated views conflict with code/tests/schemas/policy/diary, treat generated views as stale
```

Use `harbor-context-refresh` when generated context needs refresh.

Common commands:

```powershell
harbor project structure --write
harbor docs --changed --write
harbor module seal --changed --write
harbor finish --sync-context
harbor stale
harbor doctor
```

---

## 19. Step 12: Diary Handling

Diary:

```text
.harbor/diary/YYYY-MM.jsonl
```

Rules:

```text
Diary records why important changes happened.
Diary is not changelog.
Diary is not commit message.
Do not write Diary unless user explicitly requests or workflow explicitly includes it.
If Diary is needed but not written, output Diary Draft.
```

Workspace layout decisions often need Diary Draft.

Examples:

```text
workspace layout change
managed block strategy change
migration strategy change
dry-run semantics change
rules path change
views path change
diary path change
skill export strategy change
```

Use `harbor-ddt-diary` when Diary is needed.

---

## 20. Step 13: Skill Export Handling

External skills live under:

```text
.agents/skills/**
```

Rules:

```text
skills are workflow entrypoints
skills are not source of truth
skills should route to .harbor/rules/** and .harbor/views/**
skills must not override .harbor/policy.yaml or .harbor/safety.yaml
changing skills may affect AI agent behavior
```

Use safety preflight before broad skill changes.

Do not run:

```powershell
harbor module promote-skill <module>
```

unless the user explicitly requests it.

---

## 21. Step 14: AGENTS.md Handling

`AGENTS.md` is the lightweight cross-tool entrypoint.

Rules:

```text
do not overwrite user-authored AGENTS.md without confirmation
prefer managed block updates when modifying user-owned AGENTS.md
do not duplicate all Harbor rules inside AGENTS.md
AGENTS.md should route to .harbor/rules/**, .harbor/views/**, and skills
```

If AGENTS.md has a Harbor managed block, update only the managed block.

If AGENTS.md has no Harbor managed block, propose an insertion plan before writing.

---

## 22. Step 15: Workspace Contract Impact

Changing workspace behavior is Contract Impact.

Treat these as Contract Impact:

```text
changing canonical workspace layout
changing rules path
changing generated context path
changing diary path
changing reports path
changing cache/state semantics
changing skill export path
changing AGENTS managed block behavior
changing dry-run semantics
changing workspace inspect JSON output
changing migration plan JSON output
```

When workspace contract changes:

```text
1. Update contract / docs.
2. Update implementation.
3. Update tests / DDT.
4. Refresh generated context if needed.
5. Create Diary Draft if important.
6. Consider release notes if user-visible.
```

Use `harbor-contract-change` when workspace behavior changes.

---

## 23. Step 16: Workspace DDT

Workspace behavior should be tested when changed.

DDT should cover:

```text
canonical paths are used
rules path is .harbor/rules/**
views path is .harbor/views/**
diary path is .harbor/diary/**
cache/state are not source of truth
workspace inspect is read-only
migrate --dry-run is read-only
dry-run does not write/move/delete files
managed block updates do not overwrite user content
JSON output is stable and path-normalized
```

Use `harbor-ddt-diary` when tests / DDT are needed.

---

## 24. Step 17: Output Migration Plan

When asked to produce or interpret a migration plan, use this format:

```text
Workspace Migration Plan:
- Scope:
- Current workspace status:
- Affected areas:
- Read-only commands:
- Planned actions:
  - <action>: <target> — <reason>
- Writes files: yes | no
- Deletes files: yes | no
- Moves files: yes | no
- Risk level:
- Safety decision:
- Backup needed:
- Rollback needed:
- Diary needed:
- User confirmation required:
- Recommended next command:
```

For v1.3.0 dry-run planning, expected values should usually be:

```text
Writes files: no
Deletes files: no
Moves files: no
```

unless describing a hypothetical future write mode.

---

## 25. Step 18: Output Workspace Diagnostics

When reporting workspace diagnostics, use:

```text
Workspace Diagnostics:
- Overall status: PASS | WARN | FAIL | SKIP
- Canonical workspace:
- Rules:
- Machine policy:
- Generated views:
- Diary:
- Reports:
- Cache / state:
- Skills:
- AGENTS.md:
- Stale / doctor:
- Risks:
- Recommended next command:
```

If commands were not run, say so clearly.

---

## 26. Step 19: Tool Honesty

Do not claim the following were run unless actually run and observed:

```text
harbor workspace inspect
harbor workspace inspect --format json
harbor workspace migrate --dry-run
harbor workspace migrate --dry-run --format json
harbor stale
harbor doctor
harbor project structure --write
harbor finish --sync-context
```

Allowed wording:

```text
已运行，结果是...
未运行，建议运行...
当前环境无法运行...
我只做了静态审查，未执行命令...
```

Forbidden wording when not executed:

```text
workspace inspect 通过
dry-run 没有写文件
doctor 通过
stale check 已清理
```

unless actually observed.

---

## 27. Explicit User Request Only

Do not run the following unless the user explicitly requests it:

```powershell
harbor log
harbor accept
harbor lock
harbor module promote-skill <module>
```

Do not run hypothetical write migration commands.

Do not assume:

```powershell
harbor workspace migrate --write
```

exists.

Never run `harbor accept` to hide unresolved drift.

---

## 28. Review Labels

Use these labels when reviewing workspace issues:

```text
Workspace Contract Risk
Workspace Safety Risk
Workspace Dry-run Violation
Managed File Risk
Managed Block Risk
Rules Path Gap
Views Path Gap
Diary Path Gap
Skill Export Gap
Cache / State Misuse
Generated Context Gap
Machine Policy Gap
Tool Honesty Issue
Suggested Improvement
```

Definitions:

```text
Workspace Contract Risk:
  Workspace behavior or layout changed without contract/test/diary handling.

Workspace Safety Risk:
  Workspace operation may write, move, delete, or overwrite without confirmation.

Workspace Dry-run Violation:
  Dry-run appears to write, move, delete, or mutate state.

Managed File Risk:
  Managed file update may overwrite user-authored content.

Managed Block Risk:
  Managed block is missing, duplicated, malformed, or unsafe to update.

Rules Path Gap:
  Rule references do not point to .harbor/rules/**.

Views Path Gap:
  Generated context references do not point to .harbor/views/**.

Diary Path Gap:
  Diary references do not point to .harbor/diary/**.

Skill Export Gap:
  Skill references are missing or not aligned with .agents/skills/**.

Cache / State Misuse:
  Cache or state is treated as source of truth.

Generated Context Gap:
  Generated context is missing or stale.

Machine Policy Gap:
  .harbor/policy.yaml or .harbor/safety.yaml is missing or inconsistent.

Tool Honesty Issue:
  Output claims command execution without evidence.
```

---

## 29. Common Mistakes

Avoid:

```text
treating migrate --dry-run as a write command
assuming migrate --write exists
deleting workspace files without safety preflight
moving workspace files without backup and confirmation
treating .harbor/cache/** as source of truth
treating .harbor/state/** as source of truth
treating .agents/skills/** as source of truth
manually editing .harbor/views/** as project truth
overwriting AGENTS.md instead of using managed block
changing .harbor/*.yaml without confirmation
claiming dry-run ran without observing output
using harbor accept to hide workspace drift
running harbor module promote-skill during ordinary migration planning
```

---

## 30. Final Principle

Before any workspace migration or cleanup, ask:

```text
What is the current canonical workspace state?
Which files are managed by Harbor?
Which files are user-authored?
What would change?
Can we preview it read-only?
Can we roll it back?
Does the user need to confirm?
```

A safe Harbor workspace migration starts with inspection and dry-run, not writes.

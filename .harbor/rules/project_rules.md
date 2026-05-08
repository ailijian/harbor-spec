<!-- harbor-spec:managed version=1.3.0 kind=project-rules -->

# Project Rules

Version: Harbor-spec v1.3.0  
Canonical path: `.harbor/rules/project-rules.md`  
Purpose: Project-specific rules for the harbor-spec reference implementation

---

## 1. Project Overview

Project name:

```text
harbor-spec
```

Project goal:

```text
Harbor-spec is a context governance engine for AI Coding / Agentic Coding.
It provides a Harbor CLI and Python reference implementation for keeping implementation, contracts, tests, generated context, decision memory, runtime safety, and AI tool instructions aligned.
```

Primary users:

```text
Developers and teams using AI coding tools who need contract-first context governance, generated module context, DDT validation, runtime safety, and decision memory.
```

Primary product surface:

```text
CLI tool + Python library + AI-tool integration rules / skills
```

Core product surfaces:

```text
- Harbor CLI commands
- Python contract extraction / indexing / drift detection logic
- DDT / semantic audit support
- canonical .harbor/ workspace
- generated context views under .harbor/views/**
- Diary decision memory under .harbor/diary/**
- AI-tool adapters: AGENTS.md, TRAE rules, skills
```

Core workflows:

```text
- Initialize / inspect Harbor workspace
- Start / checkpoint / finish AI coding workflow
- Refresh generated context with finish --sync-context
- Check stale generated context
- Run doctor health checks
- Validate contract / DDT / semantic drift status
- Record important decisions through Diary when explicitly requested
- Preview workspace migration or cleanup with migrate --dry-run
```

Default language:

```text
Simplified Chinese
```

Default shell:

```text
Windows 11 PowerShell
```

---

## 2. Boundary With AGENTS.md, Rules, and Skills

`AGENTS.md` is the cross-tool lightweight entrypoint.

This file is Project Rules for the harbor-spec repository itself.

Do not merge their responsibilities.

Use these layers:

```text
AGENTS.md
  Cross-tool lightweight entrypoint.

.harbor/rules/project-rules.md
  This file. Project-specific rules for harbor-spec itself.

.harbor/rules/**
  Generic Harbor rule docs.

.harbor/views/**
  Canonical generated context views.

.harbor/diary/**
  Decision memory.

.harbor/policy.yaml
.harbor/safety.yaml
  Machine-readable policy.

.agents/skills/**
  On-demand workflow skills.
```

Rules:

```text
- Project Rules should stay project-specific.
- Project Rules should not duplicate full Contract / DDT / Diary / Runtime Safety docs.
- If this file conflicts with .harbor/policy.yaml or .harbor/safety.yaml, prefer YAML policy.
- If this file conflicts with source code, tests, schemas, or actual CLI behavior, inspect the conflict and update the stale side.
- Skills are workflow entrypoints, not source of truth.
- Generated context is orientation, not source of truth.
```

---

## 3. Technology Stack

Backend / implementation language:

```text
Python 3.9+
```

Frontend:

```text
None / not applicable
```

Primary interface:

```text
CLI
```

Library surface:

```text
Python package
```

Database / index backend:

```text
Local runtime cache or SQLite-like storage may be used under .harbor/cache/** when enabled.
Runtime cache is not source of truth.
```

Storage:

```text
Local filesystem
Canonical Harbor workspace under .harbor/**
```

Queue / async:

```text
None confirmed / inspect project config before assuming
```

LLM / Agent framework:

```text
Optional provider integrations may exist.
Do not assume network access or provider availability without checking project config.
```

Testing:

```text
pytest
```

Package manager:

```text
pyproject.toml-based Python package; use pip unless project config confirms uv / poetry / another tool.
```

Default shell:

```text
PowerShell
```

---

## 4. Directory Map

Important project paths:

```text
harbor/cli/
  CLI entrypoints and command orchestration.

harbor/core/
  Core Harbor domain logic: contracts, checkpoint, stale, doctor, generated context, DDT, diary, policy, workspace behavior.

harbor/adapters/python/
  Python parsing / AST / contract extraction adapter layer.

harbor/utils/
  Shared utilities such as formatting, path handling, i18n, and deterministic output helpers.

tests/
  pytest test suite.

AGENTS.md
  Cross-tool lightweight entrypoint.

.harbor/rules/
  Harbor rule docs, including this project-rules.md.

.harbor/views/
  Canonical generated context views.

.harbor/diary/
  Canonical decision memory.

.harbor/reports/
  Reports, dogfooding outputs, diagnostics, release validation evidence.

.harbor/cache/
  Runtime cache. Not source of truth.

.harbor/state/
  Runtime state. Not source of truth.

.agents/skills/
  External AI-tool skill exports.

.trae/rules/ or equivalent tool-rule location
  TRAE adapter rules, if present.
```

Dependency direction constraints:

```text
- harbor/core should not depend on harbor/cli.
- harbor/adapters/python should provide parsing / extraction capabilities needed by core.
- harbor/cli should orchestrate core / adapters, not contain core domain logic.
- tests should verify public CLI behavior, JSON output, contract extraction, DDT behavior, workspace behavior, and generated context behavior.
- .harbor/views/** should not be imported as source of truth by implementation code.
- .agents/skills/** should not be imported as source of truth by implementation code.
```

---

## 5. Harbor Strictness Map

Use `.harbor/policy.yaml` as the source of truth.

If `.harbor/policy.yaml` is missing or incomplete, use the following project-specific default mapping.

### Strict

Treat these as strict:

```text
harbor/cli/**
harbor/core/**
harbor/adapters/python/**
tests/**/test_*cli*.py
tests/**/test_*json*.py
tests/**/test_*workspace*.py
tests/**/test_*stale*.py
tests/**/test_*doctor*.py
tests/**/test_*ddt*.py
tests/**/test_*diary*.py
AGENTS.md
.harbor/policy.yaml
.harbor/safety.yaml
.harbor/rules/**
.agents/skills/**
```

Strict changes require:

```text
- Contract Impact assessment
- strictness assessment
- runtime safety assessment
- contract / docstring / schema update when behavior changes
- tests / DDT update when relevant
- no strategy="latest" for strict DDT targets
- semantic drift check when applicable
- generated context refresh if context is affected
- Diary Draft for important or release-relevant decisions
```

Strict examples:

```text
- public CLI command behavior
- public CLI options / arguments
- CLI stdout / stderr / exit code
- JSON output keys, types, nesting, sorting, path normalization
- workspace layout behavior
- generated context write targets
- stale / doctor status semantics
- DDT validation rules
- semantic audit behavior
- diary write path and JSONL shape
- module capsule generation behavior
- project structure generation behavior
- safety / policy interpretation
```

### Standard

Treat as standard by default:

```text
ordinary internal helpers
ordinary non-public service functions
module-level implementation details
internal formatting helpers used by standard paths
```

Standard changes require:

```text
- Contract Impact check
- tests recommended
- DDT recommended when behavior is meaningful
- generated context refresh if module responsibilities or public contracts changed
```

### Light

Treat as light only when clearly low-risk:

```text
low-risk local utilities
test helpers not used by strict behavior
script-local helpers
formatting-only documentation changes
```

Light changes require:

```text
- clear summary
- type clarity when helpful
- tests only when behavior is non-trivial
```

If a light helper is used by a strict path, upgrade review strictness to strict.

---

## 6. Project Contract Sources

In harbor-spec, Contract sources include:

```text
Python docstrings
type hints
CLI command names, arguments, options, stdout, stderr, and exit codes
JSON output shapes for machine-readable commands
DDT binding metadata: l3_version / strategy
tests and fixtures
snapshot / golden outputs, if present
.harbor/policy.yaml
.harbor/safety.yaml
generated context write behavior
workspace inspect output
workspace migrate --dry-run output
Diary JSONL structure under .harbor/diary/**
managed file and managed block markers
```

Primary contract sources:

```text
- public CLI behavior
- core public functions and docstrings
- JSON outputs consumed by agents / scripts / CI
- tests / DDT bindings
- .harbor/policy.yaml
- .harbor/safety.yaml
```

Contract pairs that must stay synchronized:

```text
CLI command behavior ↔ CLI tests
CLI JSON output ↔ JSON schema / snapshot / tests
workspace inspect behavior ↔ workspace tests
workspace migrate --dry-run behavior ↔ dry-run no-write tests
generated context commands ↔ .harbor/views/** expectations
diary write behavior ↔ .harbor/diary/YYYY-MM.jsonl structure
DDT decorator / metadata ↔ DDT tests
semantic audit classification ↔ review / audit tests
AGENTS.md managed block behavior ↔ managed block tests
skills export behavior ↔ .agents/skills/** expectations
```

Rules:

```text
- Contract does not mean docstring only.
- README is public documentation, but not the sole source of behavior truth.
- Generated context under .harbor/views/** is not source of truth.
- Skills under .agents/skills/** are workflow exports, not source of truth.
- If implementation and contract conflict, mark [Semantic Drift].
- If schema and implementation conflict, mark [Schema Gap].
- If tests verify old behavior, mark [Test / DDT Gap].
```

---

## 7. API / CLI / JSON / Workspace Contract Rules

When modifying public CLI, JSON output, workspace behavior, generated context behavior, DDT behavior, or Diary behavior:

```text
1. Read existing contract sources.
2. Determine Contract Impact.
3. Determine Strictness.
4. Update contract first if intended behavior changes.
5. Update implementation.
6. Update tests / fixtures / DDT.
7. Check whether the change is breaking.
8. Refresh generated context if needed.
9. Create Diary Draft if important.
10. Do not accept a new baseline unless explicitly requested.
```

Relevant paths:

```text
harbor/cli/**
harbor/core/**
harbor/adapters/python/**
tests/**
.harbor/rules/**
.harbor/views/**
.harbor/diary/**
.agents/skills/**
AGENTS.md
```

CLI / JSON output rules:

```text
- Changing command names is Contract Impact.
- Changing option names or meanings is Contract Impact.
- Changing stdout / stderr / exit code is Contract Impact.
- Changing JSON keys, types, nesting, ordering, or path format is Contract Impact.
- JSON output should be deterministic where practical.
- Paths in JSON output should be normalized.
- Avoid leaking machine-local absolute paths unless explicitly required.
```

Workspace rules:

```text
- .harbor/ is the canonical workspace.
- .harbor/rules/** contains static rule docs.
- .harbor/views/** contains generated context views.
- .harbor/diary/** contains decision memory.
- .harbor/cache/** and .harbor/state/** are runtime artifacts, not source of truth.
- .agents/skills/** contains external AI-tool workflow exports, not source of truth.
```

---

## 8. Testing Commands

Verified baseline command:

```powershell
pytest
```

Single test command:

```powershell
pytest tests/path/to/test_file.py
```

Harbor checks:

```powershell
harbor checkpoint
harbor stale
harbor doctor
```

Machine-readable Harbor checks:

```powershell
harbor stale --format json
harbor doctor --format json
harbor workspace inspect --format json
harbor workspace migrate --dry-run --format json
```

Workspace diagnostics:

```powershell
harbor workspace inspect
harbor workspace migrate --dry-run
```

Not confirmed by this file:

```text
Lint command not confirmed. Inspect pyproject.toml or project config before running.
Type check command not confirmed. Inspect pyproject.toml or project config before running.
Build command not confirmed. Inspect project config before running.
```

Execution honesty:

```text
- Do not claim pytest passed unless it was actually run and observed.
- Do not claim harbor stale / doctor passed unless actually run and observed.
- If not run, state: 未实际运行，建议执行 <command>。
```

---

## 9. DDT Rules in This Project

Strict targets must use explicit `l3_version` when DDT binding is used.

Allowed for strict targets:

```python
@harbor_ddt_target("module.func", l3_version=1)
def test_func_success_path():
    ...
```

Forbidden for strict targets:

```python
@harbor_ddt_target("module.func", strategy="latest")
def test_func_success_path():
    ...
```

If decorator support is not available in a given area, preserve binding intent with comments:

```python
# harbor-ddt-target: module.func
# l3_version: 1
def test_func_success_path():
    ...
```

When contract changes:

```text
- update contract
- upgrade l3_version when needed
- inspect old tests before updating binding
- update assertions
- add missing edge cases
- do not blindly bind tests to latest implementation
```

Strict DDT coverage should prioritize:

```text
- CLI behavior
- JSON output shape
- workspace inspect
- migrate --dry-run read-only behavior
- generated context write paths
- stale / doctor status semantics
- diary JSONL behavior
- safety policy behavior
- semantic audit classification
```

---

## 10. Runtime Safety in This Project

Use `.harbor/safety.yaml` as the source of truth.

Ask before:

```text
- deleting files
- batch-moving files
- modifying .env or secrets/**
- modifying migrations
- modifying CI/CD
- installing dependencies
- changing Docker / deployment files
- running destructive commands
- running git push
- running git reset --hard
- publishing packages / releases / tags
- modifying .harbor/*.yaml
- modifying .harbor/rules/**
- modifying .agents/skills/**
- overwriting AGENTS.md or managed blocks
```

Default deny:

```text
- reading or printing secrets
- deleting user data without explicit request
- relaxing safety policy silently
- generating allow-all permission configs
- fabricating command execution results
```

PowerShell safety:

```text
- Use PowerShell by default.
- Prefer -WhatIf for deletion previews.
- List targets before deletion.
- Do not default to rm -rf unless Bash / WSL / Git Bash is explicitly required.
```

Workspace safety:

```text
- harbor workspace migrate --dry-run is read-only.
- Do not assume harbor workspace migrate --write exists.
- Do not manually migrate workspace files unless explicitly requested and backup / rollback / diary dedupe risks are considered.
```

---

## 11. Skill Routing

Use Harbor skills for multi-step tasks:

```text
Contract or schema change:
  harbor-contract-change

Code review, diff review, implementation correctness, semantic drift:
  harbor-code-review

Risky command, protected file change, dependency, migration, CI/CD:
  harbor-safety-preflight

DDT update, l3_version, Diary Draft, changelog, release notes:
  harbor-ddt-diary

Generated context refresh, L2 README, Module Capsule, project structure:
  harbor-context-refresh

Workspace diagnostics, migrate dry-run, cleanup planning, canonical workspace validation:
  harbor-workspace-migration-plan
```

If a skill is missing:

```text
Follow AGENTS.md and the relevant .harbor/rules/*.md manually.
```

Skills are workflow entrypoints.

Skills are not source of truth.

---

## 12. Common Task Rules

### 12.1 New CLI Command or CLI Behavior Change

```text
1. Determine Contract Impact.
2. Determine Strictness.
3. Update CLI contract / help / docstring when needed.
4. Implement.
5. Add or update CLI tests.
6. Add JSON output tests if machine-readable output is involved.
7. Refresh generated context if command surface changed.
8. Create Diary Draft if release-relevant.
```

### 12.2 JSON Output Change

```text
1. Treat as Contract Impact.
2. Preserve stable keys when possible.
3. Normalize paths.
4. Avoid machine-local absolute path leakage.
5. Update tests / snapshots.
6. Update DDT if applicable.
7. Consider breaking change risk.
8. Create Diary Draft if important.
```

### 12.3 Workspace Layout or Workspace Command Change

```text
1. Treat as Contract Impact.
2. Use harbor-workspace-migration-plan for planning.
3. Keep dry-run read-only.
4. Update workspace tests.
5. Update .harbor/rules/** docs if behavior changes.
6. Refresh generated context if needed.
7. Create Diary Draft for important workspace decisions.
```

### 12.4 Generated Context Change

```text
1. Identify source of truth change.
2. Update implementation / contract first.
3. Regenerate .harbor/views/** through Harbor commands.
4. Run harbor stale / harbor doctor.
5. Do not manually edit generated views as truth.
```

### 12.5 Bugfix

```text
1. Reproduce or describe the bug.
2. Determine whether implementation or contract is wrong.
3. Add failing test when practical.
4. Fix implementation or contract.
5. Update tests / DDT.
6. Check generated context and Diary need.
```

### 12.6 Refactor

```text
1. State whether external behavior remains unchanged.
2. If behavior is unchanged, mark Contract Impact: none.
3. Add characterization tests if risk is high.
4. Avoid broad unrelated rewrites.
5. Refresh generated context if module boundaries changed.
```

### 12.7 Rule / Skill Update

```text
1. Confirm whether the change affects AGENTS.md, .harbor/rules/**, or .agents/skills/**.
2. Preserve boundary:
   - AGENTS.md = lightweight entrypoint
   - .harbor/rules/** = detailed rules
   - .agents/skills/** = task workflows
3. Do not duplicate full rules inside skills or role-rules.
4. Update role-rules only as lightweight tool adapters.
5. Run review for path consistency and stale old paths.
```

---

## 13. Generated Context Rules

Generated context lives under:

```text
.harbor/views/**
```

Do not manually edit generated context as project truth.

Refresh through Harbor commands:

```powershell
harbor project structure --write
harbor docs --changed --write
harbor module seal --changed --write
harbor finish --sync-context
harbor stale
harbor doctor
```

Refresh generated context when changes affect:

```text
- module boundaries
- project structure
- public contracts
- docstrings
- tests / DDT
- CLI behavior
- JSON output
- workspace structure
- module responsibilities
- debug workflow
- review workflow
```

---

## 14. Diary Rules in This Project

Canonical Diary path:

```text
.harbor/diary/YYYY-MM.jsonl
```

Use Diary Drafts for:

```text
- Contract Change
- Breaking Change
- important bugfix
- architecture decision
- runtime safety policy change
- workspace layout change
- generated context layout change
- CLI behavior change
- JSON output change
- DDT strategy change
- release-relevant decision
```

Do not run:

```powershell
harbor log
```

unless the user explicitly requests it.

If Diary is needed but not written, output a Diary Draft.

Do not write Diary entries to `specs/diary/**`.

---

## 15. Explicit User Request Only

Do not run the following unless explicitly requested by the user:

```powershell
harbor log
harbor accept
harbor lock
harbor module promote-skill <module>
```

Never run `harbor accept` to hide unresolved drift.

Never claim Diary was written unless it was actually written.

Never run `harbor module promote-skill` during ordinary context refresh.

---

## 16. Final Response Requirements

For implementation tasks, include:

```text
Change Summary:
- Files changed:
- Behavior changed:
- Contract Impact:
- Strictness:
- Tests / DDT:
- Runtime Safety:
- Generated Context:
- Diary:
- Harbor commands run:
- Remaining risks:
```

For review tasks, include:

```text
Review Summary:
- Overall assessment:
- Contract Impact:
- Strictness:
- Tests / DDT:
- Runtime Safety:
- Generated Context:
- Diary:
```

For DDT / Diary tasks, include:

```text
DDT / Diary Summary:
- Target:
- Contract Impact:
- Strictness:
- DDT binding:
- l3_version:
- Tests changed:
- Diary needed:
- Diary written:
- Remaining risks:
```

For workspace tasks, include:

```text
Workspace Diagnostics:
- Overall status:
- Affected areas:
- Read-only commands:
- Planned actions:
- Writes files:
- Deletes files:
- Moves files:
- Risk level:
- Safety decision:
- Diary needed:
- Recommended next command:
```

Always distinguish:

```text
已执行
未执行
建议执行
需要用户确认
```

Do not invent command results.

---

## 17. Completion Checklist

Before saying a task is complete, verify:

```text
[ ] User's current request was followed.
[ ] Relevant Harbor rules were considered.
[ ] Relevant project context was read when needed.
[ ] Contract Impact was assessed.
[ ] Strictness was assessed.
[ ] Runtime Safety was assessed.
[ ] Implementation and contract are synchronized.
[ ] Tests / DDT were updated if needed.
[ ] Generated context was refreshed if needed.
[ ] harbor checkpoint / stale / doctor were run or clearly marked as not run.
[ ] Important decisions have a Diary Draft if needed.
[ ] No risky action was performed without explicit confirmation.
[ ] Remaining risks are reported.
```

---

## 18. Anti-patterns

Avoid:

```text
- using v1.0.x / v1.2.x path assumptions in v1.3.0
- writing Diary to specs/diary/**
- treating README as the primary contract source
- treating .harbor/views/** as source of truth
- treating .agents/skills/** as source of truth
- copying full generic Harbor rules into Project Rules
- duplicating AGENTS.md inside Project Rules
- keeping app/** strictness rules that do not match this repository
- using harbor status / harbor check as the main workflow when v1.3.0 uses checkpoint / stale / doctor
- putting harbor log or harbor accept into default task flow
- using strategy="latest" for strict DDT targets
- manually editing generated context as truth
- claiming tests or Harbor checks passed without execution evidence
- using harbor accept to silence unresolved drift
```

---

## 19. Final Principle

For the harbor-spec repository itself:

```text
Dogfood Harbor-spec strictly.
```

This repository is both:

```text
1. the reference implementation of Harbor-spec
2. a Harbor-managed repository using Harbor-spec for AI coding
```

Therefore, changes should keep implementation, contracts, tests, generated context, decision memory, runtime safety, and AI-tool instructions aligned.

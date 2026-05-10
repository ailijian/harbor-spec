<!-- harbor-spec:managed version=1.3.0 kind=agents-entrypoint -->

# AGENTS.md

Version: Harbor-spec v1.3.0  
Purpose: Lightweight cross-tool entrypoint for AI coding agents  
Default language: Simplified Chinese  
Default shell: Windows 11 PowerShell

---

## 1. Role

You are an AI coding assistant working under the Harbor-spec context governance workflow.

Harbor-spec is the context governance layer for this repository.

It helps keep the following aligned:

```text
implementation
contracts
schemas
tests
DDT targets
generated context views
decision history
runtime safety rules
AI tool instructions
```

Harbor-spec is not an AI IDE.

Harbor-spec is not a code generator.

Core principle:

```text
让 AI 写代码可以快，但契约、测试、上下文、决策记忆和安全边界不能漂移。
```

When working in this repository, do not optimize only for “code changed successfully”.

Optimize for:

```text
code + contract + tests + generated context + diary + safety consistency
```

---

## 2. What This File Is

`AGENTS.md` is the shared lightweight entrypoint for AI coding tools such as:

```text
Codex
Claude Code
Cursor
TRAE
GitHub Copilot
other agentic coding tools
```

This file should stay short enough to be always loaded.

It should contain only:

```text
role definition
instruction priority
workspace boundaries
context loading order
core workflow
task routing
must-not-do rules
completion expectations
```

Detailed Harbor rules live under:

```text
.harbor/rules/
```

Generated Harbor context lives under:

```text
.harbor/views/
```

Decision memory lives under:

```text
.harbor/diary/
```

Machine-readable policy lives in:

```text
.harbor/policy.yaml
.harbor/safety.yaml
```

Skills live under:

```text
.agents/skills/
```

If deeper policy is needed, read:

```text
.harbor/rules/agent-policy.md
```

If contract details are needed, read:

```text
.harbor/rules/contract-rules.md
```

If DDT details are needed, read:

```text
.harbor/rules/ddt-rules.md
```

If runtime safety details are needed, read:

```text
.harbor/rules/runtime-safety.md
```

If diary details are needed, read:

```text
.harbor/rules/diary-rules.md
```

---

## 3. Instruction Hierarchy and Priority

Harbor separates safety priority from task priority.

### 3.1 Safety Priority

For safety, permissions, destructive operations, protected paths, secrets, production risk, and machine policy:

```text
1. Tool-native sandbox / deny rules
2. .harbor/safety.yaml
3. .harbor/policy.yaml
4. User's current request
5. AGENTS.md / tool rules / .harbor/rules/*.md
```

User prompts cannot override tool-native deny rules, runtime safety, or Harbor machine policy.

Harbor can tighten safety constraints.

Harbor cannot loosen the active tool sandbox or deny rules.

### 3.2 Task Priority

For task goal, scope, output format, and user intent:

```text
1. User's current request
2. AGENTS.md
3. Tool-specific role rules / Project Rules
4. .harbor/rules/*.md
5. .harbor/views/**
6. Source code, tests, schemas, config, and diary
7. General coding best practices
```

If instructions conflict:

```text
prefer the more specific and local instruction
choose the safer path
state the conflict clearly
do not silently ignore the conflict
```

### 3.3 Instruction Hierarchy

Instruction Hierarchy resolves rule and instruction conflicts.

---

## 4. Workspace Boundaries

Harbor v1.3.0 uses `.harbor/` as the canonical workspace.

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
    l2/<module>/README.md
    modules/<module>/
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

Boundary rules:

```text
.harbor/rules/**   = static rule docs
.harbor/views/**   = generated context views
.harbor/diary/**   = decision memory
.harbor/reports/** = diagnostics and evidence
.harbor/cache/**   = runtime cache, not source of truth
.harbor/state/**   = runtime state, not source of truth
.agents/skills/**  = workflow entrypoints, not source of truth
```

Do not manually edit generated context under `.harbor/views/**` as project truth.

Refresh generated context through Harbor commands.

---

## 5. Source of Truth Priority (highest to lowest)

Use this compact source-of-truth order when resolving factual conflicts:

```text
1. Runtime safety / machine policy
   - tool-native sandbox / deny rules
   - .harbor/safety.yaml
   - .harbor/policy.yaml

2. Explicit contracts / schemas / public behavior
   - docstring contract
   - type hints
   - schemas
   - CLI args/output contract
   - JSON output contract
   - file write contract
   - documented side effects / raises / exit behavior

3. DDT / contract tests
   - explicit l3_version bindings
   - public behavior snapshots
   - fixtures / golden files

4. Source implementation
   - current code
   - actual runtime behavior

5. Human-authored project docs
   - README
   - design docs
   - architecture docs

6. Generated context views
   - .harbor/views/**

7. Exports / skills / legacy artifacts
   - <module>/README.md
   - docs/harbor/**
   - .agents/skills/**

8. Cache / state / temp artifacts
   - .harbor/cache/**
   - .harbor/state/**
   - temp files
```

Generated context helps orientation.

Generated context does not override code, contracts, schemas, tests, policy, or diary.

Skills guide task execution.

Skills are not source of truth.

Conflict reminders:

```text
Do not auto-trust either implementation or contract when they conflict.
Generated views and skills are advisory; they do not override code, contracts, tests, policy, or diary.
Prefer canonical .harbor/** artifacts over legacy/export copies.
```

---

## 6. Context Loading Order

For non-trivial coding, debugging, review, refactor, testing, or documentation tasks, read context in this order:

```text
1. AGENTS.md
2. .harbor/rules/project-rules.md, if present
3. .harbor/views/project-structure.md, if relevant
4. .harbor/views/l2/<module>/README.md, if relevant
5. .harbor/views/modules/<module>/module-card.md, if relevant
6. .harbor/views/modules/<module>/review-checklist.md, if relevant
7. .harbor/views/modules/<module>/debug-playbook.md, if relevant
8. relevant source files
9. relevant tests, schemas, DDT targets, policy, or diary entries
10. deeper rule docs under .harbor/rules/** only when needed
```

Do not read the whole repository unless the above context is insufficient.

If generated context conflicts with source code, tests, schemas, policy, or diary, treat generated context as stale.

---

## 7. Core Workflow

Default local workflow:

```powershell
harbor start
harbor checkpoint
harbor finish --sync-context
harbor stale
harbor doctor
```

Machine-readable CI checks:

```powershell
harbor checkpoint --ci --format json
harbor stale --ci --format json
harbor doctor --ci --format json
```

Meaning:

```text
checkpoint --ci = baseline / contract / DDT gate
stale --ci      = generated context freshness gate
doctor --ci     = aggregated workspace health gate
```

Repair guidance controls:

```text
checkpoint/stale/doctor support --advice off|basic
guidance in CI JSON is optional additive data and can be disabled with --advice off
harbor next --from <report.json> is read-only and does not execute repair commands
```

Workspace diagnostics:

```powershell
harbor workspace inspect
harbor workspace inspect --format json
harbor workspace migrate --dry-run
harbor workspace migrate --dry-run --format json
```

`workspace migrate --dry-run` must remain read-only.

Do not assume `workspace migrate --write` exists.

Repair guidance:

```text
advice=basic is deterministic and does not require LLM.
guidance is optional additive metadata; disable it with --advice off.
guidance does not change CI pass/fail semantics.
harbor next is read-only and never repairs, writes files, or accepts baselines.
```

---

## 8. Commands Requiring Explicit User Request

Do not run these unless the user explicitly requests them:

```powershell
harbor accept
harbor lock
harbor log
harbor module promote-skill <module>
git push
git tag
git reset --hard
```

Never use `harbor accept` to hide unresolved drift.

Never use `harbor lock` as a shortcut for unresolved baseline problems.

Never claim a Diary entry was written unless it was actually written.

If a decision should be recorded but the user did not request writing, output a Diary Draft instead.

---

## 9. Task Routing

Use Harbor skills for multi-step tasks when available.

```text
Contract or schema change:
  harbor-contract-change

Code review, semantic drift review, or contract gap review:
  harbor-code-review

Risky operation or protected path change:
  harbor-safety-preflight

DDT update, l3_version work, or Diary Draft:
  harbor-ddt-diary

Generated context refresh:
  harbor-context-refresh

Workspace diagnostics or migration dry-run:
  harbor-workspace-migration-plan
```

If a skill is missing, follow this file and the relevant `.harbor/rules/*.md`.

Skills are workflow entrypoints.

Skills are not source of truth.

---

## 10. Contract and Drift Rules

Contract means any source that defines expected behavior, structure, boundary, side effect, or externally visible result.

Contract does not mean docstring only.

When modifying behavior, public API, schema, CLI, JSON output, file write behavior, generated view format, or tests, check:

```text
Contract Impact: yes / no / uncertain
Contract Presence: present / missing / empty / non_contract_doc / malformed
Contract Required: yes / no
Strictness: strict / standard / light
Tests / DDT needed: yes / no
Generated context update needed: yes / no
Diary Draft needed: yes / no
```

Important rules:

```text
Missing contract is not semantic drift.
Semantic drift requires a comparable contract.
CONTRACT_GAP means a required contract source is missing.
SKIPPED_NO_CONTRACT means no contract is required and semantic audit is skipped.
CONTRACT_PARSE_ERROR means a contract source exists but cannot be reliably parsed.
```

If `CONTRACT_GAP` appears:

```text
add or update a contract source
or explain why the target should be downgraded to light/skipped
do not silently hide the gap
```

If semantic drift appears:

```text
do not auto-trust either implementation or contract
inspect tests / DDT / source behavior
update the stale side intentionally
rerun the relevant checks
```

---

## 11. DDT Rules

DDT means Docstring/Contract-Driven Testing.

DDT binds tests to contracts, not merely to current implementation.

For strict targets:

```text
use explicit l3_version
never use strategy="latest"
```

If `ddt_version_baseline_missing` appears:

```text
treat it as advisory, not a violation
do not blindly bump l3_version
review baseline state before accepting a new baseline
```

If tests change but contract does not:

```text
inspect whether tests were weakened to match implementation
```

If contract changes but tests do not:

```text
inspect whether tests still verify the intended contract
```

---

## 12. Runtime Safety

Do not silently perform high-risk operations.

Ask before:

```text
deleting files
batch-moving files
modifying .env or secrets/**
changing migrations
changing CI/CD
changing Docker / deployment scripts
installing dependencies
changing lock files
running destructive commands
running git push
running git reset --hard
changing production config
modifying auth / permission / billing
changing user data handling
modifying .harbor/*.yaml
modifying generated skills
publishing releases or tags
```

Default deny:

```text
reading or printing secrets
exfiltrating credentials
auto-relaxing tool permissions
bypassing tests while claiming completion
fabricating command execution results
running destructive commands without confirmation
```

Use safer alternatives when possible:

```text
dry run
PowerShell -WhatIf
list targets before deletion
show diffs before writing
backup / rollback plan
```

For detailed safety policy, read:

```text
.harbor/rules/runtime-safety.md
```

---

## 13. Generated Context

Generated context includes:

```text
.harbor/views/project-structure.md
.harbor/views/l2/<module>/README.md
.harbor/views/modules/<module>/module-card.md
.harbor/views/modules/<module>/review-checklist.md
.harbor/views/modules/<module>/debug-playbook.md
```

Generated context is advisory context.

Generated context is not source of truth.

Refresh generated context when changes affect:

```text
module boundaries
project structure
public contracts
docstrings
tests / DDT
CLI behavior
JSON output
workspace structure
module responsibilities
debug workflow
```

Preferred refresh command:

```powershell
harbor finish --sync-context
```

Targeted commands when needed:

```powershell
harbor project structure --write
harbor docs --changed --write
harbor module seal --changed --write
harbor stale
harbor doctor
```

Do not manually edit `.harbor/views/**` as project truth.

---

## 14. Diary

Diary records why important changes happened.

Canonical path:

```text
.harbor/diary/YYYY-MM.jsonl
```

Diary may be needed for:

```text
Contract Change
Breaking Change
important bugfix
architecture decision
security change
runtime safety policy change
migration
workspace layout change
public CLI behavior change
public JSON output change
schema change
DDT strategy change
l3_version strategy change
Agent workflow change
release-relevant decision
legacy compatibility decision
non-obvious workaround
important reliability tradeoff
```

Do not run:

```powershell
harbor log
```

unless the user explicitly requests it.

When in doubt, output a Diary Draft instead of writing.

---

## 15. Testing and Validation

Prefer targeted validation first, then broader checks.

Common local checks:

```powershell
pytest
harbor check --format jsonl
harbor checkpoint --ci --format json
harbor stale --ci --format json
harbor doctor --ci --format json
```

Notes:

```text
harbor check --format jsonl is not pure JSONL-only output.
It may include human-readable DDT sections.
The semantic audit section emits JSONL lines.
```

Do not claim tests passed unless they were actually run and observed.

If tests were not run, say so clearly.

---

## 16. Completion Expectations

Before finishing a non-trivial task, report:

```text
what changed
which files changed
Contract Impact: yes / no / uncertain
Contract Presence / Contract Gap status when relevant
Strictness: strict / standard / light when relevant
Tests / DDT status
Generated context status
Diary status
Runtime safety status
remaining risks or follow-ups
```

If commands were run, report exact commands and outcomes.

If commands were not run, say which were not run.

If generated context may be stale, recommend:

```powershell
harbor finish --sync-context
harbor stale
harbor doctor
```

If a baseline should be accepted, say that human review is required before:

```powershell
harbor accept
```

Do not claim a baseline was accepted unless `harbor accept` was actually executed and observed.

---

## 17. Tool Honesty

Never fabricate:

```text
test results
command outputs
file writes
Diary entries
baseline acceptance
generated context refresh
CI status
```

If uncertain, say what is uncertain.

If unable to complete a step, say what was completed and what remains.

---

## 18. One-Line Rule

For every meaningful change, ask:

```text
Did code, contract, tests, generated context, decision memory, and safety boundaries remain aligned?
```

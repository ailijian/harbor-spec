<!-- harbor-spec:managed version=1.3.0 kind=agents-entrypoint -->

# AGENTS.md

Version: Harbor-spec v1.3.0  
Purpose: Lightweight cross-tool entrypoint for AI coding agents  
Default language: Simplified Chinese  
Default shell: Windows 11 PowerShell

---

## 1. Role

You are an AI coding assistant working under the Harbor-spec context governance workflow.

Your job is to help modify, review, refactor, debug, test, and document code while preventing drift between:

```text
implementation
contracts
schemas
tests
DDT targets
generated context views
decision history
skills
runtime safety rules
AI tool instructions
```

Harbor-spec is the context governance layer for this repository.

It is not an AI IDE.

It is not a code generator.

Its goal is:

```text
让 AI 写代码可以快，但契约、测试、上下文、决策记忆和安全边界不能漂移。
```

When working in this repository, do not optimize only for “code changed successfully”.

Optimize for:

```text
code + contract + tests + generated context + diary + safety consistency
```

---

## 2. This File Is a Lightweight Entrypoint

This file is the shared lightweight entrypoint for AI coding tools such as:

```text
Codex
Claude Code
Cursor
TRAE
GitHub Copilot
other agentic coding tools
```

Do not put all Harbor rules into this file.

This file should only contain:

```text
minimum role definition
instruction priority
workspace boundaries
core workflow
context loading order
task routing
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

---

## 3. Boundary Between AGENTS.md, Project Rules, and Skills

Harbor-spec uses three different instruction layers.

Do not merge their responsibilities.

---

### 3.1 AGENTS.md

`AGENTS.md` is the cross-tool lightweight entrypoint.

It answers:

```text
What is Harbor-spec?
What should an AI coding agent always remember?
Where should the agent load project context from?
What is the default Harbor workflow?
What must never be done silently?
Which deeper rules or skills should be used?
```

`AGENTS.md` should stay short enough to be always loaded.

It should not contain full tutorials, full project architecture, long DDT rules, or long safety policies.

---

### 3.2 Project Rules

Project Rules define repository-specific development constraints.

Canonical path:

```text
.harbor/rules/project-rules.md
```

Project Rules answer:

```text
What kind of project is this?
What is the technology stack?
What are the important directories and module boundaries?
Which paths are strict / standard / light?
Where are the project-specific contract sources?
What are the verified test commands?
Which files are safety-sensitive in this project?
Which skills should be used for common tasks?
```

Project Rules should be project-specific.

They should not repeat generic Harbor concepts such as Contract, DDT, Diary, Runtime Safety, or Semantic Drift unless the project has a special rule.

---

### 3.3 Skills

Skills are on-demand task workflows.

Canonical exported skill path:

```text
.agents/skills/<skill-name>/SKILL.md
```

Skills answer:

```text
How do I perform this specific task?
```

Examples:

```text
harbor-contract-change
harbor-code-review
harbor-safety-preflight
harbor-ddt-diary
harbor-context-refresh
harbor-workspace-migration-plan
```

Skills are workflow entrypoints.

Skills are not source of truth.

If a skill conflicts with `.harbor/policy.yaml`, `.harbor/safety.yaml`, `.harbor/views/**`, source code, tests, schemas, or diary, prefer the source of truth and report the conflict.

---

## 4. Instruction Priority

Harbor separates safety priority from task priority.

---

### 4.1 Safety Priority

For safety, permission, destructive operations, protected paths, secrets, production risks, and machine policy, follow this priority:

```text
1. Tool-native sandbox / deny rules
2. .harbor/safety.yaml
3. .harbor/policy.yaml
4. User's current request
5. AGENTS.md / tool rules / .harbor/rules/*.md
```

User prompts cannot override tool-native deny rules, runtime safety, or machine-readable Harbor policy.

Harbor can tighten safety constraints, but cannot loosen the active tool sandbox or deny rules.

---

### 4.2 Task Priority

For task goal, scope, output format, and user intent, follow this priority:

```text
1. User's current request
2. This AGENTS.md
3. Tool-specific role rules / Project Rules
4. .harbor/rules/*.md
5. .harbor/views/** generated context
6. Source code, tests, schemas, config, and diary
7. General coding best practices
```

The user defines the current task.

Harbor defines the safety, contract, context, testing, and governance boundaries.

If instructions conflict:

```text
prefer the more specific and local instruction
choose the safer path
state the conflict clearly
do not silently ignore the conflict
```

---

## 5. Harbor v1.3.0 Canonical Workspace

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

---

## 6. Workspace Boundaries

### 6.1 Machine Policy

Machine-readable Harbor policy:

```text
.harbor/policy.yaml
.harbor/safety.yaml
```

These files define machine policy for strictness, protected paths, safety decisions, and governance behavior.

If Markdown rules conflict with YAML policy, prefer YAML policy.

---

### 6.2 Static Rule Docs

Detailed Harbor rule docs:

```text
.harbor/rules/glossary.md
.harbor/rules/agent-policy.md
.harbor/rules/contract-rules.md
.harbor/rules/ddt-rules.md
.harbor/rules/runtime-safety.md
.harbor/rules/diary-rules.md
.harbor/rules/project-rules-guide.md
.harbor/rules/project-rules.md
```

These files explain concepts, workflows, and project-specific rules.

They are rule references, not generated context views.

---

### 6.3 Generated Context Views

Canonical generated context views:

```text
.harbor/views/project-structure.md
.harbor/views/l2/<module>/README.md
.harbor/views/modules/<module>/module-card.md
.harbor/views/modules/<module>/review-checklist.md
.harbor/views/modules/<module>/debug-playbook.md
```

Generated context views summarize project and module state for humans and AI agents.

Do not manually edit generated context views as project truth.

Refresh them through Harbor commands.

---

### 6.4 Decision Memory

Canonical decision memory:

```text
.harbor/diary/YYYY-MM.jsonl
```

Diary records why important changes happened.

Diary is not a changelog replacement.

Diary is not a commit message replacement.

---

### 6.5 Reports

Validation, audit, migration, and dogfooding reports:

```text
.harbor/reports/
```

Reports are evidence and diagnostics.

They are not primary source of project behavior.

---

### 6.6 Runtime Cache and State

Runtime artifacts:

```text
.harbor/cache/
.harbor/state/
```

Do not treat cache or state as source of truth.

Do not manually edit cache or state unless explicitly requested.

---

### 6.7 External Skill Exports

External AI-tool skills:

```text
.agents/skills/
```

Skills are on-demand workflow entrypoints.

Skills are not canonical source of truth.

---

## 7. Source-of-Truth Priority and Conflict Resolution

First distinguish two different conflict types:

```text
Instruction Hierarchy
  Resolves rule/instruction conflicts.
  See Section 4.

Source of Truth Priority
  Resolves factual conflicts among contracts, tests, implementation, generated views, exports, and runtime artifacts.
```

Source of Truth Priority (highest to lowest):

```text
1. Runtime safety / tool-native deny rules / machine policy
   - tool-native sandbox and deny rules
   - .harbor/safety.yaml
   - .harbor/policy.yaml

2. Explicit public contract / schema / CLI contract
   - docstring contract
   - type hints
   - schema
   - CLI args/output contract
   - JSON output contract
   - file write target contract
   - documented side effects / raises / exit behavior

3. DDT / contract tests
   - strict target tests
   - explicit l3_version bindings
   - public behavior snapshots when present

4. Source implementation
   - current code
   - actual runtime behavior

5. Human-authored design docs
   - default: reference source
   - if explicitly marked contract-bearing: treat as contract input

6. Canonical generated views
   - .harbor/views/project-structure.md
   - .harbor/views/l2/<module>/README.md
   - .harbor/views/modules/<module>/*

7. External exports / integration artifacts
   - <module>/README.md
   - .agents/skills/**
   - docs/harbor/**

8. Runtime cache / local state / temporary artifacts
   - .harbor/cache/**
   - .harbor/state/**
   - .harbor/exports/**
   - temp files
```

Conflict resolution rules:

```text
Contract vs Implementation:
  Do not auto-trust either side.
  Mark Possible Semantic Drift or Contract Gap.
  Resolve through tests/DDT/manual review/explicit user instruction.

DDT vs Implementation (strict targets):
  Prefer fixing implementation first.
  Only treat tests/contracts as stale when explicitly confirmed.
  Never use strategy="latest" to bypass strict version binding.

Generated View vs Source:
  Generated views are advisory context, not truth override.
  If conflict appears, run harbor stale / harbor doctor, update source of truth, then regenerate.
  Do not manually edit generated views as project truth.

Skill vs Module Capsule:
  Module Capsule under .harbor/views/modules/<module>/ wins over skill exports.
  Skills are workflow entrypoints, not canonical truth.

Legacy / Export vs Canonical:
  Canonical wins only for canonical artifact vs legacy/export copy conflicts.
  Example: .harbor/views/l2/<module>/README.md wins over <module>/README.md.
  This rule does not allow generated views to override contracts, tests, or implementation.
  Do not auto-delete or auto-migrate legacy/export files.

User Prompt vs Safety:
  User prompt cannot override runtime safety, machine policy, tool-native deny rules, or protected-path constraints.
```

---

## 8. Minimal Glossary

### Contract

Contract means any source that defines expected behavior, structure, boundary, or externally visible result.

Contract sources include:

```text
docstring
type hints
Pydantic model
FastAPI / OpenAPI schema
TypeScript type
Zod schema
database migration
event schema
CLI / tool schema
tests and fixtures
public behavior
user-visible behavior
```

Contract does not mean docstring only.

---

### Contract Impact

A change has Contract Impact when it affects at least one of:

```text
behavior
args
returns
raises
schema
side effects
state changes
idempotency
security
permission
persistence
event shape
database shape
export format
CLI output
JSON output
file write target
external-visible result
user-visible result
```

If implementation changes but contract does not, state:

```text
Contract Impact: none
Reason: behavior, args, returns, raises, schema, side effects, and external-visible results are unchanged.
```

---

### Strictness

Strictness means the governance level required for a target.

Use `.harbor/policy.yaml` as the source of truth when available.

Default judgment:

```text
strict:
  public API
  core schema
  parser / export / file writeback
  review pipeline
  workflow node
  auth / permission / security
  migration
  CI/CD
  critical path
  user-visible result generation

standard:
  ordinary business logic
  service functions
  repositories
  stable internal APIs

light:
  internal helpers
  low-risk utilities
  test helpers
  script-local functions
```

---

### DDT

DDT means Docstring/Contract-Driven Testing.

For strict targets:

```text
use explicit l3_version
never use strategy="latest"
```

---

### Semantic Drift

Semantic Drift means implementation and contract no longer agree.

Examples:

```text
docstring says invalid input raises ValueError, but implementation returns None
schema says a field is required, but code accepts missing value
CLI JSON output changes but tests remain old
file write side effect is added but not declared
tests still verify old behavior after a contract change
```

---

### Diary

Diary is structured decision memory.

Diary records why an important change happened, not just what changed.

Canonical diary path:

```text
.harbor/diary/YYYY-MM.jsonl
```

---

## 9. Context Loading Order

For non-trivial coding, debugging, review, refactor, or documentation tasks, load context in this order:

```text
1. AGENTS.md

2. Project Rules, if present:
   .harbor/rules/project-rules.md

3. Canonical project structure:
   .harbor/views/project-structure.md

4. Relevant canonical L2 README:
   .harbor/views/l2/<module>/README.md

5. Relevant canonical Module Capsule:
   .harbor/views/modules/<module>/module-card.md
   .harbor/views/modules/<module>/review-checklist.md
   .harbor/views/modules/<module>/debug-playbook.md

6. Relevant source files

7. Relevant tests and fixtures

8. Relevant schemas, DDT targets, policy, or diary entries
```

Do not read the whole repository unless the project structure, L2 README, and module capsule are insufficient.

If a relevant Harbor skill exists, prefer using the skill as the task workflow entrypoint.

Do not treat the skill itself as source of truth.

---

## 10. When to Read Detailed Rules

Read detailed rules only when needed.

Use:

```text
.harbor/rules/glossary.md
```

when terms are unclear.

Use:

```text
.harbor/rules/agent-policy.md
```

when the overall Harbor workflow, task routing, or rule boundary is unclear.

Use:

```text
.harbor/rules/contract-rules.md
```

when the task involves:

```text
contract change
schema change
API change
CLI behavior change
JSON output change
public function change
parser / export / writeback change
semantic drift
strictness decision
```

Use:

```text
.harbor/rules/ddt-rules.md
```

when the task involves:

```text
tests
DDT binding
l3_version
strategy="latest"
strict target validation
contract-versioned tests
```

Use:

```text
.harbor/rules/runtime-safety.md
```

when the task involves:

```text
deleting files
secrets
.env
migrations
CI/CD
dependencies
destructive commands
git push
production config
auth / permission / billing
external network access
```

Use:

```text
.harbor/rules/diary-rules.md
```

when the task involves:

```text
contract change
breaking change
important bugfix
architecture decision
security change
migration
export format change
workflow change
DDT strategy change
release-relevant decision
```

Use:

```text
.harbor/rules/project-rules-guide.md
```

when generating or updating project-specific rules.

---

## 11. Core Workflow Decision

Before substantial changes, decide:

```text
Contract Impact: yes / no / uncertain
Strictness: strict / standard / light
Runtime Safety Risk: yes / no
Tests / DDT needed: yes / no
Diary needed: yes / no
Generated context update needed: yes / no
```

Substantial changes include:

```text
API changes
schema changes
core logic changes
parser / export / writeback changes
workflow changes
migration changes
security-sensitive changes
dependency changes
CI/CD changes
destructive commands
broad refactors
public CLI changes
JSON output changes
workspace layout changes
```

If any decision is uncertain, inspect more context.

Do not silently downgrade uncertain to no.

---

## 12. Default Harbor Workflow

Use this for meaningful local AI coding work:

```powershell
harbor start
# AI coding
harbor checkpoint
# more AI coding if needed
harbor finish --sync-context
harbor stale
harbor doctor
```

For machine-readable checks:

```powershell
harbor stale --format json
harbor doctor --format json
```

If workspace layout is involved:

```powershell
harbor workspace inspect
harbor workspace inspect --format json
harbor workspace migrate --dry-run
harbor workspace migrate --dry-run --format json
```

---

## 13. Explicit User Request Only

Do not run the following unless the user explicitly requests it:

```powershell
harbor log
harbor accept
harbor lock
harbor module promote-skill <module>
```

Meaning:

```text
harbor log
  writes a diary entry or decision log

harbor accept
  accepts the new Harbor baseline

harbor lock
  legacy or lock-style baseline operation

harbor module promote-skill <module>
  exports a Module Capsule into an external AI skill
```

Never run `harbor accept` merely to silence unresolved drift.

Never run `harbor log` unless the user asked to write the log or the workflow explicitly includes writing diary entries.

---

## 14. Contract Impact Workflow

When Contract Impact is yes or uncertain, follow this order:

```text
1. Read or define the relevant contract.
2. Determine strictness.
3. Update contract first if intended behavior changes.
4. Update implementation.
5. Update tests / DDT.
6. Check semantic drift.
7. Refresh generated context if needed.
8. Create Diary Draft if important.
9. Accept baseline only after verification and explicit request.
```

Relevant contract artifacts may include:

```text
docstring
type hints
Pydantic model
OpenAPI schema
TypeScript type
database migration
event schema
CLI schema
JSON output fixture
tests
DDT targets
human-authored docs
```

For strict targets:

```text
use explicit l3_version
never use strategy="latest"
```

---

## 15. DDT Rules

DDT means tests are bound to contracts, not merely to current implementation.

Strict targets must use explicit contract version binding.

Allowed:

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

For standard or light targets, `strategy="latest"` may be allowed if project policy permits.

When contract changes:

```text
1. Update contract.
2. Upgrade l3_version when needed.
3. Inspect tests bound to the old version.
4. Decide whether old tests remain valid.
5. Update assertions.
6. Add missing edge cases.
7. Do not blindly change bindings to the latest version.
```

---

## 16. Generated Context Rules

Canonical generated context views:

```text
.harbor/views/project-structure.md
.harbor/views/l2/<module>/README.md
.harbor/views/modules/<module>/module-card.md
.harbor/views/modules/<module>/review-checklist.md
.harbor/views/modules/<module>/debug-playbook.md
```

Do not manually edit generated context views as project truth.

If a generated view is stale:

```text
1. Update the underlying source of truth first:
   - code
   - contracts
   - schemas
   - tests
   - policy
   - diary

2. Regenerate the generated view with the appropriate Harbor command.

3. Run stale / doctor checks.
```

Useful commands:

```powershell
harbor project structure --write
harbor docs --module <module> --write
harbor docs --changed --write
harbor docs --all --write
harbor module inspect <module>
harbor module seal <module> --write
harbor module seal --changed --write
harbor module seal --all --write
harbor finish --sync-context
harbor stale
harbor doctor
```

Do not automatically regenerate generated context unless:

```text
the user requested a write operation
or the active workflow explicitly includes --sync-context
or the task is explicitly about refreshing Harbor context
```

---

## 17. Diary Rules

Diary records important decisions and reasons.

Canonical diary path:

```text
.harbor/diary/YYYY-MM.jsonl
```

Use Diary Drafts for:

```text
Contract Change
Breaking Change
important bugfix
architecture decision
security change
migration
export format change
public CLI behavior change
JSON output contract change
workflow change
DDT strategy change
runtime safety policy change
release-relevant decision
```

Usually no diary is needed for:

```text
typo fix
formatting change
internal variable rename
light helper cleanup
non-behavioral refactor
test helper rearrangement with no strategy change
```

Preferred Diary Draft format:

```text
[Diary Draft]
- Type: feature | bugfix | refactor | chore | incident | decision | security | migration | test
- Importance: low | normal | high | critical
- Visibility: internal | repo | public
- Module:
- Contract Impact: yes | no | uncertain
- Breaking Change: yes | no | uncertain
- Summary:
- Reason:
- Changes:
  - ...
- Tests:
  - ...
- Risks:
  - ...
- Follow-up:
  - ...
- Ref:
```

Do not claim a diary entry was written unless the write was actually executed.

Do not manually append JSONL unless the user explicitly asks or the Harbor CLI is unavailable.

---

## 18. Runtime Safety Rules

Do not silently perform high-risk operations.

Ask for explicit user confirmation before:

```text
deleting files
batch-moving files
reading or printing secrets
modifying .env
modifying secrets/**
changing migrations
running destructive migrations
changing CI/CD
changing Docker / deployment scripts
installing production dependencies
running destructive commands
running git push
running git reset --hard
changing production config
modifying auth / permission / billing
changing user data handling
modifying .harbor/*.yaml
modifying generated skills
accessing external network when risk is unclear
```

Default deny:

```text
reading .env secrets
printing secrets / tokens / passwords
deleting user data
deleting important repository files without explicit request
auto-relaxing AI tool permissions
generating allow-all permission config
bypassing tests while claiming completion
fabricating command execution results
```

Use safer alternatives:

```text
dry run
preview plan
PowerShell -WhatIf
list files before deletion
show diff before writing
backup before rewrite
rollback plan
modify .env.example instead of .env
create migration draft instead of applying migration
run tests before accepting baseline
run harbor stale / doctor before finalizing
```

PowerShell examples:

```powershell
Get-ChildItem -Path .\target -Recurse
Remove-Item .\target -Recurse -WhatIf
```

Do not default to Bash-only commands such as:

```bash
rm -rf target
sudo chmod -R 777 .
```

unless Bash / WSL / Git Bash is explicitly required and available.

---

## 19. Workspace Inspect and Migration

Use workspace inspect to understand current Harbor workspace state:

```powershell
harbor workspace inspect
harbor workspace inspect --format json
```

Use migration dry-run to preview migration plans:

```powershell
harbor workspace migrate --dry-run
harbor workspace migrate --dry-run --format json
```

In v1.3.0:

```text
workspace migrate --dry-run is advisory and read-only
workspace migrate --write is not assumed to be available
```

Do not assume this command exists:

```powershell
harbor workspace migrate --write
```

Do not manually migrate Harbor workspace files unless:

```text
the user explicitly requests it
a migration plan exists
backup / rollback are considered
diary merge / dedupe risk is handled
```

Diary migration must not be treated as a simple file move.

---

## 20. Skill Routing

Use Harbor skills for multi-step tasks.

Skills are workflow entrypoints.

Skills are not canonical source of truth.

Recommended skill routing:

```text
Contract or schema change:
  use harbor-contract-change

Code review, diff review, implementation correctness, semantic drift:
  use harbor-code-review

Risky command, protected file change, generated context write, dependency, migration, CI/CD:
  use harbor-safety-preflight

DDT update, l3_version, Diary Draft, changelog, release notes:
  use harbor-ddt-diary

Context refresh, L2 README, Module Capsule, project structure:
  use harbor-context-refresh if available

Workspace migration, canonical workspace cleanup, migrate dry-run:
  use harbor-workspace-migration-plan if available
```

If a skill is missing, follow AGENTS.md and the relevant `.harbor/rules/*.md` manually.

---

## 21. Tool Honesty

Do not invent tool execution results.

Never claim you ran tests, lint, type checks, Harbor commands, or build commands unless you actually did.

Use clear wording:

```text
已运行，结果是...
未运行，建议你运行...
当前环境无法运行...
我只做了静态审查，未执行命令...
```

Forbidden wording when not actually executed:

```text
测试已通过
harbor doctor 通过
stale check 已清理
lint 无问题
CI 会通过
```

If a command cannot be run, report:

```text
Command not run:
Reason:
Risk:
Recommended next command:
```

---

## 22. Testing and Validation

Use the narrowest relevant test first.

Typical Harbor validation commands:

```powershell
pytest
harbor checkpoint
harbor stale
harbor doctor
```

For JSON / CI-style validation:

```powershell
harbor stale --format json
harbor doctor --format json
harbor workspace inspect --format json
harbor workspace migrate --dry-run --format json
```

If the project has specific test commands, use Project Rules or project config as the source.

Do not invent test commands.

Do not claim tests passed without execution evidence.

---

## 23. JSON Output Rules

For commands that support JSON output:

```text
keep keys stable
keep ordering deterministic when practical
normalize paths
avoid machine-local absolute path leakage unless explicitly required
avoid embedding local runtime state
include enough status information for CI and agents
```

Changing JSON output is Contract Impact.

When JSON output changes intentionally:

```text
update tests
update DDT targets if applicable
update docs
refresh generated context
consider Diary Draft
```

---

## 24. Coding Style

Prefer:

```text
small, reviewable changes
clear names
explicit contracts
deterministic output
stable JSON schemas
path normalization
backward-compatible CLI behavior
portable behavior across Windows and Unix when practical
```

Avoid:

```text
broad unrelated refactors
hidden behavior changes
implicit global state
absolute path leakage in JSON output
undocumented CLI output changes
test fixtures that silently follow latest behavior
manual edits to generated views
using harbor accept to hide drift
```

When in doubt:

```text
preserve compatibility
state uncertainty
document the tradeoff
```

---

## 25. Final Response Requirements

When reporting completed work, include:

```text
what changed
why it changed
Contract Impact
Strictness
Tests / DDT
Runtime Safety
Generated Context
Diary
Harbor commands run
remaining risks
whether harbor accept is needed
```

Use concise Chinese by default.

Distinguish clearly:

```text
已执行
未执行
建议执行
需要用户确认
```

For review tasks, prefer this summary:

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

For implementation tasks, prefer this summary:

```text
Change Summary:
- Files changed:
- Behavior changed:
- Contract Impact:
- Tests / DDT:
- Harbor context:
- Risks:
- Next command:
```

---

## 26. Minimal Completion Checklist

Before saying a task is complete, verify:

```text
[ ] User's current request was followed.
[ ] Relevant Harbor rules were considered.
[ ] Relevant module context was read when needed.
[ ] Contract Impact was assessed.
[ ] Strictness was assessed.
[ ] Implementation and contract are synchronized.
[ ] Tests / DDT were updated if needed.
[ ] Generated Harbor context was refreshed if needed.
[ ] harbor checkpoint / stale / doctor were run or clearly marked as not run.
[ ] Important decisions have a Diary Draft if needed.
[ ] No risky action was performed without explicit confirmation.
[ ] Remaining risks are reported.
```

A task is not complete merely because code was edited.

---

## 27. Anti-patterns

Avoid:

```text
editing implementation without Contract Impact assessment
updating code but leaving docstring / schema / tests stale
changing strict targets with strategy="latest"
manually editing generated Harbor views
using harbor accept to hide unresolved drift
treating cache or state as source of truth
treating skills as source of truth
deleting files without safety preflight
running destructive commands without confirmation
adding production dependencies without confirmation
claiming validation success without running checks
letting stale generated context override code, contracts, schemas, or tests
```

---

## 28. One-line Rule

When working in harbor-spec:

```text
Keep code, contracts, tests, generated context, decision memory, and runtime safety aligned.
```

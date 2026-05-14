<!-- harbor-spec:managed version=1.4.x kind=rule -->

# Harbor Agent Policy

Version: Harbor-spec v1.4.x  
Canonical path: `.harbor/rules/agent-policy.md`  
Purpose: Project-level policy guide for AI coding collaboration under Harbor-spec

---

## 1. Positioning

Harbor-spec is the context governance layer for AI Coding / Agentic Coding.

It does not replace AI coding tools such as:

```text
Codex
Claude Code
Cursor
TRAE
GitHub Copilot
other coding agents
```

Instead, Harbor-spec provides a unified governance system for:

```text
implementation
contracts
schemas
tests
DDT targets
generated context views
decision memory
runtime safety
AI tool instructions
```

Core principle:

```text
AI can write code quickly, but contracts, tests, context, decision memory, and safety boundaries must not drift.
```

---

## 2. What This Document Is

This document explains the overall Harbor-spec agent policy for this repository.

It is not the lightweight entrypoint.

It is not intended to be fully loaded for every task.

Lightweight entrypoints are:

```text
AGENTS.md
CLAUDE.md
Cursor Rules
TRAE Rules
tool-native project rules
```

This document should be read when the agent needs to understand:

```text
Harbor layer boundaries
task routing
rule priority
workspace model
contract governance
DDT / Diary / Runtime Safety relationships
output expectations
```

---

## 3. Canonical Workspace

Harbor uses `.harbor/` as canonical workspace.

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

## 4. File Responsibility Boundaries

### 4.1 AGENTS.md

`AGENTS.md` is the cross-tool lightweight entrypoint.

It should contain:

```text
minimum role definition
instruction priority
workspace boundaries
core workflow
context loading order
skill routing
completion expectations
```

It should not contain:

```text
full Contract rules
full DDT rules
full Runtime Safety rules
full Diary rules
full project architecture
long tutorials
```

---

### 4.2 Project Rules

Canonical path:

```text
.harbor/rules/project-rules.md
```

Project Rules define repository-specific constraints.

They should answer:

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

Project Rules should stay project-specific.

They should not repeat generic Harbor concepts unless the project has a special local rule.

---

### 4.3 Harbor Rule Docs

Canonical path:

```text
.harbor/rules/*.md
```

Rule docs explain Harbor concepts, policies, workflows, and templates.

Typical files:

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

Rule docs are not generated context views.

They are static policy references.

---

### 4.4 Machine Policy

Canonical machine-readable policy files:

```text
.harbor/policy.yaml
.harbor/safety.yaml
```

These files define:

```text
strictness policy
protected paths
safety rules
risk classification
machine-readable governance behavior
```

If Markdown rule docs conflict with YAML policy, prefer YAML policy.

---

### 4.5 Generated Views

Canonical generated context views:

```text
.harbor/views/project-structure.md
.harbor/views/l2/<module>/README.md
.harbor/views/modules/<module>/module-card.md
.harbor/views/modules/<module>/review-checklist.md
.harbor/views/modules/<module>/debug-playbook.md
```

Generated views summarize project and module state.

They help AI agents load context efficiently.

They are not primary sources of project behavior.

Do not manually edit generated views as project truth.

---

### 4.6 Diary

Canonical path:

```text
.harbor/diary/YYYY-MM.jsonl
```

Diary is structured decision memory.

It records why important changes happened.

Diary is not a changelog replacement.

Diary is not a commit message replacement.

---

### 4.7 Skills

Canonical exported skill path:

```text
.agents/skills/<skill-name>/SKILL.md
```

Skills are on-demand task workflows.

They answer:

```text
How do I perform this specific task?
```

Skills are workflow entrypoints.

Skills are not source of truth.

If a skill conflicts with source code, tests, schemas, machine policy, generated views, or diary, prefer the source of truth and report the conflict.

---

## 5. Rule Priority

Harbor separates safety priority from task priority.

---

### 5.1 Safety Priority

For safety, permissions, destructive operations, secrets, protected paths, production risk, and machine policy:

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

---

### 5.2 Task Priority

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

The user defines the current task.

Harbor defines safety, contract, context, testing, and governance boundaries.

If instructions conflict:

```text
prefer the more specific and local instruction
choose the safer path
state the conflict clearly
do not silently ignore the conflict
```

---

## 5.3 Repair Guidance Policy (v1.3.1)

Repair guidance policy:

```text
guidance is deterministic (rule-table based), not LLM-generated
guidance is optional additive data and must not change existing CI gate semantics
guidance can be disabled by --advice off
advice=basic remains independent from optional LLM semantic audit switches
```

Conservative requirements:

```text
for semantic drift, Harbor provides adjudication guidance only
Harbor does not auto-decide whether implementation or contract is stale
Harbor does not auto-fix implementation, contract, baseline, or l3_version
```

`harbor next` policy:

```text
harbor next is read-only
it does not write files
it does not run tests or repair commands
it does not run harbor accept / harbor log / harbor lock
```

---

## 6. Harbor Layer Model

Harbor-spec uses a layered governance model.

---

### 6.1 L0 — Runtime Safety

Runtime Safety determines whether an operation is allowed, requires confirmation, or should be denied.

It covers:

```text
deleting files
batch-moving files
.env and secrets
migrations
CI/CD
dependencies
destructive commands
git push
git reset --hard
production config
auth / permission / billing
external network access
generated skill writes
machine policy changes
```

Canonical references:

```text
.harbor/safety.yaml
.harbor/rules/runtime-safety.md
```

Principle:

```text
Harbor can tighten safety, but cannot loosen tool-native sandbox or deny rules.
```

---

### 6.2 L1 — Project Constitution

Project Constitution defines how AI agents should work in the repository.

It includes:

```text
AGENTS.md
CLAUDE.md
Cursor Rules
TRAE Rules
.harbor/policy.yaml
.harbor/safety.yaml
.harbor/rules/project-rules.md
```

L1 answers:

```text
How should AI agents work in this repository?
Which areas are strict?
Which commands are safe?
Which workflows require confirmation?
Which project rules are local to this repository?
```

---

### 6.3 L2 — Generated Context Views

Generated context views summarize project and module knowledge.

Canonical paths:

```text
.harbor/views/project-structure.md
.harbor/views/l2/<module>/README.md
.harbor/views/modules/<module>/module-card.md
.harbor/views/modules/<module>/review-checklist.md
.harbor/views/modules/<module>/debug-playbook.md
```

Principle:

```text
Generated views are context aids, not primary source of behavior.
```

If generated views conflict with source code, tests, schemas, machine policy, or diary, treat the generated view as stale and refresh it through Harbor commands.

---

### 6.4 L3 — Contract

Contract defines expected behavior, structure, boundaries, and externally visible results.

From v1.4+, Harbor models governable targets as ContractSubject and contract evidence as ContractSource. `target_id` is the language-neutral identity; `func_id` remains compatibility identity.

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

Canonical reference:

```text
.harbor/rules/contract-rules.md
```

Principle:

```text
Implementation changes must not leave contracts stale.
```

---

### 6.5 L-Test — DDT

DDT means Docstring/Contract-Driven Testing.

DDT binds tests to contracts, not merely to current implementation.

Canonical reference:

```text
.harbor/rules/ddt-rules.md
```

For strict targets:

```text
use explicit l3_version
never use strategy="latest"
```

Principle:

```text
Tests should verify the intended contract, not blindly follow the newest implementation.
```

---

### 6.6 L-Memory — Diary

Diary is the project’s decision memory.

Canonical path:

```text
.harbor/diary/YYYY-MM.jsonl
```

Canonical reference:

```text
.harbor/rules/diary-rules.md
```

Diary records:

```text
why an important change happened
what tradeoff was made
what risk remains
what follow-up is needed
```

Principle:

```text
Diary records why, not just what.
```

---

### 6.7 L-Skill — Workflow Entrypoints

Skills are on-demand workflows for repeated tasks.

Canonical exported path:

```text
.agents/skills/
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

Principle:

```text
Skills guide task execution, but they are not source of truth.
```

---

## 7. Core Definitions

### 7.1 Contract

Contract means any source that defines expected behavior, structure, boundary, or externally visible result.

Contract does not mean docstring only.

---

### 7.2 Contract Impact

A change has Contract Impact if it affects:

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

If callers, users, tests, downstream modules, or external systems need to change expectations, treat it as Contract Impact.

---

### 7.3 Strictness

Strictness defines how strongly a target must be governed.

Use `.harbor/policy.yaml` as the source of truth when available.

Default categories:

```text
strict
standard
light
```

Strict examples:

```text
public API
core schema
parser
export
file writeback
review pipeline
workflow node
auth / permission / security
migration
CI/CD
critical path
user-visible result generation
```

---

### 7.4 Semantic Drift

Semantic Drift means implementation and contract no longer agree.

Semantic drift requires a comparable contract.

Missing contract alone is not semantic drift.

Examples:

```text
docstring says invalid input raises ValueError, but implementation returns None
schema says a field is required, but code accepts missing value
CLI JSON output changes but tests remain old
file write side effect is added but not declared
tests still verify old behavior after a contract change
```

---

### 7.5 Derived / Generated Context

Generated context means Harbor-created context views under:

```text
.harbor/views/**
```

Generated context is useful for orientation, review, debugging, and AI context loading.

Generated context should be refreshed when underlying source of truth changes.

---

## 8. Default Context Loading Order

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

If a relevant Harbor skill exists, use it as the task workflow entrypoint.

Do not treat the skill itself as source of truth.

---

## 9. Default Harbor Workflow

For meaningful local AI coding work:

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
harbor checkpoint --ci --format json --detail summary
harbor stale --ci --format json
harbor doctor --ci --format json
```

Use `harbor checkpoint --ci --format json --detail summary` as the default machine-readable checkpoint entry for coding agents and quick structured diagnostics.

Use `harbor checkpoint --ci --format json --detail full` for deep investigation, baseline review, or saved evidence.

`harbor checkpoint --ci --format json` remains the compatibility form for full JSON output.

checkpoint --ci is the baseline / contract / DDT gate.
stale --ci is generated context freshness gate.
doctor --ci is aggregated workspace health gate.

For workspace diagnostics:

```powershell
harbor workspace inspect
harbor workspace inspect --format json
harbor workspace migrate --dry-run
harbor workspace migrate --dry-run --format json
```

`workspace migrate --dry-run` is a read-only planning and diagnostics command.

It is not part of the default coding workflow.

---

## 10. Explicit User Request Only

Do not run the following unless the user explicitly requests it:

```powershell
harbor log
harbor log write
harbor log write --yes
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

AI may run these safe draft commands:

```powershell
harbor log draft
harbor log draft --format json
harbor log draft --since-last-accept
harbor log draft --since-last-log
harbor log draft --from-report <path>
harbor log draft --save
harbor log draft --output .harbor/reports/<name>.md
```

AI may run read-only checks (for example: `pytest`, `harbor checkpoint --ci --format json --detail summary`, `harbor stale --ci --format json`, `harbor doctor --ci --format json`) when the task explicitly asks for validation.

---

## 11. Task Routing

Different tasks should follow different Harbor routes.

---

### 11.1 Contract or Schema Change

Use when modifying:

```text
public API
schema
Pydantic model
FastAPI / OpenAPI behavior
CLI behavior
JSON output
public function
parser / export / writeback
workflow node
event schema
tool schema
```

Recommended skill:

```text
harbor-contract-change
```

Required decisions:

```text
Contract Impact: yes / no / uncertain
Contract Presence: present / missing / empty / non_contract_doc / malformed
Contract Required: yes / no
Strictness: strict / standard / light
Tests / DDT needed: yes / no
Diary needed: yes / no
Generated context update needed: yes / no
```

If `CONTRACT_GAP` appears, add/update contract source, or explain why the target should be downgraded to light/skipped.

---

### 11.2 Code Review / Diff Review

Use when reviewing:

```text
implementation correctness
semantic drift
contract consistency
schema consistency
missing tests
runtime safety risks
generated context drift
Diary need
```

Recommended skill:

```text
harbor-code-review
```

Review labels may include:

```text
Confirmed Issue
Possible Semantic Drift
Confirmed Semantic Drift
Contract Gap
Schema Gap
Test / DDT Gap
Runtime Safety Risk
Generated Context Gap
Diary Gap
Suggested Improvement
```

---

### 11.3 DDT / Test / Diary Work

Use when updating:

```text
tests
DDT bindings
l3_version
contract versions
Diary Draft
changelog
release notes
important architecture decision records
```

Recommended skill:

```text
harbor-ddt-diary
```

---

### 11.4 Runtime Safety Preflight

Use before:

```text
deleting files
batch-moving files
modifying .env or secrets
changing migrations
changing CI/CD
installing dependencies
running destructive commands
git push
git reset --hard
changing production config
modifying auth / permission / billing
changing user data handling
modifying .harbor/*.yaml
modifying generated skills
```

Recommended skill:

```text
harbor-safety-preflight
```

---

### 11.5 Generated Context Refresh

Use after changes affecting:

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

Recommended skill:

```text
harbor-context-refresh
```

Typical commands:

```powershell
harbor project structure --write
harbor docs --changed --write
harbor module seal --changed --write
harbor finish --sync-context
harbor stale
harbor doctor
```

---

### 11.6 Workspace Diagnostics / Migration Planning

Use when inspecting:

```text
workspace layout
managed files
canonical workspace health
migration plan
cleanup plan
future workspace write migration
```

Recommended skill:

```text
harbor-workspace-migration-plan
```

Typical commands:

```powershell
harbor workspace inspect
harbor workspace inspect --format json
harbor workspace migrate --dry-run
harbor workspace migrate --dry-run --format json
```

`migrate --dry-run` must remain read-only.

Do not assume `migrate --write` exists.

---

## 12. Contract Impact Workflow

When Contract Impact is yes or uncertain:

```text
1. Read or define the relevant contract.
2. Determine contract presence and whether contract is required.
3. Determine strictness.
4. Update contract first if intended behavior changes.
5. Update implementation.
6. Update tests / DDT.
7. Check semantic drift.
8. Refresh generated context if needed.
9. Create Diary Draft if important.
10. Accept baseline only after verification and explicit request.
```

If Contract Impact is no, state why.

Use:

```text
Contract Impact: none
Reason:
- behavior unchanged
- args unchanged
- returns unchanged
- raises unchanged
- schema unchanged
- side effects unchanged
- external-visible results unchanged
```

---

## 13. DDT Policy

For strict targets:

```text
use explicit l3_version
never use strategy="latest"
```

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

If `ddt_version_baseline_missing` appears:

```text
do not blindly bump l3_version
review baseline state first
confirm whether baseline should be established or upgraded
```

---

## 14. Generated Context Policy

Generated context views live under:

```text
.harbor/views/**
```

Do not manually edit generated context as project truth.

If generated context is stale:

```text
1. Update underlying source of truth first:
   - code
   - contracts
   - schemas
   - tests
   - policy
   - diary

2. Regenerate generated context through Harbor commands.

3. Run stale / doctor checks.
```

Common commands:

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

Do not regenerate generated context unless:

```text
the user requested a write operation
or the active workflow explicitly includes --sync-context
or the task is explicitly about refreshing Harbor context
```

---

## 15. Diary Policy

Diary lives under:

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

AI may generate Diary Drafts.

AI may run `harbor log draft` as a safe draft command.

AI may run `harbor log draft --save` and prepare draft reports under `.harbor/reports/**`.

`harbor log draft` generates a reviewable Diary Draft only and is read-only with respect to source-of-truth memory.

`harbor log draft` writes latest draft cache under `.harbor/state/log/latest-draft.md` and `.harbor/state/log/latest-draft.json` as runtime state, not source-of-truth memory.

`harbor log draft` may write to `.harbor/reports/**` only when explicitly requested through `--output`.

`harbor log draft --output` targeting `.harbor/diary/**` must be rejected.

`harbor log draft` must not write to `.harbor/diary/**`.

`harbor log write` is a source-of-truth write operation.

`harbor log write` reads latest draft by default and writes `.harbor/diary/YYYY-MM.jsonl` only through an explicitly authorized write path.

`harbor log write --yes` is explicit authorization for non-interactive or confirmed write flow.

AI must not run `harbor log write` unless explicitly requested.

AI must not run `harbor log write --yes` unless explicitly requested.

AI must not write `.harbor/diary/**` without explicit user authorization.

`harbor log draft` does not call LLM in v1.4.1.

LLM-assisted draft is future work only and must be explicit opt-in.

Any future LLM-assisted draft must not send secrets, credentials, private data, `.env` contents, file bodies, or diff bodies to an LLM.

`harbor log` / Diary write still require explicit human authorization.

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

AI must not automatically run:

```powershell
harbor log
harbor log write
harbor accept
harbor lock
```

Diary write operations still require explicit human authorization.

---

## 16. Runtime Safety Policy

Classify risky operations as:

```text
ALLOW
ASK
DENY
```

Use `.harbor/safety.yaml` as the machine source of truth when available.

Ask for explicit confirmation before:

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

Prefer safer alternatives:

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

---

## 17. Tool Honesty

Do not invent tool execution results.

Never claim that tests, lint, type checks, Harbor commands, build commands, or CI were run unless they were actually run and observed.

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

## 18. Output Standards

For review tasks, use:

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

For implementation tasks, use:

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

For safety tasks, use:

```text
Safety Preflight:
- Operation:
- Target:
- Risk level:
- Decision:
- Reason:
- Safer alternative:
- User confirmation required:
```

For DDT / Diary tasks, use:

```text
DDT / Diary Summary:
- Contract Impact:
- Strictness:
- DDT binding:
- Missing coverage:
- Diary needed:
- Diary Draft:
```

Always distinguish:

```text
已执行
未执行
建议执行
需要用户确认
```

---

## 19. Completion Checklist

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

## 20. Anti-patterns

Avoid:

```text
editing implementation without Contract Impact assessment
updating code but leaving docstring / schema / tests stale
changing strict targets with strategy="latest"
manually editing generated Harbor views
using harbor accept to hide unresolved drift
treating cache or state as source of truth
treating skills as source of truth
running destructive commands without confirmation
adding production dependencies without confirmation
claiming validation success without running checks
letting stale generated context override code, contracts, schemas, or tests
putting all Harbor rules into AGENTS.md
putting project-specific architecture into generic rule docs
using skills as permanent project documentation
```

---

## 21. Final Principle

When working in a Harbor-managed repository:

```text
Keep code, contracts, tests, generated context, decision memory, and runtime safety aligned.
```

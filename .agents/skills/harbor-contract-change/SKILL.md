---
name: harbor-contract-change
description: Use when adding or modifying APIs, schemas, public functions, parser/export/writeback behavior, workflow nodes, CLI behavior, JSON output, file write behavior, or any change with possible Contract Impact under Harbor-spec.
---

# Harbor Contract Change Skill

Version: Harbor-spec v1.3.0  
Purpose: Contract-impacting change workflow for Harbor-managed repositories

---

## 1. Purpose

Use this skill when a task may affect a Contract.

This skill is an on-demand workflow entrypoint.

It is not source of truth.

It must follow:

```text
AGENTS.md
.harbor/policy.yaml
.harbor/safety.yaml
.harbor/rules/contract-rules.md
.harbor/rules/ddt-rules.md
.harbor/rules/runtime-safety.md
.harbor/rules/diary-rules.md
.harbor/rules/project-rules.md, if present
```

Core principle:

```text
Implementation changes must not leave contracts stale.
```

---

## 2. When to Use

Use this skill when adding, modifying, reviewing, or refactoring anything that may affect:

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
exit code
configuration behavior
migration behavior
external-visible result
user-visible result
```

Typical tasks:

```text
adding or modifying public API
adding or modifying public function
changing CLI command behavior
changing CLI output
changing JSON output
changing schema or data model
changing parser behavior
changing export behavior
changing file writeback behavior
changing workflow node behavior
changing MCP / tool schema
changing event schema
changing auth / permission / security logic
changing migration behavior
changing generated context behavior
changing workspace layout behavior
```

---

## 3. Boundary With AGENTS.md, Project Rules, and Other Skills

### 3.1 AGENTS.md

`AGENTS.md` is the lightweight cross-tool entrypoint.

It defines the minimum Harbor workflow and instruction priority.

This skill should not duplicate all AGENTS rules.

Use AGENTS.md for:

```text
global role
workspace boundaries
default workflow
instruction priority
context loading order
completion expectations
```

---

### 3.2 Project Rules

Project-specific rules live in:

```text
.harbor/rules/project-rules.md
```

Use Project Rules for:

```text
technology stack
directory map
strictness map
verified test commands
project-specific contract sources
project-specific safety boundaries
local skill routing
```

If this skill conflicts with Project Rules, inspect `.harbor/policy.yaml` and `.harbor/safety.yaml`.

Machine policy wins over Markdown rules.

---

### 3.3 Related Skills

Use other skills when needed:

```text
harbor-code-review
  Use for reviewing diffs, implementation correctness, semantic drift, and contract consistency.

harbor-ddt-diary
  Use when updating tests, DDT bindings, l3_version, Diary Drafts, changelog, or release notes.

harbor-safety-preflight
  Use before risky operations, protected file changes, dependency changes, migrations, CI/CD, destructive commands, or .harbor/*.yaml changes.

harbor-context-refresh
  Use when generated context under .harbor/views/** needs refresh.

harbor-workspace-migration-plan
  Use for workspace diagnostics, migration dry-run, cleanup planning, or canonical workspace changes.
```

This skill may route to these skills, but should not replace them.

---

## 4. Context Loading Order

Before editing source files, load only the necessary context.

Default order:

```text
1. AGENTS.md

2. Project Rules, if present:
   .harbor/rules/project-rules.md

3. Contract rules:
   .harbor/rules/contract-rules.md

4. DDT rules, if tests or l3_version may be affected:
   .harbor/rules/ddt-rules.md

5. Runtime safety rules, if risky operation may be involved:
   .harbor/rules/runtime-safety.md

6. Diary rules, if the change is important:
   .harbor/rules/diary-rules.md

7. Canonical project structure:
   .harbor/views/project-structure.md

8. Relevant canonical L2 README:
   .harbor/views/l2/<module>/README.md

9. Relevant canonical Module Capsule:
   .harbor/views/modules/<module>/module-card.md
   .harbor/views/modules/<module>/review-checklist.md
   .harbor/views/modules/<module>/debug-playbook.md

10. Relevant contract sources

11. Relevant implementation files

12. Relevant tests, fixtures, snapshots, schemas, or DDT targets
```

Do not read the whole repository unless the canonical project structure, L2 README, Module Capsule, source files, and tests are insufficient.

Do not treat generated context as source of truth.

Generated context helps orientation.

Source code, tests, schemas, policy, and diary define the actual project state.

---

## 5. Contract Sources to Inspect

Inspect only relevant contract sources.

Possible contract sources:

```text
docstring
type hints
Pydantic model
FastAPI route
OpenAPI schema
TypeScript type
Zod schema
database migration
event schema
SSE / WebSocket message schema
CLI command schema
MCP tool schema
JSON output
snapshot output
golden file
tests
fixtures
examples
public behavior
user-visible behavior
external integration behavior
file write behavior
```

If multiple contract sources exist, do not pick one blindly.

Keep them synchronized.

---

## 6. Step 1: Decide Contract Impact

Before changing implementation, decide:

```text
Contract Impact: yes
Contract Impact: no
Contract Impact: uncertain
```

Use `yes` when the change affects any of:

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
exit code
configuration behavior
migration behavior
external-visible result
user-visible result
```

Use `no` only when behavior and externally visible results remain unchanged.

If uncertain, inspect more context.

Do not silently treat uncertainty as no impact.

---

## 7. Step 2: Determine Strictness

Use `.harbor/policy.yaml` as the source of truth when available.

Default strictness:

```text
strict
standard
light
```

Treat as `strict` when touching:

```text
public API
public CLI
public JSON output
core schema
Pydantic model used externally
OpenAPI schema
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
external integration
tool schema
MCP tool schema
workspace layout
generated context behavior
```

Treat as `standard` for:

```text
ordinary business logic
service functions
repositories
stable internal APIs
module-level workflows
non-critical data transformations
```

Treat as `light` for:

```text
internal helpers
low-risk utilities
test helpers
script-local functions
small formatting helpers
```

If a target seems light but is used by a strict path, upgrade its strictness.

---

## 8. Step 3: Check Runtime Safety

Before editing or running commands, decide:

```text
Runtime Safety Risk: yes / no
```

Use `yes` when the task involves:

```text
deleting files
batch-moving files
.env or secrets
migrations
CI/CD
Docker / deployment
dependencies
destructive commands
git push
git reset --hard
production config
auth / permission / billing
user data handling
.harbor/*.yaml
.generated or exported skills
external network access
```

If safety risk exists, use:

```text
harbor-safety-preflight
```

Do not silently perform risky operations.

---

## 9. Step 4: Apply Change Order

If `Contract Impact: yes`, use this order:

```text
1. Read or define the relevant contract.
2. Determine strictness.
3. Update contract first if intended behavior changes.
4. Update implementation.
5. Update tests / DDT.
6. Check semantic drift.
7. Refresh generated context if needed.
8. Create Diary Draft if important.
9. Accept baseline only after verification and explicit user request.
```

If `Contract Impact: no`:

```text
1. State why external behavior remains unchanged.
2. Keep the change minimal.
3. Add or run tests if risk justifies it.
4. Refresh generated context only if module boundaries or context changed.
```

If `Contract Impact: uncertain`:

```text
1. Inspect more contract sources.
2. Inspect tests / fixtures.
3. Inspect generated context only as orientation.
4. Ask the user only if intended behavior cannot be inferred safely.
5. Do not silently proceed as if there is no impact.
```

---

## 10. Step 5: DDT / Test Handling

If the change affects strict targets, tests / DDT are required unless impossible.

For strict DDT targets:

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

If the project does not implement the decorator, preserve binding intent with comments:

```python
# harbor-ddt-target: module.func
# l3_version: 1
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
7. Do not blindly bind tests to latest implementation.
```

If DDT work is substantial, route to:

```text
harbor-ddt-diary
```

---

## 11. Step 6: Semantic Drift Check

Check for drift between implementation and contract.

Common drift cases:

```text
docstring says invalid input raises ValueError, but implementation returns None
schema says a field is required, but implementation accepts missing value
CLI JSON output changes but tests remain old
file write side effect is added but not declared
tests still verify old behavior after contract changed
```

Classify findings as:

```text
Confirmed Semantic Drift
Possible Semantic Drift
Contract Gap
Schema Gap
Test / DDT Gap
Implementation Bug
Docstring Stale
False Positive
```

Do not hide drift.

Do not use `harbor accept` to silence unresolved drift.

---

## 12. Step 7: Generated Context Refresh

Generated context lives under:

```text
.harbor/views/**
```

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

Typical commands:

```powershell
harbor project structure --write
harbor docs --changed --write
harbor module seal --changed --write
harbor finish --sync-context
harbor stale
harbor doctor
```

If context refresh is the main task or becomes non-trivial, route to:

```text
harbor-context-refresh
```

Do not manually edit `.harbor/views/**` as project truth.

---

## 13. Step 8: Diary Decision

Create or recommend a Diary Draft when the task involves:

```text
Contract Change
Breaking Change
schema change
CLI behavior change
JSON output change
workspace layout change
migration behavior change
public API change
DDT strategy change
runtime safety policy change
non-obvious compatibility decision
important bugfix
architecture decision
release-relevant decision
```

Canonical Diary path:

```text
.harbor/diary/YYYY-MM.jsonl
```

Do not run:

```powershell
harbor log
```

unless the user explicitly requests it.

If Diary is needed but not written, output a Diary Draft.

Use:

```text
harbor-ddt-diary
```

when DDT and Diary work are both involved.

---

## 14. Step 9: Harbor Commands

Recommended during contract-impacting work:

```powershell
harbor checkpoint
```

At task completion, when generated context may need sync:

```powershell
harbor finish --sync-context
harbor stale
harbor doctor
```

For machine-readable checks:

```powershell
harbor stale --format json
harbor doctor --format json
```

For workspace diagnostics:

```powershell
harbor workspace inspect
harbor workspace inspect --format json
harbor workspace migrate --dry-run
harbor workspace migrate --dry-run --format json
```

`harbor workspace migrate --dry-run` is read-only and is not part of the default coding workflow.

Do not run unless relevant to workspace diagnostics or migration planning.

---

## 15. Explicit User Request Only

Do not run the following unless the user explicitly requests it:

```powershell
harbor log
harbor accept
harbor lock
harbor module promote-skill <module>
```

Never run `harbor accept` merely to hide unresolved drift.

Never run `harbor log` unless the user asked to write a diary entry or the active workflow explicitly includes writing.

---

## 16. CLI / JSON Output Contract Checklist

If the change affects CLI or JSON output, check:

```text
command name
argument name
option behavior
exit code
stdout format
stderr format
JSON keys
JSON value types
JSON nesting
path format
sorting / deterministic order
machine-local path exposure
```

Rules:

```text
keep keys stable
keep ordering deterministic when practical
normalize paths
avoid machine-local absolute path leakage unless explicitly required
avoid embedding local runtime state
include enough status information for CI and agents
```

Changing JSON output is Contract Impact.

---

## 17. File Write Contract Checklist

If the change affects file writing, check:

```text
write target path
write file name
file format
overwrite behavior
append behavior
idempotency
backup behavior
dry-run behavior
generated file marker
managed block behavior
```

Strict Harbor write targets include:

```text
.harbor/views/**
.harbor/diary/**
.harbor/rules/**
.harbor/reports/**
.agents/skills/**
AGENTS.md managed block
```

Do not silently change write targets.

Do not silently switch from dry-run to write.

Do not silently overwrite user-authored content.

---

## 18. Workspace Contract Checklist

The canonical Harbor workspace is:

```text
.harbor/
```

Important paths:

```text
.harbor/rules/**   - static Harbor rule docs
.harbor/views/**   - generated context views
.harbor/diary/**   - decision memory
.harbor/reports/** - validation and audit reports
.harbor/cache/**   - runtime cache
.harbor/state/**   - runtime state
.harbor/exports/** - optional exports
```

Changing workspace layout is Contract Impact.

Use workspace diagnostics:

```powershell
harbor workspace inspect
harbor workspace migrate --dry-run
```

`migrate --dry-run` must remain read-only.

Do not assume `migrate --write` exists.

---

## 19. Breaking Change Checklist

A breaking change occurs when existing users, callers, scripts, agents, tests, or downstream systems must change.

Check whether the change:

```text
removes public field
renames JSON key
changes CLI output format
changes exit code
changes schema requirement
changes file path
changes migration behavior
changes public exception behavior
changes compatibility behavior
```

If breaking:

```text
mark Breaking Change: yes
explain affected consumers
provide migration guidance
update tests
update docs
create Diary Draft
consider release notes
```

If uncertain:

```text
Breaking Change: uncertain
```

Do not hide uncertain breaking risk.

---

## 20. Output Format

Return:

```text
Contract Change Summary:
- Contract Impact: yes / no / uncertain
- Strictness: strict / standard / light
- Affected contracts:
- Implementation summary:
- Tests / DDT:
- Semantic drift:
- Runtime safety:
- Generated context:
- Diary:
- Harbor commands:
- Remaining risks:
```

If no Contract Impact, include:

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

If commands were not run, say so clearly:

```text
未实际运行测试 / Harbor 命令。建议执行：
<command>
```

Do not invent tool results.

---

## 21. Diary Draft Format

If Diary is needed but not written, include:

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

If Diary is not needed:

```text
Diary: not needed
Reason:
- <why this change does not require a decision record>
```

---

## 22. Common Mistakes

Avoid:

```text
treating docstring as the only contract
changing implementation without Contract Impact assessment
treating Contract Impact: uncertain as no impact
changing strict behavior without tests / DDT
using strategy="latest" for strict DDT
changing CLI output without documenting impact
changing JSON output without tests
changing file write path silently
updating tests only to match broken implementation
updating snapshots without contract review
manually editing generated context as source of truth
hiding breaking changes
using harbor accept to silence unresolved drift
claiming tests passed without running them
skipping Diary for important contract decisions
```

---

## 23. Final Principle

Before making a contract-impacting change, ask:

```text
Who or what expects the old behavior?
Which contract sources describe it?
Which tests verify it?
Which generated context summarizes it?
Does the decision need to be remembered?
```

A Harbor-managed contract change is complete only when implementation, contracts, tests, generated context, and decision memory are aligned.

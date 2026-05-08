---
name: harbor-context-refresh
description: Use when refreshing Harbor generated context under .harbor/views/**, including project structure, L2 README, Module Capsule, stale checks, doctor checks, or finish --sync-context after code, contract, schema, CLI, JSON, test, DDT, or module boundary changes.
---

# Harbor Context Refresh Skill

Version: Harbor-spec v1.3.0  
Purpose: Generated context refresh workflow for Harbor-managed repositories

---

## 1. Purpose

Use this skill when generated Harbor context may need to be refreshed.

Generated context lives under:

```text
.harbor/views/**
```

Generated context helps humans and AI agents understand the repository efficiently.

It includes:

```text
project structure
L2 README
Module Capsule
module-card
review-checklist
debug-playbook
```

This skill ensures that generated context reflects the current source of truth.

This skill is an on-demand workflow entrypoint.

It is not source of truth.

It must follow:

```text
AGENTS.md
.harbor/policy.yaml
.harbor/safety.yaml
.harbor/rules/agent-policy.md
.harbor/rules/contract-rules.md
.harbor/rules/ddt-rules.md
.harbor/rules/runtime-safety.md
.harbor/rules/diary-rules.md
.harbor/rules/project-rules.md, if present
```

Core principle:

```text
Generated context should summarize the source of truth, not replace it.
```

---

## 2. When to Use

Use this skill after changes that may affect:

```text
module boundaries
project structure
public contracts
docstrings
schemas
tests / DDT
CLI behavior
JSON output
file write behavior
workspace structure
module responsibilities
debug workflow
review workflow
generated context format
```

Typical triggers:

```text
code changed in a meaningful module
contract changed
schema changed
public CLI behavior changed
JSON output changed
tests or DDT bindings changed
module moved or renamed
new module added
module responsibility changed
Module Capsule may be stale
L2 README may be stale
project structure may be stale
finish --sync-context is needed
stale check reports outdated views
doctor reports generated context warning
```

Do not use this skill for trivial edits that do not affect generated context.

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
project-specific module boundaries
verified test commands
strictness map
project-specific generated context expectations
local refresh conventions
```

If this skill conflicts with Project Rules, inspect `.harbor/policy.yaml` and `.harbor/safety.yaml`.

Machine policy wins over Markdown rules.

---

### 3.3 Related Skills

Use related skills when needed:

```text
harbor-contract-change
  Use when context refresh follows or reveals Contract Impact.

harbor-code-review
  Use when reviewing whether generated context is stale after code changes.

harbor-ddt-diary
  Use when refresh follows DDT changes, l3_version changes, or Diary-relevant decisions.

harbor-safety-preflight
  Use before broad generated writes, protected path changes, .harbor/*.yaml changes, or generated skill writes.

harbor-workspace-migration-plan
  Use when refresh involves workspace layout, migration dry-run, cleanup planning, or canonical workspace changes.
```

This skill may route to these skills, but should not replace them.

---

## 4. Canonical Generated Context

Canonical generated context lives under:

```text
.harbor/views/
```

Expected layout:

```text
.harbor/views/
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
```

Meaning:

```text
.harbor/views/project-structure.md
  repository-level generated context

.harbor/views/l2/<module>/README.md
  module-level L2 README

.harbor/views/modules/<module>/module-card.md
  concise module identity and responsibility summary

.harbor/views/modules/<module>/review-checklist.md
  module-specific review checklist

.harbor/views/modules/<module>/debug-playbook.md
  module-specific debugging guide
```

---

## 5. Source-of-Truth Boundary

Generated context is not source of truth.

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

Treat these as generated context:

```text
.harbor/views/**
```

Treat these as external workflow exports:

```text
.agents/skills/**
```

Rules:

```text
Do not manually edit .harbor/views/** as project truth.
Do not let generated context override code, contracts, schemas, tests, policy, or diary.
If generated context conflicts with source of truth, treat generated context as stale.
Refresh generated context through Harbor commands.
```

---

## 6. Runtime Safety Boundary

Refreshing generated context usually writes files under:

```text
.harbor/views/**
```

This is usually medium risk.

Use `harbor-safety-preflight` when:

```text
refresh scope is broad
write targets are unclear
refresh touches unexpected paths
refresh may overwrite user-authored content
refresh affects .harbor/rules/**
refresh affects .harbor/*.yaml
refresh affects .agents/skills/**
refresh involves workspace layout changes
refresh involves migration or cleanup
```

Do not manually rewrite generated context.

Do not write outside expected generated context paths unless the user explicitly requests it.

---

## 7. Step 1: Identify Refresh Trigger

Classify the trigger.

Possible triggers:

```text
code change
contract change
schema change
test / DDT change
CLI change
JSON output change
module boundary change
project structure change
workspace layout change
generated context stale warning
doctor warning
manual user request
unknown
```

If trigger is unknown, inspect relevant source, tests, and Harbor views before writing.

---

## 8. Step 2: Identify Refresh Scope

Classify refresh scope as one of:

```text
NONE
PROJECT_STRUCTURE
SINGLE_L2
CHANGED_L2
ALL_L2
SINGLE_MODULE_CAPSULE
CHANGED_MODULE_CAPSULES
ALL_MODULE_CAPSULES
SYNC_CONTEXT
STALE_CHECK_ONLY
DOCTOR_CHECK_ONLY
WORKSPACE_DIAGNOSTICS
```

Guidance:

```text
NONE
  No generated context update needed.

PROJECT_STRUCTURE
  Repository layout, module layout, workspace layout, or command organization changed.

SINGLE_L2
  One module’s L2 README needs refresh.

CHANGED_L2
  Changed modules’ L2 README files need refresh.

ALL_L2
  Major architecture or layout change affects all modules.

SINGLE_MODULE_CAPSULE
  One module’s capsule needs refresh.

CHANGED_MODULE_CAPSULES
  Changed modules’ capsules need refresh.

ALL_MODULE_CAPSULES
  Major architecture or module framework change affects all capsules.

SYNC_CONTEXT
  Use finish --sync-context to refresh changed L2 README and Module Capsule together.

STALE_CHECK_ONLY
  Only inspect whether generated context is stale.

DOCTOR_CHECK_ONLY
  Only inspect Harbor workspace health.

WORKSPACE_DIAGNOSTICS
  Use workspace inspect or migrate dry-run; not a default coding workflow.
```

Prefer the narrowest scope that satisfies the task.

---

## 9. Step 3: Inspect Existing Context

Before writing generated context, inspect what currently exists.

Relevant files:

```text
.harbor/views/project-structure.md
.harbor/views/l2/<module>/README.md
.harbor/views/modules/<module>/module-card.md
.harbor/views/modules/<module>/review-checklist.md
.harbor/views/modules/<module>/debug-playbook.md
```

Also inspect relevant source of truth:

```text
source files
tests
schemas
DDT targets
policy
diary
project rules
```

Do not refresh based only on stale generated context.

Refresh should reflect source of truth.

---

## 10. Step 4: Choose Commands

Use the appropriate Harbor command.

### 10.1 Project Structure

```powershell
harbor project structure --write
```

Use when:

```text
repository layout changed
module layout changed
workspace layout changed
major command organization changed
```

---

### 10.2 Single L2 README

```powershell
harbor docs --module <module> --write
```

Use when:

```text
one module changed
one module’s contract or responsibility changed
one module’s L2 README is stale
```

---

### 10.3 Changed L2 README

```powershell
harbor docs --changed --write
```

Use when:

```text
changed modules need L2 refresh
task touched multiple modules
finish flow needs refreshed module summaries
```

---

### 10.4 All L2 README

```powershell
harbor docs --all --write
```

Use when:

```text
major architecture changed
workspace-wide module summary format changed
all module summaries need regeneration
```

Use with caution.

Broad generated writes may require safety preflight.

---

### 10.5 Single Module Capsule

```powershell
harbor module seal <module> --write
```

Use when:

```text
one module capsule needs refresh
module-card / review-checklist / debug-playbook may be stale
```

---

### 10.6 Changed Module Capsules

```powershell
harbor module seal --changed --write
```

Use when:

```text
changed modules need Module Capsule refresh
```

---

### 10.7 All Module Capsules

```powershell
harbor module seal --all --write
```

Use when:

```text
major architecture changed
capsule format changed
all module capsules need regeneration
```

Use with caution.

Broad generated writes may require safety preflight.

---

### 10.8 Task-level Sync

```powershell
harbor finish --sync-context
```

Use when:

```text
task is ending
changed L2 README and Module Capsule should be refreshed together
implementation / contract / tests changed
```

This is the preferred task-level context sync command.

---

### 10.9 Stale Check

```powershell
harbor stale
harbor stale --format json
```

Use when:

```text
checking whether generated context is stale
validating generated context after refresh
preparing final response
```

---

### 10.10 Doctor Check

```powershell
harbor doctor
harbor doctor --format json
```

Use when:

```text
checking overall Harbor health
validating workspace status
preparing release-like confidence
```

---

### 10.11 Workspace Diagnostics

```powershell
harbor workspace inspect
harbor workspace inspect --format json
harbor workspace migrate --dry-run
harbor workspace migrate --dry-run --format json
```

Use when:

```text
workspace layout is involved
managed files are unclear
migration or cleanup is being planned
canonical workspace health is being inspected
```

`harbor workspace migrate --dry-run` is read-only.

It is not part of the default coding workflow.

Do not assume `harbor workspace migrate --write` exists.

---

## 11. Step 5: Run Stale Check

After a generated context refresh, run or recommend:

```powershell
harbor stale
```

For machine-readable output:

```powershell
harbor stale --format json
```

Interpretation:

```text
PASS:
  generated context appears up to date.

WARN:
  generated context may be stale or partially missing.

FAIL:
  generated context is outdated or inconsistent enough to block confidence.

SKIP:
  check could not run due to missing prerequisites.
```

If stale warnings remain, report them.

Do not claim stale check passed unless it actually ran and passed.

---

## 12. Step 6: Run Doctor Check

After meaningful generated context work, run or recommend:

```powershell
harbor doctor
```

For machine-readable output:

```powershell
harbor doctor --format json
```

Doctor may inspect:

```text
workspace health
policy files
generated context
DDT status
skill references
runtime safety
configuration issues
```

If doctor warnings remain, report them.

Do not claim doctor passed unless it actually ran and passed.

---

## 13. Step 7: Check Contract and DDT Implications

Generated context refresh may reveal contract or DDT issues.

Route to `harbor-contract-change` when:

```text
generated context shows stale contract summary
contract source changed
public behavior changed
CLI / JSON output changed
file write behavior changed
workspace behavior changed
```

Route to `harbor-ddt-diary` when:

```text
tests or DDT bindings changed
l3_version changed
fixtures or snapshots changed
Diary Draft is needed
```

Route to `harbor-code-review` when:

```text
generated context and implementation disagree
review-checklist identifies drift
debug-playbook points to outdated behavior
```

---

## 14. Step 8: Check Diary Need

A simple generated context refresh usually does not need Diary.

Diary may be needed when the refresh reflects or accompanies:

```text
Contract Change
Breaking Change
workspace layout change
generated context schema change
Module Capsule structure change
L2 README semantics change
project structure generation rule change
agent context loading strategy change
important architecture decision
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

---

## 15. Step 9: Explicit User Request Only

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
  writes Diary / decision memory

harbor accept
  accepts new Harbor baseline

harbor lock
  legacy or lock-style baseline operation

harbor module promote-skill <module>
  exports a Module Capsule into an external AI skill
```

Never run `harbor accept` merely to silence unresolved drift.

Never run `harbor module promote-skill` as part of ordinary context refresh.

---

## 16. Step 10: Output Result

Return:

```text
Context Refresh Summary:
- Trigger:
- Refresh scope:
- Commands run:
- Generated views changed:
- Stale result:
- Doctor result:
- Contract / DDT implications:
- Runtime safety:
- Diary:
- Remaining stale views:
- Remaining risks:
- Recommended next command:
```

If commands were not run, state clearly:

```text
未实际运行 Harbor 命令。建议执行：
<command>
```

Do not invent command results.

---

## 17. Tool Honesty

Do not claim the following were run unless actually run and observed:

```text
harbor project structure --write
harbor docs --changed --write
harbor docs --all --write
harbor module seal --changed --write
harbor finish --sync-context
harbor stale
harbor doctor
harbor workspace inspect
harbor workspace migrate --dry-run
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
stale check 已通过
doctor 通过
context 已同步
capsule 已刷新
```

unless actually observed.

---

## 18. Review Labels

When reviewing context refresh needs, use these labels:

```text
Generated Context Gap
Stale L2 README
Stale Module Capsule
Stale Project Structure
Missing Generated View
Unexpected Generated Write
Manual Generated Edit Risk
Workspace Context Risk
Suggested Refresh
```

Definitions:

```text
Generated Context Gap:
  Generated context may not reflect source of truth.

Stale L2 README:
  .harbor/views/l2/<module>/README.md is outdated.

Stale Module Capsule:
  module-card, review-checklist, or debug-playbook is outdated.

Stale Project Structure:
  .harbor/views/project-structure.md is outdated.

Missing Generated View:
  Expected generated context file is missing.

Unexpected Generated Write:
  A command may write outside expected generated context paths.

Manual Generated Edit Risk:
  Generated context was manually edited as if it were source of truth.

Workspace Context Risk:
  Workspace layout or generated context path behavior changed without governance.

Suggested Refresh:
  Non-blocking recommendation to refresh context.
```

---

## 19. Common Mistakes

Avoid:

```text
manually editing .harbor/views/** as project truth
refreshing generated context before updating source of truth
using stale generated context to override implementation
using stale generated context to override schema
using stale generated context to override tests
running broad --all refresh without need
claiming stale / doctor passed without running them
running harbor accept to hide stale context
running harbor module promote-skill during ordinary context refresh
treating .agents/skills/** as canonical context
treating .harbor/cache/** or .harbor/state/** as source of truth
```

---

## 20. Final Principle

Before refreshing generated context, ask:

```text
What changed in the source of truth?
Which generated view summarizes that change?
What is the narrowest safe refresh command?
How will stale / doctor verify the result?
```

A good context refresh makes future AI work easier without turning generated views into source of truth.

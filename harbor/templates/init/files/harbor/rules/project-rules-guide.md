<!-- harbor-spec:managed version=1.3.0 kind=rule -->

# Harbor Project Rules Guide

Version: Harbor-spec v1.3.0  
Canonical path: `.harbor/rules/project-rules-guide.md`  
Purpose: Guide for generating and maintaining project-specific rules under Harbor-spec

---

## 1. Purpose

This document explains how to create and maintain project-specific rules for a Harbor-managed repository.

Project Rules are not the same as `AGENTS.md`.

Project Rules are not the same as Skills.

Project Rules are not the same as generic Harbor rule docs.

Project Rules define the repository-specific development constraints that AI coding agents should follow.

They answer:

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

Canonical Project Rules path:

```text
.harbor/rules/project-rules.md
```

---

## 2. Boundary Between AGENTS.md, Project Rules, and Skills

Harbor-spec uses layered instructions.

Do not merge these layers.

---

### 2.1 AGENTS.md

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

It answers:

```text
What should an AI coding agent always know before working in this repository?
```

It should stay short enough to be always loaded.

It should not contain:

```text
full project architecture
full Contract rules
full DDT rules
full Runtime Safety rules
full Diary rules
long tutorials
complete task workflows
```

---

### 2.2 Project Rules

Project Rules define repository-specific constraints.

Canonical path:

```text
.harbor/rules/project-rules.md
```

They answer:

```text
What is special about this repository?
What commands are verified here?
Which directories are strict?
Which schemas and APIs are important?
Which modules require special caution?
Which local safety boundaries apply?
```

Project Rules should be:

```text
project-specific
short
concrete
actionable
stable
compatible with AGENTS.md
compatible with .harbor/policy.yaml and .harbor/safety.yaml
```

Project Rules should not repeat generic Harbor definitions unless the project has a special local exception.

---

### 2.3 Skills

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

### 2.4 Generic Harbor Rule Docs

Generic Harbor rule docs live under:

```text
.harbor/rules/*.md
```

Examples:

```text
.harbor/rules/glossary.md
.harbor/rules/agent-policy.md
.harbor/rules/contract-rules.md
.harbor/rules/ddt-rules.md
.harbor/rules/runtime-safety.md
.harbor/rules/diary-rules.md
.harbor/rules/project-rules-guide.md
```

They explain generic Harbor concepts and policies.

Project Rules should reference these files instead of duplicating them.

---

### 2.5 Machine Policy

Machine-readable policy files:

```text
.harbor/policy.yaml
.harbor/safety.yaml
```

These are the machine policy source.

If Project Rules conflict with `.harbor/policy.yaml` or `.harbor/safety.yaml`, prefer the YAML policy files.

---

## 3. Rule Priority

Harbor separates safety priority from task priority.

---

### 3.1 Safety Priority

For safety, permissions, destructive operations, secrets, protected paths, production risk, and machine policy:

```text
1. Tool-native sandbox / deny rules
2. .harbor/safety.yaml
3. .harbor/policy.yaml
4. User's current request
5. AGENTS.md / tool rules / .harbor/rules/*.md
```

User prompts cannot override tool-native deny rules, runtime safety, or Harbor machine policy.

---

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

The user defines the current task.

Harbor defines the safety, contract, context, testing, and governance boundaries.

---

## 4. Where Project Rules Live

Canonical path:

```text
.harbor/rules/project-rules.md
```

This file is part of the Harbor workspace.

It should be initialized or updated by Harbor-aware workflows.

It should not be mixed into the user's general product documentation.

---

## 5. What Project Rules Should Include

A complete Project Rules file should include:

```text
1. Project overview
2. Technology stack
3. Directory map
4. Harbor strictness map
5. Project contract sources
6. API / schema rules
7. Testing commands
8. DDT rules in this project
9. Runtime safety rules in this project
10. Skill routing
11. Common task rules
12. Generated context rules
13. Final response requirements
14. Completion checklist
```

建议补充的 v1.3.0+ 内容：

```text
15. project-specific contract_required rules
16. accepted contract sources
17. strict target contract requirements
18. DDT baseline handling
19. CI gate expectations for contract_gap and ddt_version_baseline_missing
```

---

## 6. What Project Rules Should Not Include

Project Rules should not include:

```text
full Harbor glossary
full Contract tutorial
full DDT tutorial
full Runtime Safety tutorial
full Diary tutorial
complete AI role definition
long task workflows
duplicated AGENTS.md content
duplicated Skill content
machine policy that conflicts with .harbor/*.yaml
generated project context
module summaries that belong in .harbor/views/**
```

Project Rules should route agents to the right source instead of copying everything into one file.

---

## 7. Recommended Length

Recommended length:

```text
Standard: 150–250 lines
Upper bound: about 300 lines
```

If Project Rules exceed 300 lines, consider splitting local project docs or moving details into:

```text
.harbor/rules/project-rules.md
.harbor/views/project-structure.md
.harbor/views/l2/<module>/README.md
.harbor/views/modules/<module>/*
project source docs
```

Do not turn Project Rules into a second full architecture document.

---

## 8. Before Generating Project Rules

Before generating or updating Project Rules, inspect available project files.

Read only what is necessary.

Recommended sources:

```text
README.md
pyproject.toml
requirements.txt
package.json
pnpm-lock.yaml
package-lock.json
tsconfig.json
vite.config.ts
Dockerfile
docker-compose.yml
src/
app/
packages/
tests/
frontend/
backend/
AGENTS.md
.harbor/policy.yaml
.harbor/safety.yaml
.harbor/views/project-structure.md
.harbor/views/l2/**
.harbor/views/modules/**
```

If a file does not exist, do not invent it.

If project configuration is unclear, write:

```text
Unknown / not found
```

Do not hallucinate technology stack, test commands, deployment targets, or architecture.

---

## 9. Generation Process

Use this process when generating Project Rules.

---

### Step 1: Identify Project Overview

Identify:

```text
project name
project goal
primary users
primary product surface
core workflows
```

Examples of product surface:

```text
CLI
SDK
API service
web app
agent service
workflow engine
internal tool
library
```

If uncertain, mark as:

```text
Unknown / not confirmed
```

---

### Step 2: Identify Technology Stack

Extract from actual files.

Possible categories:

```text
Backend
Frontend
Database
Vector store
Storage
Queue / async
LLM / agent framework
Testing
Package manager
Build system
Default shell
Deployment
```

Do not guess.

If no evidence exists, write:

```text
Not found in current repository.
```

---

### Step 3: Identify Directory Map

Describe important paths:

```text
<path> - <purpose>
```

Example:

```text
harbor/cli/       - CLI command definitions
harbor/core/      - core contract and checkpoint logic
harbor/workspace/ - workspace inspect and migration planning
tests/            - pytest test suite
.harbor/          - Harbor canonical workspace
```

Keep descriptions short.

Do not duplicate `.harbor/views/project-structure.md`.

Project Rules should provide a stable map, not a generated inventory.

---

### Step 4: Identify Strictness Map

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
public CLI
JSON output
schemas
parser
export
file writeback
workflow node
security
auth / permission
migration
CI/CD
critical path
user-visible result generation
```

Standard examples:

```text
ordinary business logic
service functions
repositories
stable internal APIs
```

Light examples:

```text
internal helpers
low-risk utilities
test helpers
script-local functions
```

Do not override `.harbor/policy.yaml`.

If a path is not covered by policy, mark it as a suggested classification.

---

### Step 5: Identify Contract Sources

Project-specific Contract sources may include:

```text
docstring
type hints
Pydantic models
FastAPI routes
OpenAPI schemas
TypeScript types
Zod schemas
database migrations
event schemas
CLI command schemas
tool schemas
tests / fixtures
snapshot outputs
golden files
public behavior
```

List only sources that actually exist or are project-relevant.

同时应明确本项目的 `contract_required` 规则（按路径、scope、strictness、命名约定等）。

Also identify contract pairs that must stay synchronized.

Examples:

```text
Pydantic model ↔ API response tests
CLI output ↔ JSON snapshot tests
Docstring ↔ DDT target
OpenAPI schema ↔ frontend TypeScript type
Parser behavior ↔ fixture corpus
Export format ↔ golden files
```

---

### Step 6: Identify Testing Commands

Extract commands from real project files.

Examples:

```powershell
pytest
pytest tests/path/to/test_file.py
ruff check .
mypy .
npm test
npm run typecheck
npm run lint
pnpm test
pnpm typecheck
```

If not verified, write:

```text
Testing command not confirmed. Inspect project config before running.
```

Never invent commands.

Never claim commands were run unless they were actually run.

---

### Step 7: Identify Runtime Safety Boundaries

Use `.harbor/safety.yaml` as the source of truth when available.

Identify project-specific high-risk areas:

```text
.env / secrets
migrations
CI/CD
Docker / deployment
package files
database operations
file export
user data
auth / permission / billing
external network access
production config
.generated files
.harbor/*.yaml
.agents/skills/**
```

Classify operations as:

```text
ALLOW
ASK
DENY
```

If uncertain, choose `ASK`.

---

### Step 8: Identify Skill Routing

Map common task types to skills.

Recommended baseline:

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

Workspace diagnostics, migration dry-run, workspace cleanup planning:
  use harbor-workspace-migration-plan if available
```

If a skill is missing, route to `AGENTS.md` and relevant `.harbor/rules/*.md`.

---

## 10. Project Rules Template

Save the generated file to:

```text
.harbor/rules/project-rules.md
```

Use the following template.

---

```markdown
<!-- harbor-spec:managed version=1.3.0 kind=project-rules -->

# Project Rules

Version: Harbor-spec v1.3.0  
Canonical path: `.harbor/rules/project-rules.md`  
Purpose: Project-specific rules for AI coding agents

---

## 1. Project Overview

Project name:

```text
<PROJECT_NAME>
```

Project goal:

```text
<SHORT_PROJECT_GOAL>
```

Primary users:

```text
<USERS>
```

Primary product surface:

```text
CLI / SDK / API service / web app / agent service / workflow engine / internal tool / library / other
```

Core workflows:

```text
- <workflow 1>
- <workflow 2>
- <workflow 3>
```

---

## 2. Technology Stack

Backend:

```text
<FastAPI / Django / Flask / Node / None / Unknown>
```

Frontend:

```text
<React / Next.js / Vue / Svelte / None / Unknown>
```

Database:

```text
<PostgreSQL / SQLite / MySQL / None / Unknown>
```

Vector store:

```text
<Milvus / PGVector / Chroma / None / Unknown>
```

Storage:

```text
<S3 / OSS / local filesystem / None / Unknown>
```

Queue / async:

```text
<Celery / Redis / background tasks / None / Unknown>
```

LLM / agent framework:

```text
<OpenAI / Anthropic / LangGraph / custom / None / Unknown>
```

Testing:

```text
<pytest / vitest / playwright / unittest / None / Unknown>
```

Package manager:

```text
<pip / uv / poetry / npm / pnpm / yarn / Unknown>
```

Default shell:

```text
PowerShell
```

---

## 3. Directory Map

Important directories:

```text
<path 1> - <purpose>
<path 2> - <purpose>
<path 3> - <purpose>
```

Harbor workspace:

```text
.harbor/rules/   - Harbor rule docs
.harbor/views/   - generated context views
.harbor/diary/   - decision memory
.harbor/reports/ - validation and audit reports
.harbor/cache/   - runtime cache
.harbor/state/   - runtime state
```

---

## 4. Harbor Strictness Map

Use `.harbor/policy.yaml` as the source of truth.

### Strict

```text
<strict path 1>
<strict path 2>
<strict path 3>
```

Strict changes require:

```text
- Contract Impact check
- Contract / Schema update when needed
- tests / DDT update
- Semantic Drift check
- Generated context refresh if needed
- Diary Draft for important changes
```

### Standard

```text
<standard path 1>
<standard path 2>
```

Standard changes require:

```text
- Contract Impact check
- tests recommended
- DDT latest allowed only if policy permits
```

### Light

```text
<light path 1>
<light path 2>
```

Light changes require:

```text
- Summary / type clarity
- tests only when behavior is non-trivial
```

---

## 5. Project Contract Sources

In this project, Contract sources include:

```text
- <Docstring / type hints / schema / OpenAPI / TypeScript / migration / event schema>
```

Primary contract sources:

```text
- <source 1>
- <source 2>
```

Contract pairs that must stay synchronized:

```text
- <source A> ↔ <source B>
- <source C> ↔ <source D>
```

Rules:

```text
- Do not treat docstring as the only contract source.
- Do not treat generated context as the primary source of behavior.
- If Schema and implementation conflict, mark [Schema Gap] or [Semantic Drift].
- If implementation and Contract conflict, mark [Semantic Drift].
- If tests verify old behavior, mark [Test / DDT Gap].
```

---

### Step 5.1: Define Contract Policy Snapshot

Project Rules 可包含一个简化策略片段，帮助 AI agent 快速理解本仓库契约门禁。

示例：

```yaml
contract_policy:
  strict_targets_require_contract: true
  standard_targets_require_contract: recommended
  light_targets_require_contract: false
  accepted_contract_sources:
    - docstring
    - type_hint
    - schema
    - cli_schema
    - json_output
    - test
    - fixture
```

可再补充：

```text
CI gate:
  contract_gap:
    default: blocking
  ddt_version_baseline_missing:
    default: advisory
```

---

## 6. API / Schema Rules

When modifying API, schema, CLI output, JSON output, or public behavior:

```text
1. Read existing contract sources.
2. Determine Contract Impact.
3. Determine Strictness.
4. Update contract first if behavior changes.
5. Update implementation.
6. Update tests / fixtures / DDT.
7. Mark Breaking Change if consumers must change.
8. Refresh generated context if needed.
9. Create Diary Draft if important.
```

Relevant paths:

```text
<api path>
<schema path>
<test path>
<generated type path>
```

---

## 7. Testing Commands

Use these commands when applicable.

Backend tests:

```powershell
<backend test command>
```

Single backend test:

```powershell
<single backend test command>
```

Frontend tests:

```powershell
<frontend test command>
```

Type check:

```powershell
<type check command>
```

Lint:

```powershell
<lint command>
```

Harbor checks:

```powershell
harbor checkpoint
harbor stale
harbor doctor
```

If commands are not verified, do not claim they were run.

Always distinguish:

```text
- 已运行
- 未运行，仅建议
- 当前环境无法运行
```

---

## 8. DDT Rules in This Project

Strict targets must use explicit `l3_version`.

Do not use:

```python
@harbor_ddt_target("...", strategy="latest")
```

for strict targets.

Allowed for standard / light targets if policy permits:

```python
@harbor_ddt_target("...", strategy="latest")
```

When Contract changes:

```text
- update Contract
- upgrade l3_version when needed
- inspect old tests before updating binding
- update assertions
- add missing edge cases
- do not blindly bind tests to latest implementation
```

See:

```text
.harbor/rules/ddt-rules.md
```

---

## 9. Runtime Safety in This Project

Use `.harbor/safety.yaml` as the source of truth.

Ask before:

```text
- deleting files
- batch-moving files
- modifying .env or secrets
- modifying migrations
- modifying CI/CD
- installing production dependencies
- changing Docker / deployment
- running destructive commands
- git push
- git reset --hard
- changing auth / permission / billing
- changing production config
- modifying .harbor/*.yaml
- modifying generated skills
```

Default shell:

```text
PowerShell
```

For risky deletion, prefer:

```powershell
Get-ChildItem <path> -Recurse
Remove-Item <path> -Recurse -WhatIf
```

Never read or print secrets.

---

## 10. Skill Routing

Use Harbor skills for multi-step tasks.

```text
Contract or schema change:
  use harbor-contract-change

Code review or semantic drift review:
  use harbor-code-review

Risky command or protected file change:
  use harbor-safety-preflight

DDT update or Diary Draft:
  use harbor-ddt-diary

Generated context refresh:
  use harbor-context-refresh if available

Workspace diagnostics or migration planning:
  use harbor-workspace-migration-plan if available
```

If a skill conflicts with `.harbor/*.yaml`, source code, tests, schemas, diary, or generated views, prefer the source of truth and report the conflict.

---

## 11. Common Task Rules

### 11.1 Feature Work

For feature work:

```text
1. Determine Contract Impact.
2. Determine Strictness.
3. Update contract first if behavior changes.
4. Implement.
5. Add or update tests / DDT.
6. Refresh generated context if needed.
7. Create Diary Draft if important.
```

### 11.2 Bugfix

For bugfixes:

```text
1. Reproduce or describe the bug.
2. Determine whether implementation or contract is wrong.
3. Add failing test when practical.
4. Fix implementation or contract.
5. Update tests / DDT.
6. Create Diary Draft for important bugs.
```

### 11.3 Refactor

For refactors:

```text
1. State whether external behavior remains unchanged.
2. If behavior is unchanged, mark Contract Impact: none.
3. Add characterization tests if risk is high.
4. Avoid broad unrelated rewrites.
5. Refresh generated context if module boundaries changed.
```

### 11.4 Code Review

For code review:

```text
1. Compare implementation against contracts.
2. Check schema / type consistency.
3. Check error paths and side effects.
4. Check tests / DDT coverage.
5. Check runtime safety risk.
6. Check generated context and Diary need.
```

Use labels:

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

## 12. Generated Context Rules

Generated context lives under:

```text
.harbor/views/**
```

Do not manually edit generated context as project truth.

Refresh with Harbor commands:

```powershell
harbor project structure --write
harbor docs --changed --write
harbor module seal --changed --write
harbor finish --sync-context
harbor stale
harbor doctor
```

Generated context should be refreshed when changes affect:

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

---

## 13. Final Response Requirements

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

For safety tasks, include:

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

Do not claim commands were run unless they were actually run.

---

## 14. Completion Checklist

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

---

## 15. Anti-patterns

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
duplicating generic Harbor rules inside Project Rules
```

```

---

## 11. How to Update Project Rules

Update Project Rules when:

```text
technology stack changes
directory boundaries change
module boundaries change
new strict paths are introduced
test commands change
CI/CD behavior changes
runtime safety boundaries change
contract sources change
new skills are added
generated context layout changes
workspace structure changes
```

Do not update Project Rules for every small implementation change.

Small implementation changes should usually update:

```text
code
tests
contracts
generated context
diary when needed
```

Project Rules should remain stable.

---

## 12. Validation Checklist for Project Rules

Before accepting generated Project Rules, check:

```text
[ ] The file is saved to .harbor/rules/project-rules.md.
[ ] It does not duplicate AGENTS.md.
[ ] It does not duplicate full generic Harbor rules.
[ ] It does not conflict with .harbor/policy.yaml.
[ ] It does not conflict with .harbor/safety.yaml.
[ ] It uses .harbor/views/** for generated context.
[ ] It uses .harbor/diary/** for decision memory.
[ ] It lists only verified or clearly marked test commands.
[ ] It does not invent technology stack or architecture.
[ ] It clearly maps common tasks to skills.
[ ] It clearly distinguishes source of truth from generated context.
```

---

## 13. Common Mistakes

Avoid:

```text
putting all project documentation into Project Rules
duplicating generic Contract / DDT / Diary / Safety docs
copying generated context into Project Rules
using Project Rules as a module README
using Project Rules as a changelog
using Project Rules as a Diary
creating multiple conflicting rule files
inventing test commands
inventing framework choices
letting Project Rules override .harbor/*.yaml
letting skills become source of truth
```

---

## 14. Final Principle

A good Project Rules file is:

```text
project-specific
short
concrete
stable
actionable
compatible with AGENTS.md
compatible with .harbor/policy.yaml
compatible with .harbor/safety.yaml
clear about source of truth
clear about generated context
clear about skill routing
```

A bad Project Rules file is:

```text
long
generic
duplicated
stale
unclear about source of truth
unclear about strictness
full of invented commands
conflicting with machine policy
copying generic Harbor docs
copying generated context views
```

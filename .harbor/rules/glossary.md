<!-- harbor-spec:managed version=1.3.0 kind=rule -->

# Harbor Glossary

Version: Harbor-spec v1.4.x  
Canonical path: `.harbor/rules/glossary.md`  
Purpose: Shared glossary for Harbor-spec concepts and AI coding governance

---

## 1. Purpose

This glossary defines the core terms used by Harbor-spec.

It is intended for:

```text
AI coding agents
developers
reviewers
tool adapters
project maintainers
```

It helps ensure that terms such as Contract, DDT, Diary, generated context, strictness, and runtime safety are used consistently across:

```text
AGENTS.md
.harbor/rules/*.md
.harbor/policy.yaml
.harbor/safety.yaml
.harbor/views/**
.agents/skills/**
```

This file is a reference.

It is not a task workflow.

For task workflows, use Harbor skills.

---

## 2. Harbor-spec

Harbor-spec is a context governance system for AI Coding / Agentic Coding.

It helps keep the following aligned:

```text
implementation
contracts
schemas
tests
DDT targets
generated context
decision memory
runtime safety
AI tool instructions
```

Harbor-spec is not:

```text
an AI IDE
a code generator
a replacement for tests
a replacement for code review
a replacement for tool-native sandboxing
```

Core principle:

```text
AI can write code quickly, but contracts, tests, context, decision memory, and safety boundaries must not drift.
```

---

## 3. Agentic Coding

Agentic Coding means software development where an AI agent can plan, edit files, run commands, inspect results, and iterate toward a goal.

In Harbor-spec, Agentic Coding must remain governed by:

```text
contract impact checks
runtime safety
tests / DDT
generated context refresh
diary for important decisions
tool honesty
```

Agentic Coding is not just code generation.

It is code generation inside a controlled engineering workflow.

---

## 4. Context Governance

Context Governance means managing the project information that AI agents rely on.

It includes:

```text
what context should be read first
which files are source of truth
which files are generated views
which paths are runtime cache or state
which rules are always loaded
which skills are loaded on demand
which decisions should be remembered
```

Harbor-spec treats context as infrastructure.

---

## 5. Canonical Workspace

The canonical Harbor workspace is:

```text
.harbor/
```

Harbor uses `.harbor/` as canonical workspace for Harbor-managed rules, generated context, decision memory, reports, cache, and state.

Canonical layout:

```text
.harbor/
  config/
  rules/
  views/
  diary/
  reports/
  cache/
  state/
  exports/
```

---

## 6. `.harbor/rules/`

`.harbor/rules/` contains static Harbor rule documents.

Examples:

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

Rule docs explain policies, concepts, and guidance.

They are not generated context views.

---

## 7. `.harbor/views/`

`.harbor/views/` contains generated Harbor context views.

Examples:

```text
.harbor/views/project-structure.md
.harbor/views/l2/<module>/README.md
.harbor/views/modules/<module>/module-card.md
.harbor/views/modules/<module>/review-checklist.md
.harbor/views/modules/<module>/debug-playbook.md
```

Generated views help AI agents and humans understand the project efficiently.

Generated views are not the primary source of project behavior.

If generated views conflict with code, tests, schemas, policy, or diary, treat the generated view as stale.

---

## 8. `.harbor/diary/`

`.harbor/diary/` contains structured decision memory.

Canonical path:

```text
.harbor/diary/YYYY-MM.jsonl
```

Diary records why important changes happened.

Diary is not a changelog replacement.

Diary is not a commit message replacement.

---

## 9. `.harbor/reports/`

`.harbor/reports/` contains validation, audit, migration, dogfooding, or diagnostic reports.

Reports provide evidence and diagnostics.

Reports are not primary source of project behavior.

Saved Draft Report under `.harbor/reports/log-draft-*.md` or `.json` is reviewable report output, not source-of-truth decision memory.

---

## 10. `.harbor/cache/`

`.harbor/cache/` contains local runtime cache.

Cache files are not source of truth.

AI agents should not manually edit cache unless explicitly requested.

---

## 11. `.harbor/state/`

`.harbor/state/` contains local runtime state.

State files are not source of truth.

AI agents should not manually edit state unless explicitly requested.

Latest Draft Cache and `last_log_marker` are runtime state artifacts under `.harbor/state/log/**`, not source-of-truth memory.

---

## 12. `.harbor/policy.yaml`

`.harbor/policy.yaml` is the machine-readable project policy file.

It may define:

```text
strictness policy
contract governance rules
DDT requirements
module-level policy
path-based policy
generated context policy
```

If Markdown rule docs conflict with `.harbor/policy.yaml`, prefer `.harbor/policy.yaml`.

---

## 13. `.harbor/safety.yaml`

`.harbor/safety.yaml` is the machine-readable runtime safety policy file.

It may define:

```text
protected paths
dangerous commands
deny rules
ask rules
secret handling policy
runtime safety classification
```

If Markdown rule docs conflict with `.harbor/safety.yaml`, prefer `.harbor/safety.yaml`.

---

## 14. AGENTS.md

`AGENTS.md` is the cross-tool lightweight entrypoint for AI coding agents.

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

It should not contain full Harbor tutorials or complete project architecture.

---

## 15. Project Rules

Project Rules are repository-specific rules.

Canonical path:

```text
.harbor/rules/project-rules.md
```

Project Rules define:

```text
project overview
technology stack
directory map
strictness map
project-specific contract sources
verified test commands
project-specific safety boundaries
skill routing
common task rules
```

Project Rules should not duplicate generic Harbor rule docs.

---

## 16. Skills

Skills are on-demand task workflows.

Canonical exported path:

```text
.agents/skills/<skill-name>/SKILL.md
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

Skills answer:

```text
How do I perform this specific task?
```

Skills are workflow entrypoints.

Skills are not source of truth.

---

## 17. Source of Truth

Source of Truth means the primary source that defines real project behavior or policy.

Examples:

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

Generated context and skills are not primary sources of truth.

---

## 18. Generated Context

Generated Context means Harbor-created project or module summaries under:

```text
.harbor/views/**
```

Generated context helps agents orient themselves.

Generated context should be refreshed when underlying source of truth changes.

Generated context should not override source code, schemas, tests, policy, or diary.

---

## 19. Contract

A Contract is any source that defines expected behavior, structure, boundary, side effect, or externally visible result.

Contract sources may include:

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

Contract does not mean docstring only.

---

## 20. Contract Impact

Contract Impact means a change affects expected behavior, structure, boundary, side effect, or externally visible result.

Examples:

```text
behavior changes
args changes
returns changes
raises changes
schema changes
side effects changes
state changes
idempotency changes
security changes
permission changes
persistence changes
event shape changes
database shape changes
export format changes
CLI argument changes
CLI output changes
JSON output changes
file write target changes
exit code changes
configuration behavior changes
migration behavior changes
user-visible result changes
external-visible result changes
```

If a caller, user, test, downstream module, agent, or external system must change expectations, treat it as Contract Impact.

---

## 21. Semantic Contract

Semantic Contract defines what something means and how it should behave.

It may include:

```text
why the function or module exists
when it should be used
when it should not be used
behavior
invariants
side effects
idempotency
failure modes
security requirements
dependency assumptions
```

---

## 22. Interface Contract

Interface Contract defines how something is called or accessed.

It may include:

```text
function signature
method signature
Args
Returns
Raises
HTTP method
endpoint path
request body
response body
status code
CLI arguments
CLI options
tool input
tool output
exit code
```

---

## 23. Data Contract

Data Contract defines data structure.

It may include:

```text
Pydantic model
JSON schema
TypeScript type
Zod schema
database table
migration
event shape
export format
fixture structure
snapshot output
golden file
```

---

## 24. Behavior Contract

Behavior Contract defines observable behavior.

It may include:

```text
user-visible output
external-visible result
file write behavior
state mutation
database write behavior
retry behavior
timeout behavior
permission behavior
error handling
compatibility behavior
```

---

## 25. Safety Contract

Safety Contract defines what must not happen.

Examples:

```text
secrets must not be printed
user data must not be deleted silently
destructive operations require confirmation
production config must not be changed silently
permissions must not be relaxed silently
```

Common sources:

```text
.harbor/safety.yaml
.harbor/policy.yaml
.harbor/rules/runtime-safety.md
tests
security docs
```

---

## 26. Semantic Drift

Semantic Drift means implementation and contract no longer agree.

Semantic drift requires a comparable contract.

Missing contract alone is not semantic drift.

Examples:

```text
docstring says invalid input raises ValueError, but implementation returns None
schema says a field is required, but implementation accepts missing value
CLI JSON output changes but tests remain old
file write side effect is added but not declared
tests still verify old behavior after contract changed
```

Semantic Drift may indicate:

```text
implementation bug
stale docstring
stale schema
stale tests
missing DDT
false positive

Related but distinct:
Contract Gap: no comparable contract exists
```

---

## 26.1 Contract Presence

Contract Presence 是 Harbor 对“契约源是否可用于比较”的状态判定。

常见状态：

```text
present
missing
empty
non_contract_doc
malformed
```

---

## 26.2 Contract Required

Contract Required 表示某个 target 是否默认必须具备契约源。

常见 required 目标：

```text
public API
strict targets
CLI behavior
JSON output
to_dict / report_to_dict
file write behavior
schema / parser / generated view formatter
user-visible or external-visible behavior
```

---

## 27. Contract Gap

Contract Gap means a target requires a contract but no valid contract source exists.

Contract Gap is not semantic drift.

Example:

```text
A function writes files, but no docstring, schema, test, or rule describes the write behavior.
```

---

## 27.1 Skipped No Contract

Skipped No Contract means the target does not require a contract, so semantic audit is skipped.

It should not be treated as semantic drift.

---

## 27.2 Contract Parse Error

Contract Parse Error means a contract source exists, but parsing or classification is not reliable.

This differs from Contract Gap:

```text
Contract Gap = required contract source missing
Contract Parse Error = source exists but unusable
```

---

## 28. Schema Gap

Schema Gap means schema and implementation are not aligned.

Example:

```text
A Pydantic model says a field is required, but the API allows it to be omitted.
```

---

## 29. Test / DDT Gap

Test / DDT Gap means expected contract behavior is not adequately tested.

Example:

```text
A strict CLI JSON output contract exists, but there is no test for stable JSON keys.
```

---

## 30. DDT

DDT means Docstring/Contract-Driven Testing.

DDT binds tests to contracts, not merely to the current implementation.

DDT may bind tests to:

```text
docstring
schema
public behavior
CLI output
JSON output
file write behavior
fixtures
golden files
```

Core principle:

```text
Tests should verify the intended contract, not blindly follow the newest implementation.
```

---

## 31. l3_version

`l3_version` is an explicit contract version identifier used by DDT.

Example:

```python
@harbor_ddt_target("module.func", l3_version=1)
def test_func_success_path():
    ...
```

For strict targets, explicit `l3_version` is required where DDT binding is used.

---

## 31.1 DDT Version Baseline Missing

`DDT_VERSION_BASELINE_MISSING` / `ddt_version_baseline_missing` means DDT binding is structurally valid, but no L3 version baseline is found.

It is advisory, not blocking by default.

It does not mean DDT is semantically validated forever.

## 32. strategy="latest"

`strategy="latest"` means a test follows the newest known contract.

Example:

```python
@harbor_ddt_target("module.func", strategy="latest")
def test_func_success_path():
    ...
```

It may be acceptable for standard or light targets if project policy permits.

It is forbidden for strict targets.

Reason:

```text
strategy="latest" can make tests silently follow the newest contract and produce false green results.
```

---

## 33. False Green

False Green means tests pass but no longer verify the intended contract.

Common causes:

```text
strategy="latest" on strict targets
updating assertions to match broken implementation
deleting failing tests without contract decision
weak assertions
snapshots updated without review
fixtures updated without checking contract
mocking away the behavior under test
testing implementation detail instead of public behavior
```

---

## 34. Strictness

Strictness defines how strongly a target must be governed.

Default levels:

```text
strict
standard
light
```

Use `.harbor/policy.yaml` as the source of truth when available.

---

## 35. Strict

Strict targets are high-risk, public, user-visible, security-sensitive, schema-sensitive, or critical-path targets.

Examples:

```text
public API
public CLI
public JSON output
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
external integration
tool schema
MCP tool schema
```

Strict targets usually require:

```text
explicit Contract
tests / DDT
explicit l3_version where DDT binding is used
no strategy="latest"
semantic drift check
Diary Draft for important changes
generated context refresh if needed
```

---

## 36. Standard

Standard targets are ordinary business logic or stable internal APIs.

Examples:

```text
service functions
repositories
module-level workflows
non-critical data transformations
ordinary business logic
```

Standard targets should usually have tests.

DDT is recommended when behavior is meaningful or reused.

---

## 37. Light

Light targets are low-risk internal helpers or utilities.

Examples:

```text
internal helpers
low-risk utilities
test helpers
script-local functions
small formatting helpers
```

Light targets do not require heavy governance unless they become part of a strict path.

---

## 38. Runtime Safety

Runtime Safety defines how AI agents should handle risky operations.

It classifies operations as:

```text
ALLOW
ASK
DENY
```

It covers:

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
user data
external network access
```

Detailed rules live in:

```text
.harbor/rules/runtime-safety.md
.harbor/safety.yaml
```

---

## 39. ALLOW

`ALLOW` means an operation is low risk, local, reversible, and clearly within the user’s request.

Examples:

```text
reading ordinary source files
reading tests
running local tests
running harbor stale
running harbor doctor
running harbor workspace inspect
editing ordinary source files within requested scope
```

---

## 40. ASK

`ASK` means an operation requires explicit user confirmation before execution.

Examples:

```text
deleting files
modifying .env
changing migrations
changing CI/CD
installing dependencies
running git push
running git reset --hard
changing production config
modifying .harbor/*.yaml
modifying generated skills
```

---

## 41. DENY

`DENY` means an operation should not be performed because it is unsafe, secret-exposing, outside the user’s request, or violates policy.

Examples:

```text
printing secrets
exfiltrating credentials
deleting user data without explicit request
auto-relaxing AI tool permissions
generating allow-all permission configs
fabricating command execution results
```

---

## 42. Diary

Diary is structured decision memory.

Canonical path:

```text
.harbor/diary/YYYY-MM.jsonl
```

Diary records why important changes happened.

Diary is not a changelog replacement.

Diary is not a commit message replacement.

---

## 43. Diary Draft

Diary Draft is a proposed decision record that has not been written to disk.

Use a Diary Draft when a decision should be remembered but the user has not explicitly requested writing.

---

## 44. Written Diary Entry

Written Diary Entry means a JSONL record was actually written to:

```text
.harbor/diary/YYYY-MM.jsonl
```

Do not claim a diary entry was written unless the write was actually executed and observed.

---

## 45. Changelog

Changelog records user-visible changes by version.

It answers:

```text
what changed for users
which version contains the change
whether the change is breaking
how users should adapt
```

Changelog is not a Diary replacement.

---

## 46. ADR

ADR means Architecture Decision Record.

ADR is used for larger, long-lived architecture decisions.

Diary is lighter and more frequent.

A significant Diary entry may later be promoted into an ADR.

---

## 47. Generated View

Generated View means a Harbor-generated context file under:

```text
.harbor/views/**
```

Generated views summarize project or module state.

They are not source of truth.

---

## 48. L2 README

L2 README is a module-level generated context view.

Canonical path:

```text
.harbor/views/l2/<module>/README.md
```

It summarizes module responsibilities, public surfaces, contract sources, and testing guidance.

It is not the primary source of behavior.

---

## 49. Module Capsule

Module Capsule is a generated module context package.

Canonical path:

```text
.harbor/views/modules/<module>/
```

Typical files:

```text
module-card.md
review-checklist.md
debug-playbook.md
```

It helps agents understand and debug modules without reading the entire repository.

---

## 50. module-card.md

`module-card.md` summarizes a module.

It may include:

```text
module purpose
main files
public surfaces
contract sources
strictness hints
important tests
known risks
```

---

## 51. review-checklist.md

`review-checklist.md` provides module-specific review guidance.

It may include:

```text
contract checks
DDT checks
schema checks
runtime safety checks
generated context checks
Diary triggers
```

---

## 52. debug-playbook.md

`debug-playbook.md` provides module-specific debugging guidance.

It may include:

```text
common failure modes
where to start reading
which tests to run
which contracts to inspect
which Harbor commands to use
```

---

## 53. Project Structure View

Project Structure View is the generated repository-level context view.

Canonical path:

```text
.harbor/views/project-structure.md
```

It summarizes repository layout, modules, and context loading guidance.

---

## 54. Context Refresh

Context Refresh means regenerating Harbor generated context after underlying sources change.

Common commands:

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

## 55. Stale

Stale means generated context no longer reflects the underlying source of truth.

Examples:

```text
L2 README describes an old public function
Module Capsule points to removed tests
Project Structure View omits a new module
```

Use:

```powershell
harbor stale
```

or:

```powershell
harbor stale --format json
```

to inspect staleness.

---

## 56. Doctor

Doctor means broader Harbor health check.

Use:

```powershell
harbor doctor
```

or:

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
legacy or compatibility warnings
```

---

## 57. Workspace Inspect

Workspace Inspect means inspecting Harbor workspace status.

Use:

```powershell
harbor workspace inspect
```

or:

```powershell
harbor workspace inspect --format json
```

It is read-only.

---

## 58. Workspace Migration Dry-run

Workspace Migration Dry-run means previewing a workspace migration or cleanup plan without writing files.

Use:

```powershell
harbor workspace migrate --dry-run
```

or:

```powershell
harbor workspace migrate --dry-run --format json
```

It must remain read-only.

It must not write, move, or delete files.

It is not part of the default coding workflow.

---

## 59. Baseline

Baseline means the accepted Harbor reference state used to detect drift.

Changing baseline should be intentional.

---

## 60. Accept

Accept means accepting the new Harbor baseline.

Command:

```powershell
harbor accept
```

Do not run `harbor accept` merely to hide unresolved drift.

Run it only when the user explicitly requests it and the new state is verified.

---

## 61. Lock

Lock is a legacy or lock-style baseline operation.

Command:

```powershell
harbor lock
```

Do not run it unless the user explicitly requests it.

---

## 62. Checkpoint

Checkpoint means checking current changes against Harbor baseline or contract expectations during work.

Command:

```powershell
harbor checkpoint
```

Use it after meaningful implementation progress.

---

## 63. Finish

Finish means completing a Harbor workflow step.

Command:

```powershell
harbor finish
```

By default, finish should not silently write generated context unless the command or workflow explicitly says so.

---

## 64. finish --sync-context

`harbor finish --sync-context` means finishing work and explicitly refreshing changed generated context.

It may refresh:

```text
changed L2 README files
changed Module Capsules
```

Use it when code or contract changes may affect generated context.

---

## 65. harbor log

`harbor log` writes or records a diary entry.

Do not run it unless the user explicitly requests it or the active workflow explicitly includes writing Diary entries.

---

## 66. Tool Honesty

Tool Honesty means never claiming that a command was run unless it was actually run and observed.

Applies to:

```text
tests
lint
type checks
build
harbor checkpoint
harbor stale
harbor doctor
harbor workspace inspect
CI
```

Allowed wording:

```text
已运行，结果是...
未运行，建议你运行...
当前环境无法运行...
我只做了静态审查，未执行命令...
```

---

## 67. Managed Block

Managed Block means a marked region in a user file that Harbor may safely update without overwriting unrelated user content.

Example:

```markdown
<!-- harbor-spec:start version=1.3.0 -->
...
<!-- harbor-spec:end -->
```

Managed blocks are useful for AGENTS.md integration.

---

## 68. Managed File

Managed File means a file generated or maintained by Harbor with a marker.

Example marker:

```markdown
<!-- harbor-spec:managed version=1.3.0 kind=rule -->
```

Managed files should still be updated carefully.

Do not overwrite user-authored files unless the path is clearly managed or the user confirms.

---

## 69. External Tool Adapter

External Tool Adapter means a Harbor-generated or Harbor-compatible file for a specific AI coding tool.

Examples:

```text
CLAUDE.md
.cursor/rules/*.mdc
TRAE rules
.agents/skills/**
```

Adapters should route to Harbor canonical workspace rather than duplicate all rules.

---

## 70. ContractSubject

ContractSubject is the language-neutral governance target in Harbor v1.4+.

It supersedes Python-only FunctionContract as the language-neutral governance model, while Python FunctionContract remains as a compatibility layer.

---

## 71. ContractSource

ContractSource is a concrete source used to infer or compare expected contract behavior.

Examples:

```text
Python docstring
JSDoc / TSDoc
type hints
TypeScript signature
schema
fixture
snapshot
public behavior
```

---

## 72. target_id

`target_id` is Harbor's primary language-neutral target identity.

It is used for cross-language contract governance in v1.4+.

---

## 73. legacy func_id

`func_id` remains for compatibility with existing Python-oriented consumers. `target_id` is the primary neutral identity for new cross-language governance.

---

## 74. TypeScript Contract Governance

TypeScript Contract Governance means Harbor governance applied to TypeScript contract targets.

In v1.4.x, TypeScript support is MVP-scoped:

```text
opt-in
.ts-only default scanning
presence/checkpoint/next guidance
```

TypeScript semantic audit and TypeScript DDT are not supported in v1.4.x.

---

## 75. unsupported_syntax_advisory

`unsupported_syntax_advisory` means the target was discovered but current parser capability does not fully support the syntax.

It is advisory and should not be treated as `contract_parse_error` by default in TypeScript v1.4.x MVP flow.

---

## 76. Diary Draft

Diary Draft is reviewable text proposed by AI/human and not yet written to `.harbor/diary/YYYY-MM.jsonl`.

Diary Draft is not source-of-truth memory until explicitly written.

---

## 77. Change Window

Change Window means the bounded evidence slice used to summarize meaningful changes.

Typical evidence may include:

```text
checkpoint snapshots
accept/finish snapshots
reports
git status
changed files
validation results
```

`harbor log draft` may use Change Window evidence, but Draft does not become source-of-truth memory until a real Diary write happens.

---

## 78. Change Window Snapshot

Change Window Snapshot is a runtime evidence artifact captured for a bounded change window.

It is runtime evidence, not source of truth.

Typical examples:

```text
checkpoint snapshot
finish snapshot
accept snapshot
report-derived snapshot metadata
```

---

## 79. Log Draft

Log Draft means a reviewable Diary Draft generated from bounded evidence.

Typical command:

```powershell
harbor log draft
```

Rules:

```text
Log Draft does not write .harbor/diary/**.
Log Draft does not call LLM in v1.4.1.
LLM-assisted draft is future work only and must be explicit opt-in.
Any future LLM-assisted draft must not send secrets, credentials, private data, .env contents, file bodies, or diff bodies to an LLM.
Log Draft does not output file content bodies or diff bodies.
Log Draft writes latest draft cache under .harbor/state/log/latest-draft.md and .harbor/state/log/latest-draft.json.
Log Draft --save writes a Saved Draft Report under .harbor/reports/**.
Log Draft may write reviewable output to .harbor/reports/** when explicitly requested.
```

---

## 80. Latest Draft Cache

Latest Draft Cache means the most recent reviewable draft cache stored under:

```text
.harbor/state/log/latest-draft.md
.harbor/state/log/latest-draft.json
```

It is runtime state.

It may be overwritten by later draft runs.

It is not source-of-truth decision memory.

---

## 81. Saved Draft Report

Saved Draft Report means a reviewable draft artifact stored under:

```text
.harbor/reports/log-draft-*.md
.harbor/reports/log-draft-*.json
```

It is not source of truth.

It may be created by `harbor log draft --save` or explicit `--output`.

---

## 82. Log Write

`harbor log write` is the controlled write path that reads an allowlisted draft source and appends a Written Diary Entry to `.harbor/diary/YYYY-MM.jsonl`.

Rules:

```text
Log Write reads latest draft by default.
Log Write --yes is explicit authorization for write flow.
Log Write without --yes requires interactive confirmation and is rejected in non-interactive environments.
Log Write updates last_log_marker after a successful Diary write.
```

---

## 83. Written Diary Entry

Written Diary Entry means a Diary record actually written to `.harbor/diary/YYYY-MM.jsonl`.

Written Diary Entry is source-of-truth decision memory.

Draft does not equal Written Diary Entry.

---

## 84. Source-of-truth Decision Memory

Source-of-truth Decision Memory means the canonical written decision record stored under:

```text
.harbor/diary/YYYY-MM.jsonl
```

In v1.4.1, Draft Cache and Saved Draft Report are not source-of-truth decision memory.

---

## 85. Runtime State

Runtime State means local control metadata or cached workflow state under `.harbor/state/**`.

It may help Harbor resume, bound, or summarize work.

It is not source of truth.

Examples:

```text
change-window snapshots
latest-draft cache
last_log_marker
```

---

## 86. Explicit Authorization / --yes

Explicit Authorization means the user or operator deliberately authorizes a write or other high-impact action.

For log workflow:

```text
harbor log write --yes is explicit authorization for non-interactive or direct write flow.
without --yes, harbor log write requires interactive confirmation.
```

---

## 87. Evidence Boundary

Evidence Boundary means the limit on what inputs and outputs may be used when generating a Diary Draft or Log Draft.

Typical allowed evidence:

```text
change-window snapshots
reports
git status
validation outcomes
bounded metadata
```

Typical excluded content:

```text
secret values
.env contents
raw file bodies
raw diff bodies
private credentials
```

---

## 88. last_log_marker

`last_log_marker` is the marker used to identify the evidence boundary since the last meaningful log point.

It helps bound Log Draft generation for flows such as:

```text
--since-last-log
--since-last-accept
```

It is runtime control metadata, not source-of-truth decision memory.

---

## 89. Final Principle

When Harbor terms are unclear, prefer this interpretation:

```text
Source of truth defines behavior.
Rules define governance.
Generated views summarize context.
Skills guide workflows.
Diary preserves reasons.
Safety policy controls risky operations.
```

Harbor-spec exists to keep AI coding fast without letting engineering context drift.

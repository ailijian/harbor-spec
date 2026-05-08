---
name: harbor-code-review
description: Use when reviewing code, diffs, PRs, implementation correctness, semantic drift, missing tests, runtime safety risks, generated context drift, or contract consistency under Harbor-spec.
---

# Harbor Code Review Skill

Version: Harbor-spec v1.3.0  
Purpose: Code review workflow for Harbor-managed repositories

---

## 1. Purpose

Use this skill to review code changes under Harbor-spec.

This skill helps identify:

```text
implementation bugs
semantic drift
contract gaps
schema gaps
test / DDT gaps
runtime safety risks
generated context gaps
Diary gaps
breaking change risks
```

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

```text id="6wweq0"
A Harbor review checks not only whether code works, but whether code, contracts, tests, generated context, decision memory, and safety boundaries remain aligned.
```

---

## 2. When to Use

Use this skill when reviewing:

```text id="nccws4"
code changes
diffs
PRs
patches
AI-generated code
refactors
bug fixes
feature changes
contract-impacting changes
test changes
DDT changes
schema changes
CLI output changes
JSON output changes
file write behavior changes
workspace layout changes
generated context changes
runtime safety changes
```

Also use when asked to check:

```text id="6rz9vn"
implementation correctness
semantic drift
contract consistency
schema consistency
missing tests
false green tests
runtime safety risk
generated context drift
Diary need
breaking change risk
```

---

## 3. Boundary With AGENTS.md, Project Rules, and Other Skills

### 3.1 AGENTS.md

`AGENTS.md` is the lightweight cross-tool entrypoint.

Use it for:

```text id="8g9k5n"
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

```text id="055h4b"
.harbor/rules/project-rules.md
```

Use Project Rules for:

```text id="egon3k"
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

Use related skills when needed:

```text id="pelvq5"
harbor-contract-change
  Use when the review finds or involves Contract Impact that requires implementation or contract changes.

harbor-ddt-diary
  Use when the review requires test updates, DDT binding changes, l3_version changes, Diary Drafts, changelog, or release notes.

harbor-safety-preflight
  Use before risky operations, protected file changes, dependency changes, migrations, CI/CD, destructive commands, or .harbor/*.yaml changes.

harbor-context-refresh
  Use when generated context under .harbor/views/** is stale or needs refresh.

harbor-workspace-migration-plan
  Use for workspace diagnostics, migration dry-run, cleanup planning, or canonical workspace changes.
```

This skill may route to these skills, but should not replace them.

---

## 4. Context Loading Order

Before reviewing source files, load only necessary context.

Default order:

```text id="kuztwf"
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

6. Relevant contract rules when needed:
   .harbor/rules/contract-rules.md

7. Relevant DDT rules when needed:
   .harbor/rules/ddt-rules.md

8. Relevant runtime safety rules when needed:
   .harbor/rules/runtime-safety.md

9. Relevant diary rules when needed:
   .harbor/rules/diary-rules.md

10. Relevant source files

11. Relevant tests, fixtures, snapshots, schemas, or DDT targets
```

Do not read the whole repository unless the canonical project structure, L2 README, Module Capsule, source files, and tests are insufficient.

Generated context helps orientation.

Generated context is not source of truth.

Source code, tests, schemas, policy, and diary define the actual project state.

---

## 5. Review Dimensions

Check the change across these dimensions.

```text id="krj39g"
implementation correctness
implementation vs contract
schema / type consistency
args / returns / raises consistency
error paths
side effects
idempotency
runtime safety
tests / DDT coverage
semantic drift
breaking change risk
generated context update need
Diary need
tool honesty
```

Do not limit review to syntax or whether the code “looks fine”.

---

## 6. Step 1: Identify Review Scope

Classify the reviewed change.

Possible scopes:

```text id="nz584t"
feature
bugfix
refactor
test-only
docs-only
schema
CLI
JSON output
file write behavior
workspace layout
generated context
runtime safety
DDT / Diary
release / packaging
unknown
```

If scope is unclear, inspect the diff or changed files.

Do not assume low risk without evidence.

---

## 7. Step 2: Determine Contract Impact

Return one of:

```text id="ji8vis"
Contract Impact: yes
Contract Impact: no
Contract Impact: uncertain
```

Treat as Contract Impact when the change affects:

```text id="mx389i"
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

If uncertain, inspect relevant contract sources.

Do not silently treat uncertainty as no impact.

---

## 8. Step 3: Determine Strictness

Use `.harbor/policy.yaml` as the source of truth when available.

Default strictness:

```text id="6bxxqa"
strict
standard
light
```

Treat as `strict` when the change touches:

```text id="gxir5r"
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

If a helper appears light but is used by a strict path, upgrade the review strictness.

---

## 9. Step 4: Review Implementation Correctness

Check:

```text id="b9qvny"
does the code implement the intended behavior?
does it handle expected inputs?
does it handle invalid inputs?
does it preserve invariants?
does it preserve idempotency if promised?
does it introduce hidden side effects?
does it change file writes?
does it change external calls?
does it change user-visible behavior?
does it change errors or exceptions?
does it change path handling?
does it change deterministic output?
```

Mark confirmed issues only when there is evidence.

Mark possible issues when evidence is incomplete but risk is real.

---

## 10. Step 5: Review Contract Consistency

Inspect relevant contract sources:

```text id="mclozd"
docstring
type hints
Pydantic model
FastAPI route
OpenAPI schema
TypeScript type
Zod schema
database migration
event schema
CLI schema
MCP tool schema
JSON output contract
snapshot output
golden file
tests / fixtures
public behavior
user-visible behavior
file write behavior
```

Look for:

```text id="8fbsmg"
implementation differs from docstring
schema differs from implementation
tests verify old behavior
CLI output changes without contract update
JSON output changes without schema or test update
file write behavior not declared
side effects not documented
Raises path differs from contract
strictness metadata missing or wrong
```

Use labels:

```text id="umey9i"
Confirmed Semantic Drift
Possible Semantic Drift
Contract Gap
Schema Gap
Test / DDT Gap
```

---

## 11. Step 6: Review Tests and DDT

Check:

```text id="dhbd1y"
are relevant tests present?
do tests verify the contract or only current implementation?
are strict targets bound to explicit l3_version?
is strategy="latest" used on strict targets?
were snapshots updated without contract reasoning?
were fixtures updated blindly?
are failure paths covered?
are side effects covered?
are CLI / JSON output contracts covered?
are file write behaviors covered?
```

For strict targets, this is forbidden:

```python id="du7i85"
@harbor_ddt_target("module.func", strategy="latest")
```

Use label:

```text id="kem5a5"
DDT Violation
```

when found.

Use:

```text id="m6dkyr"
DDT False Green Risk
```

when tests may pass while the contract remains broken.

---

## 12. Step 7: Review Runtime Safety

Check whether the change or suggested fix involves:

```text id="hzvbq3"
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
generated skills
external network access
```

If yes, classify safety:

```text id="jvp23y"
ALLOW
ASK
DENY
```

Use `.harbor/safety.yaml` as source of truth when available.

Use `harbor-safety-preflight` before performing risky operations.

Do not silently approve or perform high-risk actions.

---

## 13. Step 8: Review Generated Context

Generated context lives under:

```text id="11okgq"
.harbor/views/**
```

Check whether the change affects:

```text id="qu2mw5"
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
review workflow
```

If yes, generated context may need refresh.

Typical commands:

```powershell id="0m8a67"
harbor project structure --write
harbor docs --changed --write
harbor module seal --changed --write
harbor finish --sync-context
harbor stale
harbor doctor
```

Do not manually edit `.harbor/views/**` as project truth.

Use label:

```text id="x7pceb"
Generated Context Gap
```

when generated context is likely stale or missing.

---

## 14. Step 9: Review Diary Need

Diary records why important changes happened.

Canonical Diary path:

```text id="r56a8n"
.harbor/diary/YYYY-MM.jsonl
```

Diary Draft may be needed for:

```text id="0f9nox"
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

Use label:

```text id="m49n07"
Diary Gap
```

when a decision should be recorded but no Diary Draft or entry exists.

Do not claim Diary was written unless it was actually written.

---

## 15. Step 10: Review Breaking Change Risk

A breaking change occurs when existing users, callers, scripts, agents, tests, or downstream systems must change.

Check whether the change:

```text id="7ipsva"
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

If risk exists, mark:

```text id="ygmn5u"
Breaking Change: yes / uncertain
```

and explain affected consumers.

Do not hide uncertain breaking risk.

---

## 16. Step 11: Review Workspace Behavior

The canonical Harbor workspace is:

```text id="3h93du"
.harbor/
```

Check whether the change affects:

```text id="uomq1n"
.harbor/rules/**
.harbor/views/**
.harbor/diary/**
.harbor/reports/**
.harbor/cache/**
.harbor/state/**
.harbor/exports/**
.agents/skills/**
AGENTS.md managed block
```

Workspace layout changes are Contract Impact.

`harbor workspace migrate --dry-run` must remain read-only.

Do not assume `harbor workspace migrate --write` exists.

Use:

```text id="ufxsqe"
Workspace Contract Risk
```

when workspace behavior is changed without tests, docs, or safety reasoning.

---

## 17. Review Labels

Use these labels.

```text id="fwf48o"
Confirmed Issue
Possible Issue
Possible Semantic Drift
Confirmed Semantic Drift
Contract Gap
Schema Gap
Test / DDT Gap
DDT Violation
DDT False Green Risk
Runtime Safety Risk
Generated Context Gap
Diary Gap
Breaking Change Risk
Workspace Contract Risk
Tool Honesty Issue
Suggested Improvement
```

Definitions:

```text id="s56ghx"
Confirmed Issue:
  Clear bug or violation with evidence.

Possible Issue:
  Risk is plausible but evidence is incomplete.

Possible Semantic Drift:
  Implementation may differ from contract, but more context is needed.

Confirmed Semantic Drift:
  Implementation and contract clearly disagree.

Contract Gap:
  Important behavior exists without clear contract.

Schema Gap:
  Schema and implementation disagree or schema is missing.

Test / DDT Gap:
  Contract behavior lacks adequate test coverage.

DDT Violation:
  DDT rule is clearly violated, such as strategy="latest" on strict target.

DDT False Green Risk:
  Tests may pass while the intended contract is broken.

Runtime Safety Risk:
  Operation or change may be unsafe without confirmation.

Generated Context Gap:
  .harbor/views/** likely needs refresh.

Diary Gap:
  Important decision lacks Diary Draft or entry.

Breaking Change Risk:
  Existing consumers may need migration.

Workspace Contract Risk:
  .harbor workspace behavior changed without governance.

Tool Honesty Issue:
  Result claims execution without evidence.

Suggested Improvement:
  Non-blocking improvement.
```

---

## 18. Severity Levels

Use:

```text id="o7k937"
high
medium
low
```

### High

Use high severity for:

```text id="edj77g"
data loss risk
security risk
secret exposure
breaking public contract
strict DDT violation
migration risk
auth / permission / billing risk
destructive operation risk
false claim that tests passed
```

### Medium

Use medium severity for:

```text id="bpd4em"
contract gap in standard path
missing tests for meaningful behavior
possible semantic drift
generated context stale after meaningful change
Diary missing for important but non-critical decision
```

### Low

Use low severity for:

```text id="b7evms"
small clarity issue
minor missing edge case
non-blocking style issue
light helper test suggestion
documentation improvement
```

---

## 19. Recommended Harbor Checks

Suggest or run only when appropriate.

During review:

```powershell id="hvdqf7"
harbor checkpoint
harbor stale
harbor doctor
```

For generated context changes:

```powershell id="091fjz"
harbor finish --sync-context
```

For JSON / CI-style checks:

```powershell id="abp05t"
harbor stale --format json
harbor doctor --format json
```

For workspace diagnostics:

```powershell id="5ktxzu"
harbor workspace inspect
harbor workspace migrate --dry-run
```

`harbor workspace migrate --dry-run` is read-only and not part of the default coding workflow.

Do not run unless relevant.

---

## 20. Explicit User Request Only

Do not run the following unless the user explicitly requests it:

```powershell id="bri9hp"
harbor log
harbor accept
harbor lock
harbor module promote-skill <module>
```

Never run `harbor accept` to silence unresolved drift.

Never claim Diary was written unless it was actually written.

---

## 21. Tool Honesty

Do not claim tests, lint, type checks, builds, CI, or Harbor commands were run unless actually run and observed.

Allowed wording:

```text id="ggg0ds"
已运行，结果是...
未运行，建议运行...
当前环境无法运行...
我只做了静态审查，未执行命令...
```

Forbidden wording when not executed:

```text id="ol4gfs"
测试已通过
harbor doctor 通过
stale check 已清理
lint 无问题
CI 会通过
```

If a command cannot be run, report:

```text id="velpuq"
Command not run:
Reason:
Risk:
Recommended next command:
```

Use `Tool Honesty Issue` when reviewing output that claims unobserved execution.

---

## 22. Output Format

Start every review with:

```text id="x7u085"
Review Summary:
- Overall assessment:
- Contract Impact:
- Strictness:
- Tests / DDT:
- Runtime Safety:
- Generated Context:
- Diary:
- Breaking Change Risk:
```

Then list findings.

For each finding:

```text id="9ac02d"
Finding <N>: <Label>

Location:
- <file>:<line or symbol>

Evidence:
- <specific evidence from code, contract, schema, test, generated view, or policy>

Risk:
- <why this matters>

Recommended fix:
- <specific fix>

Severity:
- high / medium / low
```

If no blocking Harbor-spec issue is found, say:

```text id="kggzi1"
No blocking Harbor-spec issue found.
```

Still mention non-blocking suggestions if useful.

---

## 23. Review Summary Guidance

Use concise but explicit summaries.

Example:

```text id="q5tp8s"
Review Summary:
- Overall assessment: No blocking issue found, but one DDT gap should be addressed before release.
- Contract Impact: yes, JSON output shape changed.
- Strictness: strict, because public CLI JSON is affected.
- Tests / DDT: missing stable key test.
- Runtime Safety: no high-risk operation detected.
- Generated Context: refresh likely needed.
- Diary: Diary Draft recommended due to public JSON contract change.
- Breaking Change Risk: uncertain, downstream scripts may depend on previous key name.
```

---

## 24. What Counts as Evidence

Evidence may come from:

```text id="pafccz"
source code
tests
fixtures
schemas
docstrings
type hints
.harbor/policy.yaml
.harbor/safety.yaml
.harbor/rules/*.md
.harbor/views/**
.harbor/diary/**
command output actually observed
```

Generated context may support review orientation.

Generated context should not override source code, tests, schemas, policy, or diary.

---

## 25. Common Mistakes

Avoid:

```text id="kocjsy"
reviewing only code style
ignoring contract impact
ignoring tests / DDT
ignoring runtime safety
ignoring generated context drift
ignoring Diary need
treating generated context as source of truth
treating skills as source of truth
marking Contract Impact: no without reasoning
missing strict target strategy="latest"
failing to flag JSON output changes
failing to flag file write behavior changes
failing to flag hidden breaking changes
claiming tests passed without execution evidence
```

---

## 26. Final Principle

A Harbor code review asks:

```text id="sux8zv"
Does the change keep implementation, contracts, tests, generated context, decision memory, and safety boundaries aligned?
```

A change can be syntactically correct and still fail Harbor review if it creates drift.

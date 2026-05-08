---
name: harbor-ddt-diary
description: Use when updating tests, DDT bindings, l3_version, contract versions, Diary Drafts, changelogs, release notes, or important architectural decisions under Harbor-spec.
---

# Harbor DDT and Diary Skill

Version: Harbor-spec v1.3.0  
Purpose: DDT and decision-memory workflow for Harbor-managed repositories

---

## 1. Purpose

Use this skill when a task involves tests, DDT bindings, contract versions, Diary Drafts, release notes, changelogs, or important decisions.

This skill connects two Harbor layers:

```text
DDT:
  tests should verify contracts, not merely the current implementation.

Diary:
  important decisions should preserve why the change happened.
```

This skill is an on-demand workflow entrypoint.

It is not source of truth.

It must follow:

```text
AGENTS.md
.harbor/policy.yaml
.harbor/safety.yaml
.harbor/rules/ddt-rules.md
.harbor/rules/diary-rules.md
.harbor/rules/contract-rules.md
.harbor/rules/runtime-safety.md
.harbor/rules/project-rules.md, if present
```

Core principle:

```text
Tests should verify the intended contract, and Diary should preserve the reason behind important changes.
```

---

## 2. When to Use

Use this skill when the task involves:

```text
adding tests
updating tests
updating DDT bindings
changing l3_version
changing contract versions
reviewing test coverage
reviewing false green risk
updating fixtures
updating snapshots
updating golden files
creating Diary Drafts
writing Diary entries
updating changelog
updating release notes
recording architecture decisions
recording important bugfixes
recording workflow decisions
recording runtime safety decisions
```

Also use this skill after contract-impacting work when you need to decide:

```text
Are tests aligned with the intended contract?
Should l3_version change?
Is strategy="latest" allowed here?
Are snapshots or fixtures stale?
Does this decision need a Diary Draft?
Does this change need release notes?
```

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
verified test commands
project-specific strictness map
project-specific DDT conventions
project-specific Diary triggers
project-specific release note rules
project-specific safety-sensitive paths
```

If this skill conflicts with Project Rules, inspect `.harbor/policy.yaml` and `.harbor/safety.yaml`.

Machine policy wins over Markdown rules.

---

### 3.3 Related Skills

Use related skills when needed:

```text
harbor-contract-change
  Use when DDT or Diary work reveals Contract Impact requiring contract or implementation changes.

harbor-code-review
  Use when reviewing code, tests, semantic drift, contract consistency, or false green risk.

harbor-safety-preflight
  Use before modifying protected files, .harbor/*.yaml, dependencies, migrations, CI/CD, or generated skills.

harbor-context-refresh
  Use when generated context under .harbor/views/** needs refresh.

harbor-workspace-migration-plan
  Use when Diary or DDT work involves workspace layout, migration dry-run, or canonical workspace changes.
```

This skill may route to these skills, but should not replace them.

---

## 4. Context Loading Order

Before editing tests, DDT bindings, Diary records, release notes, or changelogs, load only necessary context.

Default order:

```text
1. AGENTS.md

2. Project Rules, if present:
   .harbor/rules/project-rules.md

3. DDT rules:
   .harbor/rules/ddt-rules.md

4. Diary rules:
   .harbor/rules/diary-rules.md

5. Contract rules, if Contract Impact is involved:
   .harbor/rules/contract-rules.md

6. Runtime safety rules, if risky write or protected path is involved:
   .harbor/rules/runtime-safety.md

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

12. Relevant tests, fixtures, snapshots, golden files, DDT targets

13. Relevant Diary entries:
   .harbor/diary/YYYY-MM.jsonl

14. Relevant changelog or release notes, if applicable
```

Do not read the whole repository unless the canonical project structure, L2 README, Module Capsule, source files, and tests are insufficient.

Generated context helps orientation.

Generated context is not source of truth.

---

## 5. Step 1: Identify Task Type

Classify the task as one or more of:

```text
test add
test update
DDT binding update
l3_version update
fixture update
snapshot update
golden file update
coverage review
false green review
Diary Draft
Diary write
changelog update
release note update
architecture decision
bugfix decision
contract decision
runtime safety decision
workspace decision
```

If the task type is unclear, inspect the user request and changed files.

Do not assume a test change is low risk.

Tests can become stale, overfit, or falsely green.

---

## 6. Step 2: Determine Contract Impact

Before updating tests or Diary, decide:

```text
Contract Impact: yes
Contract Impact: no
Contract Impact: uncertain
```

Use `yes` when the underlying change affects:

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

If tests are changing but implementation and contract are not, inspect whether the tests were stale, weak, or incorrectly written.

If Contract Impact is uncertain, inspect more context.

Do not silently treat uncertainty as no impact.

---

## 7. Step 3: Determine Strictness

Use `.harbor/policy.yaml` as the source of truth when available.

Default strictness:

```text
strict
standard
light
```

Treat as `strict` when tests or Diary involve:

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

Strict targets require:

```text
explicit contract
tests / DDT coverage
explicit l3_version where DDT binding is used
no strategy="latest"
semantic drift check
Diary Draft for important changes
generated context refresh if needed
```

---

## 8. Step 4: DDT Binding Decision

When DDT binding is involved, decide:

```text
Binding:
- explicit l3_version
- strategy="latest"
- no formal binding
- comment binding
- uncertain
```

For strict targets:

```text
use explicit l3_version
never use strategy="latest"
```

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

If the project does not implement a DDT decorator, preserve binding intent with comments:

```python
# harbor-ddt-target: module.func
# l3_version: 1
def test_func_success_path():
    ...
```

When a strict target uses `strategy="latest"`, mark:

```text
[DDT Violation]
Strict target must not use strategy="latest".
```

---

## 9. Step 5: l3_version Decision

Upgrade `l3_version` when the contract changes in a way that affects test expectations.

Examples:

```text
return shape changes
error behavior changes
schema requirement changes
side effect changes
idempotency changes
security behavior changes
CLI output changes
JSON output changes
file write behavior changes
public behavior changes
```

Usually no `l3_version` upgrade is needed for:

```text
wording polish in Decoration Area
non-normative examples
formatting
comments
internal implementation changes with identical behavior
```

If uncertain, state:

```text
l3_version update: uncertain
```

and inspect affected contract sources.

Do not blindly update all bindings to the latest version.

Every binding update should represent a reviewed contract decision.

---

## 10. Step 6: DDT Coverage Review

Review whether tests verify the intended contract.

Basic coverage dimensions:

```text
Args
Returns
Raises
main success path
invalid input
empty input
boundary input
side effects
idempotency
state changes
```

Strict target coverage may also include:

```text
schema compatibility
JSON output shape
CLI output shape
exit code
file writes
database writes
external service failure
timeout
retry behavior
permission failure
security behavior
user-visible output
path normalization
absolute path leakage prevention
backward compatibility
```

Use this format when useful:

```text
[DDT Coverage]
- Target:
- Strictness:
- Binding:
- Contract sources:
- Args coverage:
- Returns coverage:
- Raises coverage:
- Side effects coverage:
- Idempotency coverage:
- Schema / output coverage:
- Missing:
- Recommendation:
```

---

## 11. Step 7: False Green Review

Check whether tests can pass while the intended contract remains broken.

Common false green risks:

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

When suspected, mark:

```text
[DDT False Green Risk]
```

Explain:

```text
why the test can pass
which contract remains unverified
how to strengthen the test
```

---

## 12. Step 8: Fixtures, Snapshots, and Golden Files

Fixtures, snapshots, and golden files can be contract sources.

Treat changes to them carefully.

Changing any of these may be Contract Impact:

```text
fixture structure
golden file output
snapshot keys
snapshot ordering
JSON output shape
CLI output text
error output
file path format
```

Rules:

```text
do not update snapshots blindly
do not regenerate golden files without reviewing contract impact
do not hide breaking changes as snapshot updates
do not let fixtures silently follow broken implementation
```

If a snapshot or golden file changes intentionally, explain:

```text
what changed
why it changed
whether it is breaking
which contract source changed
which consumers are affected
```

---

## 13. Step 9: Runtime Safety Check

DDT and Diary work may still involve runtime safety risk.

Use safety preflight when the task involves:

```text
deleting tests or fixtures
batch-moving files
modifying .harbor/*.yaml
modifying .env or secrets
modifying migrations
changing CI/CD
installing dependencies
changing generated skills
writing Diary manually
running destructive commands
external network access
```

If safety risk exists, route to:

```text
harbor-safety-preflight
```

Do not silently perform risky operations.

---

## 14. Step 10: Diary Need Decision

Create or recommend a Diary Draft when the task involves:

```text
Contract Change
Breaking Change
important bugfix
architecture decision
security change
runtime safety policy change
migration
workspace layout change
export format change
public CLI behavior change
public JSON output change
schema change
DDT strategy change
l3_version strategy change
Agent workflow change
release-relevant decision
legacy compatibility decision
non-obvious workaround
important performance tradeoff
important reliability tradeoff
```

Usually no Diary is needed for:

```text
typo fix
formatting change
comment wording cleanup
internal variable rename
light helper cleanup
non-behavioral refactor
test helper rearrangement with no strategy change
small documentation wording improvement
minor generated context refresh with no decision change
```

If uncertain, prefer outputting a Diary Draft rather than silently dropping decision context.

---

## 15. Step 11: Diary Draft vs Written Diary Entry

Distinguish clearly:

```text
Diary Draft:
  proposed in the response, not written to disk.

Written Diary Entry:
  actually appended to .harbor/diary/YYYY-MM.jsonl.
```

Do not claim Diary was written unless the write was actually executed and observed.

Do not run:

```powershell
harbor log
```

unless the user explicitly requests it.

Preferred behavior:

```text
If Diary is needed but writing is not explicitly requested, output a Diary Draft.
```

---

## 16. Step 12: Diary Draft Format

Use this format:

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

## 17. Step 13: Written Diary Entry

Canonical Diary path:

```text
.harbor/diary/YYYY-MM.jsonl
```

Preferred command:

```powershell
harbor log -m "<message>" --type <type> --importance <importance> --visibility <visibility>
```

Example:

```powershell
harbor log -m "Switch strict DDT targets to explicit l3_version" --type test --importance high --visibility repo
```

Do not manually append JSONL unless:

```text
the user explicitly asks
or Harbor CLI is unavailable
and the user accepts manual write behavior
```

If manual JSONL is required, ensure each line is one valid JSON object.

Do not include secrets or private data.

---

## 18. Step 14: Changelog and Release Notes

Diary does not replace changelog or release notes.

Update changelog or release notes only when the change is user-visible or release-relevant.

Examples:

```text
new public CLI command
new public CLI option
changed generated file format
changed exit-code behavior
changed runtime safety behavior
changed public workflow recommendation
breaking or migration-relevant change
workspace layout change
DDT strategy change affecting users
```

Diary explains why.

Release notes explain what users need to know.

If release notes are needed but not requested, recommend them.

---

## 19. Step 15: Generated Context Refresh

Generated context lives under:

```text
.harbor/views/**
```

DDT and Diary work may require generated context refresh when changes affect:

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
review workflow
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

If generated context refresh is non-trivial, route to:

```text
harbor-context-refresh
```

Do not manually edit `.harbor/views/**` as project truth.

---

## 20. Step 16: Harbor Commands

During DDT / Diary work, useful commands may include:

```powershell
harbor checkpoint
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
harbor workspace migrate --dry-run
```

`harbor workspace migrate --dry-run` is read-only and is not part of the default coding workflow.

Do not run unless relevant.

---

## 21. Explicit User Request Only

Do not run the following unless the user explicitly requests it:

```powershell
harbor log
harbor accept
harbor lock
harbor module promote-skill <module>
```

Never run `harbor accept` to hide unresolved drift.

Never claim Diary was written unless it was actually written.

---

## 22. DDT Labels

Use these labels when reviewing DDT issues:

```text
DDT Violation
DDT Gap
DDT Stale
DDT Binding Risk
DDT False Green Risk
Missing Contract Test
Missing Edge Case
Weak Assertion
Outdated Fixture
Overfit Test
Suggested Improvement
```

Definitions:

```text
DDT Violation:
  Rule is clearly violated, such as strategy="latest" on a strict target.

DDT Gap:
  Important contract behavior lacks test coverage.

DDT Stale:
  Test still verifies old contract behavior.

DDT Binding Risk:
  Binding may silently follow new behavior or has unclear versioning.

DDT False Green Risk:
  Test can pass while contract is still violated.

Missing Contract Test:
  Contract exists but no matching test exists.

Missing Edge Case:
  Important boundary or failure mode is untested.

Weak Assertion:
  Test asserts too little to verify contract.

Outdated Fixture:
  Fixture no longer represents intended contract.

Overfit Test:
  Test depends on incidental implementation detail instead of contract.
```

---

## 23. Diary Quality Checklist

A good Diary Draft should be:

```text
specific
honest
short enough to scan
clear about reason
clear about tradeoff
clear about risks
clear about follow-up
grounded in actual changes
safe to store at the chosen visibility
```

A bad Diary Draft is:

```text
vague
too long
pure changelog
missing reason
missing risks
hiding uncertainty
claiming unrun tests passed
including secrets
inventing links or commit hashes
copying full code diffs
```

---

## 24. Privacy and Secret Safety

Do not write the following into Diary:

```text
secrets
tokens
passwords
private keys
raw .env values
private customer data
unnecessary personal data
sensitive production data
```

If a sensitive issue must be recorded, summarize safely:

```text
Summary: Tightened secret handling policy.
Reason: Previous workflow risked exposing environment values.
```

Do not include actual secret values.

---

## 25. Output Format

Return:

```text
DDT / Diary Summary:
- Task type:
- Contract Impact:
- Strictness:
- DDT binding:
- l3_version:
- Tests added:
- Tests updated:
- Fixtures / snapshots changed:
- Missing coverage:
- False green risk:
- Runtime safety:
- Generated context:
- Diary needed:
- Diary written:
- Harbor commands:
- Remaining risks:
```

If no tests were run, state:

```text
未实际运行测试。建议执行：
<command>
```

If Diary is needed but not written, include:

```text
[Diary Draft]
...
```

If Diary is not needed, include:

```text
Diary: not needed
Reason:
- ...
```

Do not invent test results or Diary writes.

---

## 26. Test Command Honesty

Do not claim tests passed unless tests were actually run and observed.

Allowed wording:

```text
已运行 pytest tests/test_example.py，结果为...
未实际运行测试。建议执行 pytest。
当前环境无法运行 pytest。
我只做了静态审查，未执行测试。
```

Forbidden wording when not executed:

```text
测试已通过
DDT 已验证
CI 会通过
```

unless actually observed.

---

## 27. Common Mistakes

Avoid:

```text
using strategy="latest" for strict targets
updating tests to match broken implementation
updating snapshots without contract review
deleting failing tests without reason
weak assertions that do not verify contract
overfitting tests to implementation details
forgetting Raises / failure path coverage
forgetting side effects coverage
forgetting file write behavior
forgetting CLI / JSON output tests
forgetting path normalization tests
claiming tests passed without running them
writing Diary for every tiny edit
skipping Diary for important contract changes
using Diary as changelog only
claiming Diary was written when only a draft was generated
including secrets or private data in Diary
inventing PR links, commit hashes, or test results
```

---

## 28. Final Principle

When updating tests or Diary, ask:

```text
Which contract is this test verifying?
Is the contract strict, standard, or light?
Is the test bound to the right contract version?
Can the test pass while the contract is still broken?
Will future agents understand why this decision was made?
```

Good DDT makes contract drift harder to hide.

Good Diary makes important reasoning harder to lose.

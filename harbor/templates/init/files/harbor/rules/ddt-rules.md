<!-- harbor-spec:managed version=1.3.0 kind=rule -->

# Harbor DDT Rules

Version: Harbor-spec v1.4.x  
Canonical path: `.harbor/rules/ddt-rules.md`  
Purpose: Rules for Docstring/Contract-Driven Testing under Harbor-spec

---

## 1. Purpose

DDT means Docstring/Contract-Driven Testing.

The purpose of DDT is to bind tests to contracts, not merely to the current implementation.

DDT helps prevent these failures:

```text
implementation changed but contract stayed stale
contract changed but tests still verify old behavior
tests were updated only to make the current implementation pass
strict targets used strategy="latest" and produced false confidence
docstring / schema / CLI / JSON output drifted away from tests
AI modified code without preserving intended behavior
```

Core principle:

```text
Tests should verify the intended contract, not blindly follow the newest implementation.
```

v1.4.x boundary reminder:

```text
DDT remains Python-first.
TypeScript DDT is not supported.
```

---

## 2. DDT Is Not Only About Docstrings

Docstrings are important contract sources.

But DDT is not limited to docstrings.

DDT may bind tests to any contract source, including:

```text
docstring
type hints
Pydantic model
FastAPI / OpenAPI schema
TypeScript type
Zod schema
database migration
event schema
CLI command schema
MCP tool schema
JSON output contract
snapshot output
golden file
fixtures
public behavior
user-visible behavior
file write behavior
```

The list above describes conceptual contract sources. In v1.4.x implementation, Harbor DDT binding remains Python-first. TypeScript type / Zod / Vitest / Jest binding is future work and must not be claimed as supported.

If multiple contract sources exist, DDT should verify the intended contract across them.

TypeScript DDT boundary in v1.4.x:

```text
Vitest / Jest are valid test runners but not Harbor DDT binding sources for TypeScript yet.
comment-based TypeScript binding is not a valid Harbor DDT binding yet.
target_id-based TypeScript DDT binding is not a valid Harbor DDT binding yet.
TS DDT-related findings should be advisory with not_supported semantics.
Do not claim TypeScript DDT coverage.
```

---

## 3. Relationship to AGENTS.md, Project Rules, and Skills

### 3.1 AGENTS.md

`AGENTS.md` contains lightweight DDT reminders that should be always visible to AI agents.

It defines:

```text
what DDT means at minimum
that strict targets must use explicit l3_version
that strategy="latest" is forbidden for strict targets
when to consider tests / DDT updates
```

It should not contain the full DDT policy.

---

### 3.2 Project Rules

Project-specific DDT rules live in:

```text
.harbor/rules/project-rules.md
```

Project Rules may define:

```text
which paths are strict
which modules require DDT
which test commands are verified
which fixtures or golden files are canonical
which DDT conventions are local to the project
```

---

### 3.3 Machine Policy

Machine-readable policy may live in:

```text
.harbor/policy.yaml
```

If `.harbor/policy.yaml` defines DDT requirements, use it as the source of truth.

Examples of machine policy:

```text
strict paths require explicit l3_version
specific modules require DDT
strategy="latest" is forbidden under certain paths
semantic audit is advisory
test coverage expectations
```

---

### 3.4 Skills

DDT-related workflow lives in:

```text
.agents/skills/harbor-ddt-diary/SKILL.md
```

Use that skill when the task involves:

```text
adding tests
updating tests
updating DDT bindings
changing l3_version
changing contract versions
creating Diary Drafts after DDT changes
updating changelog or release notes for test-relevant contract changes
```

Skills are workflow entrypoints.

Skills are not source of truth.

---

## 4. Relationship to Contract Rules

DDT depends on Contract.

Detailed Contract rules live in:

```text
.harbor/rules/contract-rules.md
```

DDT should be considered when Contract Impact is:

```text
yes
uncertain
```

Contract Impact includes changes to:

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

If behavior changes but tests do not change, inspect whether tests still verify the intended contract.

If tests change but contract does not, inspect whether tests were weakened to match implementation.

---

## 5. DDT Goals

DDT aims to:

```text
verify implementation against contract
verify tests are still aligned with contract
detect stale tests after contract changes
prevent false green tests
prevent strict targets from following latest behavior silently
help AI agents generate test scaffolds from contracts
make contract drift easier to review
```

DDT does not replace:

```text
unit tests
integration tests
E2E tests
type checking
lint
manual code review
security review
performance tests
human judgment
```

DDT is one layer in the Harbor governance system.

---

## 5.1 DDT_VERSION_BASELINE_MISSING

`DDT_VERSION_BASELINE_MISSING` / `ddt_version_baseline_missing` 表示：

```text
DDT binding is structurally valid
but no L3 contract version baseline was found
```

这属于 advisory，不是 violation。

它表示“当前缺少可核验基线”，不表示“DDT 已永久语义通过”。

处理建议：

```text
review baseline state first
do not blindly bump l3_version
decide whether contract baseline should be established or updated
```

出现该 advisory 时，不应把 DDT 绑定视为无效；应理解为“版本核验步骤尚不完整”。

---

## 5.2 Contract Gap vs DDT Gap

二者必须区分：

```text
Contract Gap:
  required contract itself is missing (or not usable).
  先补契约源，再谈语义比较和 DDT 对齐。

DDT Gap:
  contract exists, but tests / DDT binding is missing, stale, or insufficient.
```

换言之：

```text
没有契约 ≠ DDT 已通过
有契约但测试不够 = DDT Gap
必需契约缺失 = Contract Gap
```

---

## 6. Strictness and DDT

Use `.harbor/policy.yaml` as the source of truth when available.

Default strictness levels:

```text
strict
standard
light
```

---

## 7. Strict Targets

Strict targets usually include:

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
```

Strict targets require:

```text
explicit contract
tests / DDT coverage
explicit l3_version where DDT binding is used
no strategy="latest"
semantic drift check
Diary Draft for important contract or DDT strategy changes
generated context refresh if needed
```

---

## 8. Standard Targets

Standard targets usually include:

```text
ordinary business logic
service functions
repositories
stable internal APIs
module-level workflows
non-critical data transformations
```

Standard targets should usually have tests.

DDT is recommended when behavior is meaningful or reused.

`strategy="latest"` may be allowed for standard targets if project policy permits.

However, if a standard target becomes critical or public-facing, upgrade it to strict.

---

## 9. Light Targets

Light targets usually include:

```text
internal helpers
low-risk utilities
test helpers
script-local functions
small formatting helpers
```

Light targets do not always require DDT.

Tests are still useful when behavior is non-trivial.

Do not over-govern trivial helpers.

But if a light helper becomes part of a strict path, upgrade its DDT expectations.

---

## 10. Binding Strategy

DDT supports two conceptual binding styles:

```text
explicit version binding
latest binding
```

---

### 10.1 Explicit Version Binding

Explicit version binding connects a test to a specific contract version.

Recommended for strict targets:

```python
@harbor_ddt_target("module.func", l3_version=1)
def test_func_success_path():
    ...
```

Meaning:

```text
this test verifies contract version 1
the test should not silently follow newer contract changes
when the contract changes, the binding must be reviewed
```

---

### 10.2 Latest Binding

Latest binding connects a test to the newest known contract.

Example:

```python
@harbor_ddt_target("module.func", strategy="latest")
def test_func_success_path():
    ...
```

Allowed only for standard or light targets when policy permits.

Do not use latest binding for strict targets.

---

## 11. Strict DDT Rule

For strict targets, this is required:

```python
@harbor_ddt_target("module.func", l3_version=1)
def test_func_success_path():
    ...
```

This is forbidden:

```python
@harbor_ddt_target("module.func", strategy="latest")
def test_func_success_path():
    ...
```

When found, mark:

```text
[DDT Violation]
Strict target must not use strategy="latest".
```

Reason:

```text
strategy="latest" can make tests silently follow the newest contract and produce a false green result.
```

Strict baseline behavior:

```text
strict targets still need explicit l3_version
strict targets still must avoid strategy="latest"
ddt_version_baseline_missing is advisory, not an auto-pass
```

Python strict targets keep this rule unchanged in v1.4.x.

---

## 12. DDT Without Decorator

If the project has not implemented a DDT decorator yet, preserve binding intent with comments.

Example:

```python
# harbor-ddt-target: module.func
# l3_version: 1
def test_func_success_path():
    ...
```

For strict targets, the same rule applies:

```text
use explicit l3_version
do not use strategy="latest"
```

---

## 13. DDT Coverage Dimensions

DDT should verify the contract dimensions that matter for the target.

Basic dimensions:

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

Strict targets may also require:

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

---

## 14. DDT Scaffold Template

Basic DDT scaffold:

```python
from harbor.testing import harbor_ddt_target

@harbor_ddt_target("module.func", l3_version=1)
def test_func_success_path():
    """Covers main successful behavior declared by the contract."""
    ...

@harbor_ddt_target("module.func", l3_version=1)
def test_func_invalid_input_raises():
    """Covers Raises declared by the contract."""
    ...

@harbor_ddt_target("module.func", l3_version=1)
def test_func_return_shape():
    """Covers Returns declared by the contract."""
    ...
```

Without decorator support:

```python
# harbor-ddt-target: module.func
# l3_version: 1
def test_func_success_path():
    """Covers main successful behavior declared by the contract."""
    ...
```

---

## 15. Strict DDT Scaffold Template

For strict targets, include contract dimensions explicitly.

```python
from harbor.testing import harbor_ddt_target

@harbor_ddt_target("module.strict_func", l3_version=2)
def test_strict_func_success_shape():
    """Covers stable return structure and public JSON-compatible shape."""
    ...

@harbor_ddt_target("module.strict_func", l3_version=2)
def test_strict_func_invalid_input_raises():
    """Covers declared invalid input failure mode."""
    ...

@harbor_ddt_target("module.strict_func", l3_version=2)
def test_strict_func_side_effects():
    """Covers declared side-effect behavior."""
    ...

@harbor_ddt_target("module.strict_func", l3_version=2)
def test_strict_func_does_not_leak_absolute_paths():
    """Covers public output path safety contract."""
    ...
```

---

## 16. Contract Change and DDT Update Workflow

When Contract Impact is yes or uncertain:

```text
1. Read existing contract.
2. Determine strictness.
3. Decide whether intended behavior changes.
4. Update contract first if behavior changes.
5. Upgrade l3_version when needed.
6. Inspect tests bound to the old version.
7. Decide whether old tests remain valid.
8. Update assertions.
9. Add missing edge cases.
10. Check semantic drift.
11. Refresh generated context if needed.
12. Create Diary Draft if important.
```

Do not blindly change all test bindings to the newest version.

Every binding update should represent a reviewed contract decision.

---

## 17. When to Upgrade l3_version

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

Usually no version upgrade is needed for:

```text
wording polish in Decoration Area
non-normative examples
formatting
comments
internal implementation changes with identical behavior
```

If uncertain, mark:

```text
l3_version update: uncertain
```

and inspect the affected contract sources.

---

## 18. Contract Area vs Decoration Area

DDT should bind to Contract Area, not Decoration Area.

Contract Area includes:

```text
Args
Returns
Raises
Behavior
Invariants
Side Effects
Idempotency
Security
Failure Modes
Schema
state changes
external-visible behavior
user-visible behavior
file write behavior
CLI output
JSON output
```

Decoration Area usually includes:

```text
Examples
Notes
background explanation
formatting
wording polish
non-normative explanation
```

If decoration text makes a normative promise, treat it as Contract Area.

---

## 19. DDT Coverage Report Format

Use this format when reviewing DDT coverage:

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

Example:

```text
[DDT Coverage]
- Target: harbor.workspace.inspect
- Strictness: strict
- Binding: explicit l3_version=2
- Contract sources:
  - CLI JSON output
  - workspace inspect docstring
  - tests/fixtures/workspace_inspect.json
- Args coverage: yes
- Returns coverage: yes
- Raises coverage: partial
- Side effects coverage: yes, read-only behavior tested
- Idempotency coverage: yes
- Schema / output coverage: partial
- Missing:
  - path normalization edge case
  - missing .harbor/rules handling
- Recommendation:
  - add tests for missing rules directory
  - add JSON key stability snapshot
```

---

## 20. DDT Review Labels

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

## 21. False Green Risks

A false green occurs when tests pass but no longer verify the intended contract.

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

When suspected, mark:

```text
[DDT False Green Risk]
```

and explain why.

---

## 22. Fixture and Snapshot Rules

Fixtures and snapshots can be contract sources.

Treat them carefully.

Changing the following may be Contract Impact:

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

If a snapshot changes intentionally, explain:

```text
what changed
why it changed
whether it is breaking
which contract source changed
which consumers are affected
```

---

## 23. CLI and JSON Output DDT

CLI and JSON output are often strict contracts.

DDT should cover:

```text
command arguments
exit code
stdout format
stderr format
JSON keys
JSON value types
ordering when deterministic output is promised
path normalization
absolute path leakage prevention
machine-readable status
error cases
```

When CLI or JSON output changes:

```text
1. Determine Contract Impact.
2. Update contract source.
3. Update tests / snapshots / fixtures.
4. Check whether it is breaking.
5. Refresh generated context if needed.
6. Create Diary Draft if important.
```

---

## 24. File Write DDT

File write behavior is a contract when users or tools rely on it.

DDT should cover:

```text
write target path
file name
file format
overwrite behavior
append behavior
dry-run behavior
idempotency
managed block behavior
backup behavior
no-write guarantees
```

Important Harbor examples:

```text
.harbor/views/**
.harbor/diary/**
.harbor/rules/**
.harbor/reports/**
.agents/skills/**
AGENTS.md managed block
```

`harbor workspace migrate --dry-run` must be tested as read-only.

Do not allow dry-run tests to write, move, or delete files.

---

## 25. Workspace DDT

The canonical Harbor workspace is:

```text
.harbor/
```

DDT should protect workspace behavior such as:

```text
rules path: .harbor/rules/**
views path: .harbor/views/**
diary path: .harbor/diary/**
reports path: .harbor/reports/**
cache path: .harbor/cache/**
state path: .harbor/state/**
skill export path: .agents/skills/**
```

Workspace DDT should verify:

```text
canonical paths are used
generated context writes to .harbor/views/**
diary writes to .harbor/diary/**
rules are read from .harbor/rules/**
workspace inspect reports expected status
workspace migrate --dry-run remains read-only
cache/state are not treated as source of truth
```

---

## 26. Runtime Safety and DDT

Runtime Safety behavior can be tested.

Safety-related DDT should cover:

```text
protected paths
dangerous commands
ALLOW / ASK / DENY classification
secret handling
.env read/write denial
destructive command confirmation
PowerShell-safe alternatives
generated skill write confirmation
.harbor/*.yaml modification confirmation
```

Detailed safety rules:

```text
.harbor/rules/runtime-safety.md
.harbor/safety.yaml
```

---

## 27. Semantic Audit and DDT

Semantic audit may report possible drift between implementation and contract.

When semantic audit reports drift:

```text
1. Inspect implementation.
2. Inspect contract sources.
3. Inspect tests / DDT.
4. Classify the issue.
5. Update implementation, contract, or tests as appropriate.
```

Possible classifications:

```text
Confirmed Semantic Drift
Possible Semantic Drift
Contract Gap
Test / DDT Gap
Docstring Stale
Implementation Bug
False Positive
```

Do not change tests only to silence semantic audit.

---

## 28. Generated Context and DDT

Generated context lives under:

```text
.harbor/views/**
```

Generated context is not source of truth.

A generated context refresh usually does not require DDT by itself.

But changes to generated context behavior may require DDT.

Examples:

```text
L2 README schema changes
Module Capsule file structure changes
project structure output changes
debug-playbook generation semantics change
review-checklist generation semantics change
stale detection behavior changes
doctor output behavior changes
```

When generated context behavior changes:

```text
update tests
update snapshots if used
refresh generated context
consider Diary Draft
```

---

## 29. Diary and DDT

Create or recommend a Diary Draft when DDT strategy changes.

Examples:

```text
strict target changes from strategy="latest" to explicit l3_version
test binding policy changes
contract versioning strategy changes
DDT scaffold generation behavior changes
false-positive handling changes
semantic audit triage policy changes
workspace DDT behavior changes
```

Canonical Diary path:

```text
.harbor/diary/YYYY-MM.jsonl
```

Detailed Diary rules:

```text
.harbor/rules/diary-rules.md
```

Workflow skill:

```text
.agents/skills/harbor-ddt-diary/SKILL.md
```

Do not claim Diary was written unless it was actually written.

---

## 30. DDT Update Output Format

When doing DDT work, include:

```text
DDT / Test Summary:
- Target:
- Contract Impact:
- Strictness:
- Binding:
- l3_version:
- Tests added:
- Tests updated:
- Fixtures / snapshots changed:
- Missing coverage:
- Semantic drift:
- Diary needed:
- Commands run:
- Remaining risks:
```

If no tests were run, state:

```text
未实际运行测试。建议执行：
<command>
```

Do not invent test results.

---

## 31. Code Review Output Format for DDT

For review tasks involving DDT:

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

For each DDT finding:

```text
Finding <N>: <DDT Label>

Location:
- <file>:<line or symbol>

Evidence:
- <specific evidence from contract, test, fixture, or implementation>

Risk:
- <why this matters>

Recommended fix:
- <specific fix>

Severity:
- high / medium / low
```

---

## 32. Test Command Honesty

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

## 33. Common Mistakes

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
treating generated context as contract source
treating DDT as replacement for integration tests
skipping Diary for important DDT strategy changes
```

---

## 34. Final Principle

When reviewing or writing tests, ask:

```text
Which contract is this test verifying?
Is the contract strict, standard, or light?
Is the test bound to the right contract version?
Can the test pass while the contract is still broken?
```

A good DDT test makes contract drift harder to hide.

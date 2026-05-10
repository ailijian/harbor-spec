<!-- harbor-spec:managed version=1.3.0 kind=rule -->

# Harbor Contract Rules

Version: Harbor-spec v1.3.0  
Canonical path: `.harbor/rules/contract-rules.md`  
Purpose: Rules for identifying, maintaining, and validating contracts under Harbor-spec

---

## 1. Purpose

Harbor Contract Rules define how AI coding agents and developers should understand, update, and validate contracts in a Harbor-managed repository.

The goal is to prevent drift between:

```text
implementation
docstrings
type hints
schemas
tests
DDT targets
CLI behavior
JSON output
file write behavior
user-visible behavior
generated context
decision memory
```

Core principle:

```text
Implementation changes must not leave contracts stale.
```

---

## 2. Contract Does Not Mean Docstring Only

A Contract is any source that defines expected behavior, structure, boundary, side effect, or externally visible result.

Docstring is an important contract source.

But docstring is not the only contract source.

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

When multiple contract sources exist, the task is not to pick one blindly.

The task is to keep them synchronized.

---

## 2.1 Contract Presence

Harbor 使用 Contract Presence 判断一个 target 是否存在可比较契约源。

presence 状态：

```text
present
  存在可比较契约源，可进入语义比较。

missing
  未发现契约源。

empty
  存在契约容器（如 docstring）但内容为空。

non_contract_doc
  存在文档文本但不满足契约结构信号，无法可靠比较。

malformed
  存在契约源但解析失败或结构损坏，无法可靠分类。
```

关键规则：

```text
Missing contract is not semantic drift.
Semantic drift requires an existing comparable contract.
```

---

## 2.2 Contract Required

Contract Required 用于判定某个 target 是否必须具备契约源。

默认应要求契约的目标包括：

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

如果 target 被判定为 `contract_required=true`，则缺少有效契约源应归类为 `CONTRACT_GAP`。

---

## 2.3 Contract Gap

`Contract Gap` 定义：

```text
target requires a contract
but no valid contract source exists
```

`Contract Gap` 不是语义漂移。它表示“还没有可比较契约”，不是“契约与实现不一致”。

建议动作：

```text
add Harbor contract docstring
or configure an equivalent contract source
```

CONTRACT_GAP 的解决方式应优先是补充或更新契约源；只有当该目标确实不应承担契约时，才应调整项目策略或 strictness。

---

## 2.4 Skipped No Contract

`Skipped No Contract` 定义：

```text
target does not require contract
semantic audit is skipped
```

`Skipped No Contract` 不应被当作 drift，也不应被映射为 `possible_semantic_drift`。

---

## 2.5 Python Contract Authoring Standard

Python 目标的默认契约源为 docstring。

同时需明确：

```text
Docstring is the default Python contract source.
Contract does not mean docstring only.
strict/public Python targets should use Harbor Contract Docstring
unless equivalent contract source exists.
```

推荐保留的 Harbor contract 字段：

```text
@harbor.scope
@harbor.l3_strictness
@harbor.idempotency
Args
Returns
Raises
Side effects (when relevant)
```

---

## 3. Relationship to AGENTS.md, Project Rules, and Skills

### 3.1 AGENTS.md

`AGENTS.md` contains the lightweight Contract reminders that should be always visible to AI agents.

It defines:

```text
what Contract means at minimum
what Contract Impact means at minimum
when to use contract-related workflows
```

It should not contain the full Contract policy.

---

### 3.2 Project Rules

Project-specific contract rules live in:

```text
.harbor/rules/project-rules.md
```

Project Rules may define:

```text
project-specific strict paths
project-specific schema sources
verified test commands
contract pairs that must stay synchronized
module-specific contract boundaries
public API surfaces
public CLI surfaces
JSON output contracts
```

---

### 3.3 Machine Policy

Machine-readable policy may live in:

```text
.harbor/policy.yaml
```

If `.harbor/policy.yaml` defines strictness, protected contract areas, or required validation behavior, use it as the source of truth.

---

### 3.4 Skills

Contract-change workflow lives in:

```text
.agents/skills/harbor-contract-change/SKILL.md
```

Use that skill when the task involves:

```text
API change
schema change
public function change
CLI behavior change
JSON output change
parser / export / writeback change
workflow node change
tool schema change
semantic drift
```

Skills are workflow entrypoints.

Skills are not source of truth.

---

## 4. Contract Categories

Harbor recognizes several contract categories.

---

### 4.1 Semantic Contract

Semantic Contract defines what the system means and how it should behave.

It covers:

```text
why the function or module exists
when it should be used
when it should not be used
expected behavior
invariants
side effects
idempotency
failure modes
security requirements
dependency assumptions
```

Common locations:

```text
docstring
architecture notes
design docs
tests
Diary
```

---

### 4.2 Interface Contract

Interface Contract defines how something is called or accessed.

It covers:

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

Common locations:

```text
type hints
docstring
FastAPI route
OpenAPI schema
CLI schema
MCP tool schema
tests
```

---

### 4.3 Data Contract

Data Contract defines structure.

It covers:

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

### 4.4 Behavior Contract

Behavior Contract defines observable behavior.

It covers:

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

### 4.5 Safety Contract

Safety Contract defines what must not happen.

It covers:

```text
secrets must not be printed
user data must not be deleted silently
destructive operations require confirmation
production config must not be changed silently
permissions must not be relaxed silently
```

Common locations:

```text
.harbor/safety.yaml
.harbor/policy.yaml
.harbor/rules/runtime-safety.md
tests
security docs
```

---

## 5. Contract Impact

A change has Contract Impact when it affects any expected behavior, structure, boundary, side effect, or externally visible result.

Treat the following as Contract Impact:

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

Judgment rule:

```text
If a caller, user, test, downstream module, agent, or external system must change expectations, treat it as Contract Impact.
```

---

## 6. Non-Contract Impact

The following usually do not constitute Contract Impact:

```text
internal variable rename
private helper rearrangement with unchanged behavior
non-behavioral performance optimization
comment formatting
example wording improvement
documentation wording improvement with no behavior change
test helper refactor with no assertion behavior change
logging wording change when logs are not public contract
formatting-only change
```

When there is no Contract Impact, state clearly:

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

Do not use `Contract Impact: none` when behavior changed but seems small.

Small behavior changes can still be Contract Impact.

---

## 7. Contract Impact Levels

Use these levels when helpful.

```text
none
low
medium
high
critical
```

### 7.1 None

No externally meaningful behavior, schema, side effect, or interface change.

Example:

```text
rename internal variable
format code
reorder private helper logic with same output and same errors
```

---

### 7.2 Low

Small internal contract change with limited risk.

Example:

```text
private helper return detail changes
internal-only error message changes
non-public test utility behavior changes
```

---

### 7.3 Medium

Standard business logic or module boundary changes.

Example:

```text
service behavior changes
internal API behavior changes
ordinary data transformation behavior changes
```

---

### 7.4 High

Strict or public-facing contract changes.

Example:

```text
public API changes
CLI behavior changes
JSON output changes
schema changes
parser / export / writeback behavior changes
workflow node changes
migration behavior changes
```

---

### 7.5 Critical

Safety, data, production, permission, or breaking changes.

Example:

```text
auth / permission behavior changes
billing behavior changes
destructive migration behavior changes
secret handling changes
breaking public API change
user data handling changes
```

---

## 8. Strictness

Strictness defines how strongly a target must be governed.

Use `.harbor/policy.yaml` as the source of truth when available.

Default strictness levels:

```text
strict
standard
light
```

---

## 9. Strict Targets

Treat these as strict unless project policy says otherwise:

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
explicit Contract
complete type hints where practical
schema update when applicable
clear side effects
clear idempotency
clear Raises / failure modes
tests / DDT update
explicit l3_version for strict DDT
no strategy="latest" for strict DDT
semantic drift check
Diary Draft for important changes
generated context refresh if needed
```

---

## 10. Standard Targets

Standard targets include:

```text
ordinary business logic
service functions
repositories
stable internal APIs
module-level workflows
non-critical data transformations
```

Standard targets require:

```text
Contract Impact check
docstring or equivalent contract when behavior is non-trivial
type hints where practical
Args / Returns / Raises clarity where applicable
tests recommended
DDT recommended when behavior is important
generated context refresh if module responsibility changes
```

`strategy="latest"` may be allowed for standard targets if project policy permits.

---

## 11. Light Targets

Light targets include:

```text
internal helpers
low-risk utilities
test helpers
script-local functions
small formatting helpers
```

Light targets require:

```text
clear name
summary or type clarity when helpful
tests only when behavior is non-trivial
no unnecessary ceremony
```

Do not over-govern trivial light targets.

But if a light target becomes part of a critical path, upgrade its strictness.

---

## 12. Contract Sources and Synchronization

When changing behavior, identify which contract sources must stay synchronized.

Common pairs:

```text
docstring ↔ implementation
type hints ↔ implementation
Pydantic model ↔ API response tests
OpenAPI schema ↔ frontend types
CLI output ↔ snapshot tests
JSON output ↔ schema tests
parser behavior ↔ fixture corpus
export format ↔ golden files
workflow node behavior ↔ integration tests
migration ↔ database tests
MCP tool schema ↔ tool behavior tests
```

If two contract sources conflict, mark it explicitly:

```text
[Contract Conflict]
```

If implementation and contract conflict, mark:

```text
[Semantic Drift]
```

If tests verify old behavior, mark:

```text
[Test / DDT Gap]
```

---

## 13. Docstring Rules

Docstrings are semantic contracts.

They should describe behavior, not merely restate function names.

For standard targets, a docstring should usually include:

```text
summary
behavior
Args
Returns
Raises when applicable
side effects when applicable
```

For strict targets, include more complete contract fields.

---

## 14. Standard Docstring Template

```python
def example_func(arg1: str) -> bool:
    """Return whether arg1 satisfies the expected condition.

    Behavior:
      - Normalizes arg1 before evaluation.
      - Returns False for empty input.

    Args:
      arg1 (str): Input string to evaluate.

    Returns:
      bool: True when arg1 satisfies the condition; otherwise False.

    Raises:
      ValueError: If arg1 contains unsupported characters.
    """
```

---

## 15. Strict Docstring Template

```python
def strict_func(arg1: str, retry: bool = False) -> dict:
    """Execute the strict public operation.

    Why:
      - This function is the public entrypoint for the operation.

    When:
      - Use when the caller needs the normalized public result.
      - Do not use for internal-only partial validation.

    Behavior:
      - Validates input.
      - Produces deterministic JSON-compatible output.
      - Preserves backward-compatible field names.
      - Does not print secrets or write production data.

    Invariants:
      - Returned keys remain stable unless a breaking change is declared.
      - Invalid input raises ValueError.

    Side Effects:
      - Writes no files.
      - Performs no network calls.
      - Mutates no external state.

    Idempotency:
      - Pure for the same input.

    Security:
      - Must not expose secrets.
      - Must not include machine-local absolute paths in public JSON output.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: pure
    @harbor.ddt_required: true

    Args:
      arg1 (str): User-provided input.
      retry (bool): Whether retry behavior is allowed.

    Returns:
      dict: Stable JSON-compatible result.

    Raises:
      ValueError: If input is invalid.
      TimeoutError: If external dependency times out.
    """
```

---

## 16. Contract Area vs Decoration Area

### 16.1 Contract Area

Changes in these areas usually constitute Contract Impact:

```text
Summary when it states behavior
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

### 16.2 Decoration Area

Changes in these areas usually do not constitute Contract Impact:

```text
Examples
Notes
background explanation
formatting
wording polish
non-normative explanation
```

If decoration text contains normative behavior, treat it as Contract Area.

---

## 17. Schema Contract Rules

When code involves schemas, do not rely only on docstrings.

Schema-related contracts may include:

```text
Pydantic model
FastAPI response model
OpenAPI schema
TypeScript type
Zod schema
database migration
event schema
JSON output schema
MCP tool schema
```

When schema changes:

```text
1. Determine Contract Impact.
2. Determine breaking change risk.
3. Update schema source.
4. Update implementation.
5. Update tests / fixtures / snapshots.
6. Update generated types if applicable.
7. Refresh generated context if needed.
8. Create Diary Draft if important.
```

---

## 18. CLI and JSON Output Contract Rules

CLI and JSON output are strict when users, scripts, agents, CI, or downstream tools consume them.

Changing any of the following is Contract Impact:

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

For JSON output:

```text
keep keys stable
keep ordering deterministic when practical
normalize paths
avoid machine-local absolute path leakage unless explicitly required
avoid embedding local runtime state
include enough status information for CI and agents
```

When JSON output changes:

```text
update tests
update DDT if applicable
update docs
refresh generated context
consider Diary Draft
```

---

## 19. File Write Contract Rules

File write behavior is a contract when users, tools, agents, or CI rely on it.

Changing any of the following is Contract Impact:

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

Strict examples:

```text
.harbor/views/**
.harbor/diary/**
.harbor/rules/**
.harbor/reports/**
.agents/skills/**
AGENTS.md managed block
```

Rules:

```text
Do not silently change write targets.
Do not silently switch from dry-run to write.
Do not silently overwrite user-authored content.
Do not manually edit generated context as project truth.
```

---

## 20. Workspace Contract Rules

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

Workspace migration planning should use:

```powershell
harbor workspace inspect
harbor workspace migrate --dry-run
```

`migrate --dry-run` is read-only.

Do not assume `migrate --write` exists.

---

## 21. Semantic Drift

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

When Semantic Drift is found, classify it as:

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

Do not run `harbor accept` to silence unresolved drift.

---

## 22. Contract Change Workflow

When Contract Impact is yes or uncertain:

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

If Contract Impact is uncertain:

```text
inspect more context
do not silently treat as no impact
ask user only if intended behavior cannot be inferred safely
```

---

## 23. Breaking Change Rules

A breaking change occurs when existing users, callers, scripts, agents, tests, or downstream systems must change.

Breaking changes may include:

```text
removed public field
renamed JSON key
changed CLI output format
changed exit code
changed schema requirement
changed file path
changed migration behavior
changed public exception behavior
changed compatibility behavior
```

For breaking changes:

```text
mark Breaking Change: yes
explain affected consumers
provide migration guidance
update tests
update docs
create Diary Draft
consider release notes
```

If uncertain, state:

```text
Breaking Change: uncertain
```

Do not hide uncertain breaking risk.

---

## 24. DDT Relationship

DDT binds tests to contracts.

For strict targets:

```text
use explicit l3_version
never use strategy="latest"
```

When contract changes:

```text
update contract
upgrade l3_version when needed
inspect tests bound to old version
update assertions
add missing edge cases
do not blindly bind tests to latest implementation
```

Detailed rules:

```text
.harbor/rules/ddt-rules.md
```

Workflow skill:

```text
.agents/skills/harbor-ddt-diary/SKILL.md
```

---

## 25. Diary Relationship

Contract changes often need Diary.

Create or recommend a Diary Draft for:

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
non-obvious compatibility decision
```

Canonical Diary path:

```text
.harbor/diary/YYYY-MM.jsonl
```

Detailed rules:

```text
.harbor/rules/diary-rules.md
```

Do not claim Diary was written unless it was actually written.

---

## 26. Generated Context Relationship

Generated context lives under:

```text
.harbor/views/**
```

Generated context should reflect source of truth.

Generated context is not source of truth.

When contracts change, consider refreshing:

```powershell
harbor project structure --write
harbor docs --changed --write
harbor module seal --changed --write
harbor finish --sync-context
harbor stale
harbor doctor
```

Do not manually edit generated views as project truth.

---

## 27. Runtime Safety Relationship

Some contract changes are also safety-sensitive.

Use safety preflight when the change involves:

```text
.env
secrets
migrations
CI/CD
dependencies
destructive commands
production config
auth / permission / billing
user data handling
.harbor/*.yaml
generated skills
```

Detailed rules:

```text
.harbor/rules/runtime-safety.md
```

Workflow skill:

```text
.agents/skills/harbor-safety-preflight/SKILL.md
```

---

## 28. Review Output Format

For contract-related review tasks, use:

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

For each finding:

```text
Finding <N>: <Label>

Location:
- <file>:<line or symbol>

Evidence:
- <specific evidence from code, contract, schema, test, or generated view>

Risk:
- <why this matters>

Recommended fix:
- <specific fix>

Severity:
- high / medium / low
```

Useful labels:

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

## 29. Implementation Output Format

For contract-impacting implementation tasks, include:

```text
Change Summary:
- Files changed:
- Behavior changed:
- Contract Impact:
- Strictness:
- Affected contracts:
- Tests / DDT:
- Runtime Safety:
- Generated Context:
- Diary:
- Harbor commands run:
- Remaining risks:
```

If commands were not run, say so.

Do not invent results.

---

## 30. Common Mistakes

Avoid:

```text
treating docstring as the only contract
changing implementation without contract impact assessment
changing strict behavior without tests / DDT
using strategy="latest" for strict DDT
changing JSON output without tests
changing CLI output without documenting impact
changing file write path silently
manually editing generated context as source of truth
hiding breaking changes
using harbor accept to silence unresolved drift
claiming tests passed without running them
skipping Diary for important contract decisions
```

---

## 31. Final Principle

When changing behavior, ask:

```text
Who or what expects the old behavior?
Which contract sources describe it?
Which tests verify it?
Which generated context summarizes it?
Does the decision need to be remembered?
```

A Harbor-managed change is complete only when implementation, contracts, tests, generated context, and decision memory are aligned.

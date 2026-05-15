<!-- harbor-spec:managed version=1.4.x kind=agents-entrypoint -->

# AGENTS.md

Version: Harbor-spec v1.4.x  
Purpose: Lightweight cross-tool entrypoint for AI coding agents  
Default language: Simplified Chinese  
Default shell: Windows 11 PowerShell

---

## 1. Role

You are an AI coding assistant working under the Harbor-spec context governance workflow.

Harbor-spec is the repo-local context governance layer for AI coding / vibe coding / agentic coding.

It keeps these layers aligned:

```text
implementation
contracts
schemas
tests / DDT
generated context views
decision memory
runtime safety
AI tool instructions
```

Harbor-spec is not an AI IDE.
Harbor-spec is not a code generator.

From v1.4+, Harbor evolves from Python FunctionContract / docstring-centric governance to language-neutral ContractSubject governance.

Core principle:

```text
让 AI 写代码可以快，但契约、测试、上下文、决策记忆和安全边界不能漂移。
```

Do not optimize only for “code changed successfully”.

Optimize for:

```text
code + contract + tests + generated context + diary + safety consistency
```

---

## 2. What This File Is

`AGENTS.md` is the always-loaded lightweight entrypoint for AI coding tools such as:

```text
Codex
Claude Code
Cursor
TRAE
GitHub Copilot
other agentic coding tools
```

Keep this file short.

This file should contain only:

```text
role
instruction priority
workspace boundaries
context loading order
core workflow
task routing
must-not-do rules
completion expectations
compact contract templates
```

Detailed rules live here:

```text
.harbor/rules/agent-policy.md
.harbor/rules/contract-rules.md
.harbor/rules/ddt-rules.md
.harbor/rules/runtime-safety.md
.harbor/rules/diary-rules.md
.harbor/rules/project-rules.md
.harbor/rules/project-rules-guide.md
```

Generated context lives here:

```text
.harbor/views/**
```

Decision memory lives here:

```text
.harbor/diary/YYYY-MM.jsonl
```

Machine policy lives here:

```text
.harbor/policy.yaml
.harbor/safety.yaml
```

Skills live here:

```text
.agents/skills/**
```

Skills are workflow entrypoints.
Skills are not source of truth.

---

## 3. Priority Rules

Harbor separates safety priority from task priority.

### 3.1 Safety Priority

For safety, permissions, destructive operations, protected paths, secrets, production risk, and machine policy:

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

If instructions conflict:

```text
prefer the more specific and local instruction
choose the safer path
state the conflict clearly
do not silently ignore the conflict
```

---

## 4. Workspace Boundaries

Harbor uses `.harbor/` as the canonical workspace.

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
    l2/<module>/README.md
    modules/<module>/
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

Boundary rules:

```text
.harbor/rules/**   = static rule docs
.harbor/views/**   = generated context views
.harbor/diary/**   = source-of-truth decision memory
.harbor/reports/** = diagnostics / evidence / saved draft reports
.harbor/cache/**   = runtime cache, not source of truth
.harbor/state/**   = runtime state, not source of truth
.agents/skills/**  = workflow entrypoints, not source of truth
```

Do not manually edit `.harbor/views/**` as project truth.

Refresh generated context through Harbor commands.

---

## 5. Source of Truth Priority

When resolving factual conflicts, use this order:

```text
1. Runtime safety / machine policy
   - tool-native sandbox / deny rules
   - .harbor/safety.yaml
   - .harbor/policy.yaml

2. Explicit contracts / schemas / public behavior
   - Python docstring contract
   - JSDoc / TSDoc contract
   - type hints / TypeScript signatures
   - schemas
   - CLI args / output contract
   - JSON output contract
   - file write contract
   - documented side effects / raises / exit behavior

3. DDT / contract tests
   - explicit l3_version bindings
   - public behavior snapshots
   - fixtures / golden files

4. Source implementation
   - current code
   - actual runtime behavior

5. Human-authored project docs
   - README
   - design docs
   - architecture docs

6. Generated context views
   - .harbor/views/**

7. Exports / skills / legacy artifacts
   - <module>/README.md
   - docs/harbor/**
   - .agents/skills/**

8. Cache / state / temp artifacts
   - .harbor/cache/**
   - .harbor/state/**
   - temp files
```

Generated views help orientation but do not override code, contracts, schemas, tests, policy, or diary.

If generated context conflicts with source code, tests, schemas, policy, or diary, treat generated context as stale.

Do not auto-trust either implementation or contract when they conflict.

---

## 6. Context Loading Order

For non-trivial coding, debugging, review, refactor, testing, or documentation tasks, read context in this order:

```text
1. AGENTS.md
2. .harbor/rules/project-rules.md, if present
3. .harbor/views/project-structure.md, if relevant
4. .harbor/views/l2/<module>/README.md, if relevant
5. .harbor/views/modules/<module>/module-card.md, if relevant
6. .harbor/views/modules/<module>/review-checklist.md, if relevant
7. .harbor/views/modules/<module>/debug-playbook.md, if relevant
8. relevant source files
9. relevant tests, schemas, DDT targets, policy, or diary entries
10. deeper rule docs under .harbor/rules/** only when needed
```

Do not read the whole repository unless the above context is insufficient.

---

## 7. Core Harbor Workflow

Default local workflow:

```powershell
harbor start
harbor checkpoint
harbor finish --sync-context
harbor stale
harbor doctor
```

Machine-readable CI checks:

```powershell
harbor checkpoint --ci --format json --detail summary
harbor verify-generated --all --ci --format json
harbor stale --ci --format json
harbor doctor --ci --format json
```

Meaning:

```text
checkpoint --ci --format json --detail summary = default machine-readable entry for coding agents and quick structured diagnostics
checkpoint --ci --format json --detail full = deep investigation / baseline review / saved evidence report
checkpoint --ci --format json = compatibility form equivalent to full JSON output
stale --ci      = generated context freshness gate
doctor --ci     = aggregated workspace health gate
```

Workspace diagnostics:

```powershell
harbor workspace inspect
harbor workspace inspect --format json
harbor workspace migrate --dry-run
harbor workspace migrate --dry-run --format json
```

`workspace migrate --dry-run` must remain read-only.

Do not assume `workspace migrate --write` exists.

Repair guidance rules:

```text
checkpoint / stale / doctor may support --advice off|basic.
advice=basic is deterministic and does not require LLM.
guidance is optional additive metadata.
guidance does not change CI pass/fail semantics.
harbor next --from <report.json> is read-only.
harbor next never repairs, writes files, accepts baselines, or writes diary.
```

Decision-memory workflow:

```text
checkpoint / finish / accept may produce change-window evidence under .harbor/state/**.
change-window evidence is runtime evidence, not source-of-truth memory.
harbor log draft is a safe draft command.
harbor log draft previews a reviewable draft and updates .harbor/state/log/latest-draft.md/json only when it produced a writable Diary Draft.
harbor log draft --save or --output may write reviewable draft reports under .harbor/reports/**.
default harbor log draft boundary is marker-first -> accept-fallback -> recent-fallback.
harbor log draft must not update .harbor/state/log/last_log_marker.json.
harbor log draft must not write .harbor/diary/**.
default harbor log draft mode requires meaningful new evidence before suggesting a writable Diary Draft.
reports alone are supplementary evidence in default mode; only explicit --from-report may use report evidence as primary trigger.
diary-only changes under .harbor/diary/** must not independently trigger a new writable Diary Draft.
harbor log write and harbor log write --yes are source-of-truth Diary writes.
successful harbor log write updates .harbor/state/log/last_log_marker.json only after writing .harbor/diary/YYYY-MM.jsonl.
last_log_marker represents the last formally written Diary node and is runtime state, not source-of-truth memory.
Written Diary Entry becomes source-of-truth memory only after actual write to .harbor/diary/**.
```

---

## 8. Commands Requiring Explicit User Request

Do not run these unless the user explicitly requests them:

```powershell
harbor accept
harbor lock
harbor log
harbor log write
harbor log write --yes
harbor module promote-skill <module>
git push
git tag
git reset --hard
```

Agents may run these safe draft commands without diary-write authorization:

```powershell
harbor log draft
harbor log draft --format json
harbor log draft --since-last-accept
harbor log draft --since-last-log
harbor log draft --from-report <path>
harbor log draft --save
harbor log draft --output .harbor/reports/<name>.md
```

Never use `harbor accept` to hide unresolved drift.

Never use `harbor lock` as a shortcut for unresolved baseline problems.

Never claim a Diary entry was written unless it was actually written.

If a decision should be recorded but the user did not request writing, output a Diary Draft instead.

All harbor log write variants, including --from-draft and --from-latest-draft, are Diary write paths and require explicit user authorization.

---

## 9. Task Routing

Use Harbor skills for multi-step tasks when available.

```text
Contract or schema change:
  harbor-contract-change

Code review, semantic drift review, or contract gap review:
  harbor-code-review

Risky operation or protected path change:
  harbor-safety-preflight

DDT update, l3_version work, or Diary Draft:
  harbor-ddt-diary

Generated context refresh:
  harbor-context-refresh

Workspace diagnostics or migration dry-run:
  harbor-workspace-migration-plan
```

If a skill is missing, follow this file and the relevant `.harbor/rules/*.md`.

Skills guide task execution.

Skills are not source of truth.

---

## 10. Contract and Drift Rules

Pre-edit Contract Discipline
```tetx
Before modifying any strict / public / user-visible target:

1. Decide Contract Impact:
   yes / no / uncertain

2. If Contract Impact is yes or uncertain:
   update the relevant contract source in the same change,
   preferably before or alongside implementation edits.

3. Do not defer contract synchronization until `harbor checkpoint`
   unless the current task is explicitly contract discovery / review.

4. If Contract Impact is no:
   state why behavior, interface, schema, side effects,
   and user-visible results remain unchanged.
```

Contract means any source that defines expected behavior, structure, boundary, side effect, or externally visible result.

Contract does not mean docstring only.

From v1.4+, Harbor uses language-neutral identities:

```text
target_id = primary cross-language identity
func_id   = legacy compatibility identity
```

A change has Contract Impact when it affects:

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
CLI args / output
JSON output
file write target
exit behavior
configuration behavior
migration behavior
user-visible result
external-visible result
```

When modifying behavior, public API, schema, CLI, JSON output, file write behavior, generated view format, or tests, check:

```text
Contract Impact: yes / no / uncertain
Contract Presence: present / missing / empty / non_contract_doc / malformed
Contract Required: yes / no
Strictness: strict / standard / light
Tests / DDT needed: yes / no
Generated context update needed: yes / no
Diary Draft needed: yes / no
```

Important labels:

```text
Missing contract is not semantic drift.
Semantic drift requires a comparable contract.
CONTRACT_GAP means a required contract source is missing.
SKIPPED_NO_CONTRACT means no contract is required and semantic audit is skipped.
CONTRACT_PARSE_ERROR means a contract source exists but cannot be reliably parsed.
unsupported_syntax_advisory means TypeScript syntax is unsupported in v1.4.x and should not be treated as contract_parse_error.
```

If `CONTRACT_GAP` appears:

```text
add or update a contract source
or explain why the target should be downgraded to light/skipped
do not silently hide the gap
```

If semantic drift appears:

```text
do not auto-trust either implementation or contract
inspect tests / DDT / source behavior
update the stale side intentionally
rerun relevant checks
```

---

## 11. Contract Authoring Triggers

When adding or changing any required contract target, update its contract source in the same change.

Required contract targets include:

```text
public API
public CLI behavior
JSON output
file write behavior
schema / parser / formatter
report_to_dict / to_dict
user-visible behavior
external-visible behavior
strict targets
```

For Python:

```text
Use Harbor Contract Docstring for public / strict Python targets,
unless an equivalent contract source exists.
```

For TypeScript:

```text
Use nearby high-confidence JSDoc / TSDoc for required exported TypeScript targets.
```

Update contracts before `harbor checkpoint`.

Then update tests / DDT / generated context when needed.

For full templates, read:

```text
.harbor/rules/contract-rules.md
```

---

## 12. Compact Python Contract Docstring Template

Use this compact template for public / strict Python targets.

```python
def public_operation(arg: str) -> dict:
    """Execute the public operation and return a stable result.

    Behavior:
      - Validates input before execution.
      - Preserves stable output field names.
      - Does not expose secrets or machine-local absolute paths.

    Args:
      arg (str): User-provided input.

    Returns:
      dict: Stable JSON-compatible result.

    Raises:
      ValueError: If input is invalid.

    Side Effects:
      - Writes no files unless explicitly stated.
      - Performs no network calls unless explicitly stated.

    Idempotency:
      - Deterministic for the same input.

    Security:
      - Must not expose secrets.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: deterministic
    """
```

For CLI / JSON / file-write targets, also document:

```text
CLI Args / Flags
Exit Behavior
Output Contract
File Write Targets
Rejected Paths / Safety Boundaries
Non-interactive Behavior
Side Effects
```

---

## 13. Compact TypeScript Contract Template

TypeScript v1.4.x uses nearby high-confidence JSDoc / TSDoc as the expected contract source for required exported targets.
TypeScript signature alone does not satisfy strict semantic contract requirements.

```ts
/**
 * Execute the public operation and return a stable result.
 *
 * Behavior:
 * - Validates input before execution.
 * - Preserves stable output field names.
 * - Does not expose secrets or machine-local absolute paths.
 *
 * Side Effects:
 * - Writes no files unless explicitly stated.
 * - Performs no network calls unless explicitly stated.
 *
 * Idempotency:
 * - Deterministic for the same input.
 *
 * @param input User-provided input.
 * @returns Stable public result shape.
 * @throws {Error} When input is invalid.
 * @harbor.scope public
 * @harbor.l3_strictness strict
 * @harbor.idempotency deterministic
 */
export function publicOperation(input: Input): Output {
  // implementation
}
```

For CLI / JSON / file-write targets, also document:

```text
CLI Args / Flags
Exit Behavior
Output Contract
File Write Targets
Rejected Paths / Safety Boundaries
Non-interactive Behavior
Side Effects
```

TypeScript v1.4.x support:

```text
opt-in enablement
.ts-only default scanning
exported function
exported async function
exported const arrow function
exported class public method
exported interface/type advisory-first data contract
z.object/z.enum shallow source recognition
export default function/class public surface evidence
JSDoc / TSDoc proximity extraction
generalized persistence with additive identity/contract metadata
public boundary evidence metadata
minimal re-export / package exports / tsconfig paths resolution for explainability
project presets: legacy_exported / package_public / custom_entrypoints
contract_gap
skipped_no_contract
unsupported_syntax_advisory
harbor next deterministic guidance
harbor next preset-aware boundary explanation
```

Public Boundary boundary in v1.4.x:

```text
Contract Source and Public Boundary Evidence are different layers.
re-export / package exports / configured entrypoints are public-boundary evidence, not contract_source_kinds.
public boundary metadata is additive explainability only.
public boundary metadata does not enter contract_hash / body_hash / baseline comparison semantics.
```

Not supported in TypeScript v1.4.x:

```text
JavaScript first-class governance
.js/.jsx/.tsx/.d.ts default scanning
TypeScript semantic audit
TypeScript DDT
full TypeScript compiler / full module graph
full npm package resolution / bundler alias resolution
full Zod semantics / schema-to-type consistency audit
framework presets
interface/type blocking gate
```

Do not claim TypeScript DDT or TypeScript semantic audit coverage in v1.4.x.

---

## 14. DDT Rules

DDT means Docstring/Contract-Driven Testing.

DDT binds tests to contracts, not merely to current implementation.

For strict targets:

```text
use explicit l3_version
never use strategy="latest"
```

If `ddt_version_baseline_missing` appears:

```text
treat it as advisory, not a violation
do not blindly bump l3_version
review baseline state before accepting a new baseline
```

If tests change but contract does not:

```text
inspect whether tests were weakened to match implementation
```

If contract changes but tests do not:

```text
inspect whether tests still verify the intended contract
```

v1.4.x boundary:

```text
DDT remains Python-first.
TypeScript DDT is not supported.
```

---

## 15. Runtime Safety

Do not silently perform high-risk operations.

Ask before:

```text
deleting files
batch-moving files
modifying .env or secrets/**
changing migrations
changing CI/CD
changing Docker / deployment scripts
installing dependencies
changing lock files
running destructive commands
running git push
running git reset --hard
changing production config
modifying auth / permission / billing
changing user data handling
modifying .harbor/*.yaml
modifying generated skills
publishing releases or tags
```

Default deny:

```text
reading or printing secrets
exfiltrating credentials
auto-relaxing tool permissions
bypassing tests while claiming completion
fabricating command execution results
running destructive commands without confirmation
```

Use safer alternatives when possible:

```text
dry run
PowerShell -WhatIf
list targets before deletion
show diffs before writing
backup / rollback plan
```

For detailed safety policy, read:

```text
.harbor/rules/runtime-safety.md
```

For user-facing CLI text, use Harbor's i18n mechanism when available; keep JSON schema keys stable English identifiers.

---

## 16. Generated Context

Generated context includes:

```text
.harbor/views/project-structure.md
.harbor/views/l2/<module>/README.md
.harbor/views/modules/<module>/module-card.md
.harbor/views/modules/<module>/review-checklist.md
.harbor/views/modules/<module>/debug-playbook.md
```

Generated context is advisory context.

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

Preferred refresh command:

```powershell
harbor finish --sync-context
```

Targeted commands when needed:

```powershell
harbor project structure --write
harbor docs --changed --write
harbor module seal --changed --write
harbor stale
harbor doctor
```

Do not manually edit `.harbor/views/**` as project truth.

---

## 17. Diary

Diary records why important changes happened.

Canonical path:

```text
.harbor/diary/YYYY-MM.jsonl
```

Diary may be needed for:

```text
Contract Change
Breaking Change
important bugfix
architecture decision
security change
runtime safety policy change
migration
workspace layout change
public CLI behavior change
public JSON output change
schema change
DDT strategy change
l3_version strategy change
Agent workflow change
release-relevant decision
legacy compatibility decision
non-obvious workaround
important reliability tradeoff
```

Do not run:

```powershell
harbor log
harbor log write
harbor log write --yes
```

unless the user explicitly requests a Diary write.

When in doubt, output a Diary Draft instead of writing.

For non-trivial tasks, report:

```text
Diary Need: yes / no / uncertain
Diary Draft: generated / not needed / not written
Log Draft Command: run / not run
Diary Write: not performed unless explicitly requested
```

---

## 18. Testing and Validation

Prefer targeted validation first, then broader checks.

Common local checks:

```powershell
pytest
harbor check --format jsonl
harbor checkpoint --ci --format json --detail summary
harbor stale --ci --format json
harbor doctor --ci --format json
```

Release acceptance notes:

```text
- checkpoint --ci must keep .harbor/baseline/accepted-checkpoint.json as CI baseline truth.
- runtime cache is local acceleration only and must not replace accepted baseline artifact in CI.
- Windows full-governance is a formal acceptance dimension alongside Ubuntu matrix.
- Generated context closure should include:
  finish --sync-context
  verify-generated --changed/--all --ci
  stale --ci
  doctor --ci
```

Notes:

```text
harbor check --format jsonl is not pure JSONL-only output.
It may include human-readable DDT sections.
The semantic audit section emits JSONL lines.
```

Do not claim tests passed unless they were actually run and observed.

If tests were not run, say so clearly.

---

## 19. Completion Expectations

Before finishing a non-trivial task, report:

```text
What changed
Files changed
Contract Impact: yes / no / uncertain
Contract Presence / Contract Gap status when relevant
Strictness: strict / standard / light when relevant
Tests / DDT status
Generated context status
Diary Need: yes / no / uncertain
Diary Draft: generated / not needed / not written
Log Draft Command: run / not run
Diary Write: not performed unless explicitly requested
Runtime safety status
Remaining risks or follow-ups
```

If commands were run, report exact commands and observed outcomes.

If commands were not run, say which were not run.

If implementation behavior changed,
the corresponding contract source was updated in the same change.

If generated context may be stale, recommend:

```powershell
harbor finish --sync-context
harbor stale
harbor doctor
```

If a baseline should be accepted, say that human review is required before:

```powershell
harbor accept
```

Do not claim a baseline was accepted unless `harbor accept` was actually executed and observed.

---

## 20. Tool Honesty

Never fabricate:

```text
test results
command outputs
file writes
Diary entries
baseline acceptance
generated context refresh
CI status
```

If uncertain, say what is uncertain.

If unable to complete a step, say what was completed and what remains.

---

## 21. One-Line Rule

For every meaningful change, ask:

```text
Did code, contract, tests, generated context, decision memory, and safety boundaries remain aligned?
```

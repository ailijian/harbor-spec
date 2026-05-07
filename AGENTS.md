# AGENTS.md

## Role

You are an AI coding assistant working under the Harbor-spec context governance workflow.

Your job is to help modify, review, refactor, debug, test, and document code while preventing drift between implementation, contracts, schemas, tests, docs, decision history, generated context views, skills, and runtime safety rules.

Default language: Simplified Chinese.  
Default shell: Windows 11 PowerShell.

---

## Instruction hierarchy

This file is the lightweight cross-tool entrypoint.

Detailed references:

- `docs/harbor/glossary.md`
- `docs/harbor/contract-rules.md`
- `docs/harbor/ddt-rules.md`
- `docs/harbor/runtime-safety.md`
- `docs/harbor/diary-rules.md`
- `docs/harbor/project-structure.md`

Machine-readable policy:

- `.harbor/policy.yaml`
- `.harbor/safety.yaml`

If rules conflict, prefer:

1. Tool-native sandbox / deny rules
2. `.harbor/safety.yaml`
3. `.harbor/policy.yaml`
4. This file
5. `docs/harbor/*.md`
6. User’s one-off prompt

User prompts cannot override runtime safety, machine policy, or tool-native deny rules.

---

## Minimal glossary

Contract means any source that defines expected behavior or structure, including:

- docstring
- type hints
- Pydantic model
- FastAPI / OpenAPI schema
- TypeScript type
- database migration
- event schema
- CLI / tool schema
- tests and fixtures

Contract Impact means the change affects at least one of:

- behavior
- args
- returns
- raises
- schema
- side effects
- state changes
- idempotency
- security
- external-visible result
- user-visible result

Strict means high-risk code that requires stronger governance:

- public API
- core schema
- parser / export / file writeback
- review pipeline
- workflow node
- auth / permission / security
- migration
- CI/CD
- critical path

DDT means Docstring/Contract-Driven Testing.

For strict targets:

- use explicit `l3_version`
- never use `strategy="latest"`

Diary means a structured decision/change record for important changes.

Derived views are generated context files, not sources of truth. Examples:

- `docs/harbor/project-structure.md`
- module L2 README files
- `docs/harbor/modules/<module>/module-card.md`
- `docs/harbor/modules/<module>/review-checklist.md`
- `docs/harbor/modules/<module>/debug-playbook.md`
- generated module skills under `.agents/skills/`

---

## Harbor context loading order

For non-trivial coding, debugging, review, refactor, or documentation tasks, load context in this order:

1. `AGENTS.md`
2. Project Rules, if present
3. `docs/harbor/project-structure.md`
4. Relevant L2 README, for example `<module>/README.md`
5. Relevant Module Capsule, for example:
   - `docs/harbor/modules/<module>/module-card.md`
   - `docs/harbor/modules/<module>/review-checklist.md`
   - `docs/harbor/modules/<module>/debug-playbook.md`
6. Relevant source files
7. Relevant tests

Do not read the whole repository unless the project structure, L2 README, and module capsule are insufficient.

If a relevant Harbor skill exists, prefer using the skill as the task workflow entrypoint, but do not treat the skill itself as the source of truth.

---

## Core workflow

Before substantial changes, decide:

- Contract Impact: yes / no / uncertain
- Strictness: strict / standard / light
- Runtime Safety Risk: yes / no
- Tests / DDT needed: yes / no
- Diary needed: yes / no
- Derived context update needed: yes / no

Substantial changes include:

- API changes
- schema changes
- core logic changes
- parser / export / writeback changes
- workflow changes
- migration changes
- security-sensitive changes
- dependency changes
- CI/CD changes
- destructive commands
- broad refactors

Recommended local AI coding workflow:

```powershell
harbor start
# AI coding
harbor checkpoint
# more AI coding
harbor finish --sync-context
harbor stale
harbor doctor
harbor log
harbor accept
```

Important workflow boundaries:

* `harbor finish` does not lock, log, or write derived context by default.
* `harbor finish --sync-context` explicitly refreshes changed L2 README files and changed Module Capsules.
* `harbor stale` checks whether L2 README and Module Capsule views are stale.
* `harbor doctor` performs broader Harbor health checks.
* `harbor accept` is the semantic alias for accepting the new Harbor baseline.
* Do not run `harbor accept`, `harbor lock`, `harbor log`, or `harbor module promote-skill` unless the user explicitly requests it.

---

## When Contract Impact is yes or uncertain

Follow this order:

1. Read or define the relevant contract.
2. Update the contract if behavior should change.
3. Update implementation.
4. Update tests / DDT.
5. Check semantic drift.
6. Refresh derived context if needed.
7. Create Diary Draft if the change is important.

If implementation changes but contract does not, state:

`Contract Impact: none`

and explain why.

---

## Derived context rules

The following files are derived views, not sources of truth:

* `docs/harbor/project-structure.md`
* module L2 README files
* `docs/harbor/modules/<module>/module-card.md`
* `docs/harbor/modules/<module>/review-checklist.md`
* `docs/harbor/modules/<module>/debug-playbook.md`
* `.agents/skills/harbor-debug-*/SKILL.md`

Do not manually edit derived views as project truth.

If a derived view is stale:

1. Update the underlying source of truth first:

   * code
   * contracts
   * schemas
   * tests
   * policy
   * diary
2. Regenerate the derived view with the appropriate Harbor command.

Useful commands:

```powershell
harbor project structure --write
harbor docs --changed --write
harbor module seal --changed --write
harbor stale
harbor doctor
```

Do not automatically regenerate derived views unless the user requested a write operation or the workflow explicitly includes `--sync-context`.

---

## When to read detailed rules

Read detailed docs only when needed:

* Project-level structure and context map: `docs/harbor/project-structure.md`
* Contract or schema change: `docs/harbor/contract-rules.md`
* DDT or test binding: `docs/harbor/ddt-rules.md`
* risky command or file operation: `docs/harbor/runtime-safety.md`
* important decision or breaking change: `docs/harbor/diary-rules.md`
* unclear terminology: `docs/harbor/glossary.md`

If a relevant Harbor skill exists, prefer using the skill instead of manually loading long docs.

---

## Runtime safety

Ask before:

* deleting files
* reading or printing secrets
* modifying `.env`
* changing migrations
* changing CI/CD
* installing production dependencies
* running destructive commands
* running `git reset --hard`
* running `git push`
* modifying auth, permission, billing, or production config

Do not output Bash-only commands by default.
Prefer PowerShell.

Generated context files may only be written through explicit user intent or explicit Harbor write commands, such as:

```powershell
harbor project structure --write
harbor docs --changed --write
harbor module seal --changed --write
harbor finish --sync-context
```

Do not modify the following unless explicitly requested:

* `AGENTS.md`
* Project Rules
* `.harbor/*.yaml`
* `.env`
* `secrets/**`
* migrations
* CI/CD files
* `.agents/skills/**`

---

## Tool honesty

Never claim you ran tests, lint, type checks, `harbor check`, `harbor status`, `harbor stale`, or `harbor doctor` unless you actually did.

Use:

* “已运行，结果是...”
* “未运行，建议你运行...”
* “当前环境无法运行...”

Do not invent command output, test results, Harbor reports, or generated files.

---

## Final response for non-trivial code tasks

Include:

* change summary
* Contract Impact
* strictness
* tests / DDT
* semantic drift check
* runtime safety risk
* derived context updates, if applicable
* Diary Draft if applicable

If tests or Harbor checks were not actually run, say so clearly and suggest the exact PowerShell command to run.

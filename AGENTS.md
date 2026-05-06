# AGENTS.md

## Role

You are an AI coding assistant working under the Harbor-spec context governance workflow.

Your job is to help modify, review, refactor, and document code while preventing drift between implementation, contracts, schemas, tests, docs, decision history, and runtime safety rules.

Default language: Simplified Chinese.
Default shell: Windows 11 PowerShell.

## Instruction hierarchy

This file is the lightweight cross-tool entrypoint.

Detailed references:

- `docs/harbor/glossary.md`
- `docs/harbor/contract-rules.md`
- `docs/harbor/ddt-rules.md`
- `docs/harbor/runtime-safety.md`
- `docs/harbor/diary-rules.md`

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

## Core workflow

Before substantial changes, decide:

- Contract Impact: yes / no / uncertain
- Strictness: strict / standard / light
- Runtime Safety Risk: yes / no
- Tests / DDT needed: yes / no
- Diary needed: yes / no

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

## When Contract Impact is yes or uncertain

Follow this order:

1. Read or define the relevant contract.
2. Update the contract if behavior should change.
3. Update implementation.
4. Update tests / DDT.
5. Check semantic drift.
6. Create Diary Draft if the change is important.

If implementation changes but contract does not, state:

`Contract Impact: none`

and explain why.

## When to read detailed rules

Read detailed docs only when needed:

- Contract or schema change: `docs/harbor/contract-rules.md`
- DDT or test binding: `docs/harbor/ddt-rules.md`
- risky command or file operation: `docs/harbor/runtime-safety.md`
- important decision or breaking change: `docs/harbor/diary-rules.md`
- unclear terminology: `docs/harbor/glossary.md`

If a relevant Harbor skill exists, prefer using the skill instead of manually loading long docs.

## Runtime safety

Ask before:

- deleting files
- reading or printing secrets
- modifying `.env`
- changing migrations
- changing CI/CD
- installing production dependencies
- running destructive commands
- running `git reset --hard`
- running `git push`
- modifying auth, permission, billing, or production config

Do not output Bash-only commands by default.
Prefer PowerShell.

## Tool honesty

Never claim you ran tests, lint, type checks, `harbor check`, or `harbor status` unless you actually did.

Use:

- “已运行，结果是...”
- “未运行，建议你运行...”
- “当前环境无法运行...”

## Final response for non-trivial code tasks

Include:

- change summary
- Contract Impact
- tests / DDT
- semantic drift check
- runtime safety risk
- Diary Draft if applicable
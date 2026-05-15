# TRAE Harbor Rules

Version: Harbor-spec v1.4.x

Follow `AGENTS.md` as the shared Harbor-spec project workflow.

Do not change strict/public behavior first and wait for Harbor to detect drift.
For Contract Impact = yes/uncertain, update the contract source in the same patch.

Default language: Simplified Chinese.  
Default shell: Windows 11 PowerShell.

---

## Role

This is a Harbor-managed repository.

Harbor-spec is the context governance layer for AI coding.

Keep code, contracts, tests, generated context, decision memory, and runtime safety aligned.

This file is only a lightweight TRAE adapter.  
Do not duplicate full Harbor rules here.

---

## Context entrypoint

For non-trivial coding, debugging, review, refactor, or documentation tasks, read context in this order:

1. `AGENTS.md`
2. `.harbor/rules/project-rules.md`, if present
3. `.harbor/views/project-structure.md`
4. `.harbor/views/l2/<module>/README.md`
5. `.harbor/views/modules/<module>/module-card.md`
6. `.harbor/views/modules/<module>/review-checklist.md`
7. `.harbor/views/modules/<module>/debug-playbook.md`
8. relevant source files
9. relevant tests, schemas, DDT targets, policy, or diary entries

Do not read the whole repository unless the above context is insufficient.

Generated context under `.harbor/views/**` is for orientation.  
It is not source of truth.

---

## Rule boundaries

Use these layers:

- `AGENTS.md`: cross-tool lightweight entrypoint
- `.harbor/rules/**`: detailed Harbor rule docs
- `.harbor/views/**`: generated context views
- `.harbor/diary/**`: decision memory
- `.harbor/policy.yaml`: machine-readable governance policy
- `.harbor/safety.yaml`: machine-readable safety policy
- `.agents/skills/**`: on-demand workflow skills

If Markdown rules conflict with `.harbor/policy.yaml` or `.harbor/safety.yaml`, prefer the YAML policy.

If generated context conflicts with source code, tests, schemas, policy, or diary, treat generated context as stale.

Follow `AGENTS.md` for Source of Truth Priority and conflict resolution decisions.

`.harbor/views/**` is canonical generated context, but it is advisory context, not truth override.

Legacy/export artifacts are not source of truth (`docs/harbor/**`, `<module>/README.md`, `.agents/skills/**`).

Skills are workflow entrypoints, not source of truth.

---

## Skill routing

Use Harbor skills for multi-step tasks:

- Contract or schema change: `harbor-contract-change`
- Code review, semantic drift review, contract gap review: `harbor-code-review`
- Risky operation or protected path change: `harbor-safety-preflight`
- DDT update or Diary Draft: `harbor-ddt-diary`
- Generated context refresh: `harbor-context-refresh`
- Workspace diagnostics or migration dry-run: `harbor-workspace-migration-plan`

If a skill is missing, follow `AGENTS.md` and the relevant `.harbor/rules/*.md`.

---

## Harbor workflow

Default task flow:

```powershell
harbor start
harbor checkpoint
harbor finish --sync-context
harbor stale
harbor doctor
```

Machine-readable checks:

```powershell
harbor checkpoint --ci --format json --detail summary
harbor stale --ci --format json
harbor doctor --ci --format json
```

Use `harbor checkpoint --ci --format json --detail summary` as the default machine-readable checkpoint entry for coding agents and quick structured diagnostics.

Use `harbor checkpoint --ci --format json --detail full` for deep investigation, baseline review, or saved evidence.

`harbor checkpoint --ci --format json` remains the compatibility form for full JSON output.

Workspace diagnostics only:

```powershell
harbor workspace inspect
harbor workspace migrate --dry-run
```

`harbor workspace migrate --dry-run` is read-only and is not part of the default coding workflow.

---

## TypeScript contract governance (v1.4.x)

Harbor v1.4+ evolves to language-neutral ContractSubject governance.

TypeScript v1.4.x MVP scope:

- opt-in only (`typescript.enabled=true`)
- `.ts` only by default
- supported public targets: exported function / exported async function / exported const arrow / exported class public method
- contract source focus: nearby JSDoc/TSDoc
- checkpoint categories: `contract_gap`, `skipped_no_contract`, `unsupported_syntax_advisory`
- `harbor next` guidance remains deterministic

Rules:

- TypeScript signature alone does not satisfy strict semantic contract requirements.
- Missing required nearby JSDoc/TSDoc on TypeScript public targets may produce `contract_gap`.
- Unsupported TypeScript syntax should be advisory (`unsupported_syntax_advisory`), not `contract_parse_error`.
- JavaScript is not first-class in v1.4.x.
- `.js/.jsx/.tsx/.d.ts` default scanning is not enabled in v1.4.x.
- v1.4.4 adds sidecar-driven TypeScript DDT Binding Preview: opt-in, advisory-first, non-blocking.
- preview binding is governance metadata only, not coverage proof, and formal TypeScript DDT gate remains unsupported.
- v1.4.4 adds language-neutral semantic audit foundation plus TypeScript semantic audit advisory preview.
- TypeScript semantic audit preview only applies to function-like targets with direct behavior-oriented contract evidence.
- `interface` / `type` / `Zod` remain auxiliary evidence and do not independently qualify a function-level preview subject.
- preview results do not write baseline truth, do not auto-fix code, and do not become default blockers.
- release acceptance for semantic audit preview must use mock / deterministic provider rather than real LLM availability.

Contract authoring trigger:

- For public or strict Python targets, write or update the Harbor Contract Docstring before checkpoint.
- For TypeScript exported public targets, write or update nearby high-confidence `JSDoc/TSDoc` before checkpoint.
- Read `.harbor/rules/contract-rules.md` for the full authoring templates.

---

## Explicit user request only

Do not run these unless the user explicitly requests it:

```powershell
harbor log
harbor log write
harbor log write --yes
harbor accept
harbor lock
harbor module promote-skill <module>
```

Never use `harbor accept` to hide unresolved drift.

Never claim a Diary entry was written unless it was actually written.

Do not run `harbor log write` automatically.

Do not run `harbor log write --yes` automatically.

`harbor log draft` and `harbor log draft --save` are allowed as safe draft commands.

`harbor log` / Diary write still require explicit user request.

---

## Safety

Do not silently perform high-risk operations.

Ask before:

* deleting or batch-moving files
* reading or printing secrets
* modifying `.env` or `secrets/**`
* changing migrations, CI/CD, Docker, or deployment files
* installing dependencies
* running destructive commands
* running `git push` or `git reset --hard`
* changing production config, auth, permission, billing, or user data handling
* modifying `.harbor/*.yaml`
* modifying `.agents/skills/**`
* publishing releases or tags

Use `harbor-safety-preflight` before risky operations.

Prefer dry-run, PowerShell `-WhatIf`, listing targets before deletion, showing diffs before writing, backup, and rollback plans.

Do not default to Bash-only destructive commands such as `rm -rf` unless Bash / WSL / Git Bash is explicitly required and available.

---

## Tool honesty

Do not invent tool execution results.

Never claim you ran tests, lint, type checks, build commands, CI, or Harbor commands unless you actually did.

Use:

* “已运行，结果是...”
* “未运行，建议你运行...”
* “当前环境无法运行...”
* “我只做了静态审查，未执行命令...”

---

## Diary Draft rule

For non-trivial tasks:

- assess and report `Diary Need: yes / no / uncertain`
- generate a reviewable Diary Draft when needed
- do not automatically write `.harbor/diary/**`
- do not run `harbor log` / `harbor log write` without explicit user authorization

---

## One-line rule

Keep code, contracts, tests, generated context, decision memory, and runtime safety aligned.

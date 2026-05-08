# TRAE Harbor Rules

Version: Harbor-spec v1.3.0

Follow `AGENTS.md` as the shared Harbor-spec project workflow.

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

Skills are workflow entrypoints, not source of truth.

---

## Skill routing

Use Harbor skills for multi-step tasks:

- Contract or schema change: `harbor-contract-change`
- Code review or semantic drift review: `harbor-code-review`
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
harbor stale --format json
harbor doctor --format json
```

Workspace diagnostics only:

```powershell
harbor workspace inspect
harbor workspace migrate --dry-run
```

`harbor workspace migrate --dry-run` is read-only and is not part of the default coding workflow.

---

## Explicit user request only

Do not run these unless the user explicitly requests it:

```powershell
harbor log
harbor accept
harbor lock
harbor module promote-skill <module>
```

Never use `harbor accept` to hide unresolved drift.

Never claim a Diary entry was written unless it was actually written.

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

## One-line rule

Keep code, contracts, tests, generated context, decision memory, and runtime safety aligned.

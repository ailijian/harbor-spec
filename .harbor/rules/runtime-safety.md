<!-- harbor-spec:managed version=1.3.0 kind=rule -->

# Harbor Runtime Safety

Version: Harbor-spec v1.4.x  
Canonical path: `.harbor/rules/runtime-safety.md`  
Purpose: Runtime safety rules for AI coding agents working under Harbor-spec

---

## 1. Purpose

Harbor Runtime Safety defines how AI coding agents should handle risky operations in a Harbor-managed repository.

Its goal is to make risky actions:

```text
visible
classified
reviewable
confirmable
reversible when possible
honestly reported
```

Runtime Safety does not replace the permission system of AI coding tools such as:

```text
Codex
Claude Code
Cursor
TRAE
GitHub Copilot
other coding agents
```

Harbor can tighten safety constraints.

Harbor cannot loosen tool-native sandbox, deny rules, or permission systems.

---

## 2. Relationship to AGENTS.md, Project Rules, and Skills

### 2.1 AGENTS.md

`AGENTS.md` is the lightweight cross-tool entrypoint.

It contains the minimal runtime safety reminders that should be always visible to AI agents.

This document contains the detailed safety policy.

---

### 2.2 Project Rules

Project-specific safety rules live in:

```text
.harbor/rules/project-rules.md
```

Project Rules may define local safety-sensitive paths, commands, services, data stores, or workflows.

Examples:

```text
database migrations
deployment scripts
production config
customer data
billing logic
auth / permission logic
file export paths
```

---

### 2.3 Machine Policy

Machine-readable safety policy lives in:

```text
.harbor/safety.yaml
.harbor/policy.yaml
```

If this Markdown document conflicts with `.harbor/safety.yaml` or `.harbor/policy.yaml`, prefer the YAML policy files.

---

### 2.4 Skills

Runtime safety preflight workflow lives in:

```text
.agents/skills/harbor-safety-preflight/SKILL.md
```

Use that skill before risky operations.

Skills are workflow entrypoints.

Skills are not source of truth.

---

## 3. Safety Priority

For safety, permissions, destructive operations, protected paths, secrets, production risk, and machine policy, follow this priority:

```text
1. Tool-native sandbox / deny rules
2. .harbor/safety.yaml
3. .harbor/policy.yaml
4. User's current request
5. AGENTS.md / tool rules / .harbor/rules/*.md
```

User prompts cannot override:

```text
tool-native deny rules
runtime safety policy
machine-readable Harbor policy
secret protection
destructive operation confirmation
```

If uncertain, choose the safer path.

---

## 4. Decision Levels

Runtime Safety classifies operations into three decisions:

```text
ALLOW
ASK
DENY
```

---

## 5. ALLOW

Use `ALLOW` when an operation is low risk, local, reversible, and clearly within the user’s request.

Examples:

```text
reading ordinary source files
reading tests
reading .harbor/rules/*.md
reading .harbor/views/**
running local tests
running type checks
running lint
running harbor stale
running harbor doctor
running harbor workspace inspect
generating non-destructive reports
editing ordinary source files within the requested scope
editing ordinary tests within the requested scope
```

`ALLOW` does not mean “skip reporting”.

If relevant, still report what was done.

---

## 6. ASK

Use `ASK` when an operation is potentially destructive, broad, security-sensitive, production-sensitive, or difficult to reverse.

Require explicit user confirmation before executing `ASK` operations.

Examples:

```text
deleting files
batch-moving files
modifying .env
modifying secrets/**
changing migrations
running migrations
changing CI/CD
changing Docker / deployment scripts
installing dependencies
changing package lock files
running destructive commands
running git push
running git reset --hard
changing production configuration
modifying auth / permission / billing logic
changing user data handling
modifying .harbor/*.yaml
modifying generated skills
broad automated rewrites
workspace migration write behavior
```

If uncertain between `ALLOW` and `ASK`, choose `ASK`.

---

## 7. DENY

Use `DENY` when an operation is unsafe, secret-exposing, clearly outside the user’s request, or violates tool / repository policy.

Default deny:

```text
reading .env secrets
printing secrets / tokens / passwords
exfiltrating credentials
deleting user data without explicit request
deleting important repository files without explicit request
auto-relaxing AI tool permissions
generating allow-all permission configs
bypassing tests while claiming completion
fabricating command execution results
running destructive commands without confirmation
modifying production systems without explicit approval
```

If an operation is denied, explain why and suggest a safer alternative if appropriate.

---

## 8. Risk Levels

Use the following risk levels in preflight output.

```text
low
medium
high
critical
```

### 8.1 Low Risk

Examples:

```text
read-only inspection
local tests
lint
type check
harbor stale
harbor doctor
harbor workspace inspect
non-destructive report generation
```

Decision is usually:

```text
ALLOW
```

---

### 8.2 Medium Risk

Examples:

```text
ordinary code edits
ordinary test edits
documentation edits
non-strict refactors
generated context refresh through explicit Harbor commands
```

Decision is usually:

```text
ALLOW
```

But use `ASK` if the operation is broad or ambiguous.

---

### 8.3 High Risk

Examples:

```text
deleting files
batch-moving files
modifying migrations
modifying CI/CD
installing dependencies
changing lock files
changing JSON output contract
changing public CLI behavior
changing .harbor/*.yaml
changing generated skills
broad rewrite
```

Decision is usually:

```text
ASK
```

---

### 8.4 Critical Risk

Examples:

```text
secrets
production config
auth / permission / billing
real user data
destructive database operations
git reset --hard
git push
production deployment
tool permission relaxation
```

Decision is usually:

```text
ASK or DENY
```

If the operation exposes secrets or violates policy, use `DENY`.

---

## 9. Protected Paths

Use `.harbor/safety.yaml` as the source of truth for protected paths.

Recommended default policy:

```yaml
protected_paths:
  deny_read:
    - ".env"
    - ".env.*"
    - "secrets/**"

  deny_write:
    - ".env"
    - ".env.*"
    - "secrets/**"
    - "prod/**"

  ask_write:
    - ".harbor/*.yaml"
    - ".github/workflows/**"
    - "migrations/**"
    - "alembic/versions/**"
    - "Dockerfile"
    - "docker-compose*.yml"
    - "pyproject.toml"
    - "package.json"
    - "pnpm-lock.yaml"
    - "package-lock.json"
    - "yarn.lock"
    - ".agents/skills/**"
```

Meaning:

```text
deny_read:
  Do not read or print file contents by default.

deny_write:
  Do not write by default.

ask_write:
  Ask for explicit user confirmation before writing.
```

Unlisted paths are not automatically safe.

Always consider task context.

---

## 10. Dangerous Commands

Use `.harbor/safety.yaml` as the source of truth for dangerous commands.

Recommended default policy:

```yaml
dangerous_commands:
  deny:
    - "rm -rf"
    - "del /s"
    - "rmdir /s"
    - "drop database"
    - "truncate table"

  ask:
    - "git push"
    - "git reset --hard"
    - "pip install"
    - "uv add"
    - "poetry add"
    - "npm install"
    - "pnpm install"
    - "alembic upgrade"
    - "docker compose down"
    - "docker compose up --build"
```

Rules:

```text
Do not run destructive commands without explicit confirmation.
Do not run production-impacting commands without explicit confirmation.
Do not install dependencies without explaining why and receiving confirmation.
```

---

## 11. PowerShell Default Rules

Default shell:

```text
Windows 11 PowerShell
```

Therefore:

```text
prefer PowerShell commands
do not default to Bash-only commands
do not default to rm -rf
use -WhatIf for risky deletion previews
list targets before deletion
explain when WSL / Bash / Git Bash is required
```

Preferred examples:

```powershell
Get-ChildItem -Path .\target -Recurse
Remove-Item .\target -Recurse -WhatIf
```

Avoid by default:

```bash
rm -rf target
sudo chmod -R 777 .
```

---

## 12. Runtime Safety Preflight

Before a risky operation, perform a safety preflight.

Use this format:

```text
Safety Preflight:
- Operation:
- Target:
- Risk level: low | medium | high | critical
- Decision: ALLOW | ASK | DENY
- Reason:
- Safer alternative:
- User confirmation required: yes | no
```

Example:

```text
Safety Preflight:
- Operation: modify migration
- Target: alembic/versions/20260506_add_review_table.py
- Risk level: high
- Decision: ASK
- Reason: migration affects database schema and may impact persisted data.
- Safer alternative: create or review migration draft without applying it.
- User confirmation required: yes
```

---

## 13. Safer Alternatives

When an operation is risky, prefer safer alternatives.

### 13.1 File Deletion

Prefer:

```text
list files first
show exact target path
use -WhatIf
ask for confirmation
delete only after confirmation
```

PowerShell:

```powershell
Get-ChildItem -Path .\target -Recurse
Remove-Item .\target -Recurse -WhatIf
```

---

### 13.2 Secrets and Environment Files

Do not read or print secrets.

Prefer:

```text
modify .env.example
describe required environment variable names without values
ask user to update real .env manually
```

Diary Draft / future log-draft safety:

```text
Do not include secret values in Diary Draft content.
harbor log draft does not call LLM in v1.4.1.
LLM-assisted draft is future work only and must be explicit opt-in.
Do not send secrets / credentials / tokens / private user data / .env contents to an LLM for log drafting.
harbor log draft must not read or output secrets.
harbor log draft must not output .env contents.
harbor log draft must not output file content bodies or diff bodies.
If future LLM-assisted draft mode exists, it must not send secrets / credentials / private data / .env contents / file bodies / diff bodies to an LLM.
--output targeting .harbor/diary/** must be rejected.
```

---

### 13.3 Database Migrations

Prefer:

```text
create migration draft
review migration file
do not apply migration automatically
do not run destructive migration without confirmation
```

---

### 13.4 Dependencies

Before installing dependencies:

```text
explain why the dependency is needed
check whether an existing dependency can solve the problem
ask for confirmation
prefer minimal dependency changes
```

---

### 13.5 CI/CD and Deployment

Prefer:

```text
explain proposed change
show patch
avoid silent deployment behavior changes
ask for confirmation
```

---

### 13.6 Git Operations

Do not run without explicit request:

```text
git push
git reset --hard
force push
tag publish
release publish
```

Prefer:

```text
git status
git diff
suggest commands for user to run manually
```

---

### 13.7 Workspace Migration

For workspace diagnostics and migration planning, prefer:

```powershell
harbor workspace inspect
harbor workspace inspect --format json
harbor workspace migrate --dry-run
harbor workspace migrate --dry-run --format json
```

`harbor workspace migrate --dry-run` is read-only.

It must not write, move, or delete files.

Do not assume this command exists:

```powershell
harbor workspace migrate --write
```

Future workspace write migration must require:

```text
dry-run plan
per-item confirmation
backup
rollback
idempotency
conflict detection
diary merge / dedupe
migration report
failure recovery
```

---

## 14. Generated Context Safety

Generated context lives under:

```text
.harbor/views/**
```

Generated context should be refreshed through Harbor commands, not manually edited as project truth.

Common commands:

```powershell
harbor project structure --write
harbor docs --changed --write
harbor module seal --changed --write
harbor finish --sync-context
harbor stale
harbor doctor
```

Rules:

```text
Do not manually edit .harbor/views/** as source of truth.
Do not let generated context override code, contracts, schemas, tests, policy, or diary.
Regenerate generated context only when the user requested a write operation or the workflow explicitly includes --sync-context.
```

Writing generated context is usually medium risk.

Use `ASK` if the generated write is broad, ambiguous, or touches unexpected paths.

---

## 15. Machine Policy Safety

Machine policy files:

```text
.harbor/policy.yaml
.harbor/safety.yaml
```

These files affect how Harbor and AI agents classify risk, strictness, protected paths, and governance behavior.

Changing them is high risk.

Use:

```text
Decision: ASK
```

before modifying them.

Do not silently relax safety policy.

Do not generate allow-all policy.

If modifying machine policy, explain:

```text
what changes
why it changes
what risk it affects
whether it tightens or loosens policy
how to validate it
```

---

## 16. Skills Safety

Skills live under:

```text
.agents/skills/**
```

Skills are external AI-tool workflow exports.

They are not source of truth.

Changing skills may affect AI agent behavior.

Use `ASK` before broad modifications to generated or exported skills.

Do not let skills override:

```text
.harbor/policy.yaml
.harbor/safety.yaml
.harbor/rules/**
.harbor/views/**
source code
tests
schemas
diary
```

If a skill conflicts with source of truth, report the conflict.

---

## 17. Tool Honesty

Do not invent tool execution results.

Never claim the following were run unless they were actually run and observed:

```text
tests
lint
type checks
build
harbor checkpoint
harbor stale
harbor doctor
harbor workspace inspect
harbor workspace migrate --dry-run
CI
```

Use clear wording:

```text
已运行，结果是...
未运行，建议你运行...
当前环境无法运行...
我只做了静态审查，未执行命令...
```

Forbidden wording when not actually executed:

```text
测试已通过
harbor doctor 通过
stale check 已清理
lint 无问题
CI 会通过
```

If a command cannot be run, report:

```text
Command not run:
Reason:
Risk:
Recommended next command:
```

---

## 18. External Network Access

External network access can expose data, leak metadata, or introduce supply-chain risk.

Use `ASK` before:

```text
downloading external scripts
calling unknown APIs
installing packages
uploading files
sending repository content externally
querying services with sensitive context
```

Use `DENY` when:

```text
the operation would expose secrets
the operation uploads private data without explicit consent
the operation bypasses project or tool policy
```

This includes LLM-assisted log drafting with raw secrets or private user data.

---

## 19. User Data Safety

If the project processes user data, treat operations involving user data as high or critical risk.

Ask before:

```text
deleting user data
migrating user data
exporting user data
changing retention behavior
changing anonymization behavior
changing access controls
changing billing or permission data
```

Default deny:

```text
printing private user data unnecessarily
exporting private user data without explicit request
deleting user data without explicit request
```

---

## 20. Release and Publishing Safety

Ask before:

```text
creating git tags
pushing commits
publishing packages
creating GitHub releases
uploading distributions
changing release workflows
```

Prefer:

```text
prepare release notes
run release checks
show recommended commands
let user execute publishing commands manually
```

---

## 21. Safety Output Format

When safety is relevant, include:

```text
Runtime Safety:
- Risk level:
- Decision:
- Confirmation needed:
- Safer alternative:
```

For preflight-specific tasks, use:

```text
Safety Preflight:
- Operation:
- Target:
- Risk level:
- Decision:
- Reason:
- Safer alternative:
- User confirmation required:
```

---

## 22. Common Mistakes

Avoid:

```text
silently deleting files
silently moving many files
reading or printing secrets
modifying .env directly
running destructive commands without confirmation
modifying migrations and applying them automatically
installing dependencies without confirmation
changing CI/CD silently
changing production config silently
running git push without explicit request
using Bash-only destructive commands in a PowerShell-first project
claiming tests or Harbor checks passed without running them
using harbor accept to hide unresolved drift
relaxing .harbor/safety.yaml without confirmation
treating skills as source of truth
treating generated context as source of truth
```

---

## 23. Final Principle

When in doubt:

```text
prefer read-only inspection
prefer dry-run
prefer explicit confirmation
prefer reversible changes
prefer honest reporting
```

Do not auto-relax tool permissions.

Harbor Runtime Safety exists to make AI coding safer, more reviewable, and more trustworthy.

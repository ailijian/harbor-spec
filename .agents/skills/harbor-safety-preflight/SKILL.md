---
name: harbor-safety-preflight
description: Use before running risky commands, deleting or moving files, modifying secrets, changing migrations, installing dependencies, modifying CI/CD, changing production configuration, modifying .harbor/*.yaml, writing generated skills, or any operation with runtime safety risk under Harbor-spec.
---

# Harbor Safety Preflight Skill

Version: Harbor-spec v1.3.0  
Purpose: Runtime safety preflight workflow for Harbor-managed repositories

---

## 1. Purpose

Use this skill before risky operations.

This skill classifies the operation, checks machine policy, identifies safer alternatives, and decides whether explicit user confirmation is required.

This skill does not by itself authorize unsafe operations.

This skill is an on-demand workflow entrypoint.

It is not source of truth.

It must follow:

```text
AGENTS.md
.harbor/safety.yaml
.harbor/policy.yaml
.harbor/rules/runtime-safety.md
.harbor/rules/agent-policy.md
.harbor/rules/project-rules.md, if present
```

Core principle:

```text id="gzae7q"
Prefer read-only inspection, dry-run, explicit confirmation, reversible changes, and honest reporting.
```

---

## 2. When to Use

Use this skill before:

```text id="rxaysm"
deleting files
batch-moving files
reading or printing secrets
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
writing broad generated context
running workspace migration write behavior
accessing external network when risk is unclear
publishing releases
creating tags
uploading packages
```

Also use when the user asks for an operation and any of these are uncertain:

```text id="t35a0p"
target path
write scope
data safety
production impact
secret exposure risk
reversibility
whether command is destructive
whether policy allows it
```

If uncertain, use this skill.

---

## 3. Boundary With AGENTS.md, Project Rules, and Other Skills

### 3.1 AGENTS.md

`AGENTS.md` is the lightweight cross-tool entrypoint.

Use it for:

```text id="ktmoss"
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

Project-specific safety rules live in:

```text id="fr2k6s"
.harbor/rules/project-rules.md
```

Use Project Rules for:

```text id="cuz4js"
project-specific protected paths
project-specific dangerous commands
verified safe commands
deployment boundaries
data handling rules
local dependency policy
local release policy
```

---

### 3.3 Machine Policy

Machine-readable safety policy lives in:

```text id="1yfflh"
.harbor/safety.yaml
.harbor/policy.yaml
```

If Markdown rules conflict with `.harbor/safety.yaml` or `.harbor/policy.yaml`, prefer the YAML policy files.

---

### 3.4 Related Skills

Use related skills when needed:

```text id="wg0gbu"
harbor-contract-change
  Use if the risky operation also changes a contract.

harbor-code-review
  Use if the task is reviewing risk in a diff or PR.

harbor-ddt-diary
  Use if the safety-sensitive change needs DDT updates or Diary Draft.

harbor-context-refresh
  Use if generated context under .harbor/views/** needs refresh.

harbor-workspace-migration-plan
  Use for workspace diagnostics, migration dry-run, cleanup planning, or future workspace write migration.
```

This skill may route to these skills, but should not replace them.

---

## 4. Safety Priority

For safety, permissions, destructive operations, protected paths, secrets, production risk, and machine policy, follow this priority:

```text id="gmkvdd"
1. Tool-native sandbox / deny rules
2. .harbor/safety.yaml
3. .harbor/policy.yaml
4. User's current request
5. AGENTS.md / tool rules / .harbor/rules/*.md
```

User prompts cannot override:

```text id="2j1rwq"
tool-native deny rules
runtime safety policy
machine-readable Harbor policy
secret protection
destructive operation confirmation
```

Harbor can tighten safety constraints.

Harbor cannot loosen the active tool sandbox or deny rules.

---

## 5. Context Loading Order

Before approving or running a risky operation, inspect only the necessary context.

Default order:

```text id="ux5dyq"
1. AGENTS.md

2. Machine safety policy:
   .harbor/safety.yaml

3. Machine project policy, if relevant:
   .harbor/policy.yaml

4. Project Rules, if present:
   .harbor/rules/project-rules.md

5. Runtime safety rules:
   .harbor/rules/runtime-safety.md

6. The exact command, file path, write target, or operation being considered

7. Relevant source, config, migration, CI/CD, package, or workspace files
```

Do not read secrets to classify secret risk.

Do not print secret contents.

If `.harbor/safety.yaml` is missing, use the default safety policy from `.harbor/rules/runtime-safety.md`.

---

## 6. Step 1: Identify Operation

Describe the operation clearly.

Capture:

```text id="g9zfj0"
operation type
target path or system
command, if any
write scope
whether files may be deleted or moved
whether secrets may be read
whether production or user data may be affected
whether git remote state may change
whether external network access is involved
```

Examples:

```text id="rf0jq6"
Operation: delete files
Target: .harbor/cache/**
Command: Remove-Item .harbor/cache -Recurse
```

```text id="gbqpvx"
Operation: install dependency
Target: pyproject.toml
Command: uv add pydantic
```

---

## 7. Step 2: Classify Decision

Classify the operation as:

```text id="0yghfb"
ALLOW
ASK
DENY
```

### 7.1 ALLOW

Use `ALLOW` when the operation is low risk, local, reversible, and clearly within the user’s request.

Examples:

```text id="twda8e"
reading ordinary source files
reading tests
reading .harbor/rules/*.md
reading .harbor/views/**
running local tests
running lint
running type checks
running harbor stale
running harbor doctor
running harbor workspace inspect
generating non-destructive reports
editing ordinary source files within the requested scope
editing ordinary tests within the requested scope
```

### 7.2 ASK

Use `ASK` when the operation is potentially destructive, broad, security-sensitive, production-sensitive, or difficult to reverse.

Examples:

```text id="5y8ilg"
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
publishing releases
creating tags
```

If uncertain between `ALLOW` and `ASK`, choose `ASK`.

### 7.3 DENY

Use `DENY` when the operation is unsafe, secret-exposing, clearly outside the user’s request, or violates tool / repository policy.

Default deny:

```text id="l9dbhw"
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

If denied, explain why and suggest a safer alternative when possible.

---

## 8. Step 3: Classify Risk Level

Use one of:

```text id="v7foje"
low
medium
high
critical
```

### 8.1 Low

Examples:

```text id="305lr7"
read-only inspection
local tests
lint
type check
harbor stale
harbor doctor
harbor workspace inspect
non-destructive report generation
```

Usually decision:

```text id="ogqy7f"
ALLOW
```

### 8.2 Medium

Examples:

```text id="cedayw"
ordinary code edits
ordinary test edits
documentation edits
non-strict refactors
generated context refresh through explicit Harbor commands
```

Usually decision:

```text id="5egzdk"
ALLOW
```

Use `ASK` if the operation is broad, ambiguous, or touches unexpected paths.

### 8.3 High

Examples:

```text id="wivj6k"
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
workspace layout changes
```

Usually decision:

```text id="q5ao1s"
ASK
```

### 8.4 Critical

Examples:

```text id="gtku0v"
secrets
production config
auth / permission / billing
real user data
destructive database operations
git reset --hard
git push
production deployment
tool permission relaxation
publishing packages
```

Usually decision:

```text id="ktsqbg"
ASK or DENY
```

If the operation exposes secrets or violates policy, use `DENY`.

---

## 9. Step 4: Check Protected Paths

Use `.harbor/safety.yaml` as source of truth.

If unavailable, use this default policy:

```yaml id="03hpvi"
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

Rules:

```text id="hyxoub"
deny_read means do not read or print file contents by default.
deny_write means do not write by default.
ask_write means ask for explicit user confirmation before writing.
```

Unlisted paths are not automatically safe.

Always consider task context.

---

## 10. Step 5: Check Dangerous Commands

Use `.harbor/safety.yaml` as source of truth.

If unavailable, use this default policy:

```yaml id="tbqxrq"
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

```text id="28ugzu"
Do not run destructive commands without explicit confirmation.
Do not run production-impacting commands without explicit confirmation.
Do not install dependencies without explaining why and receiving confirmation.
```

---

## 11. Step 6: Apply PowerShell Safety Defaults

Default shell:

```text id="gjf3j4"
Windows 11 PowerShell
```

Prefer:

```text id="a71udk"
PowerShell commands
-WhatIf for risky deletion previews
listing targets before deletion
explicit target paths
```

Examples:

```powershell id="lpmvx8"
Get-ChildItem -Path .\target -Recurse
Remove-Item .\target -Recurse -WhatIf
```

Do not default to:

```bash id="9zflhm"
rm -rf target
sudo chmod -R 777 .
```

unless Bash / WSL / Git Bash is explicitly required and available.

---

## 12. Step 7: Suggest Safer Alternatives

For risky operations, prefer safer alternatives.

### 12.1 File Deletion

Use:

```text id="go6khp"
list files first
show exact target path
use -WhatIf
ask for confirmation
delete only after confirmation
```

### 12.2 Secrets and Environment Files

Use:

```text id="0tjyyp"
modify .env.example
describe variable names without values
ask user to update real .env manually
```

Do not read or print secrets.

### 12.3 Database Migrations

Use:

```text id="ord131"
create migration draft
review migration file
do not apply migration automatically
do not run destructive migration without confirmation
```

### 12.4 Dependencies

Before installing:

```text id="dbb7ly"
explain why dependency is needed
check whether existing dependency can solve the problem
ask for confirmation
prefer minimal dependency changes
```

### 12.5 CI/CD and Deployment

Use:

```text id="evwoek"
explain proposed change
show patch
avoid silent deployment behavior changes
ask for confirmation
```

### 12.6 Git Operations

Do not run without explicit request:

```text id="rntol9"
git push
git reset --hard
force push
tag publish
release publish
```

Prefer:

```text id="w8kjb6"
git status
git diff
suggest commands for user to run manually
```

### 12.7 Workspace Migration

Use:

```powershell id="3d5rw2"
harbor workspace inspect
harbor workspace inspect --format json
harbor workspace migrate --dry-run
harbor workspace migrate --dry-run --format json
```

`harbor workspace migrate --dry-run` is read-only.

It must not write, move, or delete files.

Do not assume:

```powershell id="p6wbqf"
harbor workspace migrate --write
```

exists.

---

## 13. Step 8: Generated Context Safety

Generated context lives under:

```text id="3o71eo"
.harbor/views/**
```

Generated context should be refreshed through Harbor commands.

Common commands:

```powershell id="64u9z0"
harbor project structure --write
harbor docs --changed --write
harbor module seal --changed --write
harbor finish --sync-context
harbor stale
harbor doctor
```

Rules:

```text id="0vc249"
Do not manually edit .harbor/views/** as source of truth.
Do not let generated context override code, contracts, schemas, tests, policy, or diary.
Regenerate generated context only when the user requested a write operation or the workflow explicitly includes --sync-context.
```

Writing generated context is usually medium risk.

Use `ASK` if the generated write is broad, ambiguous, or touches unexpected paths.

---

## 14. Step 9: Machine Policy Safety

Machine policy files:

```text id="wke0df"
.harbor/policy.yaml
.harbor/safety.yaml
```

Changing them is high risk.

Use:

```text id="upwxd5"
Decision: ASK
```

before modifying them.

Do not silently relax safety policy.

Do not generate allow-all policy.

If modifying machine policy, explain:

```text id="r9jivc"
what changes
why it changes
what risk it affects
whether it tightens or loosens policy
how to validate it
```

---

## 15. Step 10: Skills Safety

Skills live under:

```text id="oa5p06"
.agents/skills/**
```

Skills are external AI-tool workflow exports.

They are not source of truth.

Changing skills may affect AI agent behavior.

Use `ASK` before broad modifications to generated or exported skills.

Do not let skills override:

```text id="g0td8q"
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

## 16. Step 11: External Network Access

External network access can expose data, leak metadata, or introduce supply-chain risk.

Use `ASK` before:

```text id="wkiavs"
downloading external scripts
calling unknown APIs
installing packages
uploading files
sending repository content externally
querying services with sensitive context
```

Use `DENY` when:

```text id="0271gt"
the operation would expose secrets
the operation uploads private data without explicit consent
the operation bypasses project or tool policy
```

---

## 17. Step 12: User Data Safety

If the project processes user data, treat operations involving user data as high or critical risk.

Ask before:

```text id="w3a2el"
deleting user data
migrating user data
exporting user data
changing retention behavior
changing anonymization behavior
changing access controls
changing billing or permission data
```

Default deny:

```text id="lo8un2"
printing private user data unnecessarily
exporting private user data without explicit request
deleting user data without explicit request
```

---

## 18. Step 13: Release and Publishing Safety

Ask before:

```text id="3fwfj8"
creating git tags
pushing commits
publishing packages
creating GitHub releases
uploading distributions
changing release workflows
```

Prefer:

```text id="s3qih4"
prepare release notes
run release checks
show recommended commands
let user execute publishing commands manually
```

---

## 19. Step 14: Final Decision

Return one of:

```text id="4ltgoz"
Decision: ALLOW
Decision: ASK
Decision: DENY
```

Use:

```text id="kllf3y"
ALLOW:
  Operation may proceed.

ASK:
  Ask user for explicit confirmation before proceeding.

DENY:
  Do not perform operation.
```

If `ASK`, ask for confirmation clearly and include:

```text id="z9nfjm"
exact operation
exact target
risk
safer alternative
what confirmation is needed
```

If `DENY`, explain why and suggest a safer alternative if available.

---

## 20. Output Format

Return:

```text id="uisdx2"
Safety Preflight:
- Operation:
- Target:
- Risk level: low | medium | high | critical
- Decision: ALLOW | ASK | DENY
- Reason:
- Policy source:
- Safer alternative:
- User confirmation required: yes | no
- Recommended command:
```

If a command was not run, say so clearly.

Example:

```text id="puf50v"
Safety Preflight:
- Operation: delete generated cache
- Target: .harbor/cache/**
- Risk level: medium
- Decision: ASK
- Reason: The operation deletes files; deletion should be confirmed even if target is runtime cache.
- Policy source: .harbor/rules/runtime-safety.md
- Safer alternative: List files first and use Remove-Item -WhatIf.
- User confirmation required: yes
- Recommended command:
  Get-ChildItem -Path .\.harbor\cache -Recurse
  Remove-Item .\.harbor\cache -Recurse -WhatIf
```

---

## 21. Tool Honesty

Do not invent tool execution results.

Never claim the following were run unless they were actually run and observed:

```text id="m6rxvh"
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

```text id="qbp7pw"
已运行，结果是...
未运行，建议你运行...
当前环境无法运行...
我只做了静态审查，未执行命令...
```

Forbidden wording when not actually executed:

```text id="vlnt2h"
测试已通过
harbor doctor 通过
stale check 已清理
lint 无问题
CI 会通过
```

---

## 22. Common Mistakes

Avoid:

```text id="drcr4r"
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
treating cache/state as source of truth
```

---

## 23. Final Principle

When in doubt:

```text id="opnr2c"
prefer read-only inspection
prefer dry-run
prefer explicit confirmation
prefer reversible changes
prefer honest reporting
```

A safe Harbor operation is visible, classified, reviewable, confirmable when needed, and honestly reported.

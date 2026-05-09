<div align="center">

# ⚓ HarborSpec

### A Context Governance Engine for Agentic Coding

[![CI Status](https://img.shields.io/github/actions/workflow/status/your-org/harbor-spec/ci.yml?style=flat-square)](https://github.com/your-org/harbor-spec/actions)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue?style=flat-square)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue?style=flat-square)](LICENSE)
[![Strictness](https://img.shields.io/badge/Harbor-L3%20Strict-purple?style=flat-square)](https://github.com/your-org/harbor-spec)

**A repo-local context governance engine for AI coding workflows.**
Keep code, contracts, tests, generated context, decision memory, and CI gates aligned.

[Quick Start](#-quick-start) · [Core Mental Model](#-core-mental-modell1--l2--l3) · [Daily Workflow](#-daily-workflow) · [CI Gates](#-ci-gates) · [Workspace Layout](#-harbor-workspace-layout) · [Cheat Sheet](#-command-cheat-sheet) · [Deep Dive](#-deep-dive)

</div>

Language: [中文](README.md) | English

---

## What is HarborSpec?

HarborSpec is a local context governance tool for **AI coding / vibe coding / agentic coding** workflows.

When AI can quickly generate and modify code, the hard part is no longer just “writing code.” The hard part becomes:

* Did the Docstring / contract stay aligned after the implementation changed?
* Do tests still validate the current behavior?
* Is the project context that AI reads still fresh?
* Why did we change this parameter, path, or return structure last time?
* Can CI tell whether the current context and baseline are safe?

HarborSpec aims to make context, contracts, generated documentation, and semantic baselines in AI coding workflows **checkable, traceable, and explicitly acceptable**.

It is not just another documentation generator.
It is not another Copilot.
It is a repo-local **context governance layer**.

---

## Problems HarborSpec Solves

### 1. Contract Drift

AI changed the implementation, but the contract did not change:

```text
Implementation changed, contract static.
```

HarborSpec surfaces potential semantic drift during `checkpoint`, and uses a Contract Impact Classifier to mark high-risk changes such as:

* CLI argument changes
* JSON output structure changes
* file write target changes
* generated view format changes
* source-of-truth rule changes

---

### 2. Stale Generated Context

AI tools often read compressed context views first, such as module README files, Module Capsules, and project structure views.
But those views can become stale.

HarborSpec maintains canonical generated views under `.harbor/views/**`, and uses integrity frontmatter plus `stale` checks to decide whether those views are still trustworthy.

---

### 3. Lost Project Memory

Important decisions often get scattered across chat logs, commit messages, and verbal discussions.

HarborSpec provides a Diary mechanism to record important changes, architectural decisions, and context evolution in:

```text
.harbor/diary/YYYY-MM.jsonl
```

---

### 4. Unsafe AI Automation

AI tools can easily run commands, modify files, refresh documents, or accept a baseline automatically.

HarborSpec explicitly separates:

* read-only checks that AI can run
* generated-context refresh commands that AI may run only in an explicit workflow
* baseline acceptance, diary logging, and release actions that require human authorization

---

## Core Mental Model：L1 / L2 / L3

HarborSpec context governance is easier to understand as three layers:

| Layer | Name                 | Role                                                             | Typical files / commands                                                      |
| ----- | -------------------- | ---------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| L1    | Constitution / Rules | Global rules, safety policies, and project governance boundaries | `AGENTS.md`, `.harbor/rules/**`, `.harbor/policy.yaml`, `.harbor/safety.yaml` |
| L2    | Module Context       | Module-level context and AI-readable generated views             | `.harbor/views/l2/**`, `.harbor/views/modules/**`, `harbor stale`             |
| L3    | Contract / Docstring | Function-level contracts, test bindings, and concrete behavior   | Docstrings, type hints, DDT, `l3_version`, `harbor checkpoint`                |

Simplified:

```text
L1 tells AI what rules to follow.
L2 tells AI which module context to read first.
L3 defines the concrete contract of a function, interface, or behavior.
```

```mermaid
flowchart TD
    L1[L1 Rules / Policy / Safety] --> L2[L2 Module Context Views]
    L2 --> L3[L3 Contracts / Docstrings / Tests]
    L3 --> Source[Source Implementation]
    Source --> Checkpoint[harbor checkpoint]
    L2 --> Stale[harbor stale]
    L1 --> Doctor[harbor doctor]
    Checkpoint --> Accept[harbor accept]
    Stale --> Doctor
```

This is why HarborSpec includes:

* `checkpoint`: checks L3 contract / implementation drift
* `stale`: checks whether L2 generated context is stale
* `doctor`: checks overall L1 / workspace / derived views / skill reference health

---

## Source of Truth Priority

HarborSpec clearly separates **sources of truth** from **generated context**.

| Priority | Layer                     | Examples                                                   |
| -------: | ------------------------- | ---------------------------------------------------------- |
|        1 | Safety / Policy           | tool sandbox, `.harbor/safety.yaml`, `.harbor/policy.yaml` |
|        2 | Explicit Contract         | docstring, schema, CLI contract, public API                |
|        3 | Contract Tests / DDT      | tests bound to explicit `l3_version`                       |
|        4 | Source Implementation     | current source code behavior                               |
|        5 | Human-authored Docs       | README, design docs, rules                                 |
|        6 | Canonical Generated Views | `.harbor/views/**`                                         |
|        7 | Exports / Skills          | `<module>/README.md`, `.agents/skills/**`                  |
|        8 | Cache / State / Temp      | `.harbor/cache/**`, `.harbor/state/**`                     |

Key rules:

* `.harbor/views/**` is canonical generated context, but it is not the source of truth.
* Generated views cannot override contracts, tests, or source implementation.
* `<module>/README.md` is an L2 README export, not the canonical L2 view.
* `docs/harbor/**` is legacy / optional export, not canonical storage.
* `specs/diary/**` is legacy diary read-compatible, not the new write target.
* When conflicts happen, mark `semantic drift` / `contract gap`, then resolve through tests, DDT, or human review.

---

## ⚡ Quick Start

### 1. Requirements

* Python 3.9+
* Windows / macOS / Linux
* Recommended usage from the root of a Git repository
* Command examples below use PowerShell

---

### 2. Install

```powershell
pip install harbor-spec
```

---

### 3. Initialize

Run this at your project root:

```powershell
harbor init
```

This creates the Harbor workspace configuration and uses `.harbor/config/harbor.yaml` as the canonical config write target.

---

### 4. First Check

```powershell
harbor checkpoint
```

This checks the current Harbor baseline state and runs a fast DDT check.

---

### 5. Recommended Daily Flow

```powershell
harbor start

# Work with your AI IDE...

harbor finish --sync-context
harbor doctor
```

If you have reviewed the changes and are ready to accept the new baseline:

```powershell
harbor accept
```

> HarborSpec works best when used from the terminal alongside AI IDEs such as Cursor, Windsurf, Trae, Claude Code, or Codex.
> Let AI read `AGENTS.md` and `.harbor/rules/**`, but do not let AI automatically run `harbor accept`.

---

## 🔄 Daily Workflow

Most AI coding tasks only need this flow:

```powershell
harbor start
# AI coding
harbor finish --sync-context
harbor doctor
# human review
harbor accept
```

| Command                        | Purpose                                                     | Should AI run it automatically?        |
| ------------------------------ | ----------------------------------------------------------- | -------------------------------------- |
| `harbor start`                 | Inspect Harbor status before starting work                  | Yes                                    |
| `harbor finish --sync-context` | Final checks and refresh changed L2 README + Module Capsule | Only in an explicit finishing workflow |
| `harbor doctor`                | Overall health check                                        | Yes                                    |
| `harbor accept`                | Human acceptance of a new Harbor baseline                   | No                                     |

For a stricter local finish:

```powershell
harbor finish --sync-context
harbor stale
harbor doctor
```

Notes:

* `finish --sync-context` refreshes generated context for changed modules.
* `stale` checks whether L2 README and Module Capsule views are stale.
* `doctor` runs broader workspace health checks.

---

## When should I run `harbor log`?

Run `harbor log` only when the change involves an important decision:

```powershell
harbor log
```

Good cases include:

* Contract Change
* Breaking Change
* architectural decision
* important bugfix
* CI / runtime safety policy change
* source-of-truth rule change

`harbor finish --sync-context` does not automatically write Diary entries.
`harbor log` requires explicit human authorization.

---

## ✅ CI Gates

HarborSpec v1.3.0 provides three CI gates:

```powershell
harbor checkpoint --ci
harbor stale --ci
harbor doctor --ci
```

### `checkpoint --ci`

Strict baseline gate.

It blocks on:

* DDT failure
* missing / untracked function
* implementation drift
* contract changed
* body + contract changed
* confirmed contract impact

It does not fail just because of `possible_contract_impact`.
`possible_contract_impact` is advisory.

---

### `stale --ci`

Generated-context freshness gate.

It blocks on:

* canonical L2 README stale / unknown
* canonical Module Capsule stale / unknown

It does not block on:

* `<module>/README.md` export mismatch
* legacy advisory
* optional export advisory

---

### `doctor --ci`

Overall health gate.

By default, it only blocks when:

```text
DoctorCheckResult.status == FAIL
```

It does not fail on ordinary WARN / SKIP results such as:

* workspace changed advisory
* legacy metadata advisory
* legacy diary advisory
* optional export advisory

---

### CI JSON Output

All CI JSON commands guarantee:

* stdout is a single JSON object
* `writes_files=false`
* no auto-fix
* no auto-refresh
* no automatic `accept`
* no human text mixed into JSON output

Examples:

```powershell
harbor checkpoint --ci --format json
harbor stale --ci --format json
harbor doctor --ci --format json
```

---

## 🧭 Harbor Workspace Layout

HarborSpec v1.3.0 uses `.harbor/*` as the canonical workspace.

```text
.harbor/
  config/
    harbor.yaml              # canonical config
  views/
    project-structure.md     # canonical project structure view
    l2/
      <module>/README.md     # canonical L2 README
      _meta.json             # canonical L2 metadata
    modules/
      <module>/
        module-card.md
        review-checklist.md
        debug-playbook.md
  diary/
    YYYY-MM.jsonl            # canonical diary
  reports/
    dogfooding/
  cache/                     # ignored runtime cache
  state/                     # ignored runtime state
  exports/                   # ignored generated exports
```

### Recommended Git tracking

Recommended to track:

```text
.harbor/config/harbor.yaml
.harbor/views/**
.harbor/diary/**
.harbor/reports/dogfooding/**
docs/design/**
```

Recommended to ignore:

```text
.harbor/cache/**
.harbor/state/**
.harbor/exports/**
.pytest_cache/**
**/__pycache__/**
```

Legacy / export paths:

| Path                   | Role                               |
| ---------------------- | ---------------------------------- |
| `.harbor/config.yaml`  | legacy config read-compatible      |
| `.harbor/l2_meta.json` | legacy L2 metadata read-compatible |
| `specs/diary/**`       | legacy diary read-compatible       |
| `docs/harbor/**`       | optional docs export / legacy      |
| `<module>/README.md`   | human-readable L2 README export    |

---

## 🧱 Generated Context Integrity

Canonical generated markdown views under `.harbor/views/**` include integrity frontmatter.

Example:

```yaml
---
generated_by: harbor-spec
harbor_version: 1.3.0
view_type: l2_readme
module: harbor/core
generation_command: harbor docs --module harbor/core --write
stale_policy: fail-closed
source_path_count: 12
source_paths_truncated: false
source_fingerprint: sha256:...
contract_fingerprint: sha256:...
generator_fingerprint: sha256:...
generated_at: 2026-05-09T10:00:00Z
---
```

Notes:

* source of truth priority applies when contracts, tests, and generated views disagree.
* `generated_at` is informational only.
* stale comparison ignores `generated_at`.
* If inputs do not change, Harbor tries to reuse the old `generated_at` to avoid meaningless Git diffs.
* canonical `.harbor/views/**` is generated context.
* generated views are advisory context, not source of truth.
* generated views are not source of truth.

---

## 📌 Command Cheat Sheet

HarborSpec has many commands, but you do not need to memorize all of them.
Use them by scenario.

### 1. Daily AI coding

| Command                        | Description                                                   |
| ------------------------------ | ------------------------------------------------------------- |
| `harbor start`                 | Inspect Harbor status before starting work                    |
| `harbor checkpoint`            | Local checkpoint: status + fast DDT + contract impact summary |
| `harbor finish`                | Final check, without refreshing generated context             |
| `harbor finish --sync-context` | Final check plus changed L2 README + Module Capsule refresh   |
| `harbor stale`                 | Check generated context freshness                             |
| `harbor doctor`                | Overall health check                                          |
| `harbor accept`                | Human acceptance of a new Harbor baseline                     |

---

### 2. CI / release gates

| Command                  | Description                              |
| ------------------------ | ---------------------------------------- |
| `harbor checkpoint --ci` | Strict baseline gate                     |
| `harbor stale --ci`      | canonical generated views freshness gate |
| `harbor doctor --ci`     | workspace health gate                    |
| `--format json`          | machine-readable JSON output             |

---

### 3. Generated context

Usually, you only need:

```powershell
harbor finish --sync-context
```

For precise control:

| Command                                 | Description                             |
| --------------------------------------- | --------------------------------------- |
| `harbor project structure --write`      | Write canonical project structure view  |
| `harbor docs --changed --write`         | Refresh changed modules' L2 README      |
| `harbor docs --module <module> --write` | Refresh one module's L2 README          |
| `harbor module seal --changed --write`  | Refresh changed modules' Module Capsule |
| `harbor module seal <module> --write`   | Refresh one module's Module Capsule     |

---

### 4. Workspace diagnostics

| Command                                            | Description                                                |
| -------------------------------------------------- | ---------------------------------------------------------- |
| `harbor workspace inspect`                         | Inspect canonical / legacy / export / cache / state layout |
| `harbor workspace inspect --format json`           | Machine-readable workspace report                          |
| `harbor workspace migrate --dry-run`               | Read-only migration plan                                   |
| `harbor workspace migrate --dry-run --format json` | Machine-readable dry-run report                            |

Note:

```text
harbor workspace migrate --write is not implemented in v1.3.0.
```

---

### 5. Module-level maintenance

| Command                                | Description                                        |
| -------------------------------------- | -------------------------------------------------- |
| `harbor module inspect <module>`       | Inspect indexed context for a module               |
| `harbor module seal <module>`          | Preview Module Capsule                             |
| `harbor module seal <module> --write`  | Write Module Capsule                               |
| `harbor module stale <module>`         | Check one module's Capsule freshness               |
| `harbor module promote-skill <module>` | Optional: promote a high-value module into a skill |

`promote-skill` is a manual action. It is not recommended for every module by default.

---

### 6. Onboarding / migration

| Command                          | Description                              |
| -------------------------------- | ---------------------------------------- |
| `harbor init`                    | Initialize Harbor workspace              |
| `harbor adopt <path>`            | Adopt existing code                      |
| `harbor config list`             | View config                              |
| `harbor config add <pattern>`    | Add scan path                            |
| `harbor config remove <pattern>` | Remove scan path                         |
| `harbor lock`                    | Low-level baseline / index operation     |
| `harbor accept`                  | Human-facing baseline acceptance command |

For daily usage, prefer `harbor accept` over direct `harbor lock`.

---

## 🤖 AI Tool Integration

HarborSpec recommends a layered rule system instead of putting everything into one long prompt.

Recommended structure:

```text
AGENTS.md                         # shared cross-tool entrypoint
.harbor/rules/role-rules.md       # TRAE / IDE lightweight entrypoint
.harbor/rules/project-rules.md    # project-specific rules
.harbor/policy.yaml               # machine-readable governance policy
.harbor/safety.yaml               # machine-readable safety policy
.agents/skills/**                 # optional skill integration artifacts
```

### Commands AI may run automatically

Read-only checks:

```powershell
harbor start
harbor checkpoint
harbor stale
harbor doctor
harbor workspace inspect
harbor workspace migrate --dry-run
```

CI gates:

```powershell
harbor checkpoint --ci
harbor stale --ci
harbor doctor --ci
```

Allowed in an explicit finishing workflow:

```powershell
harbor finish --sync-context
```

### Commands AI should not run automatically

These require explicit human authorization:

```powershell
harbor accept
harbor log
harbor lock
harbor module promote-skill <module>
git tag
git push
```

Why:

* `accept` accepts a new Harbor baseline
* `log` writes decision memory
* `lock` updates the low-level baseline
* `promote-skill` creates an external integration artifact
* `git tag/push` are release actions

---

## 🔍 Deep Dive

### 1. Checkpoint: semantic baseline check

`checkpoint` answers:

> Has the code changed semantically relative to the Harbor baseline?

It checks:

* new functions
* missing functions
* Body changed, Contract static
* Contract changed
* Body + Contract changed
* DDT binding status
* Contract Impact summary

Common commands:

```powershell
harbor checkpoint
harbor checkpoint --ci
```

---

### 2. Stale: generated context freshness check

`stale` answers:

> Are the L2 README / Module Capsule views that AI reads still fresh?

It focuses on canonical generated views under `.harbor/views/**`.

If source / contract / generator changes but generated views were not refreshed, `stale --ci` fails.

Common fix:

```powershell
harbor finish --sync-context
```

---

### 3. Doctor: workspace health check

`doctor` answers:

> Is the Harbor workspace healthy overall?

It checks:

* config / index
* workspace status
* DDT fast check
* derived views
* skill references
* legacy advisory

`doctor --ci` only blocks on FAIL by default. WARN/SKIP remain advisory.

---

### 4. L2 README: module-level context

L2 README is a module-level AI context view.

Canonical path:

```text
.harbor/views/l2/<module>/README.md
```

Default export:

```text
<module>/README.md
```

L2 README helps AI quickly understand:

* module responsibility
* key files
* public API
* test entrypoints
* maintenance suggestions

---

### 5. Module Capsule: AI maintenance context

Module Capsule is a context pack optimized for maintenance tasks.

Canonical path:

```text
.harbor/views/modules/<module>/
  module-card.md
  review-checklist.md
  debug-playbook.md
```

It helps AI decide before debug, review, or refactor:

* What is this module responsible for?
* Which files matter most?
* What should be checked before changing it?
* Where should debugging start?

Module Capsule is a derived maintenance view, not the source of truth.

---

### 6. DDT: Docstring / Contract-Driven Testing

DDT prevents “green tests that still validate the old contract.”

Example:

```python
from harbor.core.ddt import harbor_ddt_target

@harbor_ddt_target("harbor.core.sync.SyncEngine.check_status", l3_version=1)
def test_sync_engine_drift_detection():
    ...
```

Strict targets must use explicit `l3_version`. Do not use `strategy="latest"` for strict targets.

---

### 7. Diary: decision memory

Diary records important changes and decisions.

```powershell
harbor log
```

Canonical write path:

```text
.harbor/diary/YYYY-MM.jsonl
```

`specs/diary/**` is legacy read-compatible only.

---

## 🧪 Optional LLM Semantic Audit

HarborSpec core checks do not require an LLM.
If you want to enable semantic audit, configure `.env`:

```ini
HARBOR_LLM_PROVIDER=openai
HARBOR_LLM_API_KEY=sk-xxxxxx
HARBOR_LLM_BASE_URL=https://api.openai.com/v1
HARBOR_LANGUAGE=en
```

You may also use other providers compatible with the OpenAI API.

---

## 🚀 v1.3.0 Highlights

v1.3.0 upgrades HarborSpec from a contract / documentation checking tool into an **agentic coding context governance workflow**.

Highlights:

* Canonical `.harbor/*` workspace
* `.harbor/views/**` generated context views
* Generated Context Integrity frontmatter
* Source of Truth Priority
* Contract Impact Classifier MVP
* `harbor checkpoint --ci`
* `harbor stale --ci`
* `harbor doctor --ci`
* Workspace inspect
* Workspace migrate dry-run
* L2 README canonical path
* Module Capsule canonical path
* Diary canonical path
* legacy/export advisory

---

## 🧩 Advanced: adopting existing projects

For existing projects, initialize Harbor first:

```powershell
harbor init
```

View config:

```powershell
harbor config list
```

Adopt existing code:

```powershell
harbor adopt backend/ --strategy safe
```

Modes:

| Mode         | Description                                       |
| ------------ | ------------------------------------------------- |
| `safe`       | only adopt functions that already have docstrings |
| `aggressive` | insert TODO templates for public functions        |
| `--dry-run`  | preview only, no writes                           |

After adoption, humans should decide whether to accept the baseline:

```powershell
harbor accept
```

---

## 🛡️ Runtime Safety

HarborSpec follows these principles by default:

* read-only checks do not write files
* `--ci` does not auto-fix
* `workspace migrate --dry-run` does not write files
* `finish --sync-context` only refreshes generated context
* `accept` requires human authorization
* `log` requires human authorization
* `lock` should not be run automatically by AI
* release commands must be executed by humans

---

## 📚 Recommended Reading

* `AGENTS.md`: shared cross-tool entrypoint
* `.harbor/rules/role-rules.md`: TRAE / IDE lightweight entrypoint
* `.harbor/rules/project-rules.md`: project-specific rules
* `docs/design/harbor-workspace-layout-v1.md`: workspace layout design
* `.harbor/views/project-structure.md`: canonical project structure view
* `.harbor/views/l2/**`: canonical L2 README
* `.harbor/views/modules/**`: canonical Module Capsule

---

## FAQ

### Is HarborSpec a documentation generator?

No.
HarborSpec generates context views, but those views are advisory context.
Its core purpose is to govern consistency across code, contracts, tests, generated context, and baselines.

---

### Do I need to memorize all commands?

No.
Most of the time, you only need:

```powershell
harbor start
harbor finish --sync-context
harbor doctor
```

Before release, run:

```powershell
pytest
harbor checkpoint --ci
harbor stale --ci
harbor doctor --ci
```

---

### What is the difference between `harbor stale` and `harbor doctor`?

`stale` checks whether generated views are fresh.
`doctor` checks overall Harbor workspace health.

Simplified:

```text
stale = freshness check
doctor = health check
```

---

### Does `harbor finish --sync-context` automatically write Diary entries?

No.
It only refreshes changed modules' L2 README and Module Capsule, then runs final checks.

`harbor log` must be executed manually.

---

### Can AI automatically run `harbor accept`?

Not recommended.
`accept` means accepting a new Harbor baseline, and it requires human confirmation.

---

### Does v1.3.0 support `workspace migrate --write`?

No.
v1.3.0 only supports:

```powershell
harbor workspace migrate --dry-run
```

It prints a migration plan and does not write files.

---

## License

Apache-2.0

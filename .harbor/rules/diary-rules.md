<!-- harbor-spec:managed version=1.3.0 kind=rule -->

# Harbor Diary Rules

Version: Harbor-spec v1.3.0  
Canonical path: `.harbor/rules/diary-rules.md`  
Purpose: Rules for maintaining structured decision memory under Harbor-spec

---

## 1. Purpose

Harbor Diary is the decision memory layer of a Harbor-managed repository.

It records why important changes happened, not just what changed.

Diary helps humans and AI agents understand:

```text
why a contract changed
why a breaking change was accepted
why a legacy behavior was preserved
why a safety policy was tightened
why a migration strategy was chosen
why a workaround exists
why a test or DDT strategy changed
```

Diary exists to prevent decision-memory loss during AI coding.

Core principle:

```text
Diary records why, not just what.
```

---

## 2. Canonical Path

Canonical Diary write path:

```text
.harbor/diary/YYYY-MM.jsonl
```

Example:

```text
.harbor/diary/2026-05.jsonl
```

Each line should be one JSON object.

Do not write Diary entries to arbitrary documentation files.

Do not treat changelog, commit messages, generated context, or skills as Diary replacements.

---

## 3. Relationship to AGENTS.md, Project Rules, and Skills

### 3.1 AGENTS.md

`AGENTS.md` contains lightweight Diary reminders:

```text
when Diary may be needed
where Diary lives
when not to claim a Diary entry was written
```

It should not contain the full Diary schema or full Diary policy.

---

### 3.2 Project Rules

Project-specific Diary rules live in:

```text
.harbor/rules/project-rules.md
```

Project Rules may define local Diary triggers, such as:

```text
changes to public CLI behavior
changes to export format
changes to review pipeline
changes to workspace layout
changes to production safety policy
changes to customer-visible output
```

---

### 3.3 Machine Policy

Machine-readable policy may live in:

```text
.harbor/policy.yaml
```

If `.harbor/policy.yaml` defines Diary requirements, use it as the source of truth.

---

### 3.4 Skills

Diary-related workflow lives in:

```text
.agents/skills/harbor-ddt-diary/SKILL.md
```

Use that skill when the task involves:

```text
DDT updates
l3_version updates
Diary Drafts
changelog updates
release notes
important architecture decisions
```

Skills are workflow entrypoints.

Skills are not source of truth.

---

## 4. Diary Is Not Changelog

Diary and changelog are different.

Diary records:

```text
why the change happened
what tradeoff was made
what alternatives were rejected
what risks remain
what future agents should remember
```

Changelog records:

```text
what changed for users
which version contains the change
whether the change is breaking
how users should adapt
```

The same important change may need both a Diary entry and a changelog entry.

---

## 5. Diary Is Not Commit Message

Commit messages record code history.

Diary records decision history.

A commit message may say:

```text
Update workspace layout
```

A Diary entry should explain:

```text
why workspace layout changed
why .harbor/ became canonical
what paths are now generated context
what migration risk remains
what agents should do differently
```

---

## 6. Diary Is Not ADR

ADR means Architecture Decision Record.

ADR is better for large, long-lived architecture decisions.

Diary is lighter and more frequent.

Use Diary for:

```text
contract changes
important bugfixes
workflow changes
safety decisions
test strategy decisions
release-relevant tradeoffs
```

Use ADR when the project needs a formal architecture decision document.

A significant Diary entry may later be promoted into an ADR.

---

## 7. When Diary Is Required

Create or recommend a Diary Draft when the task involves:

```text
Contract Change
Breaking Change
important bugfix
architecture decision
security change
runtime safety policy change
migration
workspace layout change
export format change
public CLI behavior change
public JSON output change
schema change
DDT strategy change
l3_version strategy change
Agent workflow change
release-relevant decision
legacy compatibility decision
non-obvious workaround
important performance tradeoff
important reliability tradeoff
```

If uncertain, prefer creating a Diary Draft rather than silently dropping decision context.

---

## 8. When Diary Is Usually Not Needed

Diary is usually not needed for:

```text
typo fix
formatting change
comment wording cleanup
internal variable rename
light helper cleanup
non-behavioral refactor
test helper rearrangement with no strategy change
small documentation wording improvement
minor generated context refresh with no decision change
```

However, if a small change occurs in a strict area and carries non-obvious reasoning, a lightweight Diary Draft may still be useful.

---

## 9. Diary Draft vs Written Diary Entry

AI agents should distinguish between:

```text
Diary Draft
Written Diary Entry
```

### 9.1 Diary Draft

A Diary Draft is text proposed in the final response.

It has not been written to disk.

Use this when:

```text
the user did not explicitly request writing the Diary
the agent cannot write files
the task produced an important decision but write permission is unclear
```

### 9.2 Written Diary Entry

A Written Diary Entry is actually appended to:

```text
.harbor/diary/YYYY-MM.jsonl
```

Do not claim a Diary entry was written unless the write was actually executed and observed.

---

## 10. When Writing Requires Explicit Request

Do not run the following unless the user explicitly requests it:

```powershell
harbor log
```

Do not manually append JSONL unless:

```text
the user explicitly asks
or the Harbor CLI is unavailable
and the user accepts manual write behavior
```

When in doubt, output a Diary Draft instead of writing.

---

## 11. Preferred Write Command

Preferred command:

```powershell
harbor log -m "<message>" --type <type> --importance <importance> --visibility <visibility>
```

Example:

```powershell
harbor log -m "Adopt .harbor as canonical workspace for v1.3.0" --type decision --importance high --visibility repo
```

If the command supports additional structured fields, include them when appropriate.

---

## 12. Diary Entry Types

Allowed `type` values:

```text
feature
bugfix
refactor
chore
incident
decision
security
migration
test
```

Meaning:

```text
feature
  New user-facing or project-facing capability.

bugfix
  Important bug fix or behavior correction.

refactor
  Structural change that preserves intended behavior.

chore
  Maintenance, packaging, docs, or release-support change.

incident
  Severe issue, regression, data risk, or production-impacting problem.

decision
  Architecture, policy, workflow, or contract decision.

security
  Safety, permission, secrets, auth, or policy change.

migration
  Workspace, database, schema, data, or file layout migration.

test
  Test strategy, DDT strategy, or validation change.
```

---

## 13. Importance Levels

Allowed `importance` values:

```text
low
normal
high
critical
```

Guidance:

```text
low
  Minor but useful context.

normal
  Meaningful project change worth preserving.

high
  Affects strict paths, contracts, schemas, public behavior, workflow, safety, or release behavior.

critical
  Security, data integrity, production risk, breaking change, incident, destructive migration, or major architecture decision.
```

---

## 14. Visibility Levels

Allowed `visibility` values:

```text
internal
repo
public
```

Guidance:

```text
internal
  Sensitive team-only reasoning. Avoid public release notes.

repo
  Safe to store in repository and useful for future agents.

public
  Can be adapted into changelog, release notes, or public documentation.
```

Do not put secrets, tokens, private customer data, or sensitive internal data into Diary entries.

---

## 15. Diary Draft Format

Use this format in final responses when Diary is needed but not written:

```text
[Diary Draft]
- Type: feature | bugfix | refactor | chore | incident | decision | security | migration | test
- Importance: low | normal | high | critical
- Visibility: internal | repo | public
- Module:
- Contract Impact: yes | no | uncertain
- Breaking Change: yes | no | uncertain
- Summary:
- Reason:
- Changes:
  - ...
- Tests:
  - ...
- Risks:
  - ...
- Follow-up:
  - ...
- Ref:
```

If Diary is not needed, state:

```text
Diary: not needed
Reason:
- <why this change does not require a decision record>
```

---

## 16. JSONL Recommended Structure

A written Diary entry should be one JSON object per line.

Recommended structure:

```json
{
  "type": "decision",
  "importance": "high",
  "visibility": "repo",
  "module": "workspace",
  "contract_impact": true,
  "breaking_change": false,
  "summary": "Adopt .harbor as the canonical workspace for Harbor-spec v1.3.0.",
  "reason": "The project has few current users, so this is the right release window to remove old path ambiguity and stabilize the workspace mental model.",
  "changes": [
    "Rules move to .harbor/rules/.",
    "Generated context moves to .harbor/views/.",
    "Diary moves to .harbor/diary/.",
    "AGENTS.md remains the lightweight cross-tool entrypoint."
  ],
  "tests": [
    "harbor workspace inspect --format json",
    "harbor doctor"
  ],
  "risks": [
    "Existing pre-1.3.0 users may need workspace initialization or migration guidance."
  ],
  "follow_up": [
    "Keep workspace migrate --dry-run as read-only diagnostics.",
    "Update skills to reference .harbor/rules and .harbor/views."
  ],
  "ref": ""
}
```

---

## 17. Required Fields

A written Diary entry should include:

```text
type
importance
visibility
summary
reason
changes
risks
```

Recommended fields:

```text
module
contract_impact
breaking_change
tests
follow_up
ref
timestamp
author
```

If a value is unknown, use `null` or omit optional fields.

Do not invent commit hashes, PR links, issue links, test results, or user decisions.

---

## 18. Contract Impact in Diary

When `contract_impact` is true, include which contract sources are affected.

Recommended field:

```json
"contract_sources": [
  "CLI output",
  "JSON output",
  "Docstring",
  "DDT target"
]
```

If uncertain, use:

```json
"contract_impact": null
```

or state in the draft:

```text
Contract Impact: uncertain
```

Do not hide uncertain contract impact.

---

## 19. Breaking Change in Diary

When `breaking_change` is true, explain:

```text
who is affected
what changes
what migration is needed
whether fallback exists
whether release notes are needed
```

If uncertain, write:

```json
"breaking_change": null
```

or state in the draft:

```text
Breaking Change: uncertain
```

---

## 20. Diary and DDT

Create or recommend a Diary Draft when DDT strategy changes.

Examples:

```text
strict target changes from strategy="latest" to explicit l3_version
test binding policy changes
contract versioning strategy changes
DDT scaffold generation behavior changes
false-positive handling changes
semantic audit triage policy changes
```

Use:

```text
.harbor/rules/ddt-rules.md
```

for detailed DDT rules.

Use:

```text
.agents/skills/harbor-ddt-diary/SKILL.md
```

for DDT + Diary workflow.

---

## 21. Diary and Runtime Safety

Create or recommend a Diary Draft when safety policy changes.

Examples:

```text
protected paths change
dangerous commands change
default safety decision changes
external network policy changes
secret handling rules change
workspace migration safety rules change
generated skill write policy changes
```

Use:

```text
.harbor/rules/runtime-safety.md
.harbor/safety.yaml
```

for safety rules.

If a safety policy is loosened, the Diary entry should explain why and what mitigations exist.

---

## 22. Diary and Generated Context

Generated context lives under:

```text
.harbor/views/**
```

A simple refresh of generated context usually does not require Diary.

Diary may be needed when:

```text
generated context schema changes
Module Capsule structure changes
L2 README semantics change
project structure generation rules change
generated context is intentionally redefined
agent context loading strategy changes
```

Generated context is not a Diary substitute.

---

## 23. Diary and Workspace Migration

Create or recommend a Diary Draft when workspace layout decisions change.

Examples:

```text
adopting .harbor/ as canonical workspace
changing .harbor/rules layout
changing .harbor/views layout
changing diary path
changing migration strategy
changing workspace inspect output
changing migrate --dry-run semantics
introducing or removing managed file markers
```

Workspace migration must be handled carefully.

`harbor workspace migrate --dry-run` is read-only.

Do not write, move, or delete workspace files without explicit user confirmation.

---

## 24. Diary and Release Notes

A Diary entry may imply a changelog or release note, but it does not replace it.

Create release notes when a change is user-visible or release-relevant:

```text
new public CLI command
changed CLI behavior
changed JSON output
workspace layout change
new required initialization step
breaking change
migration guidance
changed safety behavior
changed generated context layout
```

Diary explains why.

Release notes explain what users need to know.

---

## 25. Diary Quality Standard

A good Diary entry is:

```text
specific
honest
short enough to scan
clear about reason
clear about tradeoff
clear about risks
clear about follow-up
grounded in actual changes
safe to store at the chosen visibility
```

A bad Diary entry is:

```text
vague
too long
pure changelog
missing reason
missing risks
hiding uncertainty
claiming unrun tests passed
including secrets
inventing links or commit hashes
copying full code diffs
```

---

## 26. Privacy and Secret Safety

Do not write the following into Diary:

```text
secrets
tokens
passwords
private keys
raw .env values
private customer data
unnecessary personal data
sensitive production data
```

If a sensitive issue must be recorded, summarize safely:

```text
Summary: Tightened secret handling policy.
Reason: Previous workflow risked exposing environment values.
```

Do not include actual secret values.

---

## 27. Tool Honesty

Do not claim Diary was written unless it was actually written.

Allowed wording:

```text
已生成 Diary Draft，未写入文件。
已运行 harbor log，写入 .harbor/diary/2026-05.jsonl。
未写入 Diary；建议你确认后运行 harbor log。
```

Forbidden wording when not executed:

```text
Diary 已记录
已写入决策日志
日志已更新
```

unless the write actually happened.

---

## 28. Final Response Requirements

When Diary is relevant, include:

```text
Diary:
- needed: yes | no | uncertain
- reason:
- draft: <if needed and not written>
- written: yes | no
```

For larger tasks, include Diary status in the final summary:

```text
Change Summary:
- Contract Impact:
- Tests / DDT:
- Generated Context:
- Diary:
- Remaining risks:
```

---

## 29. Common Mistakes

Avoid:

```text
writing Diary for every tiny edit
skipping Diary for important contract changes
using Diary as changelog only
using changelog as Diary
using commit message as Diary
claiming Diary was written when only a draft was generated
including secrets or private data
inventing PR links, commit hashes, or test results
omitting risks
omitting reason
hiding breaking changes
manually appending malformed JSONL
```

---

## 30. Final Principle

When a future human or AI agent asks:

```text
Why was this changed?
```

Diary should provide the answer.

If the change matters and the reason would otherwise be lost, create a Diary Draft.

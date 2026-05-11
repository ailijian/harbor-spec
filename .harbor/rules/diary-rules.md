<!-- harbor-spec:managed version=1.4.x kind=rule -->

# Harbor Diary Rules

Version: Harbor-spec v1.4.x  
Canonical path: `.harbor/rules/diary-rules.md`  
Purpose: Rules for maintaining structured decision memory under Harbor-spec

---

## 1. Purpose

Harbor Diary is the decision memory layer of a Harbor-managed repository.

It records why important changes happened, not just what changed.

Diary should capture decisions and tradeoffs, not every low-level implementation detail.

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

A Diary Draft is reviewable assistant output or report output, not source-of-truth memory.

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

For non-trivial tasks, agents should always report:

```text
Diary Need: yes / no / uncertain
```

### 9.3 Artifact Layers

Harbor v1.4.1 distinguishes three different log artifacts:

```text
Latest Draft Cache
Saved Draft Report
Written Diary Entry
```

Latest Draft Cache:

```text
.harbor/state/log/latest-draft.md
.harbor/state/log/latest-draft.json
```

Rules:

```text
Latest Draft Cache is runtime state.
Latest Draft Cache may be overwritten by later draft runs.
Latest Draft Cache is reviewable working state, not source-of-truth memory.
```

Saved Draft Report:

```text
.harbor/reports/log-draft-*.md
.harbor/reports/log-draft-*.json
```

Rules:

```text
Saved Draft Report is a reviewable report artifact.
Saved Draft Report may be produced by --save or explicit --output.
Saved Draft Report is not source-of-truth decision memory.
```

Written Diary Entry:

```text
.harbor/diary/YYYY-MM.jsonl
```

Rules:

```text
Written Diary Entry is source-of-truth decision memory.
Only an explicitly authorized write path may append it.
Draft cache and saved reports never become source of truth by themselves.
```

### 9.4 `harbor log write`

`harbor log write` is the controlled write path from a reviewable draft into source-of-truth decision memory.

Rules:

```text
harbor log write reads latest draft by default.
harbor log write --from-latest-draft explicitly reads the latest draft cache.
harbor log write without --yes requires interactive confirmation.
harbor log write without --yes must be rejected in non-interactive environments.
harbor log write --yes is explicit authorization to write.
harbor log write --from-draft only allows .harbor/reports/** or latest draft cache paths as sources.
harbor log write must reject .harbor/diary/**, .env, .env.*, secrets/**, repo-external paths, and other unallowlisted sources.
successful harbor log write updates .harbor/state/log/last_log_marker.json after writing .harbor/diary/YYYY-MM.jsonl.
last_log_marker is runtime state, not source-of-truth memory.
```

---

## 10. When Writing Requires Explicit Request

Do not run the following unless the user explicitly requests it:

```powershell
harbor log
harbor log write
```

Do not manually append JSONL unless:

```text
the user explicitly asks
or the Harbor CLI is unavailable
and the user accepts manual write behavior
```

When in doubt, output a Diary Draft instead of writing.

If `harbor log` cannot generate content in the current flow, output a human-reviewable Diary Draft instead of claiming the Diary was written.

---

## 11. `harbor log draft` Safe Draft Command

`harbor log draft` is a safe draft command for generating reviewable Diary Draft output.

Allowed examples:

```powershell
harbor log draft
harbor log draft --format json
harbor log draft --since-last-accept
harbor log draft --since-last-log
harbor log draft --from-report <path>
harbor log draft --save
harbor log draft --output .harbor/reports/<name>.md
```

Rules:

```text
Diary Draft is reviewable assistant output / report output, not written Diary.
harbor log draft is safe with respect to source-of-truth memory.
harbor log draft may be used after accept to draft a Diary from change-window evidence.
harbor log draft must not write .harbor/diary/** by default.
harbor log draft writes latest draft cache to .harbor/state/log/latest-draft.md and .harbor/state/log/latest-draft.json.
harbor log draft --save writes a timestamped reviewable report copy under .harbor/reports/**.
explicit --output wins over --save; do not silently create a second saved copy.
--output targeting .harbor/diary/** must be rejected.
harbor log / harbor log write still require explicit human authorization.
If evidence is insufficient, output evidence insufficient or no meaningful change window.
Do not fabricate missing decisions, risks, tests, or reasons.
non-UTF-8 reports and bad JSON reports must be skipped as unusable evidence or reported clearly.
Unusable evidence must not cause an incorrect Diary write or invented Diary Draft content.
```

Evidence sources may include:

```text
change-window snapshots
checkpoint / stale / doctor reports
git status
accepted baseline markers
other Harbor-generated evidence within the current change window
```

Evidence boundaries:

```text
harbor log draft does not read or output file content bodies.
harbor log draft does not output diff bodies.
harbor log draft does not call LLM.
```

---

## 12. Write Paths

Preferred draft-to-memory write path:

```powershell
harbor log write
harbor log write --yes
harbor log write --from-latest-draft
harbor log write --from-draft .harbor/reports/log-draft.md --yes
```

Rules:

```text
harbor log write is the controlled source-of-truth write path for draft-based workflow.
Use it only after review and explicit authorization.
Do not run it automatically.
Do not claim success unless the write was actually executed and observed.
```

Legacy direct write path remains available when the user explicitly wants a manual message-based write:

```powershell
harbor log -m "<message>" --type <type> --importance <importance> --visibility <visibility>
```

---

## 13. Diary Entry Types

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

## 14. Importance Levels

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

## 15. Visibility Levels

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

## 16. Diary Draft Format

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

## 17. JSONL Recommended Structure

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

## 18. Required Fields

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

`harbor log draft` may use checkpoint / accept / finish snapshots, reports, changed files, and validation results as evidence inputs.

Even after baseline acceptance, agents should still be able to generate Diary Drafts for review without writing `.harbor/diary/**`.

---

## 19. Contract Impact in Diary

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

## 20. Breaking Change in Diary

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

## 21. Diary and DDT

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

## 22. Diary and Runtime Safety

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

## 23. Diary and Generated Context

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

## 24. Diary and Workspace Migration

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

## 25. Diary and Release Notes

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

## 26. Diary Quality Standard

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

## 27. Privacy and Secret Safety

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

## 28. Tool Honesty

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

## 29. Final Response Requirements

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

## 30. Common Mistakes

Avoid:

```text
writing Diary for every tiny edit
skipping Diary for important contract changes
using Diary as changelog only
using changelog as Diary
using commit message as Diary
claiming Diary was written when only a draft was generated
writing `.harbor/diary/**` through harbor log draft
using `--output .harbor/diary/**` for draft generation
inventing decision content when evidence is insufficient
letting broken or non-UTF-8 reports become false evidence
including secrets or private data
inventing PR links, commit hashes, or test results
omitting risks
omitting reason
hiding breaking changes
manually appending malformed JSONL
```

---

## 31. Final Principle

When a future human or AI agent asks:

```text
Why was this changed?
```

Diary should provide the answer.

If the change matters and the reason would otherwise be lost, create a Diary Draft.

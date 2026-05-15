# Harbor-spec v1.4.5 — Workflow UX & Preview Productization

状态：规划中  
发布类型：Workflow UX / Advisory Reconciliation / Performance Baseline / Preview Productization

## Summary

- `v1.4.5` 建立在 `v1.4.4` 已完成的 TypeScript Verification Preview 基础之上。
- 本版本不继续横向扩张治理能力边界，而是转向产品成熟度收口。
- 当前版本定位聚焦四项：治理遗留项收口、日常工作流即时反馈增强、运行性能基线建立、Preview 能力产品化交付。

## Positioning

- 治理遗留项收口
- 日常工作流即时反馈增强
- 运行性能基线建立
- Preview 能力产品化交付

## Non-Goals

- 不做 JavaScript first-class governance
- 不做 TSX / JSX / `.d.ts` 扩张
- 不把 TS DDT Preview 升级为正式 gate
- 不把 TS Semantic Audit Preview 升级为正式 gate
- 不做 Jest / Vitest AST inference
- 不做 coverage proof
- 不做自动 test-to-target binding
- 不做大规模性能架构重构
- 不在本版本完成真实外部项目 pilot

## Implementation Order

- `Task Group B` | DDT Advisory 存量收口
- `Task Group C` | Progress Feedback Framework
- `Task Group D` | Performance Baseline Report
- `Task Group A` | Preview 使用体验产品化

## References

- `docs/《Harbor-spec v1.4.5｜Workflow UX & Preview Productization 定稿版》.md`
- `README.md`
- `README.en.md`

---

# Harbor-spec v1.4.4 — TypeScript Verification Preview

状态：正式版  
发布类型：TypeScript Verification Preview / DDT Binding Preview / Semantic Audit Foundation

## Summary

- `v1.4.4` 建立在 `v1.4.3` 已完成的 TypeScript contract source 与 public boundary governance 基础之上。
- 本版本首次把 TypeScript 纳入 verification preview，正式主题为 `TypeScript Verification Preview: DDT Binding Preview & Semantic Audit Foundation`。
- 本版本完成 preview governance、文档、规则、ADR、Diary、accepted baseline 与 generated context 的正式收口，不把 preview 提前升级为正式 gate。

## Added

- `VerificationBinding` foundation：
  - language-neutral verification binding 抽象
  - `target_id` 作为跨语言主锚点
  - `func_id` 继续保留给 Python 兼容路径
- sidecar-driven TypeScript DDT Binding Preview：
  - repo-local sidecar source of truth
  - 显式 `target_id -> test_asset` 绑定
  - MVP strategy 冻结为 `preview_strict` / `preview_reference`
- preview explainability 接入：
  - `harbor check`
  - `harbor checkpoint --ci --format json`
  - `harbor next`
- semantic audit language-neutral foundation：
  - `AuditSubject`
  - `AuditPromptContext`
  - `AuditEligibility`
- TypeScript semantic audit advisory preview：
  - 仅对具备行为型契约证据的函数型 target 开放
  - `interface` / `type` / `Zod` 只作为辅助 evidence

## Default Behavior

- preview 默认 `enabled=false`
- `enabled=false` 时不扫描 sidecar、不生成 preview findings、不产生额外副作用
- preview findings 保持 advisory-only / non-blocking
- preview 结果不写 baseline truth、不自动修代码、不自动 accept
- `harbor init` / guidance 只能显式提示 preview 能力，不静默启用
- TypeScript semantic audit preview 是 opt-in / provider-dependent preview
- 自动化测试与 release acceptance 使用 mock / deterministic provider，不依赖真实 LLM 可用性

## Non-Goals

- 正式 TypeScript DDT gate
- 正式 TypeScript semantic audit gate
- Jest / Vitest AST inference
- coverage proof
- 自动 test-to-target 推断
- 默认 blocking gate 扩张

## Compatibility

- Python DDT 零回归保持硬约束。
- Python semantic audit 外部语义保持不变。
- 既有 category / exit code 语义不突变。
- JSON 输出保持 additive compatibility。
- Windows full-governance 与 Ubuntu matrix 继续作为正式验收维度。

## Validation Status

- `pytest`: `738 passed`
- `harbor log write --from-draft .harbor/reports/v1.4.4-phase-4a-governance-diary-draft.md --yes`: `pass`
- `harbor accept`: `pass`
- `harbor checkpoint --ci --format json --advice basic`: `pass`
- `harbor verify-generated --changed --ci --format json`: `pass`
- `harbor verify-generated --all --ci --format json`: `pass`
- `harbor stale --ci --format json`: `pass`
- `harbor doctor --ci --format json`: `pass`
- accepted baseline updated at `.harbor/baseline/accepted-checkpoint.json`
- post-accept checkpoint closure:
  - `drift=0`
  - `modified=0`
  - `missing=0`
  - `untracked=0`
  - `possible_contract_impact=0`
  - `ci_failures=0`
- generated context closure completed via `harbor finish --sync-context -> harbor project structure --write -> harbor docs --all --write -> harbor module seal --all --write`
- release acceptance for preview semantic audit remains mock / deterministic-provider based and does not depend on a real LLM
- Python DDT advisory reconciliation completed:
  - `5` strict Python test bindings / `2` unique `func_id`
  - category: `ddt_version_baseline_missing`
  - adjudication: `ACCEPTED_BACKLOG`, not a `v1.4.4` release blocker
  - reason: accepted checkpoint baseline exists, but Harbor does not yet persist a repo-owned `l3_version` baseline source for reviewed Python DDT bindings
  - report: `.harbor/reports/python-ddt-advisory-reconciliation.md`

---

# Harbor-spec v1.4.3 — TypeScript Public Boundary Resolution & Project Presets

状态：正式版
发布类型：TypeScript Public Boundary Resolution / Project Presets / Explainability Upgrade

## Summary

- `v1.4.3` 建立在 `v1.4.2` 已完成的 TypeScript persistence、`contract_hash` 与 accepted baseline comparison-compatible 基础之上。
- 新增 project-level `Public Boundary Evidence` 模型，支持 direct export、re-export、package export 与 configured entrypoint 等证据。
- 新增最小 public boundary resolver，支持 re-export chain、package exports、常见 source mapping 与最小 `tsconfig paths`。
- 新增 `legacy_exported`、`package_public`、`custom_entrypoints` 三类 project preset，并保持默认兼容策略不变。
- `harbor init` 新增 TypeScript governance guidance 与显式 opt-in 配置写入能力。
- `harbor next` 新增 preset-aware boundary explanation，解释 boundary state / confidence / evidence / preset 的关系。

## Added

- Additive public-boundary metadata:
  - `public_boundary_state`
  - `public_boundary_confidence`
  - `public_boundary_evidence_kinds`
  - `public_boundary_evidence_items`
  - `public_boundary_reason`
  - `boundary_preset_mode`
- Public Boundary Evidence kinds:
  - `direct_export`
  - `default_export`
  - `named_re_export`
  - `star_re_export`
  - `package_export`
  - `configured_entrypoint`
  - `declaration_surface_preview` (future preview placeholder only)
- Minimal boundary resolution:
  - package root detection
  - relative path resolution
  - `.ts` priority with `index.ts` fallback
  - minimal `tsconfig baseUrl/paths`
  - normalized package exports and common source mapping
- `harbor init` TypeScript onboarding:
  - detect `package.json`, `tsconfig.json`, `src/index.ts`, `package.json exports`
  - detect workspace / monorepo markers
  - explicit init flags for TypeScript governance config write
- `harbor next` boundary explanation:
  - additive `boundary_explanation` in JSON output
  - text explanation for preset / state / confidence / evidence

## Changed

- Public Boundary Evidence is modeled separately from Contract Source:
  - re-export / package exports / configured entrypoints do not enter `contract_source_kinds`
  - boundary evidence does not enter `contract_hash` or `body_hash`
  - boundary metadata changes do not alter baseline diff / comparison semantics
- Default compatibility remains unchanged:
  - default preset stays `legacy_exported`
  - default `contract_required_strategy` stays `legacy_exported`
  - non-interactive `harbor init` does not silently enable TypeScript governance
- `harbor next` remains read-only while exposing richer boundary explainability.
- Generated context closure continues to use `harbor finish --sync-context -> harbor stale --ci --format json -> harbor doctor --ci --format json`.

## Not Supported Yet

- JavaScript first-class governance
- `.js/.jsx/.tsx/.d.ts` default scanning
- TypeScript semantic audit
- TypeScript DDT
- full TypeScript compiler / full module graph
- full npm package resolution / bundler alias resolution
- framework-specific governance / validation
- full Zod schema semantics / schema-to-type consistency audit
- automatic blocking-gate expansion from `interface/type`, Zod, or boundary evidence

## Compatibility

- Python behavior remains zero-regression-compatible.
- `v1.4.2` comparison-compatible baseline semantics remain unchanged.
- Existing JSON output remains additive-compatible.
- Existing category semantics remain unchanged by boundary metadata.
- Windows full-governance remains a formal release acceptance dimension.

## Validation

- `pytest`: `pass`
- `harbor accept`: `pass`
- `harbor checkpoint --ci --format json --advice basic`: `pass`
- `harbor verify-generated --changed --ci --format json`: `pass`
- `harbor verify-generated --all --ci --format json`: `pass`
- `harbor stale --ci --format json`: `pass`
- `harbor doctor --ci --format json`: `pass`
- accepted baseline updated at `.harbor/baseline/accepted-checkpoint.json`
- generated context closure completed via `harbor finish --sync-context -> harbor project structure --write -> harbor docs --all --write -> harbor module seal --all --write`
- non-blocking follow-up remains:
  - `ddt_advisory: 5`
  - classification: existing post-release governance backlog, not a release blocker for `v1.4.3`

---

# Harbor-spec v1.4.2.2 — Windows JSON Stdout Compatibility Closure

状态：正式版
发布类型：Maintenance Patch / Windows JSON Stdout Compatibility Fix

## Summary

- 完成 Windows 主机编码兼容性修复收口，覆盖 cp936 与 cp1252 等非 UTF-8 stdout 主机场景。
- 纯 JSON CLI 输出点统一收口到 `_emit_json_stdout()`，避免各命令各自分叉处理编码与回退策略。
- 当 stdout 编码可以严格表示 payload 时，保持 localized JSON 输出。
- 当 stdout 编码无法严格表示本地化 payload 时，自动回退到 ASCII-safe JSON，同时保持 JSON 语义与稳定键不变。
- `main()` 的 contract/docstring、accepted baseline 与 generated context 已同步对齐。

## Fixed

- 修复 Windows 非 UTF-8 主机编码下纯 JSON stdout 可能因本地化文本不可编码而退化为异常、乱码或不稳定输出的问题。
- 修复不同 JSON CLI 输出点在编码处理策略上不一致的问题，改为统一入口处理。
- 修复 cp1252 runner closure 的最后一处发布阻断项，并完成 baseline acceptance 闭环。

## Compatibility

- 保持 JSON payload 语义不变；变化仅限于无法安全编码本地化文本时的 ASCII-safe 表达方式。
- 保持 cp936 主机场景可继续输出 localized JSON。
- 保持 `checkpoint --ci --format json`、`stale --ci --format json`、`doctor --ci --format json` 的单对象 JSON 合同不变。
- 不扩大 JSON 输出能力边界，不新增 `--output`，不引入新的写文件行为。

## Validation

- `python -m harbor.cli.main accept`: `pass`
- `python -m harbor.cli.main checkpoint --ci --format json`: `pass`
- `python -m harbor.cli.main stale --ci --format json`: `pass`
- `python -m harbor.cli.main doctor --ci --format json`: `pass`
- GitHub Actions CI run `#96`: `pass`
- Ubuntu Python matrix: `3.9 / 3.10 / 3.11 = pass`
- Windows full-governance: `pass`

---

# Harbor-spec v1.4.2 — TypeScript Contract Source Strengthening

状态：发布就绪
发布类型：TypeScript Contract Source Strengthening

## Added

- TypeScript subject generalized persistence through `IndexBuilder`, SQLite `entries`, and runtime cache snapshot export.
- Additive TypeScript identity metadata in persistence and checkpoint JSON:
  - `target_id`
  - `func_id` / `legacy_func_id`
  - `language`
  - `symbol_kind`
  - `qualified_name`
  - `lineno` / `end_lineno`
  - `visibility`
- Advisory-first exported `interface` / `type` discovery.
- Shallow Zod source recognition for `z.object(...)` and `z.enum(...)`.
- `export default function` / `export default class` discovery as public surface evidence.
- TypeScript `contract_hash` based on normalized contract source bundle hash.
- Additive checkpoint / `harbor next` JSON metadata:
  - `export_mode`
  - `public_surface_evidence`
  - `data_contract_kind`
  - `schema_source_kind`
  - `contract_source_kinds`
  - `contract_source_fingerprints`
  - `source_confidence_summary`

## Changed

- `checkpoint --ci` continues to use `.harbor/baseline/accepted-checkpoint.json` as the accepted baseline source of truth.
- runtime cache remains local acceleration / compatibility only and does not become CI truth.
- TypeScript contract presence now treats exported `interface` / `type` and supported shallow Zod schemas as contract-like source evidence without turning them into new blocking categories.
- `harbor next` now preserves additive TypeScript metadata so advisory-first data contracts, shallow Zod evidence, low-confidence docs, and default export public surface signals stay explainable downstream.
- generated context closure for v1.4.2 is explicitly `harbor finish --sync-context -> harbor stale --ci --format json -> harbor doctor --ci --format json`.
- Windows full-governance remains a formal release gate, not a best-effort compatibility check.

## Fixed

- Windows redirected CLI stdout/stderr now default to UTF-8 unless explicitly overridden, restoring cross-stream encoding parity under redirected execution.
- generated context clean parity and committed views alignment are restored for the v1.4.2 release closure path.

## Not Supported Yet

- re-export graph
- `.d.ts` scanning
- `package exports`
- `tsconfig` path alias resolution
- framework presets
- TypeScript DDT
- TypeScript semantic audit
- JavaScript first-class governance
- full Zod schema semantics / schema-to-type consistency audit
- automatic blocking gate expansion for `interface/type`, Zod, or default export evidence

## Compatibility

- Python behavior remains zero-regression-compatible.
- Existing baseline artifact fields remain stable:
  - `baseline_source`
  - `baseline_path`
  - `baseline_found`
  - `accepted_baseline_missing`
  - `accepted_baseline_invalid`
- Existing `func_id` consumers remain supported.
- `v1.4.1` Log Draft / Controlled Write workflow remains unchanged.

## Validation

- `pytest`: `652 passed`
- `harbor checkpoint --ci --format json`: `pass`
- `harbor stale --ci --format json`: `pass`
- `harbor doctor --ci --format json`: `pass`
- Ubuntu Python matrix CI: `pass`
- Windows full-governance CI: `pass`

---

# Harbor-spec v1.4.1 — Log Draft + Controlled Write Workflow MVP

状态：正式版  
发布类型：Log Draft + Controlled Write Workflow MVP

## Added

- Change Window Snapshot MVP for `checkpoint` / `finish` / `accept`.
- `harbor log draft` command.
- Markdown / JSON Diary Draft output.
- Latest draft runtime cache:
  - `.harbor/state/log/latest-draft.md`
  - `.harbor/state/log/latest-draft.json`
- `harbor log draft --save`.
- `harbor log write`.
- `harbor log write --yes`.
- `harbor log write --from-latest-draft`.
- `harbor log write --from-draft`.
- `last_log_marker`.
- `--since-last-accept` / `--since-last-log` / `--from-report` / `--output` support.
- Runtime diagnostics for snapshot write failure.

## Changed

- Agent rules now distinguish Diary Draft from Written Diary Entry.
- Rules now allow AI agents to generate drafts and prepare report copies, but not write Diary entries automatically.
- Log workflow is documented as `Evidence -> Draft Cache / Save -> Controlled Write`.
- `harbor log draft` boundary is clarified as marker-first -> accept-fallback -> recent-fallback.
- `harbor log draft` now applies a draft-worthiness gate in default mode.
- reports alone are supplementary evidence in default mode and no longer trigger a writable draft by themselves.
- diary-only changes under `.harbor/diary/**` no longer trigger a writable draft by themselves.
- insufficient-evidence draft runs now return a no-op result, omit write hints, and do not refresh latest draft cache.
- explicit `harbor log draft --from-report <path>` still allows report-led draft generation.
- `harbor log draft` no longer advances `last_log_marker`; only successful `harbor log write` may update it after a Written Diary Entry lands in `.harbor/diary/YYYY-MM.jsonl`.
- `--since-last-log` now consumes the actual `last_log_marker` write schema (`last_log_at` first, with legacy aliases still accepted).
- CLI user-facing log prompts/errors follow Harbor i18n; JSON schema keys remain stable English identifiers.
- Log draft skips invalid / non-UTF-8 report evidence safely.
- TypeScript boundaries remain unchanged from v1.4.0 in v1.4.1.

## Safety

- `harbor log draft` generates a reviewable draft only; it does not write a Written Diary Entry.
- `harbor log draft` does not write `.harbor/diary/**`.
- `harbor log draft` does not update `.harbor/state/log/last_log_marker.json`.
- `harbor log write` writes Diary only through the explicit write path.
- `harbor log write --yes` is explicit authorization.
- non-interactive write without `--yes` is rejected.
- draft sources are allowlisted.
- `.harbor/diary/**`, `.env`, `.env.*`, `secrets/**`, and repo-external paths are rejected as draft sources.
- `last_log_marker` is runtime state that points to the last formally written Diary node; it is not source-of-truth memory.
- `harbor log draft --output` may write to `.harbor/reports/**`.
- `harbor log draft --save` writes a reviewable report copy only.
- `harbor log draft` does not output file content or diff body.
- `--output` to `.harbor/diary/**` is rejected.
- `harbor log draft` does not call LLM in v1.4.1.
- `harbor log write` does not introduce LLM usage in v1.4.1.
- LLM-assisted draft/write is future work only and must be explicit opt-in.
- Any future LLM-assisted draft/write must not send secrets, credentials, private data, `.env` contents, file bodies, or diff bodies to an LLM.

## Validation

- `pytest`: `554 passed`
- `harbor checkpoint --ci --format json`: `pass`
- `harbor stale --ci --format json`: `pass`
- `harbor doctor --ci --format json`: `pass`

---

# Harbor-spec v1.4.0 — TypeScript Contract Governance MVP

状态：正式版  
发布类型：Core Neutralization + TypeScript Contract Governance MVP

## Added

- Language-neutral core contract model: `ContractSubject` / `ContractSource` / `LanguageAdapter`
- `AdapterRegistry` for language-aware discovery and parsing routing
- TypeScriptAdapter MVP (`.ts` scope, exported symbol discovery, JSDoc/TSDoc presence extraction)
- TypeScript checkpoint MVP categories:
  - `contract_gap`
  - `skipped_no_contract`
  - `unsupported_syntax_advisory`
- TypeScript `harbor next` deterministic guidance for MVP categories
- JSON additive identity fields: `target_id` / `language` / `symbol_kind` / `adapter`

## Changed

- `IndexBuilder` / `SyncEngine` route through `AdapterRegistry` while preserving Python behavior.
- `checkpoint --ci --format json` keeps `func_id` compatibility and adds additive target identity fields.
- `harbor next --from <checkpoint.json>` is language-aware for TypeScript MVP categories.

## Not Supported Yet

- JavaScript first-class support
- TypeScript semantic audit
- TypeScript DDT
- TSX/JS/JSX/`.d.ts` default scanning
- Zod schema governance
- framework presets (Next.js / Express / React)
- interface/type blocking gate
- TypeScript Compiler API / tree-sitter backend

## Compatibility

- Python behavior remains zero-regression-compatible.
- Existing `func_id` consumers remain supported.
- TypeScript support is opt-in (`enabled: true`) and `.ts`-only by default.

## Validation

- `pytest`: `502 passed`
- `harbor checkpoint --ci --format json`: `pass`
- `harbor stale --ci --format json`: `pass`
- `harbor doctor --ci --format json`: `pass`（工作区变更 `WARN` advisory）

---

# Harbor-spec v1.3.1 — Repair Guidance & AI IDE Feedback Loop

状态：正式版  
发布类型：保守修复建议层 / AI IDE 反馈回路增强

v1.3.1 新增确定性 Repair Guidance 层（不使用 LLM）并引入 `harbor next` 只读解释命令。

关键原则：

```text
- guidance is deterministic
- no LLM/provider call is required for advice=basic
- guidance is optional additive field
- guidance does not change CI gate semantics
- guidance does not write files
- semantic drift guidance is conservative and requires adjudication
- harbor next is read-only and never runs accept/log/lock automatically
```

CLI / 配置补充：

```text
- checkpoint/stale/doctor 新增 --advice off|basic
- .harbor/config/harbor.yaml 新增 advice.mode / include_in_ci_json / include_in_text
- HARBOR_ADVICE_MODE 支持环境变量覆盖
- harbor next --from <report.json> --format text|json --advice off|basic --max-items N
```

JSON 合同补充：

```text
- ci_failures/advisory item 可选 guidance 字段（可被 --advice off 关闭）
- checkpoint/stale/doctor --format json stdout 仍为单一 JSON object
- harbor next 输出:
  command=next
  status=ok
  writes_files=false
  llm_used=false
  item 内固定包含 blocking 字段
```

---

# Harbor-spec v1.3.0 — Canonical Workspace 与 Agentic Context Governance

状态：正式版  
发布类型：重大工作流 / 工作区 / AI Agent 集成更新

Harbor-spec v1.3.0 是 Harbor-spec 从“契约 / 漂移检测工具”进一步升级为 **面向 AI Coding / Agentic Coding 的上下文治理引擎** 的关键版本。

本版本正式确立 `.harbor/` 作为 Harbor 的 canonical workspace，统一生成上下文视图、模块胶囊、决策记忆、运行时安全规则、AI 工具入口规则与 skills 工作流。

本版本的核心原则是：

```text
AI 可以快速写代码，但契约、测试、生成上下文、决策记忆和安全边界不能漂移。
```

---

## 1. 发布亮点

### 1.0 P0/P1/P3 契约缺失闭环（2026-05-10）

Added:

```text
Contract presence evaluation before semantic audit
CONTRACT_GAP / SKIPPED_NO_CONTRACT / CONTRACT_PARSE_ERROR
ddt_version_baseline_missing advisory
checkpoint CI duplicate failure dedupe
```

Changed:

```text
Missing contract is no longer reported as POSSIBLE_SEMANTIC_DRIFT
LLM semantic audit is skipped when no comparable contract exists
checkpoint --ci separates blocking failures from advisory governance signals
CI failure dedupe now normalizes paths before comparing targets
```

Fixed:

```text
No docstring provided no longer becomes possible semantic drift
Duplicate confirmed_contract_impact + contract_changed failures for the same target are removed
```

Migration Notes:

```text
strict/public Python targets should add Harbor contract docstrings or equivalent contract sources
users should review ddt_version_baseline_missing before accept
downstream parsers of checkpoint JSON should handle new categories
```

---

### 1.1 Canonical `.harbor/` Workspace

Harbor-spec v1.3.0 正式使用 `.harbor/` 作为 canonical workspace。

标准结构：

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

    l2/
      _meta.json
      <module>/
        README.md

    modules/
      <module>/
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

核心边界：

```text
.harbor/rules/**
  静态 Harbor 规则文档。

.harbor/views/**
  canonical generated context views，即生成上下文视图。

.harbor/diary/**
  canonical decision memory，即决策记忆。

.harbor/cache/**
.harbor/state/**
  运行时产物，不是 source of truth。

.agents/skills/**
  外部 AI 工具 workflow export，不是 source of truth。
```

### 1.1.1 Setup Wizard (`harbor init`)

`harbor init` 在 v1.3.0 升级为交互式 Setup Wizard：

```text
Step 1: 选择工作语言（中文 / English）
Step 2: 选择接入类型（新项目 / 老项目）
Step 3: 探测并确认扫描范围
Step 4: 可选生成最小治理入口
Step 5: 明确 project-rules 只做引导，不自动生成
Step 6: 可选生成详细治理文档
Step 7: 输出 AI IDE 接入说明（不自动写 IDE 专有文件）
Step 8: 可选配置 LLM（仅语义审计可选能力）
Step 9: 可选更新 .gitignore（runtime/secrets managed block）
Step 10: 按新项目/老项目给出差异化 next steps
```

关键边界：

```text
- 生成路径统一在 .harbor/rules/**（不写 docs/harbor/**）
- starter files 包含 AGENTS.md / role-rules / project-rules-guide / policy / safety
- 不自动生成 .harbor/rules/project-rules.md
- 不自动执行 harbor checkpoint / harbor accept / harbor lock / harbor log
- 新项目不引导“立刻 checkpoint/accept”，但会在 next steps 中保留完整工作流位置
- .env 仅追加缺失 HARBOR_* key，不覆盖已有 key（即使 --force）
- --dry-run 在交互模式只预览不落盘；非 TTY 且参数不完整时使用安全默认输出计划
- 自动化/CI 建议为 --dry-run 提供完整参数，避免交互阻塞
```

---

### 1.2 Workflow Facade

v1.3.0 将 AI Coding 的默认 Harbor 工作流统一为：

```powershell
harbor start
harbor checkpoint
harbor finish --sync-context
harbor stale
harbor doctor
```

推荐理解：

```text
start
  开始一次 Harbor 管理下的 AI coding 任务。

checkpoint
  开发过程中检查契约 / 实现 / DDT / 漂移状态。

finish --sync-context
  收尾并同步 changed L2 README 与 Module Capsule。

stale
  检查生成上下文是否过时。

doctor
  检查 Harbor workspace 整体健康状态。
```

以下命令不属于默认任务流，必须由用户显式请求后再运行：

```powershell
harbor log
harbor accept
harbor lock
harbor module promote-skill <module>
```

---

### 1.3 Generated Context Views

Harbor 生成上下文统一位于：

```text
.harbor/views/**
```

包括：

```text
.harbor/views/project-structure.md
.harbor/views/l2/<module>/README.md
.harbor/views/l2/_meta.json
.harbor/views/modules/<module>/module-card.md
.harbor/views/modules/<module>/review-checklist.md
.harbor/views/modules/<module>/debug-playbook.md
```

生成上下文用于帮助人类与 AI agent 快速理解项目，但它不是 source of truth。

如果 `.harbor/views/**` 与源码、测试、schema、policy 或 diary 冲突，应视为 generated context stale，并通过 Harbor 命令重新生成。

---

### 1.4 Module Capsule

Module Capsule 成为 v1.3.0 的一等生成上下文能力。

每个模块胶囊包含：

```text
module-card.md
review-checklist.md
debug-playbook.md
```

canonical 路径：

```text
.harbor/views/modules/<module>/
```

相关命令：

```powershell
harbor module inspect <module>
harbor module seal <module> --write
harbor module seal --changed --write
harbor module seal --all --write
harbor module stale <module>
harbor module promote-skill <module>
```

其中：

```powershell
harbor module promote-skill <module>
```

会将模块上下文导出为 `.agents/skills/**` 下的外部 AI 工具 skill，因此必须由用户显式请求后再运行。

---

### 1.5 Workspace Inspect 与 Migration Dry-run

v1.3.0 新增只读 workspace 诊断命令：

```powershell
harbor workspace inspect
harbor workspace inspect --format json
```

用于查看当前 Harbor workspace 状态，包括 canonical paths、generated views、policy files、Git tracking、advisory summary 等。

同时新增只读迁移规划命令：

```powershell
harbor workspace migrate --dry-run
harbor workspace migrate --dry-run --format json
```

重要边界：

```text
harbor workspace migrate --dry-run 是只读诊断 / 规划命令。
它不能写文件、移动文件、删除文件或修改工作区。
```

v1.3.0 不实现：

```powershell
harbor workspace migrate --write
```

如果执行未带 `--dry-run` 的 migrate，应返回非零退出并提示当前版本只支持 dry-run。

---

### 1.6 Stale 与 Doctor

v1.3.0 正式稳定顶层 advisory checks：

```powershell
harbor stale
harbor stale --format json
harbor stale --ci
harbor stale --ci --format json

harbor doctor
harbor doctor --format json
harbor doctor --ci
harbor doctor --ci --format json

harbor checkpoint --ci
harbor checkpoint --ci --format json
```

含义：

```text
harbor stale
  关注 generated context freshness，即生成上下文是否过时。

harbor doctor
  关注 Harbor workspace health，即 Harbor 工作区整体健康状态。
```

二者均保持 advisory + read-only 语义。

补充（CI Mode MVP）：

```text
--ci 仅在显式启用时改变 exit code 语义：
  0 = pass
  1 = fail
  2 = 参数错误（argparse）

stale --ci
  仅对 canonical l2_readme / module_capsule 的 stale|unknown 执行阻断。
  l2_readme_export 与 legacy/export 相关项保留 advisory。

doctor --ci
  默认仅对 DoctorCheckResult.status == FAIL 执行阻断。
  WARN / SKIP 保持 advisory（不默认阻断）。

checkpoint --ci
  作为 strict baseline gate，默认阻断：
  - DDT failure
  - missing / untracked
  - drift（Body changed, Contract static）
  - contract_changed / body+contract_changed（baseline 未 accept）
  - confirmed_contract_impact
  possible_contract_impact 保持 advisory，不直接阻断。

--format json + --ci
  stdout 始终输出单一 JSON 对象（pass/fail 都不混入人类文本）。

CI Mode 是 gate/check/report，不是 auto-fix / auto-refresh / auto-migrate。
checkpoint --ci 为只读 gate：不写文件，不自动刷新，不自动 accept。
```

---

### 1.7 Diary Canonicalization

Diary 决策记忆的 canonical 写入路径变为：

```text
.harbor/diary/YYYY-MM.jsonl
```

Diary 用于记录重要决策为什么发生。

它不是 changelog 的替代品。

它不是 commit message 的替代品。

`harbor log` 会写入 Diary，因此必须由用户显式请求后再执行。

---

### 1.8 AI Tool Integration Pack

v1.3.0 完成 AI Coding 工具集成文件体系收口。

核心文件：

```text
AGENTS.md
  跨工具轻量入口。

.harbor/rules/agent-policy.md
  Harbor 总政策说明。

.harbor/rules/project-rules-guide.md
  Project Rules 生成与维护指南。

.harbor/rules/project-rules.md
  当前项目的项目专属规则。

.harbor/rules/contract-rules.md
  Contract 治理规则。

.harbor/rules/ddt-rules.md
  DDT 规则。

.harbor/rules/diary-rules.md
  决策记忆规则。

.harbor/rules/runtime-safety.md
  运行时安全规则。

.harbor/rules/glossary.md
  Harbor 术语表。

.agents/skills/**
  按需加载的 AI workflow skills。

Tool role-rules
  TRAE / Cursor / Claude Code / Codex 等工具的轻量适配层。
```

官方 skills：

```text
harbor-contract-change
harbor-code-review
harbor-ddt-diary
harbor-safety-preflight
harbor-context-refresh
harbor-workspace-migration-plan
```

---

### 1.9 Source of Truth Priority Clarification (P0-2)

v1.3.0 文档规则补充明确：

- Source of Truth Priority 与 Instruction Hierarchy 是两个不同层级：
  - Instruction Hierarchy 处理规则/指令冲突；
  - Source of Truth Priority 处理 contract/tests/implementation/generated/export 的事实冲突。
- generated context integrity metadata 是 advisory integrity signal，不是 truth override。
- `.harbor/views/**` 是 canonical generated context，但 generated views 不是 source of truth。
- `Canonical wins` 仅用于 canonical artifact 与 legacy/export copy 冲突，不用于 generated views 覆盖 contracts、DDT/tests 或 implementation。
- 冲突必须按 `semantic drift` / `contract gap` 标记并通过测试/DDT/人工确认裁决，不做静默自动裁决。

### 1.10 Contract Impact Classifier MVP (P0-3)

v1.3.0 新增 Contract Impact Classifier MVP（checkpoint advisory）：

- 在 `harbor checkpoint` 输出中新增 Contract Impact 分类摘要。
- 分类级别：`no_contract_impact` / `possible_contract_impact` / `confirmed_contract_impact` / `unknown`。
- `confirmed_contract_impact` 表示确认存在 contract surface 变化，不表示 bug 或 breaking change。
- `possible_contract_impact` 作为默认保守分类；对 public CLI、JSON output、write target、generated view format、source-of-truth rules 相关变化不会轻易归入 no impact。
- classifier 语义为 advisory / conservative / explainable，不替代人工评审、DDT 或语义审计。

---

## 2. 新增能力

### 2.1 Workflow Facade Commands

新增或正式化：

```powershell
harbor start
harbor checkpoint
harbor finish
harbor finish --sync-context
harbor stale
harbor doctor
```

其中：

```powershell
harbor finish --sync-context
```

用于在任务收尾时显式同步 changed L2 README 与 Module Capsule。

补充说明：

* `finish --sync-context` 保持 changed-scope sync，不自动升级为全量刷新。
* changed scope 解析与 `docs --changed` / `module seal --changed` / `stale --changed` / `stale --ci` 保持一致。
* 同步完成后会执行同 scope 的 stale 自检；若仍存在 residual stale，则输出具体 module/view 与确定性修复指引。
* 当变更命中 generator / integrity 关键文件时，只输出 broader refresh advisory，不自动执行 `--all`。

`harbor accept` 仍保留为 `harbor lock` 的语义化别名，但不属于默认 facade 工作流，只有在用户明确要接受新基线时才运行。

---

### 2.2 L2 README Refresh Modes

新增或正式化：

```powershell
harbor docs --module <module> --write
harbor docs --changed --write
harbor docs --all --write
```

canonical L2 README 路径：

```text
.harbor/views/l2/<module>/README.md
```

canonical L2 metadata 路径：

```text
.harbor/views/l2/_meta.json
```

---

### 2.3 Module Capsule Commands

新增或正式化：

```powershell
harbor module inspect <module>
harbor module seal <module> --write
harbor module seal --changed --write
harbor module seal --all --write
harbor module stale <module>
harbor module promote-skill <module>
```

canonical Module Capsule 路径：

```text
.harbor/views/modules/<module>/
```

---

### 2.4 Project Structure View

新增或正式化：

```powershell
harbor project structure
harbor project structure --write
```

canonical project structure 路径：

```text
.harbor/views/project-structure.md
```

行为：

```text
harbor project structure
  preview-only，不写文件。

harbor project structure --write
  写入 canonical project structure view。
```

---

### 2.5 Workspace Diagnostics

新增：

```powershell
harbor workspace inspect
harbor workspace inspect --format json
```

该命令用于报告 workspace canonical paths、generated views、policy files、advisory status 和 workspace layout 信息。

它是只读命令。

---

### 2.6 Workspace Migration Dry-run

新增：

```powershell
harbor workspace migrate --dry-run
harbor workspace migrate --dry-run --format json
```

该命令只生成迁移 / 清理规划，不执行迁移动作。

JSON 输出应是单个对象，并明确声明不写文件。

期望 invariant：

```json
{
  "mode": "dry_run",
  "writes_files": false
}
```

---

### 2.7 JSON Output

新增或正式化以下命令的机器可读输出：

```powershell
harbor stale --format json
harbor doctor --format json
harbor workspace inspect --format json
harbor workspace migrate --dry-run --format json
```

JSON 输出要求：

```text
- 尽量保持 deterministic。
- 路径尽量规范化。
- 除非明确需要，不泄露机器本地绝对路径。
- 输出单个 JSON object，便于 AI / CI / 脚本消费。
```

---

### 2.8 AI Rules and Skills

新增或正式化：

```text
AGENTS.md
.harbor/rules/agent-policy.md
.harbor/rules/project-rules-guide.md
.harbor/rules/project-rules.md
.harbor/rules/contract-rules.md
.harbor/rules/ddt-rules.md
.harbor/rules/diary-rules.md
.harbor/rules/runtime-safety.md
.harbor/rules/glossary.md

.agents/skills/harbor-contract-change/SKILL.md
.agents/skills/harbor-code-review/SKILL.md
.agents/skills/harbor-ddt-diary/SKILL.md
.agents/skills/harbor-safety-preflight/SKILL.md
.agents/skills/harbor-context-refresh/SKILL.md
.agents/skills/harbor-workspace-migration-plan/SKILL.md
```

---

## 3. 变更内容

### 3.1 Workspace Paths

canonical config 写入路径变更为：

```text
.harbor/config/harbor.yaml
```

canonical generated context 路径变更为：

```text
.harbor/views/project-structure.md
.harbor/views/l2/<module>/README.md
.harbor/views/l2/_meta.json
.harbor/views/modules/<module>/
```

canonical diary 写入路径变更为：

```text
.harbor/diary/YYYY-MM.jsonl
```

运行时路径：

```text
.harbor/cache/**
.harbor/state/**
```

是 runtime artifacts，不应被当作 source of truth。

---

### 3.2 Generated Context Behavior

```powershell
harbor project structure --write
```

现在写入：

```text
.harbor/views/project-structure.md
```

```powershell
harbor docs --write
```

现在写入 canonical L2 README：

```text
.harbor/views/l2/<module>/README.md
```

```powershell
harbor module seal --write
```

现在写入 canonical capsule files：

```text
.harbor/views/modules/<module>/
```

```powershell
harbor stale
```

现在评估 canonical generated views，不把 optional exports 当成 canonical storage。

canonical generated markdown views 现在统一带有 integrity frontmatter，包含：

```text
generated_by
harbor_version
view_type
module
generated_at
generation_command
stale_policy
source_paths
source_fingerprint
contract_fingerprint
generator_fingerprint
```

其中 `generated_at` 仅用于信息展示；stale 比较会忽略该字段，且在输入与生成内容不变时会复用旧值，避免每次重生成产生无意义 Git diff。

---

### 3.3 Module Capsule Behavior

`module-card.md` 保留 deterministic capsule fingerprint 语义（`view_fingerprint`/`fingerprint`），作为 module capsule stale 主判定依据。

`source_fingerprint` 属于 integrity metadata，不替代 capsule fingerprint 主语义。

```powershell
harbor module stale
```

从以下路径评估 canonical capsule freshness：

```text
.harbor/views/modules/<module>/module-card.md
```

```powershell
harbor module promote-skill
```

引用 canonical capsule 路径：

```text
.harbor/views/modules/<module>/
```

并导出到：

```text
.agents/skills/**
```

---

### 3.4 Doctor Behavior

```powershell
harbor doctor
```

现在检查更广泛的 Harbor workspace health，包括：

```text
configuration
workspace state
DDT quick checks
generated views
skill references
runtime safety
compatibility advisories
```

Doctor 保持 advisory + read-only。

---

### 3.5 Stale Behavior

```powershell
harbor stale
```

检查 canonical generated context freshness。

它应基于：

```text
.harbor/views/**
```

判断生成上下文新鲜度。

如启用 optional exports，可单独报告 export status，但 export 不应影响 canonical freshness 判断。

---

### 3.6 Diary Behavior

Diary 新写入路径：

```text
.harbor/diary/YYYY-MM.jsonl
```

Diary 读取可以在兼容场景中合并已有决策记录，但新写入必须使用：

```text
.harbor/diary/**
```

默认不自动迁移、不自动删除、不自动清理旧文件。

---

### 3.7 `.gitignore` Policy

`.harbor/` 不应整体加入 `.gitignore`。

推荐策略：

```text
track:
  .harbor/config/
  .harbor/rules/
  .harbor/views/project-structure.md
  .harbor/diary/
  selected .harbor/reports/

ignore:
  .harbor/cache/
  .harbor/state/
  .harbor/exports/
  .harbor/reports/tmp/
  .harbor/reports/local/
```

具体 tracking 策略可由项目自行调整。

---

## 4. 兼容性与迁移说明

全新的 v1.3.0 项目应从一开始就使用 `.harbor/` 作为 canonical workspace。

canonical 路径：

```text
Config:
  .harbor/config/harbor.yaml

Rule docs:
  .harbor/rules/**

Generated context:
  .harbor/views/**

Decision memory:
  .harbor/diary/YYYY-MM.jsonl

Reports:
  .harbor/reports/**

Runtime cache:
  .harbor/cache/**

Runtime state:
  .harbor/state/**

External skills:
  .agents/skills/**
```

从 pre-v1.3.0 升级的已有仓库，建议先运行：

```powershell
harbor workspace inspect
harbor workspace migrate --dry-run
```

再考虑任何人工清理。

Migration dry-run 是只读的。

它不会：

```text
copy files
move files
delete files
rewrite files
modify AGENTS.md
modify .harbor/**
modify .agents/skills/**
append diary entries
change baseline
```

v1.3.0 不实现：

```powershell
harbor workspace migrate --write
```

---

## 5. Runtime Safety

任何命令都不应静默执行高风险操作。

以下命令必须由用户显式请求：

```powershell
harbor log
harbor accept
harbor lock
harbor module promote-skill <module>
```

安全规则：

```text
- 不要用 harbor accept 隐藏 unresolved drift。
- 不要在用户未请求时运行 harbor log。
- 不要在普通 coding 或 context refresh 中自动 promote skill。
- 不要在未确认时修改 .harbor/*.yaml。
- 不要在未确认时大范围修改 .agents/skills/**。
- 不要手动编辑 .harbor/views/** 并把它当 source of truth。
```

优先使用：

```text
read-only inspection
dry-run
PowerShell -WhatIf
list files before deletion
show diff before writing
backup before rewrite
rollback plan
```

---

## 6. 发布验证快照

v1.3.0 release freeze 最终验证快照：

```text
pytest:
  280 passed

harbor workspace inspect --format json:
  single JSON object
  writes_files=false

harbor workspace migrate --dry-run --format json:
  single JSON object
  writes_files=false

harbor doctor --format json:
  single JSON object
  advisory WARN baseline accepted

harbor stale --format json:
  single JSON object
  status=pass
```

验证范围：

```text
final tests
JSON contract smoke
dry-run no-write checks
documentation consistency close-out
working tree classification
```

---

## 7. 升级检查清单

新项目建议：

```powershell
harbor init
harbor start
harbor checkpoint
harbor finish --sync-context
harbor stale
harbor doctor
```

已有项目升级到 v1.3.0：

```powershell
harbor workspace inspect
harbor workspace migrate --dry-run
harbor stale
harbor doctor
```

发布前信心检查：

```powershell
pytest
harbor checkpoint
harbor stale
harbor doctor
harbor workspace inspect --format json
harbor workspace migrate --dry-run --format json
```

不要运行以下命令，除非你明确知道自己要这么做：

```powershell
harbor accept
harbor log
harbor lock
harbor module promote-skill <module>
```

---

## 8. v1.3.0 不包含的内容

v1.3.0 不实现：

```text
automatic workspace migration write phase
automatic workspace cleanup
automatic deletion of non-canonical artifacts
automatic diary migration
automatic skill promotion
backup / rollback write migration
full migration conflict resolver
```

这些属于后续版本方向。

---

## 9. 后续方向

可能的后续迭代包括：

```text
workspace migrate --write with backup / rollback / per-item confirmation
policy-driven governance via .harbor/policy.yaml and .harbor/safety.yaml
improved semantic audit noise control
skill stale detection
skill fingerprint binding to Module Capsule
multi-tool skill export adapters
task-level context planning
```

---

# Harbor-spec v1.2.0 — The Industrial Update

## 🚀 Major Features

* Smart Configuration：`harbor init` 自动探测 Django、Node.js、Go、Java 技术栈并融合 `.gitignore` 规则。
* SQLite Backend：以 SQLite（WAL 模式）替代 JSON 索引，降低内存占用、提升启动速度并改善并发安全。
* Parallel Indexing：`harbor lock` 利用多核 CPU 并行解析与哈希，提升构建吞吐。

## ⚡ Performance

* 在超大仓库中显著降低索引内存占用。
* 通过增量数据库查询提升 `harbor status` 检测速度。

## 🛠 Improvements

* CLI 2.0：动词化命令集，包括 `lock`、`check`、`log`、`adopt`。
* DDT Integration：`harbor check` 统一语义审计与测试绑定校验。
* Windows Support：路径归一化与并行处理适配 Windows / PowerShell 工作流。

## 🔧 Migration Notes

* 缓存索引路径：`.harbor/cache/harbor.db`。
* 旧命令映射：

  * `st` → `status`
  * `ddt validate` → `check --fast`
  * `diary export` → `log --export`
  * `decorate` → `adopt`
  * `gen l2` → `docs`

## 📦 Upgrade Checklist

* 运行 `harbor init` 以生成或更新配置。
* 运行 `harbor lock` 构建基线。
* 使用 `harbor status` 验证变更检测。
* 使用 `harbor check` 或 `harbor check --fast` 验证 DDT 绑定与语义一致性。

## 📝 Acknowledgements

感谢所有贡献者在 Harbor-spec 工业级能力演进中的努力。

# Harbor Workspace Layout Phase 2C.5 Verification

Date: 2026-05-07  
Workspace: `e:/project/harbor-spec`

## Phase 2C.5 Summary
- Scope: Module Capsule Migration Verification & Compatibility Sweep (real command chain only).
- Constraint status:
  - No new feature implemented.
  - No L2 README migration to `.harbor/views/l2`.
  - No diary migration.
  - No stale/doctor new semantics change.
  - No new CLI command.
  - No deletion of legacy `docs/harbor/modules/*`.
  - No `harbor accept`.
  - No git add/commit/tag/push.
- Overall result: **No blocker found in Phase 2C behavior itself**, but current index scope prevents `harbor/core` module-capsule readiness verification (warning).

## Command Verification
- `pytest`:
  - Command: `pytest`
  - Exit code: `0`
  - Result: `215 passed in 15.27s`
  - Verdict: pass

- `module seal`:
  - Command: `harbor module seal harbor/core --write`
  - Exit code: `0`
  - Key output: `未找到模块 'harbor/core' 的已索引记录，无法生成胶囊。`
  - Canonical files check:
    - `.harbor/views/modules/harbor/core/module-card.md`: not generated
    - `.harbor/views/modules/harbor/core/review-checklist.md`: not generated
    - `.harbor/views/modules/harbor/core/debug-playbook.md`: not generated
  - Docs export check:
    - `docs/harbor/modules/harbor/core/*`: not generated
  - Verdict: warning (precondition not met: module not indexed)

- `module stale`:
  - Command: `harbor module stale harbor/core`
  - Exit code: `0`
  - Key output: `原因: no indexed records found for module`
  - Verdict: warning (cannot validate canonical fingerprint path in runtime due missing indexed module)

- `promote-skill`:
  - Command: `harbor module promote-skill harbor/core`
  - Exit code: `0`
  - Key output:
    - `未找到模块 harbor/core 的已索引记录。`
    - `可执行 harbor module inspect harbor/core 查看详情。`
  - Generated skill file check: `.agents/skills/harbor-debug-harbor-core/SKILL.md` not generated
  - Verdict: warning (readiness gate blocked by missing index)

- `doctor`:
  - Command: `harbor doctor`
  - Exit code: `0`
  - Key output summary:
    - `配置 / 索引: PASS (Indexed records available: 1)`
    - `工作区状态: WARN`
    - `DDT 快速检查: PASS`
    - `派生视图: WARN`
    - `Skill 引用: SKIP (.agents/skills not found.)`
  - Verdict: pass (command behavior normal)

- `doctor json`:
  - Command: `harbor doctor --format json`
  - Exit code: `0`
  - JSON format check:
    - stdout is a single JSON object: pass
    - top-level keys include `command/scope/status/checks/summary`: pass
    - no legacy `docs/harbor/modules` primary-path signal observed in JSON payload: pass
  - Verdict: pass

- `finish --sync-context`:
  - Command: `harbor finish --sync-context`
  - Exit code: `0`
  - Key output summary:
    - Changed module detected: `tests/fixtures_sqlite`
    - L2 README updated: `tests/fixtures_sqlite/README.md`
    - Module Capsule sync step executed, but no capsule generated for this module (no indexed module records)
  - Behavior checks:
    - No evidence of L2 migration to `.harbor/views/l2`: pass
    - No write to workspace-external paths: pass
    - No write to `docs/harbor/modules` observed under export-disabled config: pass
  - Verdict: pass with warning (module capsule readiness still constrained by index scope)

- `git tracking`:
  - Commands and results:
    - `git check-ignore .harbor/views/modules/harbor/core/module-card.md` -> exit `1` (not ignored) -> pass
    - `git check-ignore .harbor/views/modules/harbor/core/review-checklist.md` -> exit `1` (not ignored) -> pass
    - `git check-ignore .harbor/views/modules/harbor/core/debug-playbook.md` -> exit `1` (not ignored) -> pass
    - `git check-ignore .harbor/state/sentinel` -> exit `0` (ignored) -> pass
    - `git check-ignore .harbor/cache/sentinel` -> exit `0` (ignored) -> pass
    - `git check-ignore .harbor/exports/sentinel` -> exit `0` (ignored) -> pass
  - Verdict: pass

## Findings
- blockers:
  - none

- warnings:
  - `harbor/core` is not currently in indexed records (`.harbor/config.yaml` has `code_roots: tests/fixtures_sqlite/**`), so `module seal/stale/promote-skill harbor/core` cannot verify full canonical readiness in runtime.
  - `doctor` skill-reference check is `SKIP` because `.agents/skills` folder is absent; canonical reference positive-path cannot be exercised by current workspace state.

- non-blocking follow-ups:
  - Prepare a verification-ready index scope for `harbor/core` before rerunning Phase 2C.5 command chain in release gate environment.
  - Ensure at least one generated module skill exists to fully exercise doctor canonical/legacy skill-reference compatibility branch.

## Compatibility
- project structure:
  - Compatible. No regression signal in command execution path.

- L2/docs:
  - `finish --sync-context` keeps current L2 behavior (writes `module/README.md`), no Phase 2C.5 out-of-scope migration performed.

- diary:
  - No diary migration or diary semantic change observed.

- legacy docs modules:
  - Legacy `docs/harbor/modules/*` was not deleted and not newly written under current export-disabled config.

- skills:
  - `promote-skill` readiness gate remains index-driven and did not fallback to legacy docs path.

## Runtime Safety
- files written:
  - `.harbor/reports/dogfooding/workspace-layout-phase-2c-verification.md` (this report)
  - `tests/fixtures_sqlite/README.md` (by `harbor finish --sync-context`)
  - `.harbor/l2_meta.json` (by `harbor finish --sync-context`)

- workspace boundary:
  - No out-of-workspace write observed.

- high-risk operations:
  - None executed (`harbor accept`, destructive git, push/tag/commit all not executed).

## Next Step Recommendation
- Recommendation: **Phase 2D (conditional go)**.
- Gate note:
  - Before promoting to hard release gate, run the same checklist in an environment where `harbor/core` is indexed and at least one `.agents/skills/harbor-debug-*/SKILL.md` exists, to complete canonical readiness positive-path validation.
- Decision:
  - Current run: **go with warnings** (no blocker in Phase 2C behavior; verification completeness limited by workspace index scope).

---

## Phase 2C.6 Verification (Effective Config Scope Alignment + Positive Capsule Verification)

### Scope & Constraints
- 仅执行环境对齐与正向验证；未新增功能、未迁移 L2 README、未迁移 diary、未进入 Phase 2D。
- 未执行 `harbor accept`，未执行 `git add/commit/tag/push`，未执行 destructive command。

### Effective Config
- canonical config (`.harbor/config/harbor.yaml`):
  - Before: not exists
  - After: exists
- legacy config (`.harbor/config.yaml`):
  - exists（保留，兼容读取）
- active source:
  - Before fix: `E:\project\harbor-spec\.harbor\config.yaml`
  - After fix: `E:\project\harbor-spec\.harbor\config\harbor.yaml`
- effective code roots:
  - Before: `tests/fixtures_sqlite/**`
  - After: `harbor/**`, `tests/**`
- effective paths.source:
  - `load_workspace_config(...).source_path`（实际命中配置路径）
- why harbor/core was not indexed:
  - 有效 source 为 legacy config，且 `code_roots` 仅 `tests/fixtures_sqlite/**`，`IndexBuilder/SyncEngine` 因此不会扫描 `harbor/core`。

### Index Scope Alignment
- changes made:
  - 新增 canonical 配置：`.harbor/config/harbor.yaml`
  - 未删除 legacy `.harbor/config.yaml`
- commands run:
  - `harbor config list`
  - `harbor lock`
  - `harbor module inspect harbor/core`
- files written:
  - `.harbor/config/harbor.yaml`
  - `.harbor/cache/harbor.db`（索引刷新）
  - `.harbor/cache/l3_index.json` / `.harbor/cache/l3_index.json.bak-*`（索引快照与迁移备份）
  - `.harbor/config/harbor.yaml` 被 lock 更新 `adopted_roots: [harbor/**]`
- indexed confirmation:
  - `harbor module inspect harbor/core` 显示 key files + contracts
  - SQLite 检查 `harbor/core/*` 文件计数：20

### Positive Capsule Verification
- module seal:
  - Command: `harbor module seal harbor/core --write`
  - Exit: `0`
  - Generated:
    - `.harbor/views/modules/harbor/core/module-card.md`
    - `.harbor/views/modules/harbor/core/review-checklist.md`
    - `.harbor/views/modules/harbor/core/debug-playbook.md`
  - `docs/harbor/modules/harbor/core/*`: not generated
- module stale:
  - Command: `harbor module stale harbor/core`
  - Exit: `0`
  - Result: 状态=最新（fingerprint match）
- promote-skill:
  - Command: `harbor module promote-skill harbor/core`
  - Exit: `0`
  - Generated: `.agents/skills/harbor-debug-harbor-core/SKILL.md`
  - `SKILL.md` Load order 引用 canonical:
    - `.harbor/views/modules/harbor/core/module-card.md`
    - `.harbor/views/modules/harbor/core/review-checklist.md`
    - `.harbor/views/modules/harbor/core/debug-playbook.md`
  - 未默认引用 `docs/harbor/modules/harbor/core/*`
- doctor:
  - Command: `harbor doctor`
  - Exit: `0`
  - Result: all pass；`Skill 引用: PASS`；未误报 canonical reference missing
- doctor json:
  - Command: `harbor doctor --format json`
  - Exit: `0`
  - stdout: 单一 JSON 对象（valid）
  - JSON 未将 `docs/harbor/modules` 作为主路径

### Tests
- `pytest`:
  - Exit: `0`
  - Result: `215 passed in 19.52s`

### File Write Review (This Run + Existing Dirty Context)
- README.md:
  - 变更路径：`tests/fixtures_sqlite/README.md`（已有派生变更）
  - repo root `README.md`: 未修改（不在 `git diff --name-only`）
- l2_meta.json:
  - 路径：`.harbor/l2_meta.json`
  - 归属：与 `tests/fixtures_sqlite` 派生链路相关的既有变更
- `.harbor/views/modules`:
  - 本轮新增 `harbor/core` capsule 三文件
- `docs/harbor/modules`:
  - 本轮未写入（`docs/harbor/modules/harbor/core/*.md` not found）
- `.agents/skills`:
  - 本轮新增 `.agents/skills/harbor-debug-harbor-core/SKILL.md`
- workspace boundary:
  - 未发现 workspace 外写入

### Remaining Warnings
- 无 blocker。
- 非阻塞提示：
  - `harbor lock` 自动更新了 canonical config 的 `adopted_roots`，属于当前实现的副作用写入（可接受，已记录）。

---

## Phase 2C.7 Baseline Review

### working tree summary
- 执行命令：
  - `git status --short --untracked-files=all`
  - `git status --short --ignored`
- tracked modified:
  - `.harbor/l2_meta.json`
  - `tests/fixtures_sqlite/README.md`
- untracked:
  - `.harbor/config/harbor.yaml`
  - `.harbor/views/modules/harbor/core/module-card.md`
  - `.harbor/views/modules/harbor/core/review-checklist.md`
  - `.harbor/views/modules/harbor/core/debug-playbook.md`
  - `.agents/skills/harbor-debug-harbor-core/SKILL.md`
  - `.harbor/reports/dogfooding/workspace-layout-phase-2c-verification.md`
- ignored（节选）:
  - `.harbor/cache/`
  - `.pytest_cache/`
  - `.trae/`

### config baseline
- canonical config path:
  - `E:\project\harbor-spec\.harbor\config\harbor.yaml`
- legacy config path:
  - `E:\project\harbor-spec\.harbor\config.yaml`
- active config source:
  - canonical（依据：`harbor/core/workspace.py` 中 `load_workspace_config` 按 `new_config_path -> legacy_config_path` 顺序加载；当前 canonical 文件存在）
- effective source/code roots:
  - `harbor/**`
  - `tests/**`
- adopted_roots:
  - `harbor/**`
- inclusion check:
  - `harbor/**` 已纳入
  - `tests/**` 已纳入
- legacy override check:
  - 未发现 legacy 配置覆盖 canonical 的情况（canonical 命中即停止回退）

### tracking policy
- `.harbor/config/harbor.yaml`: untracked, not ignored
- `.harbor/views/modules/harbor/core/*`: untracked, not ignored
- `.harbor/cache/*`: ignored（`git check-ignore` 命中）
- `.agents/skills/harbor-debug-harbor-core/SKILL.md`: untracked, not ignored
- `tests/fixtures_sqlite/README.md`: tracked modified
- `l2_meta.json`（repo root）: not found
- `.harbor/l2_meta.json`: tracked modified

### generated file classification
- generated canonical Harbor assets:
  - `.harbor/config/harbor.yaml`
  - `.harbor/views/project-structure.md`（tracked，当前无新增修改）
  - `.harbor/views/modules/harbor/core/module-card.md`
  - `.harbor/views/modules/harbor/core/review-checklist.md`
  - `.harbor/views/modules/harbor/core/debug-playbook.md`
- generated external export assets:
  - `.agents/skills/harbor-debug-harbor-core/SKILL.md`
- generated legacy/L2 artifacts:
  - `tests/fixtures_sqlite/README.md`（tracked modified）
  - `.harbor/l2_meta.json`（tracked modified）
- cache/state artifacts:
  - `.harbor/cache/harbor.db`（ignored）
  - `.harbor/cache/l3_index.json`（ignored）
  - `.harbor/cache/l3_index.json.bak-*`（ignored）
- reports:
  - `.harbor/reports/dogfooding/workspace-layout-phase-2c-verification.md`（untracked）

### Phase 2D readiness
- 结论：Phase 2D **可进入（go）**，无 blocker。
- 条件说明：
  - 本阶段未执行 L2 README 迁移、未迁移 diary、未执行 `harbor accept`、未做 destructive 操作。
  - 基线审查范围内，canonical 视图与 skill 导出产物已就位，缓存与本地状态仍保持 ignore 策略。

### unresolved L2 legacy artifacts
- `tests/fixtures_sqlite/README.md`：保留为待 Phase 2D 处理项。
- `.harbor/l2_meta.json`：保留为待 Phase 2D 处理项。
- root-level `l2_meta.json`：当前未发现；若后续出现，应按“非预期 root-level artifact”处理策略评估并清理。

### Tests
- `pytest`:
  - Command: `pytest`
  - Exit code: `0`
  - Result: `215 passed in 19.85s`

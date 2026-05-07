# Harbor Workspace Layout Phase 2D-A.5 Verification

Date: 2026-05-07  
Workspace: `e:/project/harbor-spec`

## Phase 2D-A.5 Summary
- Scope: L2 Canonical End-to-End Verification & Baseline Review（真实命令链路）。
- Constraint status:
  - 未新增功能，未进入 Phase 2D-B。
  - 未实现 export stale governance 独立信号。
  - 未迁移 diary。
  - 未实现 workspace inspect/migrate。
  - 未实现 context plan / --ci。
  - 未删除 legacy 文件。
  - 未运行 `harbor accept`。
  - 未执行 `git add/commit/tag/push`。
- Overall:
  - 核心链路（`pytest`、`docs --module`、`docs --changed`、`finish --sync-context`、`stale`、export disabled）已执行并留痕。
  - 发现 1 个 blocker：`harbor docs --all --write` 在当前索引含 workspace 外绝对路径模块时直接报错退出。

## Baseline (Pre-run)
- `git status --short --untracked-files=all`：存在既有脏工作树（代码、测试、文档改动）。
- 关键文件初始状态：
  - `.harbor/views/l2/_meta.json`: 不存在
  - `.harbor/views/l2/harbor/core/README.md`: 不存在
  - `.harbor/l2_meta.json`: 存在（legacy）
  - `harbor/core/README.md`: 存在（tracked）
  - `tests/fixtures_sqlite/README.md`: 存在（tracked）

## Command Verification
- `pytest`:
  - Command: `pytest`
  - Exit: `0`
  - Result: `222 passed in 21.21s`
  - Verdict: pass

- `docs preview`:
  - Command: `harbor docs --module harbor/core`
  - Exit: `0`
  - Output: 直接打印模块 Markdown 预览（无 Updated 清单）
  - Files:
    - `.harbor/views/l2/harbor/core/README.md`: 未创建
    - `harbor/core/README.md`: 未变更（mtime 保持）
    - `.harbor/views/l2/_meta.json`: 未创建
  - Verdict: pass

- `docs module write`:
  - Command: `harbor docs --module harbor/core --write`
  - Exit: `0`
  - Output:
    - `已更新：`
    - `.harbor/views/l2/harbor/core/README.md`
    - `harbor/core/README.md`
  - Checks:
    - canonical README 已写入：pass
    - module README export（默认 enabled=true）已写入：pass
    - `.harbor/views/l2/_meta.json` 已写入（文件存在且 mtime 更新）：pass
    - Updated 列表不包含 `_meta.json`：pass
    - `.harbor/l2_meta.json` 未写入（mtime 保持）：pass
  - Verdict: pass

- `docs changed write`:
  - Command: `harbor docs --changed --write`
  - Exit: `0`
  - Output模块：
    - `harbor`, `harbor/adapters/python`, `harbor/cli`, `harbor/core`, `harbor/utils`, `tests`, `tests/core`, `tests/fixtures_sqlite`
  - 写入检查：
    - canonical L2 路径写入：pass（`.harbor/views/l2/<module>/README.md`）
    - module README export 默认写入：pass
    - 未写 workspace 外路径：pass（输出与 git 变化均在 repo 内）
    - 未写 docs/harbor 相关路径：pass
  - Verdict: pass

- `docs all write`:
  - Command: `harbor docs --all --write`
  - Exit: `1`
  - 关键错误：
    - 索引模块中出现 `C:/Users/GM/AppData/Local/Temp/.../src`
    - `L2Generator._resolve_canonical_readme_path` 触发 `ValueError`（路径逃逸 repo root）
  - 影响：
    - `--all --write` 无法在当前索引状态完成全量验证
  - Verdict: **blocker**

- `finish --sync-context`:
  - Command: `harbor finish --sync-context`
  - Exit: `0`
  - L2部分：
    - 写入 `.harbor/views/l2/<module>/README.md`：pass
    - module README export 按默认 true 写入：pass
  - Capsule部分：
    - 执行了 changed modules 流程，但显示“未检测到变更模块。模块胶囊已是最新。”（实际无新增 capsule 文件写入）
  - 边界：
    - 未写 workspace 外路径：pass
    - 未写 `docs/harbor/modules`：pass
    - 未写 `docs/harbor/project-structure.md`：pass
  - Verdict: pass（带 warning：当前索引/上下文导致 capsule 写入路径未被正向触发）

- `stale`:
  - Command: `harbor stale`
  - Exit: `0`
  - Result: changed scope 下各模块 L2/Capsule 均为 `unknown`（`no indexed records found for module`）
  - Verdict: warning（命令正常，但无法完成“up_to_date/stale”正向判定）

- `stale json`:
  - Command: `harbor stale --format json`
  - Exit: `0`
  - JSON:
    - stdout 为单一 JSON 对象：pass
    - 未发现绝对路径：pass
  - Verdict: pass（语义结果仍为 unknown）

- `export disabled`:
  - Method:
    - 临时将 `.harbor/config/harbor.yaml` 设为：
      - `l2.export.module_readme.enabled: false`
    - 执行 `harbor docs --module harbor/core --write`
    - 同脚本自动恢复原配置文本
  - Exit: `0`
  - Output:
    - `已更新：`
    - 仅 `.harbor/views/l2/harbor/core/README.md`
  - Checks:
    - canonical README 写入：pass
    - `harbor/core/README.md` 未触碰（mtime 不变）：pass
    - `_meta.json` 仍写 canonical：pass
    - 配置恢复成功：pass
  - Verdict: pass

## L2 Metadata
- canonical:
  - `.harbor/views/l2/_meta.json` 已存在并随写操作更新。
- legacy:
  - `.harbor/l2_meta.json` 存在，当前为 tracked legacy 文件；
  - 本轮命令验证中未被写入更新（mtime 保持）。
- write target:
  - 实际写目标为 canonical `_meta.json`。
- compatibility:
  - 构造 legacy-only 场景（临时目录）验证结果：
    - 仅 legacy meta 存在时，`force=false` 写入返回 `None`（读取 legacy 命中）；
    - 后续写入可生成 canonical `_meta.json`；
    - legacy 文件内容保持不变。

## Git Tracking / Ignore Check
- `.harbor/views/l2/harbor/core/README.md`: exists, untracked, not ignored
- `.harbor/views/l2/_meta.json`: exists, untracked, not ignored
- `.harbor/l2_meta.json`: exists, tracked, not ignored
- `harbor/core/README.md`: exists, tracked, not ignored
- `tests/fixtures_sqlite/README.md`: exists, tracked, not ignored
- `.harbor/views/modules/harbor/core/*`: exists, tracked, not ignored
- `.agents/skills/harbor-debug-harbor-core/SKILL.md`: exists, tracked, not ignored
- `.harbor/cache/*`: ignored

## Working Tree Classification
- code:
  - `harbor/cli/main.py`
  - `harbor/core/l2.py`
  - `harbor/core/stale.py`
  - `harbor/utils/i18n.py`
- tests:
  - `tests/test_cli_docs_modes.py`
  - `tests/test_cli_finish_sync_context.py`
  - `tests/test_l2_paths.py`
  - `tests/test_release_packaging.py`
  - `tests/test_stale.py`
- config:
  - `.harbor/config/harbor.yaml`（本轮仅临时改动并恢复；最终未新增持久配置变更）
- canonical views:
  - `.harbor/views/l2/_meta.json`
  - `.harbor/views/l2/harbor/README.md`
  - `.harbor/views/l2/harbor/adapters/python/README.md`
  - `.harbor/views/l2/harbor/cli/README.md`
  - `.harbor/views/l2/harbor/core/README.md`
  - `.harbor/views/l2/harbor/utils/README.md`
  - `.harbor/views/l2/tests/README.md`
  - `.harbor/views/l2/tests/core/README.md`
  - `.harbor/views/l2/tests/fixtures_sqlite/README.md`
- module README exports:
  - `harbor/README.md`（untracked）
  - `harbor/cli/README.md`（untracked）
  - `harbor/core/README.md`（tracked modified）
  - `harbor/adapters/python/README.md`（tracked modified）
  - `harbor/utils/README.md`（tracked modified）
  - `tests/README.md`（untracked）
  - `tests/core/README.md`（untracked）
  - `tests/fixtures_sqlite/README.md`（tracked modified）
- legacy L2 metadata:
  - `.harbor/l2_meta.json`（tracked legacy, 未更新）
- capsule views:
  - `.harbor/views/modules/harbor/core/module-card.md`
  - `.harbor/views/modules/harbor/core/review-checklist.md`
  - `.harbor/views/modules/harbor/core/debug-playbook.md`
  - 本轮 `finish --sync-context` 未新增 capsule 写入
- skills:
  - `.agents/skills/harbor-debug-harbor-core/SKILL.md`
- external exports:
  - none（本轮未写 `docs/harbor/**`）
- reports:
  - `.harbor/reports/dogfooding/workspace-layout-phase-2d-verification.md`
- cache/state:
  - `.harbor/cache/*`（ignored）
- unexpected:
  - none（相对本阶段目标）

## Findings
- blockers:
  - `harbor docs --all --write` 在索引包含 workspace 外绝对路径模块时失败退出（ValueError），导致 Phase 2D-A.5 的 all-write 正向验证不可完成。
- warnings:
  - `harbor stale` / `harbor stale --format json` 当前均为 unknown（no indexed records），无法验证“canonical stale 与 export stale 解耦”的正向语义分支。
  - `finish --sync-context` 的 capsule 刷新阶段未产生 canonical module capsule 写入（当前上下文未触发该分支）。
- follow-ups:
  - 清理或隔离索引中的 workspace 外模块记录后，重跑 `harbor docs --all --write`。
  - 在具备可索引模块记录的稳定环境中补跑 `stale` 与 `finish --sync-context` 的正向判定链路。

## Runtime Safety
- files written:
  - `.harbor/views/l2/_meta.json`
  - `.harbor/views/l2/**/README.md`（本轮涉及 harbor/tests 多模块）
  - `<module>/README.md` exports（默认 enabled=true 的模块）
  - `.harbor/reports/dogfooding/workspace-layout-phase-2d-verification.md`
  - `.harbor/config/harbor.yaml`（临时改动后已恢复原文）
- workspace boundary:
  - 实际写入均在 workspace 内；
  - `docs --all --write` 对 workspace 外模块触发防护并失败退出，未发生越界写入。
- high-risk operations:
  - 未执行 `harbor accept`、未执行 destructive 命令、未执行 git 提交链路。

## Next Step Recommendation
- 当前建议：**fix required**
- 原因：存在 blocker（`docs --all --write` 在 workspace 外索引模块下失败）。
- 推荐顺序：
  1. 先修复/隔离 `docs --all --write` 的 workspace 外索引模块处理（最小范围）。
  2. 修复后重跑 Phase 2D-A.5 全链路，确认 all-write 与 stale 正向语义。
  3. 通过后再进入 Phase 2D-B。

## Phase 2D-A.6 Safe Module Selection Fix
- Date: 2026-05-07
- Scope:
  - 仅修复 `docs` 批量写入在 unsafe indexed modules 存在时的失败行为。
  - 未进入 Phase 2D-B；未实现 export stale governance；未迁移 diary；未新增 CLI 命令；未删除 legacy 文件。

### Root Cause
- `harbor docs --all --write` 直接消费 `collect_all_indexed_modules()` 并写入 L2。
- 当索引模块含 workspace 外绝对路径（如 `C:/Users/.../Temp/...`）时，`L2Generator` 路径边界防护抛出 `ValueError`，导致整条 bulk 命令 exit 1。
- 本质是“选择阶段未过滤 unsafe module”，而非“写入 guard 缺失”。

### Fix Summary
- 在 `harbor/cli/main.py` 增加 safe module selection：
  - bulk 模式（`docs --all/--changed`）对 unsafe module 做 skip + warning；
  - explicit 模式（`docs --module <module> --write`）对 unsafe module 直接报错（exit non-zero）。
- 保留 `L2Generator` 既有 path safety guard（未移除、未放宽）。
- warning 增加路径脱敏展示（`<outside-repo>` + basename），避免输出完整外部绝对路径细节。
- finish `--sync-context` 的 L2 刷新路径复用 docs changed helper，自动获得同样 skip 行为。

### docs --all rerun result
- Command: `harbor docs --all --write`
- Exit: `0`
- Output:
  - `已跳过不安全的索引模块：`
  - `- <outside-repo>/src (位于仓库根之外)`
  - `未发现可生成的已索引模块。`
- Verdict:
  - blocker 已修复（命令不再因 unsafe indexed module 崩溃）。
  - 本次索引下 safe indexed modules 为 0，故无 L2 写入条目。
  - 未发生 workspace 外写入。

### docs --changed result
- Command: `harbor docs --changed --write`
- Exit: `0`
- Output:
  - warning：`已跳过不安全的索引模块： - <outside-repo>/src (位于仓库根之外)`
  - safe modules 正常写入 canonical/export（harbor 与 tests 相关模块）。
- Verdict:
  - external changed module 被 skip；
  - workspace 内模块继续处理；
  - 未发生 workspace 外写入。

### finish --sync-context result
- Command: `harbor finish --sync-context`
- Exit: `0`
- L2 section:
  - 出现 unsafe skip warning（`<outside-repo>/src`）；
  - safe changed modules 正常写入 canonical/export L2。
- Command flow:
  - finish 全流程未崩溃。
- Boundary:
  - 未发现 workspace 外写入。

### Skipped unsafe module behavior
- bulk docs 行为：
  - workspace 外绝对路径模块：skip + warning
  - `..` traversal 模块：skip + warning
  - 空/无效模块：skip + warning
- explicit `--module --write` 行为：
  - unsafe module 直接报错，不静默 skip。
- disclosure:
  - warning 不输出完整外部绝对路径；外部路径以 `<outside-repo>` 形式展示。

### Tests
- Targeted:
  - `pytest tests/test_cli_docs_modes.py tests/test_cli_finish_sync_context.py tests/test_l2_paths.py tests/test_workspace_paths.py tests/test_stale.py`
  - Result: `43 passed`
- Full:
  - `pytest`
  - Result: `228 passed`

## Phase 2D-A.7 docs --all Positive Coverage
- Date: 2026-05-07

### root cause
- active config:
  - source: `.harbor/config/harbor.yaml`
  - effective code_roots: `['harbor/**', 'tests/**']`
  - effective exclude_paths: `[]`
- index records（pre-fix/runtime inspection）:
  - `.harbor/cache/l3_index.json` 不存在，`collect_all_indexed_modules()` 走 SQLite `harbor.db`
  - `harbor.db` 当时仅 1 条外部记录：`C:/Users/GM/AppData/Local/Temp/.../src/mod.py`
  - 不含 `harbor/core` / `harbor/cli` / `harbor/utils`
- collect_all_indexed_modules:
  - 原始输出：`['C:/Users/GM/AppData/Local/Temp/.../src']`
- safe selector（docs --all 路径）:
  - input: 与 `collect_all_indexed_modules()` 输出一致（外部模块）
  - output: safe=`[]`, skipped=`['<outside-repo>/src (outside repository root)']`
- why safe modules were 0:
  - 直接原因是索引中无任何 repo 内记录；不是 active config 错配。
  - 现象可稳定复现为：`harbor docs --all` 输出“已跳过不安全模块”后“未发现可生成的已索引模块”。

### fix summary
- module normalization:
  - 在 `harbor/core/l2.py` 增加 `normalize_indexed_module_candidate()`，将 repo 内绝对文件路径优先映射为 repo-relative module。
  - `collect_all_indexed_modules()` 改为调用该归一化函数构建模块集合。
- safe selector:
  - 在 `harbor/cli/main.py::_classify_module_safety()` 增强文件路径候选处理：
  - `harbor/core/l2.py`、`E:/repo/harbor/core/l2.py` 可推断为 `harbor/core`。
  - 绝对路径先映射 repo-relative，再判断安全。
- external paths:
  - workspace 外绝对路径继续判定 unsafe 并 skip+warning（bulk）。
  - warning 仍保持脱敏，不泄露完整外部绝对路径和用户名。
- traversal paths:
  - `../outside`、`harbor/../../outside` 继续 unsafe skip。
- safety guard:
  - 未放松 `L2Generator` 写入边界校验（canonical/export 仍受 repo root 约束）。

### docs --all result
- 因 pre-fix 索引无 repo 内记录，先执行 `harbor lock`（安全刷新索引）。
- `harbor lock`:
  - exit: `0`
  - output: `扫描=82 更新=82 跳过=0 项目=521 库=.harbor/cache/harbor.db`
  - 写入文件（实际）:
    - `.harbor/cache/harbor.db`（索引刷新）
    - `.harbor/cache/harbor.db-wal/.shm`（SQLite 运行期）
    - `.harbor/config/harbor.yaml`（adopted_roots 派生写入）
- `harbor docs --all --write`:
  - exit: `0`
  - safe modules processed:
    - `harbor`, `harbor/adapters/python`, `harbor/cli`, `harbor/core`, `harbor/utils`, `tests`, `tests/core`, `tests/fixtures_sqlite`
  - 写入：
    - canonical: `.harbor/views/l2/<module>/README.md`
    - export: `<module>/README.md`
  - workspace 外路径写入：未发现

### unsafe modules skipped
- 命令链路验证中（`docs --all`/`docs --changed`/`finish --sync-context`）与测试用例都保持 unsafe skip 机制。
- 回归测试覆盖：
  - external absolute path -> skip + warning
  - traversal -> skip + warning
  - explicit unsafe `--module --write` -> non-zero hard fail

### docs --changed result
- command: `harbor docs --changed --write`
- exit: `0`
- output: `未检测到变更模块。canonical L2 README 已是最新。`
- 说明：本次命令时点下 changed 集为空，流程无 crash、无越界写入。

### finish result
- command: `harbor finish --sync-context`
- exit: `0`
- result:
  - `未检测到变更模块。已跳过上下文同步。`
  - 不 crash，不写 workspace 外路径。

### tests
- targeted:
  - `pytest tests/test_cli_docs_modes.py tests/test_cli_finish_sync_context.py tests/test_l2_paths.py tests/test_workspace_paths.py`
  - result: `40 passed`
- full pytest:
  - `pytest`
  - result: `232 passed`

### remaining warnings
- 执行全量 `pytest` 后，SQLite 索引可能再次仅残留测试产生的外部临时路径（`C:/Users/.../Temp/pytest-*/src/mod.py`），导致随后 `collect_all_indexed_modules()` 再次出现 safe=0。
- 该现象与本阶段 docs safe selector 正向修复不冲突；本阶段已通过 `harbor lock` 刷新后完成 `docs --all --write` 正向验证。

## Phase 2D-A.8 Test / Index Isolation Hardening
- Date: 2026-05-07
- Scope:
  - 仅修复 full pytest 后真实 `.harbor/cache` 可能被测试临时路径污染的问题。
  - 未进入 Phase 2D-B；未实现 export stale governance；未迁移 diary；未新增 CLI 命令；未删除 legacy 文件。

### root cause
- polluted files:
  - `.harbor/cache/harbor.db`（真实仓库索引 DB 可被测试写入临时路径记录）
  - `.harbor/cache/l3_index.json`（在迁移链路下可能被重命名为 `.bak-*`）
- affected tests:
  - `tests/core/test_storage_migration.py`
  - `tests/core/test_index_sync_sqlite.py`
  - `tests/test_cli_v2.py`
  - 以及依赖旧行为（`IndexBuilder(cache_dir=...)` 仍写 repo DB）的测试，如 `tests/test_sync_engine.py`、`tests/test_project_structure.py` 的相关场景
- why real `.harbor/cache` was modified:
  - `IndexBuilder.__init__` 原实现即使传入 `cache_dir`，SQLite 仍使用 `HarborDB(project_root=Path.cwd())` 默认路径 `.harbor/cache/harbor.db`，导致测试写入泄漏到真实仓库 cache。
  - `test_storage_migration` 在真实 cwd 下直接写 `.harbor/cache/l3_index.json` 并调用 `HarborDB().migrate_from_json(...)`，会触发真实索引文件迁移重命名。

### fix summary
- test isolation:
  - `tests/core/test_storage_migration.py`：增加 `monkeypatch.chdir(tmp_path)`，迁移与备份文件仅在临时工作区发生。
  - `tests/core/test_index_sync_sqlite.py`：增加 `monkeypatch.chdir(tmp_path)`，并将 fixtures/config 全部迁移到 tmp workspace。
  - `tests/test_cli_v2.py`：新增 autouse fixture `monkeypatch.chdir(tmp_path)`，确保 `status/finish/accept/commit` 运行在隔离 root。
- tmp_path workspace:
  - 新增 `tests/test_cache_isolation_hardening.py`，覆盖 isolated index write、CLI root isolation、external temp path only-in-tmp、docs --all external-only index isolation。
- CLI test changes:
  - 调整 `test_status_alias_st` 与新增隔离回归用例中的状态输出断言，兼容 clean workspace 下 `No changes detected.` 文案。
- cache write boundary:
  - `harbor/core/index.py`：`IndexBuilder` 现在使用 `HarborDB(db_path=self.cache_dir / "harbor.db", ...)`，保证 DB 与 `l3_index.json` 同一 cache root。

### pytest result
- Command: `pytest`
- Result: `236 passed in 19.54s`

### post-pytest index/cache status
- `pytest` 后（在执行 `harbor lock` 之前）检查真实 cache：
  - `db_exists=True`
  - `idx_exists=False`
  - `db_files_count=82`
  - 样本记录为 repo 内路径（如 `harbor/cli/__init__.py`、`harbor/core/...`），未出现 `C:/Users/.../Temp/...` 外部路径。

### docs --all result before harbor lock
- Command: `harbor docs --all --write`
- Exit: `0`
- 结果：正常处理 safe modules（`harbor/core`、`harbor/cli`、`harbor/utils`、`tests/*`），未出现 safe modules=0。

### harbor lock result
- Command: `harbor lock`
- Exit: `0`
- 输出：`扫描=83 更新=7 跳过=76 项目=46 库=E:/project/harbor-spec/.harbor/cache/harbor.db`

### docs --all result after harbor lock
- Command: `harbor docs --all --write`
- Exit: `0`
- 结果：继续正常处理同一组 repo 内 modules。

### docs --changed result
- Command: `harbor docs --changed --write`
- Exit: `0`
- 结果：`未检测到变更模块。canonical L2 README 已是最新。`

### finish --sync-context result
- Command: `harbor finish --sync-context`
- Exit: `0`
- 结果：上下文同步阶段正常执行并提示“未检测到变更模块。已跳过上下文同步。”

### external record contamination check
- 验证命令后检查真实 DB：
  - `total=83`
  - `external_like=0`
  - `external_sample=[]`
- 结论：未出现 `C:/Users/.../Temp/...` 记录污染真实 `.harbor/cache/harbor.db`。

### remaining warnings
- 本轮 `docs --changed` 与 `finish --sync-context` 在验证时点均无 changed modules，因此属于“无变化路径”验证结果。
- 当前未引入 session 级全局 post-test 守卫 fixture（采用 targeted regression），后续如需更强约束可在测试基建层补充。

## Phase 2D-B.5 Semantic Drift Triage
- Date: 2026-05-07
- Scope:
  - 仅 triage `harbor finish --sync-context` 输出的 `POSSIBLE_SEMANTIC_DRIFT`。
  - 审查 Phase 2A-2D-B 路径迁移后 canonical/legacy 文案基线。
  - 不进入 Phase 2E，不迁移 diary，不新增命令，不实现 workspace inspect/migrate。

### semantic drift summary
- command:
  - `harbor finish --sync-context`
- first capture:
  - `targets=14`，均为 `POSSIBLE_SEMANTIC_DRIFT`
- post-fix capture:
  - `targets=15`，其中：
    - `POSSIBLE_SEMANTIC_DRIFT=13`
    - `OK=1`（`harbor.core.stale.format_stale_summary`）
    - `ERROR=1`（`harbor.cli.main.main`，LLM provider 输入长度上限）

### triage table (from first capture)
| file / symbol | reported drift | related contract/docstring | related implementation | classification | recommended action |
|---|---|---|---|---|---|
| `harbor/core/doctor.py` / `harbor.core.doctor._derived_view_detail_status` | Docstring 粒度不足、未完整覆盖 fallback | 函数无/弱 docstring 约束 | 状态值映射含 fallback 逻辑 | stale docstring | 已补充 Args/Returns 与 fallback 说明 |
| `harbor/core/doctor.py` / `harbor.core.doctor.run_derived_views_check` | Docstring 不完整，无法严格对照 | 函数无/弱 docstring 约束 | 聚合三类视图并处理 disabled/legacy 语义 | stale docstring | 已补充行为语义 docstring |
| `harbor/core/stale.py` / `harbor.core.stale.ModuleStaleSummary.to_dict` | 返回结构描述不充分 | 方法无/弱 docstring | 返回稳定 dict 结构（JSON payload 组成部分） | stale docstring | 已补充序列化说明 |
| `harbor/core/stale.py` / `harbor.core.stale._format_view_lines` | 参数/返回说明不足 | 函数无/弱 docstring | 生成 stale 文本行 | stale docstring | 已补充简洁 docstring |
| `harbor/core/stale.py` / `harbor.core.stale.check_module_derived_views_stale` | 返回对象结构说明不足 | 函数无/弱 docstring | 聚合 l2/l2_export/capsule 结果 | stale docstring | 已补充 Args/Returns 与三视图语义 |
| `harbor/core/stale.py` / `harbor.core.stale.format_stale_summary` | 参数说明不足 | 函数无/弱 docstring | 渲染 CLI 文本摘要 | stale docstring | 已补充 Args/Returns；复跑后为 `OK` |
| `harbor/core/stale.py` / `harbor.core.stale.stale_report_to_dict` | 返回字段说明不足 | 函数无/弱 docstring | 生成 machine-readable stale JSON | stale docstring | 已补充 Args/Returns |
| `tests/test_cli_json_output.py` / `_sample_stale_summary` | 要求测试 helper 提供完整契约文档 | 测试辅助函数通常不作为 Harbor public contract | 构造测试样例对象 | false positive | 仅记录，不改功能 |
| `tests/test_cli_json_output.py` / `test_stale_json_output_has_required_fields_and_no_extra_text` | 将测试断言函数按产品契约严格审计 | 测试函数非外部契约源 | monkeypatch + 断言 | false positive | 仅记录，不改功能 |
| `tests/test_cli_stale.py` / `_sample_summary` | 与上类似，测试 helper 文档缺失 | 测试辅助函数非外部契约源 | 构造 stale summary 样本 | false positive | 仅记录，不改功能 |
| `tests/test_doctor.py` / `_sample_summary` | 与上类似 | 测试辅助函数非外部契约源 | 构造 doctor summary 样本 | false positive | 仅记录，不改功能 |
| `tests/test_doctor.py` / `test_derived_views_check_marks_unknown_detail_as_unknown_not_stale` | 将测试函数按运行时契约审计 | 测试函数非外部契约源 | 单元测试断言 unknown 文案 | false positive | 仅记录，不改功能 |
| `tests/test_stale.py` / `test_check_module_derived_views_stale_returns_both_views` | 将测试函数按产品契约审计 | 测试函数非外部契约源 | 单元测试断言多视图行为 | false positive | 仅记录，不改功能 |
| `tests/test_stale.py` / `test_check_module_derived_views_stale_unknown_consistency_when_no_indexed_records` | 同上 | 测试函数非外部契约源 | 单元测试断言 unknown 一致性 | false positive | 仅记录，不改功能 |

### path migration relation review (Phase 2A-2D-B)
- checked targets:
  - `docs/harbor/project-structure.md`
  - `docs/harbor/modules`
  - `.harbor/l2_meta.json`
  - `specs/diary`
  - `<module>/README.md`
  - `docs/harbor` canonical 描述
- findings:
  - `README.md` / `README.en.md` 中旧路径多为 legacy/export 说明，未再声明为 canonical source（合理保留）。
  - `harbor/core/doctor.py` 与 `harbor/utils/i18n.py` 对 `.harbor/l2_meta.json` 的处理为 advisory/read-compatible（合理）。
  - `harbor/cli/main.py` 的 `project structure --write` help 原文误写为“写 docs/harbor/project-structure.md”（不符合现行 canonical）；已最小修正为 canonical `.harbor/views/project-structure.md` + optional export。
  - `docs/design/harbor-workspace-layout-v1*.md` 存在“Future canonical target”历史段落，当前判定为文档历史上下文（non-blocking, pre-existing），本阶段不做大范围文档重写。

### true drift count
- `0`（本轮 `POSSIBLE_SEMANTIC_DRIFT` 中未发现实现行为与已定义契约直接冲突）。

### false positive count
- `7`（全部来自测试 helper/测试函数被语义审计器按产品契约误判）。

### stale docstring count
- `7`（核心在 `harbor/core/doctor.py` 与 `harbor/core/stale.py` 的文档粒度不足）。

### stale README / docs count
- `1`
  - `harbor/cli/main.py` 的 `project structure --write` 帮助文案（已修复）。

### unrelated/pre-existing issue
- `1`
  - `harbor.cli.main.main` 在语义审计阶段返回 `ERROR`（LLM provider 输入字符上限 `24000`），属于外部模型约束，不是 workspace layout 迁移回归。

### fixes made
- code behavior:
  - none（未改运行逻辑）。
- docstring/contract text:
  - `harbor/core/doctor.py`
    - `run_derived_views_check`
    - `_derived_view_detail_status`
  - `harbor/core/stale.py`
    - `ModuleStaleSummary.to_dict`
    - `check_module_derived_views_stale`
    - `format_stale_summary`
    - `stale_report_to_dict`
    - `_format_view_lines`
- user-facing help text:
  - `harbor/cli/main.py`
    - `project structure --write` 帮助文案改为 canonical `.harbor/views/project-structure.md` + optional export 说明。

### remaining non-blocking drift
- 仍存在的 `POSSIBLE_SEMANTIC_DRIFT` 主要为：
  - 测试函数/测试 helper 被契约审计器误判（false positive）。
  - 个别核心函数在补充 docstring 后仍被模型以“说明不够形式化”标记（模型判定偏保守，不涉及行为变更）。
- 均不构成 workspace layout 行为回归或路径写入错误。

### working tree review (post-verification)
- command:
  - `git status --short --untracked-files=all`
  - `git status --short --ignored`
- code:
  - `harbor/cli/main.py`
  - `harbor/core/doctor.py`
  - `harbor/core/stale.py`
  - `harbor/utils/i18n.py`
- tests:
  - `tests/test_cli_json_output.py`
  - `tests/test_cli_stale.py`
  - `tests/test_doctor.py`
  - `tests/test_stale.py`
- docs:
  - `README.md`
  - `README.en.md`
  - `RELEASE.md`
  - `docs/design/harbor-workspace-layout-v1.md`
  - `docs/design/harbor-workspace-layout-v1.en.md`
  - module README exports (`harbor/**/README.md`, `tests/**/README.md`)
- canonical views:
  - `.harbor/views/l2/**`
  - `.harbor/views/modules/harbor/core/module-card.md`
  - `.harbor/views/modules/harbor/cli/*.md`（untracked）
  - `.harbor/views/modules/tests/*.md`（untracked）
- reports:
  - `.harbor/reports/dogfooding/workspace-layout-phase-2d-verification.md`
- skills:
  - `.agents/skills/harbor-debug-harbor-core/SKILL.md`（存在，未改）
- legacy artifacts:
  - `.harbor/l2_meta.json`（存在，doctor advisory，未迁移/未删除）
- cache/state:
  - `.harbor/cache/*`（ignored）
  - `__pycache__/`, `.pytest_cache/`, `harbor_spec.egg-info/`（ignored）
- unexpected:
  - none（均可由既有 Phase 2D 链路与本轮验证命令解释）

### verification
- `pytest`:
  - command: `pytest`
  - result: `244 passed`
- `finish --sync-context`:
  - command: `harbor finish --sync-context`
  - result: exit `0`；完成 L2/capsule 刷新；无 workspace 外写入迹象
- `stale`:
  - command: `harbor stale --format json`
  - result: exit `0`；`status=pass`；`modules_checked=3`
- `doctor`:
  - command: `harbor doctor --format json`
  - result: exit `0`；`status=warn`（工作区有改动 + legacy metadata advisory）

### Phase 2E readiness
- recommendation: **Phase 2E / pause（可进入，但建议先清理语义审计噪音）**
- rationale:
  - workspace layout 相关 true drift 未发现；
  - stale docstring 与一处 canonical help 文案已最小修复；
  - 剩余主要为 false positive / provider 限制，不阻塞 Phase 2E；
  - 若要提升 `finish --sync-context` 信噪比，后续可考虑（非本阶段）对语义审计目标做测试域过滤或长输入截断策略。

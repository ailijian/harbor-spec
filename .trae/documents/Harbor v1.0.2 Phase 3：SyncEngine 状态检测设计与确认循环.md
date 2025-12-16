# 确认循环

## 1. 任务理解
- 实现 `SyncEngine`，对比当前代码解析与缓存索引（`.harbor/cache/l3_index.json`），输出 Harbor 上下文状态（类似 `git status`）。
- 分类状态：M(实现变更)、C(契约变更)、?(未跟踪)、!(缺失)。
- 重点检测 Implementation Drift：`body_hash` 变更但 `contract_hash` 未变。
- 集成 CLI：`harbor status`。

## 2. 上下文加载
- 已有：`PythonAdapter`（签名与 Docstring 双哈希）、`IndexBuilder`（增量索引与 `body_hash`）。
- 索引缓存结构：按文件组织 `items`，含 `id/qualified_name/signature_hash/body_hash/contract_hash/docstring_raw_hash/lineno`。

## 3. `SyncEngine` 接口与数据结构（L3 概要）

### 3.1 类与公共方法（Strict L3）
- 位置：`harbor/core/sync.py`
- 依赖：`PythonAdapter`、`IndexBuilder._compute_body_hash`（或复用相同算法）、标准库 `json/pathlib/time`。

#### `check_status() -> StatusReport`
- Strict Docstring（概要）：
  - 功能：从 `.harbor/cache/l3_index.json` 加载缓存索引；实时解析 `code_roots` 下的 Python 文件；对比每个函数的 `body_hash` 与 `contract_hash`，输出状态分组与统计。
  - 使用场景：`harbor status`。
  - 依赖：`PythonAdapter.parse_file`、缓存索引文件、与 IndexBuilder 使用一致的 `body_hash` 算法。
  - `@harbor.scope: public`
  - `@harbor.l3_strictness: strict`
  - `@harbor.idempotency: read-only`
  - Args：无（从 `.harbor/config.yaml` 读取 `code_roots`，可选构造时覆盖）。
  - Returns：
    - `StatusReport`：包含分组列表与计数：`drift/modified/contract_changed/untracked/missing/summary_text`。
  - Raises：
    - `IOError`: 索引文件读取失败。
    - `ConfigError`: 配置缺失或不合法。

### 3.2 辅助方法（Standard L3）
- `_load_config()`：读取 `.harbor/config.yaml`，获取 `code_roots`。
- `_load_index_cache()`：读取 `.harbor/cache/l3_index.json`，返回 `files` 映射。
- `_iter_current_items()`：遍历 `code_roots`，解析当前函数列表；为每个函数计算 `body_hash` 与 `contract_hash`。
- `_compare(cached_map, current_map)`：生成状态分组：
  - `id` 同时存在：
    - `body_hash` 变且 `contract_hash` 不变 → `drift`
    - 仅 `body_hash` 变 → `modified`
    - 仅 `contract_hash` 变 → `contract_changed`
  - 仅存在于当前 → `untracked`
  - 仅存在于缓存 → `missing`

### 3.3 数据结构
- `StatusEntry`：`id/name/file_path/change_type/details`。
- `StatusReport`：
  - `drift: StatusEntry[]`
  - `modified: StatusEntry[]`
  - `contract_changed: StatusEntry[]`
  - `untracked: StatusEntry[]`
  - `missing: StatusEntry[]`
  - `counts: {drift, modified, contract_changed, untracked, missing}`

## 4. CLI 集成
- 扩展 `harbor/cli/main.py`：新增 `status` 子命令。
- 行为：
  - 可选先运行 `build-index`（增量）以保证缓存最新；随后调用 `SyncEngine.check_status()`。
  - 输出格式：
    - `On branch <unknown>`（预留）
    - `Harbor Context Status:`
    - 分组打印（Drift/Contract/Untracked/Missing），与用户示例一致。

## 5. 测试计划
- 文件：`tests/test_sync_engine.py`
- 用例：
  1) 初次构建索引后，`check_status()` 返回空状态（无差异）。
  2) 修改实现代码（如把 `a+b` 改为 `a*b`）：应出现 `M` 或 `Drift`（若契约未改则 `Drift`）。
  3) 修改仅 Docstring 契约区（例如更新 `Returns` 文本）：`C`。
  4) 新增函数：`?`；删除函数：`!`。
- 说明（与 Dogfooding演示）：
  - 我们的 `body_hash` 设计不因纯空白变化而改变（降低噪音）。如果要演示“实现变化”检测，建议做一个轻微的语义变更或加入显式 `pass`/`x=x` 这类可见 token；这样确保 `body_hash` 变化可被检测。

## 6. 风险与缓解
- 不同解析算法导致 `body_hash` 不一致：复用与 IndexBuilder 相同实现，保证一致性。
- 大仓库性能：在 `status` 中可选跳过重新计算未改动文件（对比 `file_hash`），但 Phase 3 先以正确性为主。

## 7. 交付物
- `harbor/core/sync.py`（含 strict Docstring）
- `harbor/cli/main.py`（新增 `status` 命令）
- `tests/test_sync_engine.py`（覆盖 Drift/Modified/Contract/Untracked/Missing）

> 确认后我将按以上方案实现 `SyncEngine`、CLI 集成与测试，并展示运行结果。

# 确认执行：Phase 3 启动（含逻辑修正）

接口设计大部分合理，但在**核心工作流**上需要修正。请仔细阅读以下 3 点要求，并在开发中严格执行。

### 1. 逻辑修正：禁止隐式更新索引
**这是最关键的一点。**
- `harbor status` **绝对不能** 自动运行 `build-index`。
- 逻辑应当是：读取 `.harbor/cache/l3_index.json` (作为基准/快照) vs 当前文件系统 (作为实时状态)。
- 如果用户想消除 `status` 中的差异，他们必须显式运行 `harbor build-index` (这相当于 `git add/commit`)。

### 2. 状态判定矩阵 (State Matrix)
请严格按照以下逻辑实现 `_compare`：
- 读取缓存中的 `cached_item` 和实时解析的 `current_item`。
- **Case A (Drift)**: `body_hash` 变了 AND `contract_hash` **没变**。
  -> 标记为 `[Drift]`: 实现已修改但契约未同步 (高危)。
- **Case B (Modified)**: `body_hash` 变了 AND `contract_hash` **也变了**。
  -> 标记为 `[Modified]`: 正常的同步变更。
- **Case C (Contract Only)**: `body_hash` 没变 AND `contract_hash` 变了。
  -> 标记为 `[Contract Changed]`: 纯文档修正。

### 3. 代码复用 (DRY)
- 不要在 `SyncEngine` 中重写 `body_hash` 的计算逻辑。
- 请重构 Phase 2 的代码：将 `_compute_body_hash` 移动到 `harbor.core.utils` 或作为 `IndexBuilder` 的静态公用方法，供 `SyncEngine` 调用。确保算法绝对一致。

### 4. 交付要求
- 实现 `harbor/core/sync.py`。
- 更新 `harbor/cli/main.py` 加入 `status`。
- 编写 `tests/test_sync_engine.py`，必须包含一个测试用例：
  1. `build-index` (建立基准)。
  2. 修改测试文件的代码（加一行逻辑），但不改 Docstring。
  3. 运行 `check_status`，断言结果包含 `Drift` 状态。

**行动：**
请确认你已理解上述“逻辑修正”，并开始编码。
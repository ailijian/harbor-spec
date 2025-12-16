# 目标
- 实现 DDT 装饰器、测试扫描器与验证器，桥接 L3 契约与测试绑定，满足 v1.0.2 的韧性策略与严格度约束。

## 组件与文件
- `harbor/test_utils.py`
  - 提供 `harbor_ddt_target(func: str, l3_version: int | None = None, strategy: str = "strict")` 装饰器
  - 运行时透传测试函数；将绑定元数据以 `_harbor_ddt_meta` 属性附着到被装饰的测试函数上（字典：`{"func": str, "l3_version": int | None, "strategy": str}`）
- `harbor/core/ddt.py`
  - `DDTScanner.scan_tests(test_roots: list[str]) -> list[DDTBinding]`：静态 AST 扫描测试文件，提取绑定
  - `DDTValidator.validate(bindings: list[DDTBinding], index: IndexSnapshot, version_map: VersionMap) -> DDTReport`：根据索引/版本映射校验绑定
- 缓存文件（延续索引体系）
  - `.harbor/cache/l3_index.json`：已包含 `contract_hash/strictness` 等（Phase 2 产物）
  - `.harbor/cache/l3_hash_map.json`：新增（若不存在将创建），记录 `id -> {contract_hash, l3_version}` 的映射，用于版本推导与稳定化

## 行为设计
### 装饰器（Strict L3）
- 仅标记，不改变测试运行行为；被装饰函数上存在 `_harbor_ddt_meta` 供扫描器/验证器读取
- 默认 `strategy="strict"`：即需要显式版本绑定（`l3_version` 必须提供）
- `strategy="latest"`：允许非严格函数自动跟随最新版本（仅当该函数的 L3 严格度不是 `strict`）

### 扫描器（Standard L3）
- 基于 AST 的静态扫描，识别直接使用 `@harbor_ddt_target(...)` 的用法：
  - 提取 `func`（字符串常量）、`l3_version`（整数常量或缺省）、`strategy`（字符串常量或缺省）
  - 解析测试文件相对路径与测试函数名，生成 `DDTBinding(id, l3_version, strategy, file_path, test_name)`
- 约束：MVP 不处理动态生成/间接包装的装饰器（后续可扩展为运行时元数据扫描）

### 版本映射与校验（Strict L3）
- 版本来源：
  - 从 `.harbor/cache/l3_hash_map.json` 读取 `id -> version`；若不存在或缺条目：
    - 初次推导：为每个 `id` 设置 `version=1` 并记录当前 `contract_hash`
    - 当检测到某 `id` 的 `contract_hash` 与映射中的不一致时，推导为 `version++` 并更新记录
  - 与 Phase 2 的 `build-index` 协作：在后续构建中维护该版本映射（本阶段验证器可独立维护一次临时更新）
- 校验矩阵：
  - `strict` 函数 + `strategy="latest""` → 违规，报错（`forbid_latest_for_strict: true`）
  - 显式版本绑定：`binding.l3_version == actual_version` → 通过；否则 → 版本不匹配
  - `strategy="latest"` 且 `strictness in {standard, light}` → 通过（不比较版本）
- 报告结构：
  - `valid`: 通过项列表
  - `violations`: 包含：`version_mismatch`、`strict_forbid_latest`、`missing_binding_info`
  - 统计计数与人类可读摘要

## CLI 集成
- 扩展 `harbor/cli/main.py`：新增命令
  - `harbor ddt validate [--module <path>] [--func <id>]`：
    - 从 `test_roots` 扫描绑定 → 加载索引与版本映射 → 校验并输出报告
  - `harbor ddt rebuild-map`（可选）：
    - 依据当前 `l3_index.json` 重新生成/更新 `.harbor/cache/l3_hash_map.json`（便于版本稳定化）

## L3 Docstring（概要）
- `harbor_ddt_target`（public, strict）：描述绑定策略/参数含义与异常（错误策略时抛 `ValueError` 可选）
- `DDTScanner.scan_tests`（internal, standard）：输入/输出与解析限制（仅常量参数）
- `DDTValidator.validate`（public, strict）：明确策略矩阵与返回的 `DDTReport` 字段

## 测试计划
- `tests/test_ddt_validate.py`
  1) 绑定 strict 函数且 `l3_version` 匹配：应通过
  2) 绑定 strict 函数但 `l3_version` 不匹配：报 `version_mismatch`
  3) 绑定 non-strict 函数使用 `strategy="latest"`：通过
  4) 绑定 strict 函数使用 `strategy="latest"`：报 `strict_forbid_latest`
  5) 初次创建版本映射：`l3_hash_map.json` 生成，后续 contract 变化触发 `version++`

## 风险与缓解
- AST 扫描的表达式复杂性：MVP 限定常量参数；后续可扩展运行时元数据读取（导入测试模块）
- 版本映射与索引协作：本阶段由验证器维护最小可用的映射，后续在 `build-index` 中统一更新（与 Phase 2 衔接）
- 严格度来源：从 `l3_index.json` 读取 `strictness` 字段，若缺失则默认 `standard`

## 交付物
- `harbor/test_utils.py`（装饰器）
- `harbor/core/ddt.py`（扫描器 + 验证器）
- `harbor/cli/main.py`（`ddt validate` 命令）
- `.harbor/cache/l3_hash_map.json`（版本映射存储）
- `tests/test_ddt_validate.py`（策略矩阵与版本比对用例）

请确认以上方案，我将据此完成实现与测试，并展示验证结果。

# 确认执行：Phase 4 启动

方案评估通过。引入 `l3_hash_map.json` 来持久化版本历史是一个非常棒的设计。

## 启动 Phase 4: DDT 子系统

请按你的计划执行，并注意以下 3 点工程细节：

### 1. 版本推导逻辑 (Read-Only Safety)
在 `DDTValidator.validate` 运行过程中：
- 如果发现 `l3_index` 中的 `contract_hash` 与 `hash_map` 中的记录不一致：
  - **不要** 立即修改磁盘上的 `l3_hash_map.json`。
  - **而是** 在内存中认为 "Current Version = Stored Version + 1"。
  -以此 "Target Version" 去校验测试代码中的绑定。
  - 报错信息应提示：`Version Mismatch: Contract changed. Expected v{N+1}, found v{N}.`

### 2. AST 扫描的鲁棒性
- 你的扫描器只支持常量参数。请确保如果用户写了动态参数（如 `l3_version=get_version()`），扫描器应**优雅地忽略**或报 Warning，而不是抛出异常导致整个流程崩溃。

### 3. Dogfooding (必须)
- 在实现完装饰器后，请立即修改 `tests/test_sync_engine.py`。
- 将 `test_drift_detection` (或类似测试) 绑定到 `harbor.core.sync.SyncEngine.check_status` 上。
- 设置 `l3_version=1`。
- 运行 `harbor ddt validate` 验证它能通过。

**交付物清单确认**：
- `harbor/test_utils.py`
- `harbor/core/ddt.py`
- `harbor/cli/main.py`
- `.harbor/cache/l3_hash_map.json` (自动生成)

请开始编码。完成后，请展示 `harbor ddt validate` 命令在本项目上的运行输出。
## 任务理解
- 在 `harbor/utils` 中新增 `format_size(bytes: int) -> str`，以 Strict L3 规范实现，并完成从编码→索引→DDT→L2→Diary 的全链路演练与验证。

## 上下文加载
- 代码结构已存在：`harbor/cli/main.py`、`harbor/core/*`、`harbor/adapters/python/*`、`harbor/utils/__init__.py`、`tests/*`、`.harbor/config.yaml`、`.harbor/cache/l3_index.json`。
- CLI 命令存在：`status / build-index / gen l2 / ddt validate / diary log`。

## 技术要点
- L3 Strict Docstring，包含 `@harbor.scope: public`、完整 Args/Returns/Raises；只变更 Contract 才升级 `l3_version`。
- DDT 绑定使用显式版本：`@harbor_ddt_target(func="harbor.utils.format_size", l3_version=1)`。
- L2 README 由生成命令产出，视图只读；索引为 `.harbor/cache` 的构建产物。

## 实施步骤
### Step 1｜初始状态检查
- 运行：`harbor status`
- 期望：Workspace clean（可能存在 Untracked）。将截图/文本记录输出。

### Step 2｜编码与 L3
- 新增文件：`harbor/utils/formatting.py`
- 导出：在 `harbor/utils/__init__.py` 增加 `from .formatting import format_size`
- 实现 `format_size(bytes: int) -> str`：
  - 单位：`Bytes/KB/MB`，边界按 1024 转换，保留 2 位小数（如 `1536 -> 1.50 KB`，`1048576 -> 1.00 MB`）。
  - 负数参数抛 `ValueError`。
  - L3 Strict Docstring：`@harbor.scope: public`、Google 风格、列出 Raises。

### Step 3｜状态检测新增
- 运行：`harbor status`
- 期望：显示 `? Untracked` 或 `M Modified`，记录输出。

### Step 4｜索引纳管
- 运行：`harbor build-index`
- 再次运行：`harbor status`
- 期望：索引更新到 `.harbor/cache/l3_index.json`，状态回到 clean，记录输出。

### Step 5｜DDT 测试编写
- 新增文件：`tests/test_utils_format.py`
- 绑定：`@harbor_ddt_target(func="harbor.utils.format_size", l3_version=1)`
- 测例：
  - `0 -> "0 B"`、`1024 -> "1.00 KB"`、`1536 -> "1.50 KB"`、`1048576 -> "1.00 MB"`
  - 负数触发 `ValueError`
- 运行：`pytest -q`，记录输出。

### Step 6｜DDT 验证
- 运行：`harbor ddt validate`
- 期望：新函数绑定状态 ✅ Valid，记录输出。

### Step 7｜L2 生成
- 运行：`harbor gen l2 --module harbor/utils --write`
- 期望：生成/更新 `harbor/utils/README.md`，包含新函数条目，记录输出。

### Step 8｜Diary 留存
- 运行：`harbor diary log --type feature --summary "新增 format_size 工具函数" --importance normal --visibility public`
- 期望：写入 `specs/diary/2025-12.jsonl` 当前月条目，记录输出。

## 交付物
- 每一步的 CLI 输出文本（或截图），整理成演练日志。
- 新增/更新的文件路径清单与内容摘录：
  - `harbor/utils/formatting.py`（含 Strict L3 Docstring）
  - `harbor/utils/__init__.py`（导出）
  - `tests/test_utils_format.py`（DDT 绑定）
  - `.harbor/cache/l3_index.json`（索引更新）
  - `harbor/utils/README.md`（L2 视图）
  - `specs/diary/2025-12.jsonl`（Diary 条目）

## 风险与应对
- 函数 ID 规范不匹配：若 `harbor.utils.format_size` 未被适配器正确索引，回退为在 `__init__.py` 中定义函数，确保解析路径简化。
- L2 抖动：通过现有 `l2_meta.json` 控制展示顺序，避免不必要 diff。
- Pytest 环境：若依赖未安装，先安装 dev 依赖或使用本地 venv。

## 验收与报告
- 所有命令可稳定执行且输出符合预期；DDT 验证通过；L2 与 Diary 产物就绪。
- 如遇报错或体验不顺畅，将记录为 Bug Report 并附上复现步骤与建议修复。

# 确认执行：Phase 6.5 全链路演练 (Action)

计划评估通过。特别是对 "Untracked/Modified" 状态的检查步骤，非常关键。

## 执行指导

### 1. ID 绑定原则 (针对你提出的风险)
在 **Step 5 (DDT 绑定)** 中，请使用函数的**物理路径 ID**：
`func="harbor.utils.formatting.format_size"`
不要使用 `__init__.py` 导出的缩写路径，以确保 Indexer 能准确匹配。

### 2. 演练心态 (Fix-it-now)
如果在演练过程中发现报错（例如 Adapter 解析失败、CLI 崩溃），**请立即修复代码**，这正是 Dogfooding 的目的。不要只记录 Bug，要修复它，并在演练日志中注明“已修复问题：...”。

### 3. 输出要求
请按顺序输出 Step 1 到 Step 8 的执行结果。
对于 **Step 3 (Status)** 和 **Step 6 (Validate)**，请务必展示 CLI 的原始输出文本，我需要检查格式是否直观。

**行动：**
Start the Engine. 请开始演练。
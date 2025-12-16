# 确认循环

## 1. 任务理解
- 目标：完成 Phase 0（项目基建脚手架）与 Phase 1（Python AST 适配器 MVP）。
- 要求：遵循 Harbor-spec v1.0.2 Dogfooding 原则；核心组件使用 `strict` L3 Docstring（公共 API 严格绑定）。
- 交付：可解析 Python 源文件，输出函数/方法的 `name / signature_hash / docstring_raw_hash / contract_hash`，并含基础测试。

## 2. 上下文加载
- 已阅读并对齐两份文档：
  - `docs/harbor-spec设计蓝图 v1.0.2.md`
  - `docs/harbor-spec分阶段实施计划 v1.0.2.md`
- 关键约束：
  - 去中心化索引（构建到 `.harbor/cache/**`，不入库）。
  - Python-only 参考实现；核心/适配器/CLI 属于 `strict` 范畴。
  - L3 区分 Contract/Decoration；初版可采用简化提取策略并预留接口。
- 当前仓库状态：主要为文档与规则文件，尚未有 `harbor/` 代码目录，需要自举脚手架。

## 3. 执行计划（Phase 0 → Phase 1）

### 3.1 目录与文件（Phase 0）
将创建以下结构与模板文件：
- `harbor/cli/__init__.py`
- `harbor/core/__init__.py`
- `harbor/adapters/__init__.py`
- `harbor/adapters/python/__init__.py`
- `harbor/utils/__init__.py`
- `specs/diary/`（空目录，按月轮转写入 JSONL）
- `.harbor/config.yaml`（v1.0.2 模板，`profile=enforce_l3`，`code_roots`/`test_roots` 指至 `modules/*/src`、`modules/*/tests`；本仓初期可指向 `harbor/**` 以便自举）
- `tests/__init__.py`

说明：不改动现有 `.gitignore`；后续如需将 `.harbor/cache/**` 加入忽略，将在 CLI/init 步骤处理。

### 3.2 Python AST 适配器 MVP（Phase 1）
- 新建：`harbor/adapters/python/parser.py`
- 类：`PythonAdapter`
- 公开方法（严格 L3）：
  - `parse_file(file_path: str) -> list[FunctionContract]`
    - 解析指定 Python 文件，返回函数/方法信息列表。
- 内部辅助（标准 L3）：
  - `_extract_functions(tree: ast.AST, module_qual: str) -> list[FunctionContract]`
  - `_signature_hash(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> str`
  - `_docstring_hashes(doc: str | None) -> tuple[str | None, str | None]`
  - `_contract_area(doc: str) -> str`（简化版：基于 Google 风格 `Args/Returns/Raises` 区段提取；找不到则回退为完整 docstring）
- 数据结构：
  - `FunctionContract`（dataclass）字段：
    - `id: str`（如 `harbor.adapters.python.parser.PythonAdapter.parse_file` 或 `package.module.Class.method`）
    - `name: str`
    - `qualified_name: str`
    - `signature_hash: str`
    - `docstring: str | None`
    - `docstring_raw_hash: str | None`
    - `contract_hash: str | None`
    - `lineno: int`
    - `col_offset: int`
    - `scope: "public" | "internal" | None`（从 Docstring tag 解析）
    - `strictness: "strict" | "standard" | "light" | None`（从 Docstring tag 解析）

### 3.3 L3 Docstring（Dogfooding：严格）
- 为 `PythonAdapter.parse_file` 编写 `strict` 级 Docstring，包含：
  - 功能/使用场景/依赖描述
  - `@harbor.scope: public`
  - `@harbor.l3_strictness: strict`
  - `@harbor.idempotency: read-only`
  - `Args`/`Returns`/`Raises`（Google 风格）
- 辅助方法使用 `standard` 级 Docstring，标注 `@harbor.scope: internal`。

### 3.4 验证（测试）
- 新建：`tests/test_adapter_basic.py`
- 测试内容：
  - 使用 `PythonAdapter` 解析自身文件 `harbor/adapters/python/parser.py`。
  - 断言：
    - 能找到 `PythonAdapter.parse_file` 的条目；
    - `docstring` 非空；
    - `docstring_raw_hash` 与（简化）`contract_hash` 可计算且为非空字符串；
    - `signature_hash` 存在且随参数列表变化而变化（通过构造一个辅助函数对比）。

## 4. 接口设计（概要）

### 4.1 `PythonAdapter`
- `parse_file(file_path: str) -> list[FunctionContract]`
  - 输入：文件路径（绝对或相对）。
  - 行为：读取源代码 → `ast.parse` → 遍历模块、类、函数 → 生成 `FunctionContract` 列表。
  - 输出：列表项包含签名哈希与 Docstring 双哈希（raw/contract）。
  - 失败：
    - 文件读取异常 → `IOError`；
    - AST 解析异常 → `SyntaxError`；
    - 配置错误（后续适配）→ `ConfigError`（预留）。

### 4.2 哈希策略（MVP）
- `signature_hash`：
  - 组成：参数名顺序 + 位置参数/关键字参数/仅限关键字/可变参数标记 + 是否存在默认值（不包含默认值具体文本）。
  - 归一化：去空白，统一分隔符；`sha256`。
- `docstring_raw_hash`：
  - 组成：去除尾部空白的完整 Docstring 文本；`sha256`。
- `contract_hash`（简化版）：
  - 组成：提取 `Args/Returns/Raises` 与 `@harbor.*` tag 的文本；如提取失败则回退为完整 Docstring；`sha256`。

### 4.3 标识符生成
- `qualified_name`：`<module_path>.<Class?>.<func>`（基于文件相对路径转换为点分路径）。
- `id`：与 `qualified_name` 等价；后续可加入包名策略与模块根（与 `.harbor/config.yaml` 的 `code_roots` 对齐）。

## 5. 风险与决策
- 合同区提取策略为简化版，可能误判装饰性文本为契约；将来替换为更健壮的解析器。
- 签名哈希不包含默认值具体内容，可能漏检某些变更；权衡为“降低因默认值微调导致的噪音”，若后续需要可升级策略。
- `qualified_name` 的模块根定位需与仓库结构一致；当前以文件相对路径推导，后续与 `config.yaml` 对齐。

## 6. 需要你确认
- 文件/目录创建列表是否满足期望？
- `PythonAdapter` 接口与哈希策略（特别是 `contract_hash` 简化提取）是否同意作为 Phase 1 MVP？
- `.harbor/config.yaml` 初始模板是否按 `enforce_l3` 自举，代码根指向 `harbor/**`？

> 确认后我将按以上计划实现代码与测试，并在本地完成验证。

# 确认执行：Phase 0 & Phase 1 启动

我已评估你的计划，批准执行。请按原计划推进，并补充以下 3 点修正：

1. **依赖管理**：在 Phase 0 创建 `pyproject.toml`，加入 `pyyaml` 和 `pytest` 依赖。
2. **Hash 回退策略**：在计算 `contract_hash` 时，如果无法解析出 Args/Returns 区段，**必须**直接使用 `docstring_raw_hash` 的值，确保安全兜底。
3. **ID 格式**：确保 `id` 和 `qualified_name` 使用点分格式（如 `harbor.adapters.python.parser`），并处理好跨平台路径兼容性。

**行动：**
请现在开始编写代码。
完成 Phase 0（目录/配置）和 Phase 1（Adapter 实现）后，请运行你设计的 `tests/test_adapter_basic.py` 进行自测，并向我展示测试结果和 `PythonAdapter` 的源代码（重点展示其 L3 Docstring）。
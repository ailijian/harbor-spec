# 确认循环

## 1. 任务理解
- 基于已完成的 `PythonAdapter`，实现去中心化索引构建器：`IndexBuilder`。
- 输出 `.harbor/cache/l3_index.json`，支持增量构建与实现指纹 `body_hash`。
- 保持 Dogfooding：公共方法使用 strict L3 Docstring，辅助方法使用 standard。
- 提供 CLI 命令 `harbor build-index` 调用 IndexBuilder。

## 2. 上下文加载
- 参考 v1.0.2 设计：索引缓存不入库；严格度与 DDT 策略由后续 Sync 使用。
- 当前仓库已有 `.harbor/config.yaml`（profile=enforce_l3；code_roots: `harbor/**`）。

## 3. IndexBuilder 接口设计（L3 概要）

### 3.1 `class IndexBuilder`
- 位置：`harbor/core/index.py`
- 依赖：
  - `PythonAdapter`（`harbor.adapters.python.parser.PythonAdapter`）
  - 标准库：`ast`, `hashlib`, `json`, `tokenize`, `io`, `pathlib`, `time`

#### `build(incremental: bool = True) -> IndexReport`
- Strict L3 Docstring（概要）：
  - 功能：扫描 `code_roots` 下的 Python 文件，解析 L3 元数据，计算 `signature_hash` 与 `body_hash`，并将结果写入 `.harbor/cache/l3_index.json`。支持增量，仅更新变更文件条目。
  - 使用场景：`harbor build-index`、`harbor status` 自动构建。
  - 依赖：`PythonAdapter.parse_file`、文件 mtime 与 `file_hash`。
  - `@harbor.scope: public`
  - `@harbor.l3_strictness: strict`
  - `@harbor.idempotency: once`
  - Args：
    - `incremental (bool)`: 是否启用增量构建，默认 True。
  - Returns：
    - `IndexReport`: 统计（扫描文件数、更新条目数、跳过数、耗时、缓存路径）。
  - Raises：
    - `ConfigError`: 配置无效或缓存目录不可写。
    - `IOError`: 读取/写入索引缓存失败。

#### 辅助方法（Standard L3）
- `_iter_py_files() -> list[Path]`
  - 基于 `code_roots` 展开 glob，返回所有 `*.py` 文件路径。
- `_load_cache() -> dict`
  - 读取 `.harbor/cache/l3_index.json`，不存在则返回空结构。
- `_save_cache(cache: dict) -> None`
  - 将更新后的索引写回缓存文件。
- `_file_hash(p: Path) -> str`
  - 计算文件级 `sha256`（原始字节），用于增量判断。
- `_compute_body_hash(source: str, fn_node: ast.AST) -> str`
  - 核心：实现指纹。
  - 步骤：
    1) 去除函数体首个 Docstring（若存在 `Expr(str)`）。
    2) 基于 `tokenize` 过滤掉 `COMMENT/NL/NEWLINE/INDENT/DEDENT` 与空白，仅保留语义 token（NAME, NUMBER, STRING, OP 等）。
    3) 归一化串联为稳定序列 → `sha256`。
- `_index_entry(fc: FunctionContract, body_hash: str, file_path: Path) -> dict`
  - 将适配器条目与 `body_hash` 拼装为索引项。

### 3.2 索引 JSON 结构（示例）
```jsonc
{
  "meta": {
    "generated_at": "2025-12-16T10:00:00Z",
    "schema_version": "1.0.2"
  },
  "files": {
    "harbor/adapters/python/parser.py": {
      "mtime": 1734300000.123,
      "file_hash": "sha256:...",
      "items": [
        {
          "id": "harbor.adapters.python.parser.PythonAdapter.parse_file",
          "qualified_name": "harbor.adapters.python.parser.PythonAdapter.parse_file",
          "name": "parse_file",
          "signature_hash": "...",
          "body_hash": "...",
          "contract_hash": "...",
          "docstring_raw_hash": "...",
          "scope": "public",
          "strictness": "strict",
          "lineno": 29
        }
      ]
    }
  }
}
```

### 3.3 增量构建策略
- 若 `incremental` 为 True：
  - 读取旧缓存，比较目标文件的 `mtime` 与 `file_hash`：两者均未变 → 跳过解析，复用旧 `items`；否则 → 调用 `PythonAdapter.parse_file` 重新解析并重建条目。
- 若 `incremental` 为 False：
  - 全量重建所有文件索引，并覆盖旧缓存。

## 4. CLI 集成
- 位置：`harbor/cli/main.py`
- 采用标准库 `argparse`（避免额外依赖）：
  - 命令：`build-index`（可选 `--no-incremental` / `--code-root <glob>` 覆盖）
  - 行为：实例化 `IndexBuilder`，调用 `build()`，打印统计与缓存路径。
- 未来可在 `pyproject.toml` 添加 entry-point，将命令注册为 `harbor`。

## 5. 测试计划
- 文件：`tests/test_index_builder.py`
- 用例：
  1) 初次构建：在临时目录创建示例模块文件，运行 `build(incremental=True)`，断言缓存生成且包含条目。
  2) 增量不变：不修改文件，二次构建应跳过解析（统计中 `skipped >= 1`）。
  3) 仅改 Docstring：`body_hash` 不变（若实现不涉及 docstring 内容）；`contract_hash/docstring_raw_hash` 可能变；索引项更新。
  4) 改实现代码：`body_hash` 变化；索引项更新。

## 6. 风险与缓解
- `tokenize` 归一化可能在字符串/格式细节上仍有微弱抖动：后续可采用 AST 正规化（如 `ast.unparse` 再 token 化）提高稳定性。
- 路径与 glob 在 Windows/Unix 的差异：统一使用 `pathlib.Path` 与点分 `qualified_name` 生成逻辑（沿用 PythonAdapter）。
- 缓存膨胀：按文件组织 `items`，支持增量，避免全量重写造成性能问题。

## 7. 需要你确认
- 是否同意 `IndexBuilder.build` 的 strict L3 设计与参数/返回值？
- `body_hash` 的实现采用 `tokenize` 过滤策略是否符合 Phase 2 目标？
- CLI 使用 `argparse` 最小实现是否可接受？

> 确认后我将据此实现 `harbor/core/index.py`、`harbor/cli/main.py` 与 `tests/test_index_builder.py` 并完成验证。

# 确认执行：Phase 2 启动

方案已评估，批准执行。设计思路非常清晰，请按计划推进。

**补充 3 点具体要求：**

1.  **Entry Point**: 请在 `pyproject.toml` 中添加 `[project.scripts]` 配置，将 `harbor` 命令指向 `harbor.cli.main:main`（假设入口函数名为 main）。
2.  **Body Hash 鲁棒性**: 在实现 `_compute_body_hash` 时，务必编写单元测试验证：**仅修改函数内的 Docstring 或注释，`body_hash` 必须保持不变。** 这是 v1.0.2 检测“实现漂移”的核心机制。
3.  **JSON 序列化**: 在写入 `l3_index.json` 时，请使用 `ensure_ascii=False` 和 `indent=2`，确保生成的索引文件对人类（和 Git Diff，虽然不入库）友好，方便调试。

**行动：**
请开始编码。完成后，请展示 `tests/test_index_builder.py` 的执行结果，重点展示“修改文档不影响 Body Hash”的测试用例通过情况。
## 任务理解
- 目标：先完成 DX 稳定化（可用 `harbor` 命令、索引干净），再实现 AI 语义审计（Soft Check）。
- 范围：新增 `harbor/core/audit.py` 与 CLI `harbor audit --semantic [--diff-only]`，提供 MockProvider 与测试闭环。

## 上下文加载
- CLI 使用 `argparse`（`harbor/cli/main.py`），已有 `status/build-index/ddt/gen/diary` 子命令。
- `SyncEngine.check_status()` 返回 `StatusReport`，含 `drift/modified/contract_changed/untracked/missing` 列表与 `file_path`。
- 适配器 `PythonAdapter.parse_file()` 返回 `FunctionContract`（含 `id/name/docstring/contract_hash/lineno`）。

## 确认循环
- 1. 任务：实现 `SemanticGuard`（Strict L3），将 L3 契约与源码送入 LLM Provider，输出审计结果。
- 2. 上下文：使用 `FunctionContract`（契约区来源于解析器）与源代码文本。
- 3. 执行计划：
  - Step A：DX 稳定化（`pip install -e .` → `harbor build-index` → `harbor status`，确保 clean）。
  - Step B：实现 `audit.py` 与 Provider 抽象；新增 CLI `audit --semantic`；默认仅审计 `drift/modified`（支持 `--diff-only=false` 全量）。
  - Step C：编写 `tests/test_audit.py`（MockProvider 恒返回 OK），验证 CLI 输出与 Soft Check 语义。
- 4. 风险：Provider 超时或返回异常时不应阻断；统一为 Soft Check。

## 接口设计
- `class AuditResult`：`status: Literal["OK","MISMATCH","ERROR"]`、`reason: Optional[str]`、`provider: str`、`func_id: str`。
- `class LLMProvider`：`name: str`、`def infer(prompt: str) -> str`（抽象）。
- `class MockProvider(LLMProvider)`：`infer()` 恒返回 `[OK]`；用于测试与默认运行。
- （可选）`class OpenAIProvider(LLMProvider)`：从 `OPENAI_API_KEY` 读取，若未设置则抛并回退 Mock；MVP 可留空实现。
- `class SemanticGuard`：
  - `def build_prompt(contract: FunctionContract, source_code: str) -> str`
  - `def audit(contract: FunctionContract, source_code: str, provider: LLMProvider) -> AuditResult`

## Prompt 模板
```
You are a code auditor. Check if the implementation matches the docstring contract.
Docstring:
{doc}
Code:
{code}
Focus on: Args, Returns, Raises.
If mismatch, output [MISMATCH]: reason. Else output [OK].
```
- 解析规则：
  - 若返回文本包含 `[MISMATCH]` → `status="MISMATCH"`，`reason` 为后续文本。
  - 若包含 `[OK]` → `status="OK"`。
  - 否则 → `status="ERROR"`，`reason="unrecognized output"`。

## CLI 集成
- 新增子命令：`audit`，选项：`--semantic`、`--diff-only`（默认 `true`）。
- 执行流：
  - 调用 `SyncEngine.check_status()` 获取候选函数：`diff-only=true` → `drift + modified`；否则包含 `contract_changed`。
  - 对每个 `StatusEntry`：读取 `file_path` 源码；使用 `PythonAdapter.parse_file(file_path)` 找到匹配 `FunctionContract`；交给 `SemanticGuard.audit()`。
  - 输出：
    - `Harbor Semantic Audit:`
    - `OK func_id` 或 `POSSIBLE_SEMANTIC_DRIFT func_id :: reason`
  - 退出码：始终 0（Soft Check）。

## 测试交付
- `tests/test_audit.py`：
  - 构造一个最小函数与 Docstring；MockProvider 返回 `[OK]`；断言 CLI 输出含 `OK`。
  - 人为制造不一致（例如 Docstring 声称抛 `ValueError`，代码不抛）；将 MockProvider覆写为返回 `[MISMATCH]: Raises not implemented`；断言输出含 `POSSIBLE_SEMANTIC_DRIFT`。
  - 验证 `--diff-only` 行为：在 `status` 无差异时不审计；有差异时审计。

## 稳定化步骤
- 运行：`pip install -e .`（开发安装，提供 `harbor` 可执行）。
- 运行：`harbor build-index`（全量构建至 `.harbor/cache/l3_index.json`）。
- 运行：`harbor status`（预期 `No changes detected.`；若仍有 Untracked，补齐 Strict L3 Docstring 或排除路径）。

## 验收标准
- 命令入口可直接使用 `harbor`；`status` 输出干净。
- `audit --semantic` 可运行，默认扫描 `drift/modified`；出现 MISMATCH 时以 `POSSIBLE_SEMANTIC_DRIFT` 标记；退出码为 0。
- 测试通过：`tests/test_audit.py` 使用 MockProvider 验证 OK 与 MISMATCH 两路径。

## 下一步
- 审计报告汇总：支持 `--format markdown` 输出汇总到文件；迭代在 PR 中作为评论使用（后续增强）。


# 确认执行：Phase 7 启动 (Final Phase)

方案评估通过。接口设计合理，"Soft Check" 策略符合预期。

## 启动 Phase 7: AI 语义审计

请按你的计划执行，并注意以下 3 个技术细节：

### 1. 源码提取 (Source Extraction)
在构建 Prompt 时，我们需要精准的函数源码。
- 请在 `SemanticGuard` 中使用 `ast.get_source_segment(source_code, node)` 来提取目标函数的具体实现代码。
- 不要发送整个文件内容，以节省 Token 并减少干扰。

### 2. Provider 配置
对于 `OpenAIProvider` (即使是 MVP 留空实现)，请预留好环境变量读取逻辑：
- `HARBOR_LLM_PROVIDER`: 默认 `mock`，可选 `openai`。
- `HARBOR_OPENAI_API_KEY`: 用于鉴权。
- `HARBOR_OPENAI_MODEL`: 默认 `gpt-4o-mini` 或 `gpt-3.5-turbo` (低成本模型足矣)。

### 3. DX 稳定化 (必须先执行)
在写代码前，务必先执行你的 Step A：
1. `pip install -e .`
2. `harbor build-index`
3. `harbor status` -> 确保 Clean。
   *(如果有 Untracked 文件，请为它们补充 minimal strict docstring 并 commit 进索引，或者将它们加入 .gitignore)*

**Dogfooding 验证:**
完成代码后，请进行一次“自主演练”：
1. 运行 `harbor audit --semantic` (使用 MockProvider)，预期输出 OK。
2. **人为制造 Drift**: 修改 `harbor/core/sync.py` 中的某个逻辑（例如改个变量名），但不改 Docstring。
3. 再次运行 `harbor audit --semantic`，确认 CLI 能识别出这个 Drift 并触发审计（MockProvider 返回 OK，所以 CLI 会显示 OK，但关键是**触发了审计流程**）。

**交付物清单**:
- `harbor/core/audit.py`
- `harbor/cli/main.py`
- `tests/test_audit.py`

请开始 Harbor v1.0.2 的最后一公里。
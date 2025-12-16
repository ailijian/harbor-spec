## 目标
- 增强 `audit --semantic` 的可观测性（Provider 名称、调试输出）。
- 验证 `.env` 加载与 Provider 选择逻辑，避免隐式回退导致假阴性。
- 在现有实现基础上支持真实 OpenAI 兼容接口（DeepSeek 等）。

## 修改点
- CLI：`harbor/cli/main.py`
  - 在审计头部打印 Provider 名称：`Harbor Semantic Audit (Provider: <name>)`。
  - 新增 `--debug` 选项：打印完整 Prompt 与 LLM 原始返回文本。
- 审计核心：`harbor/core/audit.py`
  - `AuditResult` 增加 `prompt` 与 `raw_output` 字段，便于 CLI Debug。
  - `resolve_provider()` 保持 `.env` 加载并选择 `openai/mock`，未知 Provider 明确回退。
  - `OpenAIProvider.infer()` 返回 `[ERROR]: <details>` 软失败，不抛异常。

## 验证流程
1. 检查 `.env`：当前为 `HARBOR_LLM_PROVIDER=baidu`，将导致回退 Mock。
2. 试跑：`harbor audit --semantic --debug`，观察 Provider 打印与 Prompt/Raw 文本。
3. 切换真实调用：设置 `HARBOR_LLM_PROVIDER=openai`，`HARBOR_LLM_BASE_URL=https://api.deepseek.com`，填入有效 `HARBOR_LLM_API_KEY` 与模型名。
4. 再次运行：`harbor audit --semantic --debug`，验证当代码与契约冲突时出现 `POSSIBLE_SEMANTIC_DRIFT`。

## 交付物
- 更新的 `harbor/cli/main.py` 与 `harbor/core/audit.py`。
- `.env.example` 模板（已存在），指导用户配置。
- 运行日志：包含 Provider 名称与 Debug 输出。

## 风险与提示
- 若使用 DeepSeek 等 OpenAI 兼容 API，错误信息可能为认证失败（例如 "Authentication Fails"），此时 CLI 会显示 `ERROR` 行并保持软检查。
- 若 `.env` Provider 未设为 `openai`，将显示 `Provider: mock` 并产生假阴性；Debug 输出可快速定位该问题。

# 确认执行：Phase 7.5 可观测性增强

方案评估通过。我们现在的首要任务是**让“假阴性”无处遁形**。

## 执行指导

### 1. 代码修改 (Observability)
请按你的计划修改 `harbor/core/audit.py` 和 `harbor/cli/main.py`：
- **AuditResult**: 增加 `prompt` (str) 和 `raw_output` (str) 字段。
- **CLI Header**: 必须在 `harbor audit` 输出的第一行显示：
  `Harbor Semantic Audit (Provider: <Actual_Provider_Name> Model: <Model_Name>)`
- **Debug Mode**: 当 `--debug` 开启时，打印：
  - [DEBUG] Full Prompt: ...
  - [DEBUG] Raw LLM Response: ...

### 2. 配置加载 (Critical)
确保在 `harbor/core/audit.py` 或 `config.py` 的顶层导入时调用了 `load_dotenv()`。
- 如果 `HARBOR_LLM_PROVIDER` 不为 `openai`，请打印一条 Warning 日志（在 debug 模式下），提示 "Falling back to MockProvider due to config".

### 3. 验证步骤 (The Catch)
代码修改完成后，请执行以下操作并展示输出：
1.  **检查环境**: 打印当前加载的 Provider 名称。
2.  **复现 Bug**: 针对被修改了逻辑的 `harbor.core.diary.DiaryManager.log` (if summary -> if not summary) 运行审计。
    命令: `harbor audit --semantic --debug`
3.  **预期结果**:
    - Provider 应为 `OpenAIProvider` (前提是用户已配置 .env)。
    - Raw Output 应包含 LLM 对逻辑错误的描述。
    - 最终状态应为 `POSSIBLE_SEMANTIC_DRIFT`。

**行动：**
请增强系统的眼睛，然后帮我抓住那个 Bug。
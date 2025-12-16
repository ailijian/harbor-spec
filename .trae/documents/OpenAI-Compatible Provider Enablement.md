## 目标
- 允许用户通过 `.env` 配置任意兼容 OpenAI SDK 的模型与服务（例如 DeepSeek、Moonshot、Azure OpenAI 等）。
- 在 CLI 显示实际 Provider 与 Model，并保持软失败与调试能力。

## 修改点
- `harbor/core/audit.py`
  - 将 `OpenAIProvider` 改为通用 OpenAI-Compatible 提供者：接受 `provider_name`、`base_url`、`api_key`、`model`。
  - 在 `resolve_provider()` 中：除 `mock` 外，一律按 OpenAI-Compatible 处理；从 `.env` 加载并使用 `HARBOR_LLM_*` 变量。
  - 为 `MockProvider` 增加 `model='n/a'` 字段，统一显示。
- `harbor/cli/main.py`
  - 审计头部打印：`Harbor Semantic Audit (Provider: <name> Model: <model>)`。

## 验证
1. 读取 `.env`（当前为 DeepSeek）：`HARBOR_LLM_PROVIDER=deepseek`、`HARBOR_LLM_BASE_URL=https://api.deepseek.com`、`HARBOR_LLM_MODEL=deepseek-chat`、`HARBOR_LLM_API_KEY=...`。
2. 运行 `harbor audit --semantic --debug`：
   - 头部显示 `Provider: deepseek Model: deepseek-chat`
   - 若认证失败，输出 `ERROR ...` 行，并继续软检查。

## 风险控制
- 网络或鉴权异常统一转为 `[ERROR]: ...` 文本，不抛异常、不改变退出码。
- 兼容所有 OpenAI SDK 接口规范的服务；非兼容服务（如非 OpenAI 风格）仍需单独 Provider。

## 交付物
- 更新的 `harbor/core/audit.py` 与 `harbor/cli/main.py`，无需新增依赖。
- 运行演示：头部与调试输出展示实际 Provider/Model。
## 目标
- 为审计 Prompt 提供多语言支持（en/zh），通过 `.env` 的 `HARBOR_LANGUAGE` 切换。

## 改动点
- `harbor/core/audit.py`：
  - 定义 `PROMPT_TEMPLATES = { 'en': ..., 'zh': ... }`
  - `SemanticGuard.build_prompt` 读取 `HARBOR_LANGUAGE`（默认 `en`），按模板格式化
- `.env`：添加 `HARBOR_LANGUAGE=zh` 用于验证

## 验证
- 运行 `harbor audit --semantic --debug`，观察头部 Provider/Model 与 Debug Prompt 内容为中文；若存在不一致，Reason 为中文；一致则为 OK/No targets。

## 风险
- 保持输出标记 `[MISMATCH]`/`[OK]` 英文以兼容解析；网络或鉴权错误仍为软失败。

## 交付物
- 更新后的 `harbor/core/audit.py`
- 运行日志展示中文审计提示（或 No targets）
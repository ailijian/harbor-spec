# Semantic Audit Preview Demo

这个示例专门演示 `semantic_audit_preview` 的最小可见路径。

当前实现里，TypeScript semantic audit preview 只会对进入 semantic candidate set 的 TypeScript target 产生输出。  
这里故意保留一个没有 nearby JSDoc/TSDoc 的导出函数，用来触发：

- `preview=true`
- `eligible=false`
- `eligibility_reason=behavior_contract_missing`
- `llm_called=false`

## What To Run

```powershell
python -m harbor.cli.main check --format jsonl
```

## Expected JSONL Excerpt

```json
{
  "status": "SKIPPED_NO_CONTRACT",
  "target_id": "typescript:E:/project/harbor-spec/examples/typescript-verification-preview/semantic-audit-preview/src/index.ts:function:noDoc",
  "file_path": "src/index.ts",
  "provider": "mock",
  "model": "n/a",
  "reason": "TypeScript semantic audit preview requires behavior contract evidence such as JSDoc/TSDoc.",
  "llm_called": false,
  "preview": true,
  "language": "typescript",
  "symbol_kind": "function",
  "eligible": false,
  "eligibility_reason": "behavior_contract_missing",
  "evidence_kinds": []
}
```

## Why This Demo Matters

- 它说明 `semantic_audit_preview` 不是默认 blocker。
- 它说明没有行为型契约证据时，系统会给出 explainability，而不是伪装成正式 gate。
- 它说明 preview path 可以在 `mock / deterministic` provider 下被稳定演示，不依赖真实 LLM 可用性。

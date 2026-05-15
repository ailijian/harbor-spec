# ADR｜v1.4.4 Sidecar-driven TypeScript DDT Preview

状态：Proposed  
日期：2026-05-15  
范围：TypeScript DDT Binding Preview / VerificationBinding / explainability-first governance

## 1. Context

`v1.4.3` 已经完成 TypeScript contract source 与 public boundary governance，但 TypeScript 仍未进入 Harbor 的验证层。  
`v1.4.4` 需要在以下前提下首次引入 TypeScript DDT preview：

- Python DDT zero regression。
- 默认 gate 不扩张。
- JSON / checkpoint / `harbor next` 只做 additive explainability。
- preview 结果必须 advisory-first、non-blocking。
- `target_id` 已经成为跨语言主标识，`func_id` 仍需保留给 Python 兼容路径。

此时存在两个方向：

- 直接做 Jest / Vitest AST inference 与测试体语义推断。
- 先做显式、可审阅、可版本化的 sidecar-driven binding preview。

## 2. Decision

`v1.4.4` 采纳 sidecar-driven TypeScript DDT Binding Preview，而不是 Jest / Vitest AST inference。

具体决策：

- 引入 language-neutral `VerificationBinding` foundation。
- TypeScript preview binding 采用 repo-local sidecar 作为 source of truth。
- preview binding 以 `target_id` 为主锚点；`func_id` 仅保留给 Python 兼容映射。
- sidecar 只声明治理关系，不声明 coverage proof，不解析测试体语义。
- MVP strategy 冻结为：
  - `preview_strict`
  - `preview_reference`
- validator 结果保持 advisory-only / non-blocking，并通过现有 `check` / `checkpoint` / `next` 进行 explainability 暴露。

## 3. Why

- sidecar 明确、可审阅、可版本化，符合 Harbor 对 source-of-truth 与治理证据分层的定位。
- sidecar 不依赖具体测试框架 AST，可避免把 `v1.4.4` 扩张成 Jest / Vitest 解析工程。
- 显式 binding 更容易实现 deterministic ordering、dedupe、路径归一化与跨平台稳定输出。
- sidecar 让 preview 能保持 opt-in、advisory-first，而不会误导用户认为 Harbor 已经拥有正式 TypeScript DDT gate。

## 4. Risks of the Rejected Path

如果直接走 Jest / Vitest AST inference：

- 容易把版本范围从 governance preview 扩张成 framework-aware parser 工程。
- 推断结果的不确定性会污染 explainability，并放大 false green / false negative 风险。
- 框架差异、测试体语义与 helper 包装会显著削弱 deterministic output。
- 很难保证 preview-only、non-blocking 的边界不被错误升级为准正式 gate。

## 5. Consequences

- Harbor 在 `v1.4.4` 获得了首个 TypeScript DDT preview 入口，但仍保持 formal gate 未支持。
- `VerificationBinding` 成为未来跨语言验证治理的基础抽象。
- `bindings_file` / `test_asset.path` / preview findings 可以通过统一的 deterministic 规则进入 CLI / JSON explainability。
- 未来是否引入框架 AST inference，将作为后续版本的独立评估主题，而不是在本版本混入。

## 6. Non-Goals

以下内容明确不属于 `v1.4.4`：

- 正式 TypeScript DDT gate
- Jest / Vitest AST inference
- coverage proof
- 自动 test-to-target 推断
- 通过 preview findings 扩大默认 blocking gate

## 7. Validation

Phase 4A 对应的治理收口包括：

- README / README.en / RELEASE 统一改写为 preview-first 口径
- AGENTS.md 与 DDT / contract 规则同步 sidecar-driven preview 边界
- generated context refresh 与 `verify-generated --changed` / `stale --ci` / `doctor --ci`

Phase 4B 仍需补完：

- `pytest`
- `harbor checkpoint --ci --format json --advice basic`
- `harbor verify-generated --all --ci --format json`
- Windows full-governance 与 Ubuntu matrix release acceptance

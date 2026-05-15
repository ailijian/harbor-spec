# ADR｜v1.4.4 Generalize Semantic Audit Foundation Before TypeScript Preview

状态：Proposed  
日期：2026-05-15  
范围：Semantic Audit Foundation / TypeScript advisory preview / provider-dependent preview governance

## 1. Context

在 `v1.4.3` 之前，Harbor 的 semantic audit 仍然主要是 Python-first 路径。  
`v1.4.4` 需要让 TypeScript 首次进入 semantic audit preview，但同时必须满足：

- Python semantic audit zero regression。
- preview 结果不能写 baseline truth。
- preview 结果不能成为默认 blocker。
- release acceptance 不能依赖真实 LLM 服务。
- TypeScript target 的 eligibility 必须可解释、可约束，而不是“见到类型就审计”。

如果直接在现有 Python-specific substrate 上叠加 TypeScript 特判，会把语言耦合进一步固化，并削弱后续跨语言扩展的一致性。

## 2. Decision

`v1.4.4` 先泛化 semantic audit foundation，再引入 TypeScript advisory preview。

具体决策：

- 抽象 language-neutral foundation：
  - `AuditSubject`
  - `AuditPromptContext`
  - `AuditEligibility`
- Python 适配到新 foundation，但保持外部行为语义不变。
- TypeScript preview 只对具备直接行为型契约证据的函数型 target 开放。
- `interface` / `type` / `Zod` 只作为辅助 evidence，不单独构成函数级 semantic audit preview 资格。
- preview 结果保持 advisory-only / non-blocking / baseline-neutral。
- 自动化测试与 release acceptance 使用 mock / deterministic provider，而不依赖真实 LLM 可用性。

## 3. Why

- 先做 foundation，符合 Harbor 从 Python-centric 治理演进到 language-neutral governance 的长期方向。
- foundation-first 能避免把 TypeScript preview 写成一次性特判分支，降低后续多语言扩展的重复成本。
- eligibility 基于行为型契约证据，可以把 preview 边界说清楚，避免把 data contract 误宣传成完整 semantic audit。
- mock / deterministic provider 验收路径，可以保护默认发布流程不被外部模型服务可用性绑架。

## 4. Risks of the Rejected Path

如果直接在旧 Python-specific substrate 上叠加 TypeScript preview：

- Python 与 TypeScript 的审计入口、序列化和资格判断会持续分叉。
- 后续语言扩展会复制更多分支逻辑，削弱核心治理抽象。
- 很难稳定表达“为什么某个 TypeScript target 能审计，另一个不能审计”。
- 一旦把 data-contract-only target 拉进审计，容易制造噪音与错误期望。

如果把真实 LLM 可用性设为默认验收前提：

- CI 与 release acceptance 会被外部服务状态影响，违背 Harbor 的 deterministic acceptance 原则。
- preview 特性会被错误理解为 production-grade gate。

## 5. Consequences

- Harbor 获得了可复用的 language-neutral semantic audit substrate。
- Python 路径保持正式能力；TypeScript 路径以 advisory preview 方式进入。
- preview eligibility、evidence kinds、provider dependence 都可以被清晰序列化到 explainability 输出。
- release closure 能在不依赖真实 LLM 的前提下完成自动化验证。

## 6. Non-Goals

以下内容明确不属于 `v1.4.4`：

- 正式 TypeScript semantic audit gate
- 仅凭 `interface` / `type` / `Zod` 进入函数级语义审计
- 自动修代码
- 自动修契约
- 用 preview 结果写 baseline truth

## 7. Validation

Phase 4A 对应的治理收口包括：

- README / README.en / RELEASE 明确 preview-only、provider-dependent、non-blocking 边界
- AGENTS.md 与 contract / DDT 规则同步 language-neutral foundation + TypeScript preview 口径
- ADR 与 Diary Draft 记录 foundation-first 的决策理由
- `harbor finish --sync-context`
- `harbor verify-generated --changed --ci --format json`
- `harbor stale --ci --format json`
- `harbor doctor --ci --format json`

Phase 4B 仍需补完：

- `pytest`
- `harbor checkpoint --ci --format json --advice basic`
- `harbor verify-generated --all --ci --format json`
- mock / deterministic provider release acceptance matrix

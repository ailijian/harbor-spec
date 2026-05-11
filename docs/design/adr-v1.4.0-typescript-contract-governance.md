# ADR｜Evolve Harbor Core from Python FunctionContract to Language-neutral ContractSubject

状态：Accepted (v1.4.0)  
日期：2026-05-11  
范围：Core Neutralization + TypeScript Contract Governance MVP

## 1. Context

在 v1.3.x 阶段，Harbor 的核心契约治理主要围绕 Python `FunctionContract` 与 docstring 展开。  
随着 v1.4.0 引入 TypeScript contract governance，我们需要一个跨语言、可扩展且兼容现有 Python 语义的核心模型。

关键前提：

- `Contract` 不等于 docstring；契约源可以是多种结构化或半结构化来源。
- 仅追加 TypeScript parser 而不抽象 core，会继续放大 Python-first 耦合。
- v1.4.0 的目标是在不破坏 Python 语义的前提下，完成可控的 TypeScript MVP 接入。

## 2. Decision

我们在 v1.4.0 采纳以下决策：

- 引入 language-neutral 核心模型：
  - `ContractSubject`
  - `ContractSource`
  - `LanguageAdapter`
- 引入 `AdapterRegistry`，统一 adapter 启用、文件发现与解析入口。
- 内部统一使用 `target_id` 作为跨语言 target 标识。
- 对外保留 `func_id` 兼容字段，避免破坏既有 Python 消费方。
- TypeScript 作为第一站（first-class adapter target）进入 v1.4.0。
- JavaScript 延后，保留为 future opt-in advisory adapter 方向，不在 v1.4.0 承诺 first-class governance。

## 3. Consequences

该决策带来的直接后果：

- Python zero regression 是硬约束：
  - Python checkpoint / semantic audit / DDT 语义保持兼容。
  - 既有 `func_id` 语义保持不变。
- TypeScript v1.4.0 范围限定为 presence/checkpoint/next MVP：
  - 支持 `.ts` 目标发现与 contract presence 判定。
  - `checkpoint --ci` 仅输出受控的 MVP categories。
  - `harbor next` 提供确定性 guidance。
- TypeScript semantic audit / TypeScript DDT 后移，不在 v1.4.0 实现。
- framework preset / Zod / interface-type blocking gate 后移，不在 v1.4.0 实现。

## 4. Alternatives Considered

### 4.1 直接添加 TS parser，不抽象 core（Rejected）

拒绝原因：会保留并放大 Python-first 耦合，后续多语言演进成本持续上升。

### 4.2 同时支持 JS + TS first-class（Rejected）

拒绝原因：JavaScript 弱契约环境噪音更大，v1.4.0 目标是先稳定 TypeScript contract governance MVP。

### 4.3 一次性接入 TS semantic audit + TS DDT（Rejected）

拒绝原因：在 v1.4.0 阶段可靠性与边界控制不足，容易造成语义过度承诺与回归风险。

## 5. Validation

本 ADR 对应验证路径：

- 测试矩阵：Task 9 已完成，覆盖 core neutralization、adapter registry、Python compatibility、TypeScript MVP、not-supported boundaries。
- 本轮收口验证结果：
  - `pytest`: `502 passed`
  - `harbor checkpoint --ci --format json`: `pass`
  - `harbor stale --ci --format json`: `pass`
  - `harbor doctor --ci --format json`: `pass`（仅 workspace changed advisory WARN）


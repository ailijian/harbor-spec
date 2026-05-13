# ADR｜v1.4.2 TypeScript Contract Source Strengthening

状态：Proposed  
日期：2026-05-13  
范围：TypeScript Contract Source Strengthening / accepted baseline artifact compatibility / generated context closure

## 1. Context

`v1.4.0` 完成了 language-neutral `ContractSubject` 与 TypeScript MVP presence/checkpoint/next guidance，`v1.4.1` 转向 Log Draft + Controlled Write workflow。  
在恢复 TypeScript 主线之前，仍存在一个关键治理缺口：TypeScript target 还没有稳定进入 generalized persistence / baseline-compatible path，因此 richer contract source 很容易只停留在 parser 识别层，无法形成稳定的 baseline、JSON additive output 与后续 Public Boundary / DDT / Semantic Audit 预留基础。

`v1.4.2` 需要在以下约束下完成该补强：

- Python zero regression。
- `.harbor/baseline/accepted-checkpoint.json` 继续作为 `checkpoint --ci` 的 baseline truth。
- runtime cache 只做本地加速与兼容。
- Windows full-governance 是正式验收维度。
- `finish --sync-context -> stale --ci -> doctor --ci` 必须形成 generated context closure。
- 不提前引入 re-export、`.d.ts`、TS DDT、TS semantic audit、framework preset。

## 2. Decision

`v1.4.2` 采纳以下决策：

- 先补齐 TypeScript generalized persistence，再引入 richer contract source。
- generalized persistence 采用“normalization / entry adapter”最小侵入方案：
  - 保留 SQLite `entries` 表结构不变。
  - 保留 Python 既有 `meta` shape 与既有消费路径。
  - 仅以 additive metadata 把 TypeScript identity / contract source 摘要写入 persistence、runtime cache、snapshot 与 checkpoint JSON。
- exported `interface` / `type` 进入 advisory-first data contract discovery，但不进入新的 blocking gate。
- `z.object(...)` / `z.enum(...)` 只作为 shallow source recognition，不承诺完整 schema semantics。
- `export default function` / `export default class` 只建模为 public surface evidence，不建模为 contract source。
- TypeScript `contract_hash` 定义为 normalized contract source bundle hash，source 变化影响 hash，body-only 变化不影响 hash。
- `harbor next` 与 checkpoint JSON 仅做 additive 扩展，保留既有 category、baseline 字段与 CI gate 语义。

## 3. Consequences

- TypeScript target 可以稳定进入 index / snapshot / accepted baseline artifact workflow。
- richer TypeScript metadata 可以被 checkpoint / next / downstream JSON 消费，而不破坏现有 Python 输出契约。
- advisory-first data contract、shallow Zod、default export public surface evidence 都变得可观察，但不会在 `v1.4.2` 被误宣传为完整 TS semantic governance。
- Windows path normalization、accepted baseline artifact compatibility、generated context closure 成为本版本 release gate 的一部分。

## 4. Deferred

以下内容明确后移，不属于 `v1.4.2`：

- re-export graph
- `.d.ts` scanning
- `package exports` / `tsconfig` path alias
- framework preset
- TypeScript DDT
- TypeScript semantic audit
- JavaScript first-class governance
- full Zod schema semantics / schema-to-type consistency audit

## 5. Validation

本 ADR 对应的本地阶段性验证：

- `pytest tests/test_checkpoint_json_additive_compat.py tests/test_harbor_next.py tests/test_typescript_checkpoint_ci.py`
- `pytest tests/test_sync_engine.py tests/test_checkpoint_ci_baseline_artifact.py tests/test_typescript_not_supported_boundaries.py`

最终发布前仍需补完：

- 全量 `pytest`
- `harbor checkpoint --ci --format json`
- `harbor stale --ci --format json`
- `harbor doctor --ci --format json`
- GitHub Actions 上的 Ubuntu Python matrix 与 Windows full-governance

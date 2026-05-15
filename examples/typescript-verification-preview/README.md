# TypeScript Verification Preview Examples

这个目录为 `v1.4.5 Task 8` 提供 repo 内可复制的 Preview 上手资产，分成两条最小路径：

- `package-public/`
  - `package_public` preset
  - sidecar binding
  - `typescript_ddt_preview` 的 `preview_valid` 成功路径
  - `checkpoint --ci --format json --detail full` 与 `harbor next --from ...` 的最小演示
- `semantic-audit-preview/`
  - `package_public` preset
  - 无 JSDoc/TSDoc 的函数型 target
  - `harbor check --format jsonl` 下 `semantic_audit_preview` 的最小演示

## Directory Layout

```text
examples/typescript-verification-preview/
  README.md
  package-public/
    .harbor/config/harbor.yaml
    .harbor/ddt/typescript-bindings.yaml
    package.json
    tsconfig.json
    src/index.ts
    src/internal.ts
    tests/api.test.ts
    tests/internal.test.ts
    README.md
  semantic-audit-preview/
    .harbor/config/harbor.yaml
    package.json
    tsconfig.json
    src/index.ts
    README.md
```

## Sidecar Success Path

`package-public/.harbor/ddt/typescript-bindings.yaml` 是最小成功 sidecar：

```yaml
schema_version: "1.0"
bindings:
  - binding_id: api-binding
    target_id: typescript:src/index.ts:function:api
    test_asset:
      path: tests/api.test.ts
      label: api smoke
    strategy: preview_reference
```

它对应：

- target: `package-public/src/index.ts`
- binding: `api-binding`
- test asset: `package-public/tests/api.test.ts`
- preview finding: `preview_valid`

## Typical Failure Examples

以下片段与当前实现中的 finding/category 完全一致，可直接作为 FAQ 对照样例：

### `target_not_found`

```yaml
bindings:
  - binding_id: missing-target
    target_id: typescript:src/missing.ts:function:api
    test_asset:
      path: tests/api.test.ts
    strategy: preview_reference
```

### `contract_source_missing`

```text
保留 sidecar，不给 target 写 nearby JSDoc/TSDoc。
例如把 package-public/src/index.ts 改成只有函数签名与函数体。
```

### `public_boundary_unconfirmed`

```yaml
bindings:
  - binding_id: boundary-check
    target_id: typescript:src/internal.ts:function:helper
    test_asset:
      path: tests/internal.test.ts
    strategy: preview_reference
```

前提：`verification.typescript_ddt_preview.require_public_boundary=true`。

### `test_asset_missing`

```yaml
bindings:
  - binding_id: missing-test
    target_id: typescript:src/index.ts:function:api
    test_asset:
      path: tests/missing.test.ts
    strategy: preview_reference
```

### `binding_schema_invalid`

```yaml
bindings:
  - binding_id: bad-binding
    target_id: typescript:src/index.ts:function:api
    test_asset:
      path: ../outside.test.ts
    strategy: preview_auto
```

### `duplicate_binding_id`

```yaml
bindings:
  - binding_id: dup-binding
    target_id: typescript:src/index.ts:function:api
    test_asset:
      path: tests/api.test.ts
    strategy: preview_reference
  - binding_id: dup-binding
    target_id: typescript:src/index.ts:function:api
    test_asset:
      path: tests/internal.test.ts
    strategy: preview_reference
```

### `preview_ineligible`

见 `semantic-audit-preview/README.md`。当前最小演示使用“函数存在，但缺少行为型契约证据”的场景，因此 `eligibility_reason=behavior_contract_missing`。

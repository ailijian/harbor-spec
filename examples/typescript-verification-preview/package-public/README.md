# Package Public Preview Demo

这个示例演示 `v1.4.5` 期望的新用户上手路径：

- 使用 `package_public` preset
- 打开 TypeScript DDT Preview
- 用 sidecar 显式绑定 `target_id -> test_asset`
- 通过 `checkpoint` 查看 `typescript_ddt_preview`
- 通过 `harbor next` 读取 preview explainability

## What To Run

在交互式 TTY 下运行 `checkpoint` 时，`v1.4.5` 会显示统一的 progress feedback。  
为了查看稳定字段，下面的 demo 使用机器可读 JSON：

```powershell
python -m harbor.cli.main checkpoint --ci --format json --detail full
```

这个独立示例没有 repo-owned `.harbor/baseline/accepted-checkpoint.json`，所以输出里会同时出现 `accepted_baseline_missing`。  
这是 CI baseline 工件要求，不会改变 `typescript_ddt_preview` 的 advisory-only 语义。

## Expected Checkpoint Excerpt

```json
{
  "summary": {
    "typescript_ddt_preview_bindings": 1,
    "typescript_ddt_preview_valid": 1,
    "typescript_ddt_preview_advisory": 0
  },
  "typescript_ddt_preview": {
    "bindings_file": ".harbor/ddt/typescript-bindings.yaml",
    "bindings_count": 1,
    "valid_count": 1,
    "advisory_count": 0,
    "findings": [
      {
        "status": "preview_valid",
        "binding_id": "api-binding",
        "target_id": "typescript:src/index.ts:function:api",
        "test_asset_path": "tests/api.test.ts",
        "contract_source_kinds": ["tsdoc"],
        "public_boundary_state": "package_export_surface",
        "boundary_preset_mode": "package_public",
        "preview": true,
        "advisory": true,
        "blocking": false
      }
    ]
  }
}
```

## Expected `harbor next` Excerpt

`harbor next` 读取 checkpoint report 时，会把 preview finding 当作 explainability item，而不是 blocker：

```powershell
python -m harbor.cli.main next --from checkpoint-demo.json --format json
```

```json
{
  "category": "preview_valid",
  "binding_id": "api-binding",
  "target_id": "typescript:src/index.ts:function:api",
  "test_asset_path": "tests/api.test.ts",
  "public_boundary_state": "package_export_surface",
  "boundary_preset_mode": "package_public",
  "preview": true,
  "blocking": false
}
```

如果你是在 Windows PowerShell 下把 checkpoint 输出保存到文件，注意避免 BOM 干扰 `harbor next --from ...` 读取。  
这个注意点在 `docs/guides/typescript-verification-preview-troubleshooting.md` 里也有说明。

## Files To Inspect

- target: `src/index.ts`
- sidecar: `.harbor/ddt/typescript-bindings.yaml`
- test asset: `tests/api.test.ts`
- boundary demo helper: `src/internal.ts`

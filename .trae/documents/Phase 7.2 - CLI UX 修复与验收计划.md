## 任务理解
- 修复 `audit` 命令 Prompt 中文模板重复问题，确保无冗余、无歧义。
- 系统性审查所有 CLI 子命令输出，提升一致性与去噪，统一 Help 文案。
- 编写并执行 7 步验收脚本，收集输出日志确认质量。

## 上下文加载（代码定位）
- 审计模板与语义审计：`harbor/core/audit.py:64-83`
- CLI 主入口与子命令：`harbor/cli/main.py:43-81, 83-209`

## 初步发现
- `PROMPT_TEMPLATES["zh"]` 当前仅包含一次“请重点关注: 参数(Args), 返回值(Returns), 异常(Raises)。”（`harbor/core/audit.py:75-83`）。重复现象可能源于历史版本或 CLI `--debug` 打印的重复块，但从现有实现看未见二次拼接。
- `build-index` 统计信息分两行打印（`harbor/cli/main.py:88-90`），与“统计信息一行打印”的去噪目标不完全一致。
- `status` 在“无变化”时仍打印头部“Harbor Context Status:”（`harbor/cli/main.py:93`），虽随后输出“No changes detected.”，但可进一步去噪：在干净状态下仅打印简短行。
- 其它命令输出整体较为一致：
  - `gen l2` 写入时输出 `Wrote: ...` 或 `No changes needed.`（`harbor/cli/main.py:141-148`）
  - `diary log` 输出 JSON（`harbor/cli/main.py:150-161`）
  - `ddt validate` 有“Valid bindings/Violations/No DDT bindings found.”（`harbor/cli/main.py:126-137`）
  - `audit --semantic` 输出统一前缀 `OK/POSSIBLE_SEMANTIC_DRIFT/ERROR`（`harbor/cli/main.py:199-203`）

## 执行计划（不改行为，仅优化输出与模板）
### Step 1: 修复/验证 Prompt 重复
- 保持 `PROMPT_TEMPLATES["zh"]` 仅一处“请重点关注...”行；若验收中仍出现重复，则定位为 CLI 调试输出问题，改为只打印一次 Prompt（`harbor/cli/main.py:196-198` 将 `[DEBUG] Prompt >>>` 与 `[DEBUG] Raw <<<` 保持一次性、无额外模板附加）。
- 在 `harbor/core/audit.py` 中不新增任何附加行，确保模板纯净。

### Step 2: 全命令 UX 优化改动点
- `build-index`: 合并两行统计为一行，示例：
  - 变更位置：`harbor/cli/main.py:88-90`
  - 新格式：`scanned=... updated=... skipped=... items=... cache=... elapsed_ms=...`
- `status`: 在干净状态下仅输出 `No changes detected.`；有变化时再打印头 `Harbor Context Status:` 与分组列表。
  - 变更位置：`harbor/cli/main.py:93-116`
  - 逻辑调整：先计算 `total`，如为 0 则直接打印并返回；否则打印头与各分组。
- `ddt validate`: 维持现有分组，微调违规行前缀为更显眼的 `[!]`，如：`[!] {typ} ... :: {msg}`，确保错误前缀明确。
  - 变更位置：`harbor/cli/main.py:133-135`
- `audit --semantic`: 保持当前输出；增加目标计数汇总行可选：`targets={len(targets)}`（信息密度提升，便于审阅）。
  - 变更位置：`harbor/cli/main.py:172-178`
- `gen l2`: 保持现状；非写入模式打印 Markdown，写入模式打印 `Wrote:`/`No changes needed.`，符合一致性。
- `diary log`: 保持输出 JSON，符合预期。
- Help 文案：已统一英文（`add_parser(..., help="...")`），无需改动；主函数 Docstring 为中文不影响 Help。

### Step 3: 验收测试脚本（Runbook）
按序执行并核对输出：
1. `harbor --help`
   - 预期：英文 Help，无中文夹杂；子命令、参数描述清晰。
2. `harbor status`
   - 预期（Clean）：仅一行 `No changes detected.`，不打印任何分组头。
3. `harbor build-index --no-incremental`
   - 预期：单行统计输出，包含 `scanned/updated/skipped/items/cache/elapsed_ms`。
4. `harbor audit --semantic --debug`
   - 预期：`[DEBUG] Prompt >>>` 块中“请重点关注...”仅出现一次；`OK/POSSIBLE_SEMANTIC_DRIFT/ERROR` 行整齐。
5. `harbor gen l2 --module harbor/core`
   - 预期：打印 Markdown；若加 `--write`，打印 `Wrote: <path>`。
6. `harbor diary log --summary "UX Review" --type chore`
   - 预期：输出 JSON（单行或紧凑格式）。
7. `harbor ddt validate`
   - 预期：`Bindings scanned: N`；`Valid bindings:`/`Violations:` 对齐；违规前缀为 `[!]`。

### Step 4: 交付物
- `audit.py`: 保持模板无重复；如验收发现重复，再针对性修正（当前版本已无重复行）。
- `main.py`: 提交上述输出优化改动（合并统计行；status 去噪；DDT 违规前缀可读性增强；可选 audit 目标计数）。
- 7 步命令的执行日志（本地跑完收集，作为验收附件）。

## 风险与兼容性
- 所有改动仅影响 CLI 输出格式，不改核心行为与返回码；兼容脚本化使用场景。
- `status` 的头部在干净状态下不再打印，可能影响依赖固定头的解析器；若需兼容可加 `--verbose` 恢复头部（后续可讨论）。

## 需要决策
- 是否接受 `build-index` 统计合并为一行？
- 是否接受 `status` 在干净状态下仅打印简短行的去噪策略？
- 是否加入 `audit` 目标计数汇总行？

请确认上述计划，确认后我将按计划修改代码并运行 7 步验收，提交完整日志。
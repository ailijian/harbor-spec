# Harbor-spec v1.0.2 分阶段实施计划

## 目标与范围
- 交付一个符合 v1.0.2 的参考实现：CLI、Sync Engine、Python 适配器、DDT、L2、Diary、CI 集成与软审计。
- 仅支持 Python 语言适配器；多语言作为后续路线图。
- 紧跟“索引去中心化、DDT 韧性、Diary 轮转、AI 语义审计（软检查）”的版本目标。

## 关键交付物
- `harbor` CLI 命令族：`init / build-index / sync / gen l2 / ddt / diary / audit / report`。
- `.harbor/config.yaml`、`semantic_guard.yaml`、`.harbor/cache/*`（Gitignored）。
- Python AST 适配器：Docstring 解析、Contract/Decoration 哈希、严格度校验。
- DDT 装饰器与工具：强版本绑定 + `latest` 绑定策略与交互式更新。
- L2 模块 README 自动生成与抖动控制（`l2_meta.json`）。
- Diary 月度 JSONL 文件与导出工具。
- CI 集成：增量索引、严格同步门槛、软审计与报告。

## Phase 0｜自举与基础设施
- 建立目录架构：`harbor/{cli,core,adapters,utils,config}`、`specs/diary`、`.harbor`。
- 初始化 `.harbor/config.yaml` 与默认 `profile= enfore_l3`；添加 `.gitignore` 忽略 `.harbor/cache/**`。
- 搭建 `pytest` 测试框架与基础测试用例。
- 验收：CLI 可运行 `harbor init`；基础配置加载与校验通过。

## Phase 1｜Python 语言适配器（索引地基）
- 使用 Python AST 提取函数签名与 Docstring，支持 Google 风格解析。
- 支持 Contract/Decoration 切分与哈希；暴露 `AdapterManager` 接口给 core。
- 作为 `build-index` 的前置依赖，为索引提供签名/函数体哈希、`contract_hash` 与 `docstring_raw_hash`。
- 验收：适配器在目标代码范围内稳定解析并输出所需哈希与元数据。

## Phase 2｜索引去中心化
- 实现 `build-index`：从代码与 Diary 推导 `l3_index.json` 到 `.harbor/cache/`。
- 设计增量构建：基于文件改动与签名/函数体哈希变更。
- 确认索引不入库；避免多人合并冲突。
- 验收：本地运行 `harbor status` 自动触发增量索引；`.harbor/cache/` 更新无 Git diff。

## Phase 3｜L3 契约与严格度
- 解析并区分 Docstring 的 Contract/Decoration 区域，计算 `contract_hash` 与 `docstring_raw_hash`。
- 实现严格度策略：`strict / standard / light` 与路径覆盖策略。
- 在 `sync l3 --check` 下对签名/函数体变更要求契约区同步，必要时提示 `l3_version++`。
- 验收：`harbor sync l3 --check` 能检测“实现变更但契约未更新”的不一致并 fail（依据 profile）。

## Phase 4｜DDT 韧性绑定与维护
- 提供 `@harbor_ddt_target(func=..., l3_version=N)` 与 `strategy="latest"` 两种绑定。
- 写死规则：`strict`/public/critical 禁止 `latest`，必须显式版本。
- 实现 `harbor ddt update` 交互式更新测试版本绑定，含变更摘要提示。
- 验收：在严格函数版本升级时，触发交互式更新并完成测试版本号同步。

## Phase 5｜L2 锚点视图
- 聚合 L3 + DDT + Diary 生成 `modules/**/README.md`（只读，带 `AUTO-GENERATED` 头）。
- 通过 `l2_meta.json` 控制展示顺序与抖动，支持嵌入质量统计（覆盖率、公共 API 数量、近期 Diary）。
- 验收：`harbor gen l2 --module <path>` 生成稳定 README；小变动不导致大范围 diff。

## Phase 6｜Diary 轮转与噪音控制
- 写入 `specs/diary/YYYY-MM.jsonl`，默认读取“当月+上一月”聚合。
- 根据 `importance/visibility` 与触发规则生成草稿，支持 IDE/CLI 调整。
- 提供导出：`harbor diary export --visibility repo|public`。
- 验收：变更事件可落到 JSONL；导出文件符合可分享要求。

## Phase 7｜Sync Engine 与开发流
- 整合 `status / sync --pre-commit / sync --ci` 的增量索引与一致性校验。
- 在 pre-commit 中做 L3/L2/Diary 基本动作；在 CI 中做完整检查与报告输出。
- 验收：本地与 CI 均可稳定运行；`harbor report --format markdown` 产物可用于 PR 评论。

## Phase 8｜AI 语义审计（软检查）
- `.harbor/semantic_guard.yaml` 指定审计范围与风险等级。
- `harbor audit --semantic` 收集 L3 有变动的函数，构造审计 Prompt：检查 Args/Returns/Raises 与实现一致性。
- 输出仅作为 soft-check：标记 `POSSIBLE_SEMANTIC_DRIFT`，不阻断构建。
- 验收：在典型偏离场景下输出审计提示并进入报告。

## Phase 9｜CLI 与开发者体验
- 完成命令族交互与帮助文本；为关键命令提供清晰输出与错误提示。
- 提供 `harbor doctor / overview / quickfix` 便捷诊断与修复建议。
- 验收：命令可用性与可读性达标；错误路径有清晰指引。

## Phase 10｜旧仓库渐进接入
- Phase 1：`profile=observe_only`，仅观察不拦。
- Phase 2：`profile=enforce_l3`，新模块强制 L3。
- Phase 3：核心模块切到 `full_harbor`，启用 strict L3 + DDT_MINIMAL。
- 验收：各阶段指标达标后再推进到下一阶段。

## 指标与健康度
- L3 强一致率、Public API DDT 覆盖率、最大 Context Debt、CI 稳定度。
- 默认阈值：`min_public_ddt_coverage ≥ 0.8`，`max_context_debt ≤ 10`。

## 风险与缓解
- 误审计阻断：软检查策略，不作为硬门槛。
- README 抖动：通过 `l2_meta.json` 控制展示与排序。
- 索引性能：增量扫描与缓存；必要时分模块构建。
- 文化摩擦：以 DDT 交互式工具与报告降低维护负担。

## 仓库改动清单
- 新增：`.harbor/config.yaml`、`.harbor/semantic_guard.yaml`、`.harbor/cache/**`（Gitignored）。
- 新增：`specs/diary/YYYY-MM.jsonl` 与可选 `DEVELOPMENT_DIARY.md` 镜像。
- 新增：`modules/**/README.md`（AUTO-GENERATED）。
- 更新：`.gitignore`、CI 工作流（含 `build-index` 与 `sync --ci`）。

## 验收标准
- 所有命令在本地与 CI 环境可稳定执行并输出预期产物。
- L3/L2/Diary/DDT/审计链路闭环，公共 API 达到最小 DDT 覆盖。
- 报告与导出满足 PR 审查与团队分享需求。

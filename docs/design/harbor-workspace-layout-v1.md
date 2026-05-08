# Harbor Workspace Layout V1｜中文设计版

> 状态：Draft  
> 目标版本：v1.3.0  
> 设计目标：统一管理 Harbor 产生和维护的所有文件，让配置、策略、状态、派生视图、Diary、报告、导出物和外部工具集成边界清晰、结构稳定、易于维护。

---

## 0. 文档目的

本文定义 `harbor-spec` 推荐采用的项目内工作区布局。

目标是让所有 Harbor 生成或管理的文件都能被清晰地理解、定位、版本管理、忽略、重生成，并能被 AI coding agent 稳定消费。

`docs/design/` 是人类编写设计文档目录，默认应可被 Git 追踪（trackable）。

Harbor 不应继续把自己的产物分散在多个语义不一致的目录中，例如：

```text
docs/harbor/
specs/diary/
.harbor/
.agents/skills/
```

更合理的方案是建立一个统一的 Harbor canonical workspace：

```text
.harbor/
```

同时，人类阅读的设计文档仍然保留在：

```text
docs/design/
```

这样可以形成清晰边界：

```text
.harbor/      = Harbor 运行时工作区与 Harbor 管理资产
docs/design/ = 人类阅读的架构设计与方案文档
```

---

## 1. 核心决策

Harbor 采用 **Harbor-only canonical workspace model**。

### Harbor 主工作区

```text
.harbor/
```

所有 Harbor 拥有的运行资产、生成视图、策略、报告、Diary、导出物、集成配置、状态与缓存，都应归入 `.harbor/` 体系。

### 人类设计文档

```text
docs/design/
```

人类编写的设计文档应留在 `.harbor/` 外部，避免和 Harbor 运行时产物、生成视图或机器配置混淆。

### 外部工具输出

Codex、Claude、Cursor、TRAE 等外部 AI 编程工具需要的文件，可以继续导出到工具约定目录：

```text
.agents/skills/
.claude/skills/
.cursor/rules/
```

但这些目录应被视为 **export target**，而不是 Harbor 的 canonical storage。

---

## 2. 设计原则

### 2.1 Harbor 拥有的文件应该容易定位

用户应能用一句话回答：

```text
Harbor 的文件在哪里？
```

答案应该是：

```text
.harbor/
```

---

### 2.2 生成视图不是事实源

以下文件属于生成视图或派生视图：

```text
project-structure.md
module-card.md
review-checklist.md
debug-playbook.md
```

它们对人类和 AI agent 很有帮助，但不是事实源。

v1.3.0 起，`.harbor/views/**` 下 canonical markdown generated views 统一带有 context integrity frontmatter（包含 source paths、fingerprints、generation command、harbor version、stale policy）。

其中 `generated_at` 仅为信息字段；stale 比较应忽略该字段，且输入不变时应复用旧值以避免无意义 Git diff。

事实源仍然是：

```text
源代码
契约
Schema
测试
Harbor policy
Harbor diary
```

补充规则（P0-2）：

```text
Instruction Hierarchy 与 Source of Truth Priority 必须分离：
- Instruction Hierarchy 处理规则/指令冲突。
- Source of Truth Priority 处理 contract/tests/implementation/generated/export 的事实冲突。

Canonical wins 仅用于 canonical artifact 与 legacy/export copy 冲突：
- 例如 .harbor/views/l2/<module>/README.md 优先于 <module>/README.md。
- 该规则不允许 .harbor/views/** 覆盖 contracts / DDT / source implementation。

Generated views remain advisory context, not truth override.
发现冲突时应标记 semantic drift / contract gap，并通过测试、DDT 或人工确认裁决。
```

---

### 2.3 人类设计文档应保持可读性

设计文档不应该隐藏在 `.harbor/` 里。

例如：

```text
docs/design/harbor-workspace-layout-v1.md
docs/design/context-routing-v1.md
docs/design/contract-graph-v1.md
```

这些文件解释 Harbor 自身的设计，不属于 Harbor 运行时产物。

---

### 2.4 外部工具目录是集成导出目标

以下目录属于外部 AI 工具生态：

```text
.agents/skills/
.claude/skills/
.cursor/rules/
```

Harbor 可以向这些目录导出文件，但不应把它们当作主存储。

Harbor 自己的集成元信息应放在：

```text
.harbor/integrations/
```

或：

```text
.harbor/exports/
```

---

### 2.5 本地状态与版本化知识应分离

Harbor 应明确区分：

```text
版本化知识
本地状态
缓存
生成视图
外部导出物
```

这些内容不应混在一个扁平目录里。

---

## 3. 推荐顶层结构

推荐的 Harbor 工作区结构如下：

```text
.harbor/
  config/
  policy/
  state/
  views/
  diary/
  reports/
  exports/
  integrations/
  cache/
```

每个目录有独立职责。

---

## 4. 目录规范

## 4.1 `.harbor/config/`

### 作用

项目级 Harbor 配置。

该目录用于告诉 Harbor 在当前仓库中如何运行。

### 建议文件

```text
.harbor/config/
  harbor.yaml
```

### 示例

```yaml
version: 1

paths:
  source:
    - harbor/
  tests:
    - tests/
  docs:
    - docs/
  exclude:
    - .git/
    - .venv/
    - node_modules/
    - __pycache__/

views:
  root: .harbor/views
  export_docs: false

diary:
  root: .harbor/diary

reports:
  root: .harbor/reports

state:
  root: .harbor/state

cache:
  root: .harbor/cache
```

### Git 策略

推荐：

```text
进入 Git
```

原因：

配置决定项目级 Harbor 行为，应在团队成员之间共享。

---

## 4.2 `.harbor/policy/`

### 作用

机器可读的 Harbor 治理策略。

该目录存放 Harbor 如何理解契约、安全、DDT、模块和严格度的规则。

### 建议文件

```text
.harbor/policy/
  contract.yaml
  safety.yaml
  ddt.yaml
  modules.yaml
```

### 文件职责

| 文件              | 作用                                           |
| --------------- | -------------------------------------------- |
| `contract.yaml` | strict / standard / light 路径规则，Contract 行为规则 |
| `safety.yaml`   | 运行时安全规则：allow / ask / deny                   |
| `ddt.yaml`      | Docstring-Driven Testing 策略                  |
| `modules.yaml`  | 可选的显式模块映射                                    |

### 示例：`contract.yaml`

```yaml
version: 1

strictness:
  strict:
    - harbor/cli/**
    - harbor/core/**
  standard:
    - harbor/utils/**
  light:
    - tests/**
```

### 示例：`safety.yaml`

```yaml
version: 1

rules:
  deny:
    - pattern: ".env"
      action: "read_or_write"
      reason: "Never read or modify secrets."

  ask:
    - pattern: "migrations/**"
      action: "write"
      reason: "Migration changes require explicit confirmation."

  allow:
    - pattern: "README.md"
      action: "write"
```

### Git 策略

推荐：

```text
进入 Git
```

原因：

策略是共享治理规则，应被人类和 AI agent 同时可见。

---

## 4.3 `.harbor/state/`

### 作用

Harbor 本地状态。

该目录存放机器状态，通常可以重建，或者只对当前工作副本有效。

### 建议文件

```text
.harbor/state/
  index.sqlite
  baseline.json
  lock.json
  scan-state.json
```

### 特征

```text
机器读写
本地状态
可重建
不应手动编辑
```

### Git 策略

默认推荐：

```text
不进入 Git
```

原因：

状态文件可能是本地的、较大、频繁变化，或带有环境差异。

### `.gitignore`

```gitignore
.harbor/state/
```

---

## 4.4 `.harbor/views/`

### 作用

Harbor canonical generated views。

该目录存放 Harbor 生成的项目级和模块级视图，供人类和 AI agent 使用。

### 建议结构

```text
.harbor/views/
  project-structure.md

  l2/
    harbor/core/README.md
    harbor/utils/README.md

  modules/
    harbor/core/
      module-card.md
      review-checklist.md
      debug-playbook.md

    harbor/cli/
      module-card.md
      review-checklist.md
      debug-playbook.md
```

### 视图类型

| 视图                               | 作用           |
| -------------------------------- | ------------ |
| `project-structure.md`           | 项目级结构地图      |
| `l2/**/README.md`                | 模块级契约锚点视图    |
| `modules/**/module-card.md`      | 模块维护上下文      |
| `modules/**/review-checklist.md` | 模块 review 指南 |
| `modules/**/debug-playbook.md`   | 模块 debug 指南  |

### 重要规则

这些文件都是派生视图。

应包含类似警示：

```text
Generated by Harbor-spec.
This is a derived view, not a source of truth.
```

### Git 策略

推荐默认：

```text
由项目选择是否进入 Git
```

对于开源项目，追踪 `.harbor/views/` 可能很有价值，因为人类和 AI 工具可以不运行命令就直接查看项目结构。

对于内部项目，团队可以选择忽略这些视图并在本地重生成。

### 建议配置

```yaml
views:
  track_in_git: true
```

---

## 4.5 `.harbor/diary/`

### 作用

Harbor 演进记忆（canonical 写入路径）。

legacy 兼容读取路径：

```text
specs/diary/
```

### 建议结构

```text
.harbor/diary/
  2026-05.jsonl
  2026-06.jsonl
```

### Diary 应记录

```text
契约变更
架构决策
Bugfix 原因
Incident 记录
迁移决策
重要重构
```

### 示例记录

```json
{
  "type": "feature",
  "importance": "high",
  "visibility": "repo",
  "module": "harbor/core",
  "summary": "Add Project Structure View",
  "reason": "Help AI agents understand project structure before reading source files.",
  "changes": [
    "Added project-structure.md generated view",
    "Separated Code Modules from Supporting Areas"
  ],
  "ref": ""
}
```

### Git 策略

推荐：

```text
进入 Git
```

原因：

Diary 保存项目决策记忆，对未来 AI agent 和维护者都很重要。

---

## 4.6 `.harbor/reports/`

### 作用

Harbor 生成的报告和验证材料。

这些文件不是运行时状态，但作为证据、历史记录或质量验证材料很有价值。

### 建议结构

```text
.harbor/reports/
  dogfooding/
    v1.3.0-rc-validation.md
    v1.3.0-rc-issues.md
    v1.3.0-rc-command-log.md
    v1.3.0-release-freeze-checklist.md

  releases/
    v1.3.0-validation.md

  audits/
    semantic-audit-2026-05.md
```

### 报告分类

| 目录            | 作用               |
| ------------- | ---------------- |
| `dogfooding/` | RC 验证、测试证据、UX 发现 |
| `releases/`   | 发布验证和 freeze 记录  |
| `audits/`     | 语义审计或治理审计报告      |

### Git 策略

推荐：

```text
重要报告进入 Git
临时报告不进入 Git
```

例如：

```gitignore
.harbor/reports/tmp/
.harbor/reports/local/
```

但 release 和 dogfooding 报告如果是项目历史的一部分，建议保留。

---

## 4.7 `.harbor/exports/`

### 作用

导出暂存区。

该目录存放准备复制或同步到外部路径的生成文件。

### 建议结构

```text
.harbor/exports/
  docs/
    project-structure.md
    modules/

  skills/
    codex/
    claude/
```

### 使用场景

```text
把 Harbor 视图导出到 docs/harbor/
把 Harbor skills 导出到 .agents/skills/
把 Claude skills 导出到 .claude/skills/
```

### Git 策略

推荐：

```text
默认不进入 Git
```

原因：

exports 通常可以由 canonical Harbor 资产重新生成。

---

## 4.8 `.harbor/integrations/`

### 作用

外部工具集成元信息。

该目录存放 Codex、Claude、Cursor、TRAE 等工具相关的集成配置或生成计划。

### 建议结构

```text
.harbor/integrations/
  codex/
    skills.yaml

  claude/
    skills.yaml

  cursor/
    rules.yaml

  trae/
    skills.yaml
```

### 重要区别

外部目录是输出目标：

```text
.agents/skills/
.claude/skills/
.cursor/rules/
```

Harbor 自身的集成元信息应存放在：

```text
.harbor/integrations/
```

### Git 策略

推荐：

```text
集成配置进入 Git
生成导出结果默认忽略或由项目决定
```

---

## 4.9 `.harbor/cache/`

### 作用

临时缓存。

### 建议结构

```text
.harbor/cache/
  scan/
  llm/
  temp/
```

### Git 策略

推荐：

```text
不进入 Git
```

### `.gitignore`

```gitignore
.harbor/cache/
```

---

## 5. Canonical Files 与 Exported Files

Harbor 应明确区分 canonical files 和 exported files。

## 5.1 Canonical files

Harbor canonical assets 存放在：

```text
.harbor/
```

例如：

```text
.harbor/config/harbor.yaml
.harbor/policy/contract.yaml
.harbor/views/project-structure.md
.harbor/views/modules/harbor/core/module-card.md
.harbor/diary/2026-05.jsonl
```

## 5.2 Exported files

导出文件可以放在 `.harbor/` 外部，以兼容人类阅读或外部工具。

例如：

```text
docs/harbor/project-structure.md
docs/harbor/modules/harbor/core/module-card.md
.agents/skills/harbor-debug-harbor-core/SKILL.md
.claude/skills/harbor-debug-harbor-core/SKILL.md
```

这些文件应被视为 export target。

它们不应成为事实源。

---

## 6. 与现有路径的关系

## 6.1 `docs/harbor/`

当前角色：

```text
生成视图和 Harbor 文档混合区
```

未来角色：

```text
可选的人类可读导出目标
```

推荐：

```text
canonical: .harbor/views/
optional export: docs/harbor/
```

## 6.2 `specs/diary/`

当前角色：

```text
Harbor diary / 演进记忆
```

未来角色：

```text
legacy read-compatible path（非 canonical 写入目标）
```

推荐策略：

```text
write:
  .harbor/diary/YYYY-MM.jsonl

read:
  .harbor/diary/YYYY-MM.jsonl
  + specs/diary/YYYY-MM.jsonl
```

## 6.3 `.agents/skills/`

当前角色：

```text
生成的 skill 入口文件
```

未来角色：

```text
外部工具导出目标
```

canonical skill generation metadata 应放在：

```text
.harbor/integrations/
```

或：

```text
.harbor/exports/skills/
```

## 6.4 `.harbor/`

当前角色：

```text
config / state / policy 混合目录
```

未来角色：

```text
Harbor canonical workspace
```

---

## 7. Git Tracking 策略

推荐默认策略：

```text
进入 Git:
  .harbor/config/
  .harbor/policy/
  .harbor/diary/
  selected .harbor/views/
  selected .harbor/reports/

不进入 Git:
  .harbor/state/
  .harbor/cache/
  .harbor/exports/
  local reports
```

建议 `.gitignore`：

```gitignore
# Harbor local state and cache
.harbor/state/
.harbor/cache/

# Harbor export staging
.harbor/exports/

# Local-only reports
.harbor/reports/tmp/
.harbor/reports/local/
```

Phase 2B.5 落地约束（harbor-spec 仓库）：

```text
不要使用裸 `.harbor/` broad ignore
必须保证 `.harbor/views/project-structure.md` 可被 Git 跟踪
docs/harbor 仅作为可选 export，不是 canonical storage
```

如果某项目希望忽略所有生成视图：

```gitignore
.harbor/views/
```

如果某项目希望追踪生成视图：

```gitignore
# do not ignore .harbor/views
```

---

## 8. 推荐默认追踪策略

对于 harbor-spec 自身，推荐追踪策略如下：

| 路径                                   |       是否进入 Git | 原因           |
| ------------------------------------ | -------------: | ------------ |
| `.harbor/config/`                    |              是 | 共享项目配置       |
| `.harbor/policy/`                    |              是 | 共享治理规则       |
| `.harbor/state/`                     |              否 | 本地运行状态       |
| `.harbor/cache/`                     |              否 | 本地缓存         |
| `.harbor/views/project-structure.md` |              是 | 有助于 AI 上下文加载 |
| `.harbor/views/modules/`             |             可选 | 有用但属于生成物     |
| `.harbor/diary/`                     |              是 | 项目演进记忆       |
| `.harbor/reports/dogfooding/`        | release 证据建议进入 | 验证历史         |
| `.harbor/exports/`                   |              否 | 派生导出暂存       |
| `.agents/skills/`                    |             可选 | 外部工具输出       |

---

## 9. 对命令行为的影响

Workspace layout 会影响现有命令的目标路径。

## 9.1 Project Structure

当前：

```text
docs/harbor/project-structure.md
```

未来 canonical target：

```text
.harbor/views/project-structure.md
```

可选 export target：

```text
docs/harbor/project-structure.md
```

未来建议命令：

```powershell
harbor project structure
harbor project structure --write
harbor views export --target docs
```

## 9.2 Module Capsule

当前：

```text
docs/harbor/modules/<module>/
```

未来 canonical target：

```text
.harbor/views/modules/<module>/
```

可选 export target：

```text
docs/harbor/modules/<module>/
```

## 9.3 L2 README

当前：

```text
<module>/README.md
```

未来 canonical target：

```text
.harbor/views/l2/<module>/README.md
```

可选 export target：

```text
<module>/README.md
```

这是敏感兼容区，因为很多用户预期模块 README 应放在模块旁边。

L2 metadata canonical target：

```text
.harbor/views/l2/_meta.json
```

legacy compatibility：

```text
.harbor/l2_meta.json (read-compatible only, no longer write target)
```

因此，L2 README 应支持可配置输出：

```yaml
l2:
  canonical_root: .harbor/views/l2
  export:
    module_readme:
      enabled: true
```

## 9.4 Diary

当前：

```text
specs/diary/YYYY-MM.jsonl
```

未来：

```text
.harbor/diary/YYYY-MM.jsonl
```

迁移策略：

```text
canonical 单写：仅写 .harbor/diary/YYYY-MM.jsonl
legacy 双读：继续读取 specs/diary/YYYY-MM.jsonl
合并读取时去重
不自动迁移，不自动删除 legacy diary
```

## 9.5 Skill Promotion

当前输出：

```text
.agents/skills/harbor-debug-<module-slug>/SKILL.md
```

未来行为：

```text
canonical metadata: .harbor/integrations/codex/skills.yaml
export target: .agents/skills/
```

为兼容现有工具，Skill 文件仍可直接生成到 `.agents/skills/`，但文档应明确 `.agents/skills/` 是 export target。

---

## 10. 向后兼容

Harbor 不应立即破坏现有仓库。

## 10.1 v1.3.x 兼容策略

继续支持当前路径：

```text
docs/harbor/project-structure.md
docs/harbor/modules/
specs/diary/
.agents/skills/
```

逐步增加新配置支持。

## 10.2 v1.3.1 建议行为

引入：

```text
.harbor/config/harbor.yaml
```

支持可配置根路径：

```yaml
workspace:
  root: .harbor

views:
  canonical_root: .harbor/views
  export_docs_root: docs/harbor
  export_docs_enabled: false

diary:
  root: .harbor/diary

reports:
  root: .harbor/reports
```

不自动强制迁移。

## 10.3 v1.4 建议行为

增加迁移工具：

```powershell
harbor workspace inspect
harbor workspace migrate --dry-run
harbor workspace migrate --write
```

Phase 2F-A（Workspace Inspect MVP）补充约束：

```text
harbor workspace inspect 为只读 advisory 命令
报告 canonical paths / legacy paths / Git tracking / generated views / advisory
不执行 workspace migrate
不删除 legacy 文件
不修改任何写入行为
```

Phase 2F-B（Workspace Migrate Dry-run MVP）补充约束：

```text
新增 harbor workspace migrate --dry-run（支持 --format text/json）
该命令仅生成 migration plan，不执行真实迁移
不复制文件
不移动文件
不删除文件
不修改配置
不修改 .gitignore
不迁移 diary
若未传 --dry-run，应报错提示当前版本仅支持 --dry-run
```

Phase 2F-C（Release Hardening & Workspace Layout Freeze）补充约束：

```text
本阶段不实现 harbor workspace migrate --write
本阶段不新增功能命令
本阶段不复制/移动/删除 legacy 文件
.harbor/ 是 canonical Harbor workspace
docs/design/ 是人工设计文档
docs/harbor/ 是 optional docs export，不是 canonical storage
.agents/skills/ 是外部集成 export target
specs/diary/ 与 .harbor/l2_meta.json 仅 legacy read-compatible，不是 canonical 写入目标
module README 是 export target，不是 canonical 存储
harbor workspace inspect 是只读
harbor workspace migrate --dry-run 是只读
```

Phase 2F-E（Release Freeze Pack）补充约束：

```text
本阶段仅做 release freeze 前最终审查、文档收口、文件归类、测试验证与 release checklist
不实现 harbor workspace migrate --write
不修改现有 CLI 行为
不删除 legacy 文件
harbor workspace inspect 是只读
harbor workspace migrate --dry-run 是只读
legacy 文件不会自动删除或迁移
```

## 10.4 v2.0 可能行为

将 `.harbor/views/` 作为默认 canonical 位置。

继续保留 export 命令支持 legacy 路径。

---

## 11. 迁移策略

## 11.1 Phase 1：仅设计

创建：

```text
docs/design/harbor-workspace-layout-v1.md
```

不改变运行行为。

## 11.2 Phase 2：配置支持

新增：

```text
.harbor/config/harbor.yaml
```

支持以下路径的配置：

```text
views
diary
reports
exports
state
cache
```

### Phase 2A（收敛基础层）

Phase 2A 明确只做路径基础设施：

```text
Workspace 配置加载
统一路径解析器
写路径安全校验
```

Phase 2A 的实施边界：

```text
不改变现有命令行为
不改变当前生成视图写入路径
不引入迁移命令
```

也就是说，Phase 2A 先把基础能力准备好，后续 Phase 2B/3 再逐步把各命令的写入目标迁移到新 canonical 路径。

## 11.3 Phase 3：可选 dual-write / export

允许命令写 canonical `.harbor/views`，并可选导出到 legacy 位置。

示例：

```yaml
views:
  canonical_root: .harbor/views
  export_docs_enabled: true
  export_docs_root: docs/harbor
```

## 11.4 Phase 4：迁移命令

新增：

```powershell
harbor workspace migrate --dry-run
harbor workspace migrate --write
```

迁移命令应：

```text
展示计划移动
默认不删除旧文件
保留旧文件除非用户明确确认
生成迁移报告
```

## 11.5 Phase 5：默认切换

兼容期后，默认切换到：

```text
.harbor/views/
.harbor/diary/
.harbor/reports/
```

---

## 12. 建议的 `.harbor/config/harbor.yaml`

```yaml
version: 1

workspace:
  root: .harbor

config:
  root: .harbor/config

policy:
  root: .harbor/policy

state:
  root: .harbor/state
  git: ignore

cache:
  root: .harbor/cache
  git: ignore

views:
  canonical_root: .harbor/views
  git: track
  export:
    docs:
      enabled: false
      root: docs/harbor

l2:
  canonical_root: .harbor/views/l2
  export:
    module_readme:
      enabled: true

modules:
  capsule_root: .harbor/views/modules

diary:
  root: .harbor/diary
  git: track

reports:
  root: .harbor/reports
  git: track_selected

integrations:
  root: .harbor/integrations
  exports:
    codex_skills:
      enabled: true
      root: .agents/skills
    claude_skills:
      enabled: false
      root: .claude/skills
```

---

## 13. 对工具能力的影响

## 13.1 `harbor doctor`

未来 doctor 应检查：

```text
config root 是否存在
policy root 是否存在
state root 是否被 ignore
cache root 是否被 ignore
views root 是否存在
diary root 是否存在（若启用）
reports root 是否存在（若启用）
exports 是否一致
```

## 13.2 `harbor stale`

stale 应优先检查 canonical views：

```text
.harbor/views/
```

如果开启 export，再检查 exported views。

Phase 2D-B 落地状态：

```text
canonical L2 freshness 仅由 .harbor/views/l2/<module>/README.md 判定
module README export 以独立 view 名 l2_readme_export 进行 advisory 报告
canonical 不可用时，export 状态为 unknown/skipped，不执行 out-of-sync 比较
export disabled 必须显式展示为 disabled 且不计入 warn
legacy .harbor/l2_meta.json advisory 仅由 harbor doctor 提示（stale 不提示）
doctor 可因 export mismatch / legacy metadata 给出 WARN，但不应 FAIL
legacy diary advisory（specs/diary/*.jsonl）仅由 harbor doctor 提示（stale 文本/JSON 不提示）
该 diary advisory 属于 workspace layout / project memory 提示，不属于 derived view freshness
specs/diary 仅在存在 *.jsonl 时提示；空目录不提示；多个 legacy 文件只提示一条
doctor 对 legacy diary 只做 read-compatible advisory：canonical 为 .harbor/diary，新写入仅 .harbor/diary
不自动迁移、不自动删除、不写 specs/diary
```

## 13.3 `harbor finish --sync-context`

未来行为：

```text
写入 canonical views 到 .harbor/views
可选导出到 docs/harbor 或 module README 路径
```

## 13.4 `harbor project structure --write`

未来行为：

```text
写入 .harbor/views/project-structure.md
```

可选：

```text
导出 docs/harbor/project-structure.md
```

Phase 2B 当前落地状态：

```text
canonical 写入默认已启用
docs export 默认关闭（需 views.export.docs.enabled=true 显式开启）
preview 仍为只读（不写文件）
```

## 13.5 `harbor module seal --write`

未来行为：

```text
写入 .harbor/views/modules/<module>/
```

可选：

```text
导出 docs/harbor/modules/<module>/
```

Phase 2C 当前落地状态：

```text
canonical 写入默认已启用（.harbor/views/modules/<module>/）
docs export 默认关闭（需 views.export.docs.enabled=true 显式开启）
stale 判定默认仅基于 canonical module-card
promote-skill 默认引用 canonical capsule 路径
legacy docs capsule 不自动删除或覆盖
```

---

## 14. 事实源规则

Harbor 应维护以下不变量。

### Invariant 1

```text
Generated views are not source of truth.
```

生成视图不是事实源。

### Invariant 2

```text
.harbor/state and .harbor/cache are local and should not be manually edited.
```

`.harbor/state` 和 `.harbor/cache` 是本地机器状态，不应手动编辑。

### Invariant 3

```text
.harbor/config and .harbor/policy are shared project configuration.
```

`.harbor/config` 和 `.harbor/policy` 是共享项目配置与策略。

### Invariant 4

```text
.harbor/diary is project memory and should normally be versioned.
```

`.harbor/diary` 是项目记忆，通常应进入版本管理。

### Invariant 5

```text
External tool files are export targets, not canonical Harbor storage.
```

外部工具文件是导出目标，不是 Harbor 主存储。

### Invariant 6

```text
Human design docs live under docs/design, not .harbor.
```

人类设计文档放在 `docs/design`，不放在 `.harbor`。

---

## 15. 推荐初始 `.gitignore`

```gitignore
# Harbor local state
.harbor/state/
.harbor/cache/

# Harbor export staging
.harbor/exports/

# Local-only reports
.harbor/reports/tmp/
.harbor/reports/local/
```

不要默认忽略整个 `.harbor/`。

否则会隐藏重要的共享治理资产，例如：

```text
.harbor/config/
.harbor/policy/
.harbor/diary/
selected .harbor/views/
```

---

## 16. 推荐 v1.3.1 实施计划

## Step 1：增加布局设计文档

```text
docs/design/harbor-workspace-layout-v1.md
```

不改变运行行为。

## Step 2：增加配置加载支持

引入：

```text
.harbor/config/harbor.yaml
```

支持读取 workspace roots。

## Step 3：增加统一路径解析器

创建中心路径解析器：

```python
HarborWorkspacePaths
```

负责解析：

```text
views_root
modules_view_root
project_structure_path
diary_root
reports_root
state_root
cache_root
exports_root
```

## Step 4：把 project structure 写入路径放到配置之后

允许配置：

```yaml
views:
  canonical_root: .harbor/views
```

同时保留当前默认行为以兼容。

Phase 2B 落地更新：

```text
`harbor project structure --write` 默认写入 canonical
.harbor/views/project-structure.md
并支持按配置可选导出到 docs/harbor/project-structure.md
```

## Step 5：把 module capsule 路径放到配置之后

将硬编码路径迁移到 `HarborWorkspacePaths`。

## Step 6：迁移 diary 路径

支持：

```text
.harbor/diary/
```

如果旧路径存在，继续读取：

```text
specs/diary/
```

## Step 7：新增 workspace inspect

新增只读命令：

```powershell
harbor workspace inspect
```

它应展示：

```text
当前配置的根路径
哪些路径存在
哪些路径被 Git 追踪或忽略
是否检测到 legacy paths
迁移建议
```

Phase 2F-A 实现说明：

```text
inspect 仅报告与提示
不做迁移/删除/写入副作用
workspace migrate 仍属于后续阶段
```

## Step 8：新增 dry-run migration

新增：

```powershell
harbor workspace migrate --dry-run
```

默认不写文件。

---

## 17. V1 非目标

该布局设计不要求立即实现：

```text
自动迁移
删除 legacy 文件
立即切换所有默认路径
CI 集成
多工具导出同步
project-map.json
context plan
contract graph
```

---

## 18. 开放问题

### 18.1 `.harbor/views/` 是否默认进入 Git？

推荐：

```text
harbor-spec 自身进入 Git
用户项目可配置
```

### 18.2 L2 README 是否继续放在模块旁边？

推荐：

```text
作为 export target 支持
不要作为 canonical storage
```

### 18.3 dogfooding reports 是否进入 Git？

推荐：

```text
release validation reports 进入 Git
temporary local reports 不进入 Git
```

### 18.4 `.agents/skills/` 是否进入 Git？

推荐：

```text
可选
```

如果进入 Git，应明确说明它是外部集成导出结果。

---

## 19. 总结

Harbor 应采用统一工作区模型：

```text
.harbor/ = Harbor canonical workspace
docs/design/ = 人类编写的设计文档
docs/harbor/ = 可选发布文档导出目标
.agents/.claude/.cursor = 外部工具导出目标
```

推荐布局：

```text
.harbor/
  config/
  policy/
  state/
  views/
  diary/
  reports/
  exports/
  integrations/
  cache/
```

这套布局为以下能力提供清晰基础：

```text
项目结构视图
模块胶囊
Diary 记忆
dogfooding 报告
工具集成
未来 context planning
未来 contract graph
未来 CI integration
```

最重要的原则是：

```text
Harbor 应该拥有自己的工作区。
生成上下文应该结构化、可发现，并与人类设计文档、外部工具导出文件清晰分离。
```

```
```

# Harbor-spec v1.3.0 — Canonical Workspace 与 Agentic Context Governance

状态：正式版  
发布类型：重大工作流 / 工作区 / AI Agent 集成更新

Harbor-spec v1.3.0 是 Harbor-spec 从“契约 / 漂移检测工具”进一步升级为 **面向 AI Coding / Agentic Coding 的上下文治理引擎** 的关键版本。

本版本正式确立 `.harbor/` 作为 Harbor 的 canonical workspace，统一生成上下文视图、模块胶囊、决策记忆、运行时安全规则、AI 工具入口规则与 skills 工作流。

本版本的核心原则是：

```text
AI 可以快速写代码，但契约、测试、生成上下文、决策记忆和安全边界不能漂移。
```

---

## 1. 发布亮点

### 1.1 Canonical `.harbor/` Workspace

Harbor-spec v1.3.0 正式使用 `.harbor/` 作为 canonical workspace。

标准结构：

```text
.harbor/
  config/
    harbor.yaml

  rules/
    glossary.md
    agent-policy.md
    contract-rules.md
    ddt-rules.md
    runtime-safety.md
    diary-rules.md
    project-rules-guide.md
    project-rules.md

  views/
    project-structure.md

    l2/
      _meta.json
      <module>/
        README.md

    modules/
      <module>/
        module-card.md
        review-checklist.md
        debug-playbook.md

  diary/
    YYYY-MM.jsonl

  reports/

  cache/

  state/

  exports/
```

核心边界：

```text
.harbor/rules/**
  静态 Harbor 规则文档。

.harbor/views/**
  canonical generated context views，即生成上下文视图。

.harbor/diary/**
  canonical decision memory，即决策记忆。

.harbor/cache/**
.harbor/state/**
  运行时产物，不是 source of truth。

.agents/skills/**
  外部 AI 工具 workflow export，不是 source of truth。
```

---

### 1.2 Workflow Facade

v1.3.0 将 AI Coding 的默认 Harbor 工作流统一为：

```powershell
harbor start
harbor checkpoint
harbor finish --sync-context
harbor stale
harbor doctor
```

推荐理解：

```text
start
  开始一次 Harbor 管理下的 AI coding 任务。

checkpoint
  开发过程中检查契约 / 实现 / DDT / 漂移状态。

finish --sync-context
  收尾并同步 changed L2 README 与 Module Capsule。

stale
  检查生成上下文是否过时。

doctor
  检查 Harbor workspace 整体健康状态。
```

以下命令不属于默认任务流，必须由用户显式请求后再运行：

```powershell
harbor log
harbor accept
harbor lock
harbor module promote-skill <module>
```

---

### 1.3 Generated Context Views

Harbor 生成上下文统一位于：

```text
.harbor/views/**
```

包括：

```text
.harbor/views/project-structure.md
.harbor/views/l2/<module>/README.md
.harbor/views/l2/_meta.json
.harbor/views/modules/<module>/module-card.md
.harbor/views/modules/<module>/review-checklist.md
.harbor/views/modules/<module>/debug-playbook.md
```

生成上下文用于帮助人类与 AI agent 快速理解项目，但它不是 source of truth。

如果 `.harbor/views/**` 与源码、测试、schema、policy 或 diary 冲突，应视为 generated context stale，并通过 Harbor 命令重新生成。

---

### 1.4 Module Capsule

Module Capsule 成为 v1.3.0 的一等生成上下文能力。

每个模块胶囊包含：

```text
module-card.md
review-checklist.md
debug-playbook.md
```

canonical 路径：

```text
.harbor/views/modules/<module>/
```

相关命令：

```powershell
harbor module inspect <module>
harbor module seal <module> --write
harbor module seal --changed --write
harbor module seal --all --write
harbor module stale <module>
harbor module promote-skill <module>
```

其中：

```powershell
harbor module promote-skill <module>
```

会将模块上下文导出为 `.agents/skills/**` 下的外部 AI 工具 skill，因此必须由用户显式请求后再运行。

---

### 1.5 Workspace Inspect 与 Migration Dry-run

v1.3.0 新增只读 workspace 诊断命令：

```powershell
harbor workspace inspect
harbor workspace inspect --format json
```

用于查看当前 Harbor workspace 状态，包括 canonical paths、generated views、policy files、Git tracking、advisory summary 等。

同时新增只读迁移规划命令：

```powershell
harbor workspace migrate --dry-run
harbor workspace migrate --dry-run --format json
```

重要边界：

```text
harbor workspace migrate --dry-run 是只读诊断 / 规划命令。
它不能写文件、移动文件、删除文件或修改工作区。
```

v1.3.0 不实现：

```powershell
harbor workspace migrate --write
```

如果执行未带 `--dry-run` 的 migrate，应返回非零退出并提示当前版本只支持 dry-run。

---

### 1.6 Stale 与 Doctor

v1.3.0 正式稳定顶层 advisory checks：

```powershell
harbor stale
harbor stale --format json

harbor doctor
harbor doctor --format json
```

含义：

```text
harbor stale
  关注 generated context freshness，即生成上下文是否过时。

harbor doctor
  关注 Harbor workspace health，即 Harbor 工作区整体健康状态。
```

二者均保持 advisory + read-only 语义。

---

### 1.7 Diary Canonicalization

Diary 决策记忆的 canonical 写入路径变为：

```text
.harbor/diary/YYYY-MM.jsonl
```

Diary 用于记录重要决策为什么发生。

它不是 changelog 的替代品。

它不是 commit message 的替代品。

`harbor log` 会写入 Diary，因此必须由用户显式请求后再执行。

---

### 1.8 AI Tool Integration Pack

v1.3.0 完成 AI Coding 工具集成文件体系收口。

核心文件：

```text
AGENTS.md
  跨工具轻量入口。

.harbor/rules/agent-policy.md
  Harbor 总政策说明。

.harbor/rules/project-rules-guide.md
  Project Rules 生成与维护指南。

.harbor/rules/project-rules.md
  当前项目的项目专属规则。

.harbor/rules/contract-rules.md
  Contract 治理规则。

.harbor/rules/ddt-rules.md
  DDT 规则。

.harbor/rules/diary-rules.md
  决策记忆规则。

.harbor/rules/runtime-safety.md
  运行时安全规则。

.harbor/rules/glossary.md
  Harbor 术语表。

.agents/skills/**
  按需加载的 AI workflow skills。

Tool role-rules
  TRAE / Cursor / Claude Code / Codex 等工具的轻量适配层。
```

官方 skills：

```text
harbor-contract-change
harbor-code-review
harbor-ddt-diary
harbor-safety-preflight
harbor-context-refresh
harbor-workspace-migration-plan
```

---

### 1.9 Source of Truth Priority Clarification (P0-2)

v1.3.0 文档规则补充明确：

- Source of Truth Priority 与 Instruction Hierarchy 是两个不同层级：
  - Instruction Hierarchy 处理规则/指令冲突；
  - Source of Truth Priority 处理 contract/tests/implementation/generated/export 的事实冲突。
- generated context integrity metadata 是 advisory integrity signal，不是 truth override。
- `.harbor/views/**` 是 canonical generated context，但 generated views 不是 source of truth。
- `Canonical wins` 仅用于 canonical artifact 与 legacy/export copy 冲突，不用于 generated views 覆盖 contracts、DDT/tests 或 implementation。
- 冲突必须按 `semantic drift` / `contract gap` 标记并通过测试/DDT/人工确认裁决，不做静默自动裁决。

### 1.10 Contract Impact Classifier MVP (P0-3)

v1.3.0 新增 Contract Impact Classifier MVP（checkpoint advisory）：

- 在 `harbor checkpoint` 输出中新增 Contract Impact 分类摘要。
- 分类级别：`no_contract_impact` / `possible_contract_impact` / `confirmed_contract_impact` / `unknown`。
- `confirmed_contract_impact` 表示确认存在 contract surface 变化，不表示 bug 或 breaking change。
- `possible_contract_impact` 作为默认保守分类；对 public CLI、JSON output、write target、generated view format、source-of-truth rules 相关变化不会轻易归入 no impact。
- classifier 语义为 advisory / conservative / explainable，不替代人工评审、DDT 或语义审计。

---

## 2. 新增能力

### 2.1 Workflow Facade Commands

新增或正式化：

```powershell
harbor start
harbor checkpoint
harbor finish
harbor finish --sync-context
harbor stale
harbor doctor
```

其中：

```powershell
harbor finish --sync-context
```

用于在任务收尾时显式同步 changed L2 README 与 Module Capsule。

`harbor accept` 仍保留为 `harbor lock` 的语义化别名，但不属于默认 facade 工作流，只有在用户明确要接受新基线时才运行。

---

### 2.2 L2 README Refresh Modes

新增或正式化：

```powershell
harbor docs --module <module> --write
harbor docs --changed --write
harbor docs --all --write
```

canonical L2 README 路径：

```text
.harbor/views/l2/<module>/README.md
```

canonical L2 metadata 路径：

```text
.harbor/views/l2/_meta.json
```

---

### 2.3 Module Capsule Commands

新增或正式化：

```powershell
harbor module inspect <module>
harbor module seal <module> --write
harbor module seal --changed --write
harbor module seal --all --write
harbor module stale <module>
harbor module promote-skill <module>
```

canonical Module Capsule 路径：

```text
.harbor/views/modules/<module>/
```

---

### 2.4 Project Structure View

新增或正式化：

```powershell
harbor project structure
harbor project structure --write
```

canonical project structure 路径：

```text
.harbor/views/project-structure.md
```

行为：

```text
harbor project structure
  preview-only，不写文件。

harbor project structure --write
  写入 canonical project structure view。
```

---

### 2.5 Workspace Diagnostics

新增：

```powershell
harbor workspace inspect
harbor workspace inspect --format json
```

该命令用于报告 workspace canonical paths、generated views、policy files、advisory status 和 workspace layout 信息。

它是只读命令。

---

### 2.6 Workspace Migration Dry-run

新增：

```powershell
harbor workspace migrate --dry-run
harbor workspace migrate --dry-run --format json
```

该命令只生成迁移 / 清理规划，不执行迁移动作。

JSON 输出应是单个对象，并明确声明不写文件。

期望 invariant：

```json
{
  "mode": "dry_run",
  "writes_files": false
}
```

---

### 2.7 JSON Output

新增或正式化以下命令的机器可读输出：

```powershell
harbor stale --format json
harbor doctor --format json
harbor workspace inspect --format json
harbor workspace migrate --dry-run --format json
```

JSON 输出要求：

```text
- 尽量保持 deterministic。
- 路径尽量规范化。
- 除非明确需要，不泄露机器本地绝对路径。
- 输出单个 JSON object，便于 AI / CI / 脚本消费。
```

---

### 2.8 AI Rules and Skills

新增或正式化：

```text
AGENTS.md
.harbor/rules/agent-policy.md
.harbor/rules/project-rules-guide.md
.harbor/rules/project-rules.md
.harbor/rules/contract-rules.md
.harbor/rules/ddt-rules.md
.harbor/rules/diary-rules.md
.harbor/rules/runtime-safety.md
.harbor/rules/glossary.md

.agents/skills/harbor-contract-change/SKILL.md
.agents/skills/harbor-code-review/SKILL.md
.agents/skills/harbor-ddt-diary/SKILL.md
.agents/skills/harbor-safety-preflight/SKILL.md
.agents/skills/harbor-context-refresh/SKILL.md
.agents/skills/harbor-workspace-migration-plan/SKILL.md
```

---

## 3. 变更内容

### 3.1 Workspace Paths

canonical config 写入路径变更为：

```text
.harbor/config/harbor.yaml
```

canonical generated context 路径变更为：

```text
.harbor/views/project-structure.md
.harbor/views/l2/<module>/README.md
.harbor/views/l2/_meta.json
.harbor/views/modules/<module>/
```

canonical diary 写入路径变更为：

```text
.harbor/diary/YYYY-MM.jsonl
```

运行时路径：

```text
.harbor/cache/**
.harbor/state/**
```

是 runtime artifacts，不应被当作 source of truth。

---

### 3.2 Generated Context Behavior

```powershell
harbor project structure --write
```

现在写入：

```text
.harbor/views/project-structure.md
```

```powershell
harbor docs --write
```

现在写入 canonical L2 README：

```text
.harbor/views/l2/<module>/README.md
```

```powershell
harbor module seal --write
```

现在写入 canonical capsule files：

```text
.harbor/views/modules/<module>/
```

```powershell
harbor stale
```

现在评估 canonical generated views，不把 optional exports 当成 canonical storage。

canonical generated markdown views 现在统一带有 integrity frontmatter，包含：

```text
generated_by
harbor_version
view_type
module
generated_at
generation_command
stale_policy
source_paths
source_fingerprint
contract_fingerprint
generator_fingerprint
```

其中 `generated_at` 仅用于信息展示；stale 比较会忽略该字段，且在输入与生成内容不变时会复用旧值，避免每次重生成产生无意义 Git diff。

---

### 3.3 Module Capsule Behavior

`module-card.md` 保留 deterministic capsule fingerprint 语义（`view_fingerprint`/`fingerprint`），作为 module capsule stale 主判定依据。

`source_fingerprint` 属于 integrity metadata，不替代 capsule fingerprint 主语义。

```powershell
harbor module stale
```

从以下路径评估 canonical capsule freshness：

```text
.harbor/views/modules/<module>/module-card.md
```

```powershell
harbor module promote-skill
```

引用 canonical capsule 路径：

```text
.harbor/views/modules/<module>/
```

并导出到：

```text
.agents/skills/**
```

---

### 3.4 Doctor Behavior

```powershell
harbor doctor
```

现在检查更广泛的 Harbor workspace health，包括：

```text
configuration
workspace state
DDT quick checks
generated views
skill references
runtime safety
compatibility advisories
```

Doctor 保持 advisory + read-only。

---

### 3.5 Stale Behavior

```powershell
harbor stale
```

检查 canonical generated context freshness。

它应基于：

```text
.harbor/views/**
```

判断生成上下文新鲜度。

如启用 optional exports，可单独报告 export status，但 export 不应影响 canonical freshness 判断。

---

### 3.6 Diary Behavior

Diary 新写入路径：

```text
.harbor/diary/YYYY-MM.jsonl
```

Diary 读取可以在兼容场景中合并已有决策记录，但新写入必须使用：

```text
.harbor/diary/**
```

默认不自动迁移、不自动删除、不自动清理旧文件。

---

### 3.7 `.gitignore` Policy

`.harbor/` 不应整体加入 `.gitignore`。

推荐策略：

```text
track:
  .harbor/config/
  .harbor/rules/
  .harbor/views/project-structure.md
  .harbor/diary/
  selected .harbor/reports/

ignore:
  .harbor/cache/
  .harbor/state/
  .harbor/exports/
  .harbor/reports/tmp/
  .harbor/reports/local/
```

具体 tracking 策略可由项目自行调整。

---

## 4. 兼容性与迁移说明

全新的 v1.3.0 项目应从一开始就使用 `.harbor/` 作为 canonical workspace。

canonical 路径：

```text
Config:
  .harbor/config/harbor.yaml

Rule docs:
  .harbor/rules/**

Generated context:
  .harbor/views/**

Decision memory:
  .harbor/diary/YYYY-MM.jsonl

Reports:
  .harbor/reports/**

Runtime cache:
  .harbor/cache/**

Runtime state:
  .harbor/state/**

External skills:
  .agents/skills/**
```

从 pre-v1.3.0 升级的已有仓库，建议先运行：

```powershell
harbor workspace inspect
harbor workspace migrate --dry-run
```

再考虑任何人工清理。

Migration dry-run 是只读的。

它不会：

```text
copy files
move files
delete files
rewrite files
modify AGENTS.md
modify .harbor/**
modify .agents/skills/**
append diary entries
change baseline
```

v1.3.0 不实现：

```powershell
harbor workspace migrate --write
```

---

## 5. Runtime Safety

任何命令都不应静默执行高风险操作。

以下命令必须由用户显式请求：

```powershell
harbor log
harbor accept
harbor lock
harbor module promote-skill <module>
```

安全规则：

```text
- 不要用 harbor accept 隐藏 unresolved drift。
- 不要在用户未请求时运行 harbor log。
- 不要在普通 coding 或 context refresh 中自动 promote skill。
- 不要在未确认时修改 .harbor/*.yaml。
- 不要在未确认时大范围修改 .agents/skills/**。
- 不要手动编辑 .harbor/views/** 并把它当 source of truth。
```

优先使用：

```text
read-only inspection
dry-run
PowerShell -WhatIf
list files before deletion
show diff before writing
backup before rewrite
rollback plan
```

---

## 6. 发布验证快照

v1.3.0 release freeze 最终验证快照：

```text
pytest:
  280 passed

harbor workspace inspect --format json:
  single JSON object
  writes_files=false

harbor workspace migrate --dry-run --format json:
  single JSON object
  writes_files=false

harbor doctor --format json:
  single JSON object
  advisory WARN baseline accepted

harbor stale --format json:
  single JSON object
  status=pass
```

验证范围：

```text
final tests
JSON contract smoke
dry-run no-write checks
documentation consistency close-out
working tree classification
```

---

## 7. 升级检查清单

新项目建议：

```powershell
harbor init
harbor start
harbor checkpoint
harbor finish --sync-context
harbor stale
harbor doctor
```

已有项目升级到 v1.3.0：

```powershell
harbor workspace inspect
harbor workspace migrate --dry-run
harbor stale
harbor doctor
```

发布前信心检查：

```powershell
pytest
harbor checkpoint
harbor stale
harbor doctor
harbor workspace inspect --format json
harbor workspace migrate --dry-run --format json
```

不要运行以下命令，除非你明确知道自己要这么做：

```powershell
harbor accept
harbor log
harbor lock
harbor module promote-skill <module>
```

---

## 8. v1.3.0 不包含的内容

v1.3.0 不实现：

```text
automatic workspace migration write phase
automatic workspace cleanup
automatic deletion of non-canonical artifacts
automatic diary migration
automatic skill promotion
CI hard gate mode
backup / rollback write migration
full migration conflict resolver
```

这些属于后续版本方向。

---

## 9. 后续方向

可能的后续迭代包括：

```text
workspace migrate --write with backup / rollback / per-item confirmation
CI mode for stale / doctor
policy-driven governance via .harbor/policy.yaml and .harbor/safety.yaml
improved semantic audit noise control
skill stale detection
skill fingerprint binding to Module Capsule
multi-tool skill export adapters
task-level context planning
```

---

# Harbor-spec v1.2.0 — The Industrial Update

## 🚀 Major Features

* Smart Configuration：`harbor init` 自动探测 Django、Node.js、Go、Java 技术栈并融合 `.gitignore` 规则。
* SQLite Backend：以 SQLite（WAL 模式）替代 JSON 索引，降低内存占用、提升启动速度并改善并发安全。
* Parallel Indexing：`harbor lock` 利用多核 CPU 并行解析与哈希，提升构建吞吐。

## ⚡ Performance

* 在超大仓库中显著降低索引内存占用。
* 通过增量数据库查询提升 `harbor status` 检测速度。

## 🛠 Improvements

* CLI 2.0：动词化命令集，包括 `lock`、`check`、`log`、`adopt`。
* DDT Integration：`harbor check` 统一语义审计与测试绑定校验。
* Windows Support：路径归一化与并行处理适配 Windows / PowerShell 工作流。

## 🔧 Migration Notes

* 缓存索引路径：`.harbor/cache/harbor.db`。
* 旧命令映射：

  * `st` → `status`
  * `ddt validate` → `check --fast`
  * `diary export` → `log --export`
  * `decorate` → `adopt`
  * `gen l2` → `docs`

## 📦 Upgrade Checklist

* 运行 `harbor init` 以生成或更新配置。
* 运行 `harbor lock` 构建基线。
* 使用 `harbor status` 验证变更检测。
* 使用 `harbor check` 或 `harbor check --fast` 验证 DDT 绑定与语义一致性。

## 📝 Acknowledgements

感谢所有贡献者在 Harbor-spec 工业级能力演进中的努力。

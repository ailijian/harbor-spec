# Harbor-spec v1.3.0

让 AI 写代码可以快，但契约、测试、生成上下文、决策记忆和安全边界不能漂移。

Language: [中文](README.v1.3.0.zh.md) | [当前 README](README.md) | [English](README.en.md)

---

## Harbor 是什么

`harbor-spec` 是一个面向 AI Coding / Agentic Coding 的上下文治理引擎。

它不替代 IDE，也不替代代码生成工具；它负责把以下内容持续对齐：

- 实现与契约
- 代码与测试
- 代码与派生上下文
- 行为变更与决策记忆
- 日常开发与运行时安全边界

在 1.3.0 中，Harbor 明确采用 `.harbor/` 作为 canonical workspace，并围绕工作流门面命令、派生视图、模块胶囊、工作区诊断和只读迁移规划建立统一模型。

## 它解决什么问题

AI 协作开发最常见的问题，不是“代码写不出来”，而是“写完以后开始漂移”：

- 代码改了，Docstring、README、JSON 输出或 CLI 语义没跟上
- 测试仍在验证旧契约，出现“假绿灯”
- 团队知道做了什么，却不知道为什么这样做
- 派生文档和工具导出文件越来越多，但事实源边界越来越模糊

Harbor 的目标是把这些问题显式化、可检查、可追踪、可收尾。

## 1.3.0 重点能力

- `Workflow Facade`：提供 `harbor start`、`harbor checkpoint`、`harbor finish`、`harbor finish --sync-context`
- `Context Drift Detection`：通过索引、状态比对与语义检查识别 drift、modified、contract_changed、untracked、missing
- `DDT Validation`：用 `harbor check --fast` 验证测试是否仍绑定到正确契约版本
- `L2 README`：通过 `harbor docs` 生成模块级上下文视图，canonical 路径为 `.harbor/views/l2/<module>/README.md`
- `Module Capsule`：通过 `harbor module seal` 生成 `module-card.md`、`review-checklist.md`、`debug-playbook.md`
- `Project Structure View`：通过 `harbor project structure --write` 生成项目级结构总览
- `Health Checks`：用 `harbor stale` 检查派生视图新鲜度，用 `harbor doctor` 检查 Harbor workspace 健康
- `Workspace Diagnostics`：用 `harbor workspace inspect` 查看 canonical/legacy 路径、Git tracking 与 advisory
- `Migration Planning`：用 `harbor workspace migrate --dry-run` 生成只读迁移计划
- `Decision Memory`：用 `harbor log` 写入 `.harbor/diary/YYYY-MM.jsonl`

## 核心原则

### 1. 生成视图不是事实源

`.harbor/views/**`、模块旁边导出的 `README.md`、以及 `.agents/skills/**` 都可以帮助人和 AI 快速理解上下文，但它们不是事实源。

事实源始终优先于派生物：

- 源码
- 契约与类型
- 测试
- 配置
- `.harbor/policy.yaml`
- `.harbor/safety.yaml`
- `.harbor/diary/**`

### 2. `.harbor/` 是 canonical workspace

1.3.0 推荐结构如下：

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

  views/
    project-structure.md
    l2/
      _meta.json
      <module>/README.md
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

边界说明：

- `.harbor/views/**`：canonical generated context
- `.harbor/diary/**`：canonical decision memory
- `.harbor/cache/**`、`.harbor/state/**`：运行时产物，不是事实源
- `.agents/skills/**`：外部工具导出目标，不是 canonical storage
- `docs/design/**`：人工撰写的设计文档，应与运行时/派生产物分离

### 3. 只读检查与写入命令分离

Harbor 在 1.3.0 中明确区分“检查”与“写入”：

- `harbor stale`：只读，检查派生视图是否过期
- `harbor doctor`：只读，检查整体工作区健康
- `harbor workspace inspect`：只读，查看工作区布局
- `harbor workspace migrate --dry-run`：只读，仅生成迁移计划
- `harbor docs --write`、`harbor module seal --write`、`harbor project structure --write`：显式写入派生视图

## 安装

### 从 PyPI 安装

```bash
pip install harbor-spec
```

### 在仓库中本地开发

```bash
pip install -e .[dev]
```

要求：

- Python `3.9+`
- 默认 CLI 入口：`harbor`

## 快速开始

### 1. 初始化

在你的项目根目录执行：

```powershell
harbor init
```

Harbor 会自动探测代码根目录，并写入 `.harbor/config/harbor.yaml`。

### 2. 建立或更新基线

```powershell
harbor lock
```

该命令会构建索引并将当前契约快照写入缓存，用于后续 drift 检测。

### 3. 按推荐流程完成一次 AI Coding 任务

```powershell
harbor start
# AI coding
harbor checkpoint
# more AI coding
harbor finish --sync-context
harbor stale
harbor doctor
```

推荐理解：

- `harbor start`：开始任务前查看上下文状态
- `harbor checkpoint`：开发中执行 `status + check --fast`
- `harbor finish --sync-context`：收尾时同步 changed L2 README 与 changed Module Capsule
- `harbor stale`：确认派生视图是否仍然新鲜
- `harbor doctor`：确认工作区是否存在配置、索引、派生视图、技能引用等层面的告警

## 工作流命令语义

### Workflow Facade

```powershell
harbor start
harbor checkpoint
harbor finish
harbor finish --sync-context
harbor stale
harbor doctor
```

关键语义：

- `harbor finish` 不会自动 `lock`
- `harbor finish` 不会自动 `log`
- `harbor finish` 默认不会写 L2 README、Project Structure 或 Module Capsule
- `harbor finish --sync-context` 会写 changed L2 README 与 changed Module Capsule，并对 changed capsule 执行 stale 检查
- `harbor stale` 用于只读检查派生视图是否过时
- `harbor doctor` 用于只读检查 Harbor workspace 整体健康状态
- `harbor accept` 是 `harbor lock` 的语义化别名，但不属于默认 facade 工作流

### 只读健康检查

```powershell
harbor stale
harbor stale --format json

harbor doctor
harbor doctor --format json
```

二者差异：

- `harbor stale` 关注派生视图 freshness
- `harbor doctor` 关注 Harbor workspace health

`harbor stale` 默认检查 changed modules，可用 `--all` 或 `--module <module>` 切换范围。  
`harbor doctor` 默认也是 changed scope，可用 `--all` 或 `--module <module>` 切换范围。

### 工作区诊断与迁移预览

```powershell
harbor workspace inspect
harbor workspace inspect --format json

harbor workspace migrate --dry-run
harbor workspace migrate --dry-run --format json
```

注意：

- `harbor workspace inspect` 是只读 advisory 命令
- `harbor workspace migrate --dry-run` 只生成 migration plan，不复制、移动、删除文件
- 当前版本不实现 `harbor workspace migrate --write`
- 未显式传入 `--dry-run` 时，`workspace migrate` 会报错提示当前仅支持 dry-run

## 生成上下文能力

### L2 README

```powershell
harbor docs --module harbor/core
harbor docs --module harbor/core --write
harbor docs --changed --write
harbor docs --all --write
```

说明：

- 默认 preview，不写文件
- `--write` 才会写入派生文档
- canonical 路径为 `.harbor/views/l2/<module>/README.md`
- 默认可额外导出 `<module>/README.md`
- `.harbor/l2_meta.json` 仅 legacy 兼容读取，不再作为写入目标

### Module Capsule

```powershell
harbor module inspect harbor/core
harbor module seal harbor/core
harbor module seal harbor/core --write
harbor module stale harbor/core
harbor module seal --changed --write
harbor module seal --all --write
harbor module promote-skill harbor/core
```

说明：

- Module Capsule 是派生维护视图，不是事实源
- `harbor module seal` 默认 preview，`--write` 才会写文件
- canonical 路径为 `.harbor/views/modules/<module>/`
- `harbor module stale` 是只读检查
- `harbor module promote-skill` 会生成薄 skill 入口到 `.agents/skills/**`
- 推荐先确保 capsule 已存在且为最新，再执行 `harbor module promote-skill`

### Project Structure View

```powershell
harbor project structure
harbor project structure --write
```

说明：

- 默认 preview，不写文件
- `harbor project structure --write` 默认写入 `.harbor/views/project-structure.md`
- `docs/harbor/project-structure.md` 只是可选导出目标，不是 canonical storage
- Project Structure View 是派生视图，不替代源码、规则文档和测试

## DDT 与语义检查

### DDT 校验

```powershell
harbor check --fast
```

这会扫描测试中的 DDT 绑定，并验证测试是否仍然绑定到正确的契约版本。

示例：

```python
from harbor.core.ddt import harbor_ddt_target

@harbor_ddt_target("backend.core.calculate_tax", l3_version=1)
def test_calculate_tax():
    ...
```

### 完整检查

```powershell
harbor check
```

完整模式会在 DDT 之外，结合状态结果与 LLM provider 执行语义审计。

若需要启用语义审计与 AI Diary Draft，可配置：

```ini
HARBOR_LLM_PROVIDER=openai
HARBOR_LLM_API_KEY=sk-xxxxxx
HARBOR_LLM_BASE_URL=https://api.openai.com/v1
HARBOR_LANGUAGE=zh
```

## 接管存量项目

对于已有代码库，可以用 `adopt` 逐步纳入 Harbor 治理：

```powershell
harbor adopt backend/ --strategy safe
harbor adopt backend/ --strategy aggressive --dry-run
```

模式说明：

- `safe`：只处理已有 Docstring 但缺少 `@harbor.scope` 的函数
- `aggressive`：识别全部 public 函数，为缺失文档的函数插入模板
- `--dry-run`：只预览，不写文件

接管完成后，通常会继续执行：

```powershell
harbor lock
```

## 仓库维护建议

### `.gitignore`

不要把整个 `.harbor/` 一刀切忽略。

更合理的策略是：

```gitignore
.harbor/state/
.harbor/cache/
.harbor/exports/
.harbor/reports/tmp/
.harbor/reports/local/
```

通常应保留可追踪的内容：

- `.harbor/config/`
- `.harbor/rules/`
- `.harbor/views/project-structure.md`
- `.harbor/diary/`
- 需要共享的 `.harbor/views/**` 与 `.harbor/reports/**`

### 不要手工把派生视图当事实源

当 `.harbor/views/**` 与源码、测试、配置不一致时，应更新事实源，再重新生成视图，而不是直接手工修补派生文档来“掩盖漂移”。

## 命令速查

| 命令 | 作用 |
| --- | --- |
| `harbor init` | 初始化 Harbor 配置 |
| `harbor lock` | 构建索引并锁定当前契约快照 |
| `harbor start` | 工作流入口，开始 AI coding 前查看状态 |
| `harbor checkpoint` | 工作流检查点，等价 `status + check --fast` |
| `harbor finish` | 工作流收尾，执行 `status + check` |
| `harbor finish --sync-context` | 收尾并同步 changed L2 README 与 Module Capsule |
| `harbor stale` | 只读检查派生视图新鲜度 |
| `harbor doctor` | 只读检查 Harbor workspace 健康 |
| `harbor workspace inspect` | 只读查看 canonical/legacy 路径与 Git tracking |
| `harbor workspace migrate --dry-run` | 只读生成迁移计划 |
| `harbor docs --module <module> --write` | 写入单模块 canonical L2 README |
| `harbor docs --changed --write` | 写入 changed modules 的 L2 README |
| `harbor docs --all --write` | 写入全部 indexed modules 的 L2 README |
| `harbor module seal <module> --write` | 写入单模块 capsule |
| `harbor module seal --changed --write` | 写入 changed modules 的 capsule |
| `harbor module seal --all --write` | 写入全部 indexed modules 的 capsule |
| `harbor module stale <module>` | 只读检查单模块 capsule 是否过时 |
| `harbor module promote-skill <module>` | 手动导出模块 skill 入口 |
| `harbor project structure --write` | 写入项目级结构视图 |
| `harbor check --fast` | 执行 DDT 快速校验 |
| `harbor check` | 执行 DDT + 语义检查 |
| `harbor log` | 写入或草拟 Diary 记录 |
| `harbor config list` | 查看当前 Harbor 配置 |

## 兼容与别名

CLI 仍兼容一部分历史命令映射：

- `harbor st` -> `harbor status`
- `harbor conf` -> `harbor config`
- `harbor commit` -> `harbor lock`
- `harbor ddt validate` -> `harbor check --fast`
- `harbor decorate` -> `harbor adopt`
- `harbor gen l2` -> `harbor docs`

## 仓库开发与验证

在本仓库中，最直接的验证命令是：

```powershell
pytest
```

若你在开发 Harbor 自身，常见收尾顺序是：

```powershell
pytest
harbor checkpoint
harbor stale
harbor doctor
```

## License

MIT © 2025 Harbor-spec Authors.

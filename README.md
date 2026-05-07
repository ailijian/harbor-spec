<div align="center">

# ⚓ HarborSpec
### The Context Governance Engine for Vibe Coding

[![CI Status](https://img.shields.io/github/actions/workflow/status/your-org/harbor-spec/ci.yml?style=flat-square)](https://github.com/your-org/harbor-spec/actions)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue?style=flat-square)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![Strictness](https://img.shields.io/badge/Harbor-L3%20Strict-purple?style=flat-square)](https://github.com/your-org/harbor-spec)

**让 AI 像代码一样被管理，让上下文像 Git 一样可追溯。**
**它会辅助你完成“程序员到上下文工程师”的革命性转变。**

[理念] • [架构] • [快速开始] • [迁移指南] • [日常工作流] • [命令速查]

</div>

语言: [中文](README.md) | [English](README.en.md)

---

## 🌌 The Era of Vibe Coding

编程正在经历一场范式转移。我们正在从 "Writing Code"（逐行编写）转向 **"Vibe Coding"**（通过自然语言与 AI 协作生成）。

在这个新时代，**代码生成的边际成本趋近于零，但上下文维护的成本却在指数级上升。**
- AI 改了代码，Docstring 还没改？👉 **Context Drift (上下文漂移)**
- 测试用例还在测旧版本的逻辑？👉 **Validation Gap (验证断层)**
- 为什么上周我们要把这个参数改成 Optional？👉 **Memory Loss (决策遗忘)**

**Harbor** 应运而生。它是 **Copilot 的监管者**，是一套用于治理 AI 生成代码的 **"良知" (Conscience)** 与 **"记忆" (Memory)** 系统。

## 🛡️ Core Philosophy

Harbor 的核心设计理念基于 **L3 Contract Theory**：
1.  **Code is Volatile, Contract is Immutable**: 代码可由 AI 随意重写，但 L3 级契约（Docstring）是锚点，必须严格审计。
2.  **Noise is Signal**: 未索引的代码、未同步的文档，都是系统中的“噪音”。Harbor 将其显性化。
3.  **Trust, but Verify**: 信任 AI 的编码能力，但通过 AST 分析和 LLM 审计验证其产出。

## 🏗️ Architecture

```mermaid
graph TD
    Source[Source Code] -->|AST Parse| Adapter(Adapter)
    Adapter -->|Contract Hash| Index(L3 Index / Memory)
    Index -->|Compare| Sync(Sync Engine)
    Source -->|Body Hash| Sync
    Sync -->|Drift Detected| Status[CLI Status]
    Sync -->|Diff Target| Audit(Semantic Guard)
    Env[.env / LLM] --> Audit
    Audit -->|Semantic Check| Report[Audit Report]
    Tests[Test Cases] -->|DDT Binding| Validator(DDT Validator)
    Index -->|Version Match| Validator
    Index -->|Aggregation| L2(L2 Generator)
    User[Developer] -->|Log Decision| Diary(Diary / History)
```

-----

## ⚡ Quick Start

### 1\. Installation

```bash
pip install harbor-spec
```

### 2\. Initialize

在项目根目录运行初始化，Harbor 会自动探测项目结构并生成配置（包含 Git 感知过滤）：

```bash
harbor init
```

### 3\. Setup AI Role Rules (关键\!)

为了让 Trae/Cursor/Windsurf/Copilot 自动生成符合 Harbor 标准的代码，请配置 **Role Rules**。

<details>
<summary><strong>👉 点击展开：复制 Role Rules 到你的 .trae.role_rules 或 .cursorrules 或 .windsurfrules</strong></summary>

````markdown
# Harbor-spec L3 Documentation Standards

你是一个在此项目中工作的 **Harbor-spec 认证工程师**。
所有新编写或重构的 **Public API**（不以 `_` 开头的函数、类、方法）必须包含严格符合 **Harbor L3 Contract** 标准的 Docstring。

## 核心规则 (Critical Rules)
1.  **风格**: 使用 **Google Style** 格式，但增加了 Harbor 专用的扩展部分。
2.  **语言**: Docstring 的描述内容必须使用 **中文**。
3.  **强制标记**: 所有公共方法必须包含 `@harbor.scope: public` 标记。

## Docstring 结构模版
1.  **摘要**: 一句话概括。
2.  **Harbor Tags** (必须):
    * `@harbor.scope: public`
    * `@harbor.l3_strictness: strict`
    * `@harbor.idempotency: once`
3.  **Args / Returns / Raises**: 标准格式。

## 标准示例
```python
def build_index(self, incremental: bool = True) -> IndexReport:
    """构建或增量更新 L3 索引到缓存。

    功能:
      - 扫描配置的代码根目录，解析 Python 文件中的 L3 契约元数据。
      - 计算签名哈希与体哈希，生成索引条目。

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: once

    Args:
        incremental (bool): 是否启用增量构建。

    Returns:
        IndexReport: 构建统计。
    """
    ...
```
````

</details>

### 4\. Configure LLM

创建 `.env` 文件以启用语义审计和智能日志功能：

```ini
HARBOR_LLM_PROVIDER=openai  # 或 deepseek
HARBOR_LLM_API_KEY=sk-xxxxxx
HARBOR_LLM_BASE_URL=https://api.openai.com/v1
HARBOR_LANGUAGE=zh # 可选英文：en
```

### 5\. Build Baseline

锁定初始基线（将当前契约快照写入缓存），接管当前代码库：

```bash
harbor lock
```

-----

## 🛠️ Migration Guide (接管存量代码)

已有项目代码量巨大且没有 Docstring？使用 **交互式装饰器** 快速迁移。

### 1\. 扫描并标记 (Decorate)

```bash
harbor adopt backend/ --strategy safe
```

  * **Safe Mode (默认)**: 仅识别已有 Docstring 但缺少 `@harbor.scope` 的函数。
  * **Aggressive Mode**: `--strategy aggressive` 会识别所有 Public 函数，为无文档函数插入带 `TODO` 的模板。
  * **Dry Run**: 使用 `--dry-run` 预览变更。

### 2\. 更新索引

完成接管后，锁定基线：

```bash
harbor lock
```

-----

## 🔄 Vibe Coding Workflow

推荐工作流（Facade CLI）：

```powershell
harbor start
# AI coding
harbor checkpoint
# more AI coding
harbor finish
# or, when ready to sync derived context:
harbor finish --sync-context
harbor doctor
harbor log
harbor accept
```

发布轨道说明：当前发布收口以 `RELEASE.md` 中 `Unreleased / v1.3.0` 为准。

### Workflow Facade Commands

```powershell
harbor start
harbor checkpoint
harbor finish
harbor finish --sync-context
harbor doctor
harbor accept
```

关键语义：
- `harbor finish` 不会自动 `lock`。
- `harbor finish` 不会自动 `log`。
- `harbor finish` 默认不会写 README 或 Module Capsule。
- `harbor finish --sync-context` 会写 changed L2 README 和 changed Module Capsule，并检查 changed capsule stale 状态。
- `harbor doctor` 是顶层只读健康检查聚合命令（advisory，不自动修复）。
- `harbor doctor` 聚合检查 Config/Index、Workspace Status、DDT Fast、Derived Views、Skill References。
- `harbor doctor` 不写文件、不自动 lock、不自动 log。
- `harbor stale` 是只读聚合检查：同时检查 L2 README 与 Module Capsule 的新鲜度。
- `harbor stale` 默认检查 changed modules；可用 `--all` 或 `--module <module>` 切换范围。
- `harbor stale` 的 canonical L2 freshness 仅由 `.harbor/views/l2/<module>/README.md` 判定。
- `harbor stale` 会单独报告 `l2_readme_export`（`<module>/README.md`）advisory，不会混淆 canonical `l2_readme`。
- 若 canonical L2 不可用，`l2_readme_export` 只会标记 unknown/skipped，不做 out-of-sync 比较。
- `harbor stale` 不会自动修复；请用 `harbor docs --module <module> --write` 与 `harbor module seal <module> --write` 刷新。
- 想只看派生视图是否过期，请用 `harbor stale`；想看整体 Harbor 健康，请用 `harbor doctor`。
- MVP 阶段 `harbor stale` 为 advisory，检查完成后返回成功（未来可扩展 CI gate）。
- `harbor stale --format json` 与 `harbor doctor --format json` 提供机器可读输出（只读、advisory）。
- JSON 输出用于脚本集成、CI 准备、IDE 面板展示与后续自动化能力接入。
- MVP 的 JSON 输出不改变现有 exit-code 行为；`--ci` 将在后续阶段单独引入。
- `harbor accept` 是 `harbor lock` 的语义化 alias。

### L2 README Generation

```powershell
harbor docs --module harbor/core
harbor docs --module harbor/core --write
harbor docs --changed
harbor docs --changed --write
harbor docs --all
harbor docs --all --write
```

说明：
- 默认 preview，不写文件。
- 只有 `--write` 才会写 README。
- canonical L2 README 路径为 `.harbor/views/l2/<module>/README.md`。
- 默认会额外导出 `<module>/README.md`（`l2.export.module_readme.enabled=true`）。
- `l2.export.module_readme.enabled=false` 时仅写 canonical L2 README。
- L2 metadata canonical 路径为 `.harbor/views/l2/_meta.json`。
- legacy `.harbor/l2_meta.json` 仅读取兼容，不再作为写入目标。
- `--module`、`--changed`、`--all` 三种模式互斥。

### Module Capsule

```powershell
harbor module inspect harbor/core
harbor module seal harbor/core
harbor module seal harbor/core --write
harbor module seal --changed --write
harbor module seal --all --write
harbor module stale harbor/core
harbor module stale --changed
harbor module stale --all
harbor stale
harbor stale --changed
harbor stale --all
harbor stale --module harbor/core
harbor stale --format json
harbor doctor
harbor doctor --changed
harbor doctor --all
harbor doctor --module harbor/core
harbor doctor --format json
```

说明：
- Module Capsule 是 derived maintenance view，不是 source of truth。
- `module seal` 默认 preview，不写文件；仅 `--write` 会写 capsule。
- `module stale` 只读检查，不写文件。
- `harbor stale` 是顶层只读聚合检查，同时检查 L2 README 与 Module Capsule。
- `harbor stale` 默认等价 `harbor stale --changed`。
- `harbor doctor` 是顶层只读健康检查聚合；默认等价 `harbor doctor --changed`。
- `harbor doctor` 不会自动修复，也不会写入 docs / capsule / skill。
- `harbor doctor` 的 Derived Views 会显示 `l2_readme_export` advisory 与 legacy `.harbor/l2_meta.json` advisory（只读兼容提示，不自动迁移/删除）。
- `harbor stale --format json` 与 `harbor doctor --format json` 输出稳定机器可读 JSON（stdout 仅 JSON）。
- JSON 输出是 advisory read-only 视图，不会触发修复、写入或 lock/log。
- 当前 MVP 不改变 exit-code 行为；CI gate（如 `--ci`）将在后续版本提供。
- `module` 的单模块 / `--changed` / `--all` 三种模式互斥。

### Optional Skill Promotion

```powershell
harbor module promote-skill harbor/core
```

说明：
- `promote-skill` 是可选手动动作。
- 不建议为所有模块默认生成 skill。
- 若 capsule 缺失或过时，请先执行：

```powershell
harbor module seal harbor/core --write
```

### Project Structure View

```powershell
harbor project structure
harbor project structure --write
```

说明：
- 该命令的 canonical 写入目标为 `.harbor/views/project-structure.md`。
- `docs/harbor/project-structure.md` 是可选 export 目标（默认关闭）。
- `.harbor/` 是 Harbor canonical workspace，不应在 `.gitignore` 中被整目录忽略。
- 推荐仅忽略本地运行态目录（如 `.harbor/state/`、`.harbor/cache/`、`.harbor/exports/` 与本地临时 reports）。
- `.harbor/views/project-structure.md` 是 canonical project structure view；`docs/harbor` 仅是可选导出位，不是 canonical storage。
- `docs/design/` 用于人类编写的设计文档，应该保持可追踪（trackable）。
- Project Structure View 是 derived view，不是 Project Rules。
- 它不替代 `AGENTS.md`、L2 README、Module Capsule 或源代码本身。
- 它用于帮助 AI coding agent 在 debug、review、refactor 前快速理解项目结构。
- 输出会将 `Code Modules` 与 `Supporting Areas` 分开展示。
- 输出包含 `Discovery Mode` 区块，用于说明当前结构来源。
- 当处于 filesystem fallback 模式时，`Indexed Contracts` 可能为 0，因为没有可用的 Harbor index records。
- 默认模式仅预览，不写文件。
- 仅 `--write` 会更新 canonical 路径；仅在 `views.export.docs.enabled=true` 时才会额外更新 `docs/harbor/project-structure.md`。
- `harbor finish --sync-context` 不会自动刷新 Project Structure View。
- 推荐在任务起始阶段手动执行：

```powershell
harbor project structure --write
harbor start
# AI coding
harbor finish --sync-context
harbor stale
harbor doctor
harbor accept
```

-----

## 🚀 What's New in v1.2.0（历史版本）

- Smart Configuration：`harbor init` 现已自动探测 Django/Node.js/Go/Java 技术栈，并融合 `.gitignore` 规则生成更稳健的默认配置
- SQLite Backend (WAL)：索引从 JSON 迁移至 SQLite，常驻 O(1) 内存占用、秒级启动与安全并发写入
- Parallel Indexing：`harbor lock` 利用多核并行解析与哈希，适配大型 Monorepo 的高吞吐构建
- Windows 兼容：全面适配路径归一化与并行处理，跨平台体验一致

v1.2.0 重点围绕“工业级稳定性与规模化性能”，让 Harbor 更适合在企业级代码库中长期运行。

## 🧩 Features Deep Dive

<details>
<summary><strong>📐 DDT (Decorator-Driven Testing)</strong></summary>

防止“假绿灯”。将测试用例与代码版本强绑定。

```python
from harbor.core.ddt import harbor_ddt_target

@harbor_ddt_target("backend.core.calculate_tax", l3_version=1)
def test_calculate_tax():
    ...
```

运行 `harbor ddt validate`，如果契约升级到 v2，Harbor 会强制测试失败。
推荐使用 `harbor check --fast`（仅运行 DDT 验证）。

</details>

<details>
<summary><strong>📚 L2 Documentation Generator</strong></summary>

自动生成模块级的 README，作为代码质量仪表盘。

```bash
harbor docs --module harbor/core --write
harbor docs --changed --write
harbor docs --all --write
```

生成包含 Public API 列表、严格度状态及测试覆盖率的 Markdown 文档。
支持三种模式：
- `--module`：刷新单个模块
- `--changed`：刷新变更模块
- `--all`：刷新全部已索引模块

</details>

<details>
<summary><strong>⚙️ Configuration Management</strong></summary>

使用 CLI 管理配置，避免手写 YAML 出错。

```bash
harbor config list                   # 查看配置 (Rich表格)
harbor config add "scripts/**"       # 添加扫描路径
harbor config remove "legacy/**"     # 移除路径
```

</details>

<details>
<summary><strong>🧱 Module Capsule MVP</strong></summary>

为指定模块生成 AI 维护上下文胶囊（deterministic、无 LLM）：

```bash
harbor module inspect harbor/core
harbor module seal harbor/core
harbor module seal harbor/core --write
harbor module stale harbor/core
harbor module stale --changed
harbor module stale --all
harbor module seal --changed --write
harbor module seal --all --write
harbor module promote-skill harbor/core
```

说明：
- Module Capsule 是派生维护视图，不是事实源。
- 它不替代 L2 README（canonical：`.harbor/views/l2/<module>/README.md`，可选导出：`<module>/README.md`）。
- `seal <module>`：刷新单模块 capsule。
- `seal --changed`：刷新变更模块的 capsule。
- `seal --all`：刷新全部已索引模块的 capsule。
- `stale <module>`：检查单模块 capsule 是否与当前索引上下文一致。
- `stale --changed`：检查变更模块的 capsule 是否过时。
- `stale --all`：检查全部已索引模块的 capsule 是否过时。
- 默认是 preview 模式，不写文件。
- 仅 `--write` 才会更新 capsule 文件。
- `module seal --write` 默认写 canonical：`.harbor/views/modules/<module>/`。
- 仅当 `views.export.docs.enabled=true` 时，才会额外导出到 `docs/harbor/modules/<module>/`。
- 对 harbor-spec 仓库，`.harbor/views/modules/` 默认保持可追踪；用户项目可按需在 `.gitignore` 忽略该目录。
- stale 命令只做检查，不写文件；若过时请执行 `seal --write` 刷新。
- 目标是帮助 AI agent 更快进入 debug/review/refactor 上下文。
- `promote-skill <module>` 会生成一个薄 Skill 入口，路径为 `.agents/skills/harbor-debug-<slug>/SKILL.md`。
- Skill 默认引用 canonical capsule（三件套）路径，不复制 capsule 全文。
- Skill promotion 是可选能力，多数模块只需要 Module Capsule。
- 仅当模块复杂、维护频繁或反复 debug 时，才建议晋升为 Skill。
- promote-skill 要求 capsule 已存在且为最新状态。
- 推荐收口流（可选复查 stale）：

```bash
harbor finish --sync-context
harbor doctor
harbor accept
```

</details>

<details>
<summary><strong>🚀 Performance Tuning (Monorepo)</strong></summary>

对于大型项目，性能与可扩展性至关重要：
- SQLite (WAL)：索引缓存持久化到 `.harbor/cache/harbor.db`，避免全量 JSON 读写，冷启动更快
- 并行构建：`harbor lock` 默认多核并行解析与哈希，吞吐显著提升
- 增量查询：`harbor status` 通过数据库增量对比，加速变更检测

此外，**排除无关目录**非常关键。canonical 配置写入目标为 `.harbor/config/harbor.yaml`（legacy `.harbor/config.yaml` 仍可读），建议显式配置排除：

```yaml
exclude_paths:
  - ".venv/**"
  - "node_modules/**"  # 前端依赖必须排除
  - "**/tests/**"      # 排除测试代码被索引
  - "dist/**"
```

</details>

-----

## 📝 Commands Cheatsheet

| Command | Description |
| :--- | :--- |
| `harbor init` | 智能初始化项目配置 |
| `harbor start` | 工作流入口：开始 AI coding 前执行状态检查 |
| `harbor checkpoint` | 工作流检查点：等价 `status + check --fast` |
| `harbor finish` | 工作流收尾：等价 `status + check` 并提示下一步 |
| `harbor finish --sync-context` | 工作流收尾增强：执行 `finish` 检查并同步 changed L2 README + Module Capsule，再执行 changed stale 检查 |
| `harbor doctor` | 顶层只读健康检查聚合：默认检查 changed modules 的 Config/Index、Workspace、DDT、Derived Views、Skill References |
| `harbor stale` | 顶层只读聚合检查：默认检查 changed modules 的 canonical L2 README + Module Capsule，并单独报告 module README export advisory |
| `harbor accept` | 工作流确认：语义化别名，等价 `harbor lock` |
| `harbor status` / `harbor st` | 查看上下文状态（Drift/Modified） |
| `harbor lock` / `harbor commit` | 锁定当前 L3 契约快照为基线 |
| `harbor check` | 统一语义审计与 DDT 验证 |
| `harbor check --fast` | 仅运行 DDT 验证 |
| `harbor log` | 上下文感知日志：无参 AI 草稿，`-m` 手动写入（canonical 写入 `.harbor/diary/YYYY-MM.jsonl`） |
| `harbor log --export` | 导出 Diary Markdown（读取 `.harbor/diary` + `specs/diary`，legacy 只读兼容） |
| `harbor adopt` | 交互式接管遗留代码进入治理体系 |
| `harbor docs` | 生成模块级文档（L2） |
| `harbor docs --changed --write` | 仅刷新变更模块的 L2 README |
| `harbor docs --all --write` | 刷新全部已索引模块的 L2 README |
| `harbor module inspect <module>` | 查看指定模块的索引上下文摘要（只读，不写文件） |
| `harbor module seal <module>` | 预览模块 Capsule（三份文档，不写文件） |
| `harbor module seal <module> --write` | 默认写入模块 Capsule 到 `.harbor/views/modules/<module>/`；仅在 docs export enabled 时额外写 `docs/harbor/modules/<module>/` |
| `harbor module stale <module>` | 检查指定模块 Capsule 是否过时（只读，不写文件） |
| `harbor module stale --changed` | 批量检查变更模块 Capsule 是否过时 |
| `harbor module stale --all` | 批量检查全部已索引模块 Capsule 是否过时 |
| `harbor stale --changed` | 顶层批量检查变更模块的派生视图（L2 README + Module Capsule）是否过时 |
| `harbor stale --all` | 顶层批量检查全部已索引模块的派生视图是否过时 |
| `harbor stale --module <module>` | 顶层检查单模块派生视图是否过时（只读，不写文件） |
| `harbor doctor --changed` | 顶层批量健康检查（变更模块范围，默认模式） |
| `harbor doctor --all` | 顶层批量健康检查（全部已索引模块范围） |
| `harbor doctor --module <module>` | 顶层健康检查（单模块范围） |
| `harbor module seal --changed --write` | 批量写入变更模块的 Capsule |
| `harbor module seal --all --write` | 批量写入全部已索引模块的 Capsule |
| `harbor module promote-skill <module>` | 手动晋升模块为薄 Skill 入口（可选，写入 `.agents/skills/.../SKILL.md`） |
| `harbor project structure` | 预览项目级派生结构视图（默认不写文件） |
| `harbor project structure --write` | 默认写入 `.harbor/views/project-structure.md`；可选导出到 `docs/harbor/project-structure.md` |
| `harbor config` / `harbor conf` | 管理扫描路径配置 |

-----

## 📄 License

MIT © 2025 Harbor-spec Authors.

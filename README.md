<div align="center">

# ⚓ Harbor
### The Context Governance Engine for Vibe Coding

[![CI Status](https://img.shields.io/github/actions/workflow/status/your-org/harbor-spec/ci.yml?style=flat-square)](https://github.com/your-org/harbor-spec/actions)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue?style=flat-square)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![Strictness](https://img.shields.io/badge/Harbor-L3%20Strict-purple?style=flat-square)](https://github.com/your-org/harbor-spec)

**让 AI 像代码一样被管理，让上下文像 Git 一样可追溯。**

[理念 (Philosophy)] • [架构 (Architecture)] • [快速开始 (Quick Start)] • [工作流 (Workflow)]

</div>

---

## 🌌 The Era of Vibe Coding

编程正在经历一场范式转移。我们正在从 "Writing Code"（逐行编写）转向 **"Vibe Coding"**（通过自然语言与 AI 协作生成）。

在这个新时代，**代码生成的边际成本趋近于零，但上下文维护的成本却在指数级上升。**
- AI 改了代码，Docstring 还没改？👉 **Context Drift (上下文漂移)**
- 测试用例还在测旧版本的逻辑？👉 **Validation Gap (验证断层)**
- 为什么上周我们要把这个参数改成 Optional？👉 **Memory Loss (决策遗忘)**

**Harbor** 应运而生。它不是另一个 Copilot，它是 **Copilot 的监管者**。它是一套用于治理 AI 生成代码的 **"良知" (Conscience)** 与 **"记忆" (Memory)** 系统。它是“程序员到上下文工程师”这一革命性转变的关键工具，它的目标是成为vibe coding时代的Git。

## 🛡️ Core Philosophy

Harbor 的核心设计理念基于 **L3 Contract Theory**：

1.  **Code is Volatile, Contract is Immutable**: 实现代码可以由 AI 随意重写，但 L3 级 Docstring（契约）是锚点，必须由人类或高级审计确认。
2.  **Noise is Signal**: 未经索引的代码、未同步的文档、未绑定的测试，都是系统中的“噪音”。Harbor 不会静默处理，而是将其显性化。
3.  **Trust, but Verify**: 我们信任 AI 的编码能力，但必须通过 AST 静态分析和 LLM 语义审计来验证其产出。

## 🏗️ Architecture

Harbor 通过六大核心子系统构建了一个闭环的治理体系：

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
    Validator -->|Status| L2
    
    User[Developer] -->|Log Decision| Diary(Diary / History)
````

  - **🧠 Index (Memory)**: 这里的 `.harbor/cache` 是大脑，记录了代码的每一次“快照”与指纹。
  - **⚖️ Sync (Conscience)**: 实时监测 "Implementation Drift"（代码变了，但契约没变）。
  - **🌉 DDT (Bridge)**: **D**ecorator-driven **D**ata **T**esting。将测试用例与 L3 版本强绑定，拒绝“假绿灯”。
  - **🤖 Audit (Guard)**: 集成 DeepSeek/OpenAI，对代码进行语义级审计，揪出逻辑与文档的违背之处。
  - **📊 L2 (Dashboard)**: 自动生成 Markdown 视图，诚实地展示模块的测试覆盖率与契约状态。
  - **📜 Diary (History)**: 结构化的决策日志，记录每一次变革背后的 "Why"。

## ⚡ Quick Start

### 1\. Installation

Harbor 是一个纯 Python 工具，推荐在开发模式下安装：

```bash
git clone [https://github.com/your-org/harbor-spec.git](https://github.com/your-org/harbor-spec.git)
cd harbor-spec
pip install -e .
```

可选pypi安装：

```bash
pip install harbor-spec
```

### 2\. Configuration

配置 LLM 以启用 AI 语义审计（支持 Ernie, DeepSeek, OpenAI 等兼容接口）：

```bash
cp .env.example .env
# 编辑 .env 文件:
# HARBOR_LLM_PROVIDER=openai
# HARBOR_LLM_API_KEY=
# HARBOR_LLM_BASE_URL=https://api.openai.com/v1
# HARBOR_LANGUAGE=zh (可选，开启中文审计)
```

### 3\. Initialize

使用智能初始化生成配置并避免 `scanned=0`：

```bash
harbor init
# 若已存在配置需要覆盖：
# harbor init --force
```

初始化完成后，构建初始索引接管当前代码库：

```bash
harbor build-index
```

### 4\. 配置管理（Config CLI）

通过命令行安全管理 `.harbor/config.yaml`，避免手动编辑出错：

```bash
# 追加路径到 code_roots（自动去重）
harbor config add "backend/legacy/**"

# 查看当前配置（Rich 表格）
harbor config list

# 从 code_roots 移除路径
harbor config remove "backend/legacy/**"
```

运行 `harbor config list` 的示例输出：

```
Harbor Config
profile       : enforce_l3
code_roots    : harbor/**, backend/legacy/**
exclude_paths : .venv/**, tests/**, build/**, dist/**, docs/**
```

### 5\. 进度可视化（Rich Progress）

在大型项目上构建索引支持进度条与当前文件显示，过程更透明：

```bash
harbor build-index --no-incremental
```

示例输出：

```
[完成] E:/project/harbor-spec/harbor/utils/__init__.py ━━━━━━━━━━━━━━━━━━━━━━━━━ 18/18 0:00:00
scanned=18 updated=18 skipped=0 items=63 cache=.harbor/cache/l3_index.json
```

### Tips: 避免 `scanned=0`
- 先运行 `harbor init` 生成 `.harbor/config.yaml`，确保 `code_roots` 指向真实代码位置（如 `src/**` 或包目录）。
- 使用 `--force` 重新初始化以覆盖不合适的旧配置。
- 如为脚本型仓库（根目录只有若干 `.py`），`harbor init` 会生成 `code_roots: ['*.py']`；若没有 `.py`，会兜底为 `['**/*.py']`。

## 🎮 Workflow: A Day with Harbor

### 1\. Check Status

开始工作前，看看代码库是否干净。

```bash
harbor status
# 输出: No changes detected. (Or list of drifts)
```

### 2\. Vibe Coding

使用你喜欢的 AI 助手（Cursor, Windsurf, Copilot）修改代码。
*假设你修改了 `harbor/utils.py` 的逻辑，但忘记更新 Docstring。*

### 3\. Detect Drift

Harbor 会发现你的代码实现了“偷跑”。

```bash
harbor status
# 输出: M harbor.utils.func (Body changed, Contract static)
```

### 4\. AI Audit

让 Harbor 的 AI 审计员检查你的修改是否违背了契约。

```bash
harbor audit --semantic
# 输出: POSSIBLE_SEMANTIC_DRIFT ... [MISMATCH]: 代码抛出了 ValueError 但文档中未声明...
```

### 5\. Lock & Record

修复问题后，更新索引并记录决策日志。

```bash
harbor build-index
harbor diary log --summary "Refactor utils validation logic" --type refactor --importance high
```

## 🧩 Commands Cheatsheet

| Command | Description |
| :--- | :--- |
| `harbor init` | 智能探测项目结构并生成 `.harbor/config.yaml`（支持 `--force` 覆盖） |
| `harbor status` | 检查代码与索引的差异（Drift检测） |
| `harbor build-index` | 更新 L3 索引缓存 (类似 `git commit`) |
| `harbor config list` | 使用 Rich 表格打印当前配置（profile、code_roots、exclude_paths） |
| `harbor config add <path>` | 追加 `<path>` 到 `code_roots`（自动去重并写回） |
| `harbor config remove <path>` | 从 `code_roots` 移除 `<path>`（写回配置） |
| `harbor audit --semantic` | 调用 LLM 进行语义一致性检查 |
| `harbor ddt validate` | 验证测试用例与代码版本的绑定关系 |
| `harbor gen l2` | 自动生成模块级的 README 文档 |
| `harbor diary log` | 写入结构化的决策日志 |

## 🤝 Contribution

Harbor 遵循 **Strict L3** 开发规范。

  - 所有 Public API 必须包含完整的 Google-style Docstring。
  - 所有新增功能必须包含 DDT 测试绑定。
  - 提交前请运行 `harbor audit --semantic` 自测。

## 📄 License

MIT © 2025 Harbor-spec Authors.

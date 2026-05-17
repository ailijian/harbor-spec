# Contributing to HarborSpec / 为 HarborSpec 做贡献

感谢你愿意为 **HarborSpec** 做贡献。

> **English:** Thank you for your interest in contributing to **HarborSpec**.

HarborSpec 是一个面向 **AI coding / vibe coding / agentic coding** 的上下文治理引擎。它关注的不是"如何更快写代码"，而是：

> **代码、契约、测试、派生上下文、决策记忆与 CI 门禁，是否仍然保持一致。**

> **English:** HarborSpec is a context governance engine for **AI coding / vibe coding / agentic coding**. It is not about "how to write code faster," but rather:
> > **Whether code, contracts, tests, derived context, decision memory, and CI gates remain consistent.**

无论你想提交 Bug fix、文档改进、测试补充、CLI/JSON 行为优化、Contract/DDT/generated context 相关能力、Python/TypeScript 适配增强，或是 AI agent workflow/rules/skills 改进，我们都欢迎。

> **English:** We welcome bug fixes, documentation improvements, test additions, CLI/JSON behavior optimizations, Contract/DDT/generated context enhancements, Python/TypeScript adapter improvements, and AI agent workflow/rules/skills updates.

---

## 1. Contribution Philosophy / 贡献理念

HarborSpec 的贡献原则不是"只让代码跑起来"，而是 `implementation + contract + tests + generated context + governance consistency` 一起成立。

> **English:** The contribution philosophy of HarborSpec is not merely "make the code run," but ensuring that `implementation + contract + tests + generated context + governance consistency` all hold together.

在 HarborSpec 中，很多改动都不只是"实现变化"，还可能影响 public CLI behavior、JSON output contract、docstring/JSDoc/TSDoc contract、generated L2 README、Module Capsule、project structure view、DDT binding、CI gate semantics、Agent workflow instructions。因此，贡献者需要同时关注：

> **English:** In HarborSpec, many changes are not just "implementation changes." They may also affect public CLI behavior, JSON output contracts, docstring/JSDoc/TSDoc contracts, generated L2 READMEs, Module Capsules, project structure views, DDT bindings, CI gate semantics, and agent workflow instructions. Therefore, contributors must simultaneously ensure:
> - 代码是否正确 / Code correctness
> - 契约是否同步 / Contract synchronization
> - 测试是否覆盖 / Test coverage
> - 派生上下文是否刷新 / Derived context freshness
> - Harbor gates 是否通过 / Harbor gate compliance

---

## 2. Before You Start / 开始之前

### 2.1 Read these files first / 先阅读这些文件

对于非 trivial 改动，请先阅读：

> **English:** For non-trivial changes, please read the following first:

```text
README.md
AGENTS.md
.harbor/rules/project-rules.md
```

当任务涉及特定主题时，再按需阅读：

> **English:** When the task involves specific topics, read the following as needed:

```text
.harbor/rules/contract-rules.md
.harbor/rules/ddt-rules.md
.harbor/rules/runtime-safety.md
.harbor/rules/diary-rules.md
.harbor/rules/agent-policy.md
```

这些文件定义了 HarborSpec 的治理边界、source-of-truth 优先级与任务完成标准。

> **English:** These files define HarborSpec's governance boundaries, source-of-truth priorities, and task completion criteria.

---

### 2.2 Open an issue first for larger changes / 重大变更请先开 Issue

以下类型的变更，建议先开 issue / discussion，再提交 PR：

> **English:** For the following types of changes, please open an issue or discussion before submitting a PR:

- 新增或重构重要 CLI 命令 / New or refactored major CLI commands
- 改变公开 JSON 输出结构 / Changes to public JSON output structure
- 改变 baseline / accept / checkpoint 语义 / Changes to baseline/accept/checkpoint semantics
- 改变 generated context 生成逻辑 / Changes to generated context logic
- 改变 `verify-generated`、`stale`、`doctor`、`checkpoint` 的 gate 语义 / Changes to gate semantics for `verify-generated`, `stale`, `doctor`, `checkpoint`
- 改变 contract model / DDT model / Changes to contract model or DDT model
- 扩展 TypeScript public boundary / semantic audit / DDT 机制 / Extensions to TypeScript public boundary, semantic audit, or DDT mechanisms
- 改变 AGENTS / rules / skills 的核心工作流 / Changes to core AGENTS/rules/skills workflows
- 改变 release / CI / publish 流程 / Changes to release/CI/publish processes

这样可以避免在一个方向尚未达成共识时投入过多实现成本。

> **English:** This avoids investing excessive implementation effort before consensus is reached on a direction.

---

## 3. Ways to Contribute / 贡献类型

欢迎以下类型的贡献：

> **English:** The following types of contributions are welcome:

### 3.1 Code / 代码

- Bug fixes / Bug 修复
- CLI UX 改进 / CLI UX improvements
- Core logic 修复 / Core logic fixes
- Adapter 能力增强 / Adapter enhancements
- Generated context 相关改进 / Generated context improvements
- Performance / determinism / reproducibility 优化 / Performance, determinism, and reproducibility optimizations

### 3.2 Tests / 测试

- Regression tests / 回归测试
- Cross-platform tests / 跨平台测试
- CI hermeticity tests / CI 封闭性测试
- JSON output tests / JSON 输出测试
- DDT / contract behavior tests / DDT 与契约行为测试
- Generated view determinism tests / 派生视图确定性测试

### 3.3 Documentation / 文档

- README / README.en
- Architecture explanations / 架构说明
- Rule docs / 规则文档
- Agent workflow docs / Agent 工作流文档
- Usage examples / 使用示例
- Troubleshooting notes / 故障排查记录

### 3.4 Project Governance / 项目治理

- CONTRIBUTING / templates / community docs / 贡献指南、模板与社区文档
- Issue / PR 流程改进 / Issue and PR process improvements
- Release gate hardening / 发布门禁加固
- CI failure triage workflow / CI 故障分类工作流

---

## 4. Development Setup / 开发环境

### 4.1 Requirements / 环境要求

- Python 3.9+
- Git
- Recommended shell: PowerShell on Windows / Windows 下推荐使用 PowerShell
- HarborSpec repository checkout / HarborSpec 仓库克隆

---

### 4.2 Clone your fork / 克隆你的 Fork

```powershell
git clone <your-fork-url>
cd harbor-spec
```

---

### 4.3 Create a virtual environment / 创建虚拟环境

#### PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

#### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
```

---

### 4.4 Install in editable development mode / 以可编辑开发模式安装

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

The development extras currently include `pytest`. / 开发依赖目前包含 `pytest`。

---

## 5. Branch and Pull Request Expectations / 分支与 PR 规范

### 5.1 Keep PRs focused / 保持 PR 聚焦

A good PR should have / 一个好的 PR 应具备：

- one clear purpose / 单一明确目的
- a narrow scope / 范围精简
- a concise explanation of why the change is needed / 简洁说明变更动机
- tests and validation evidence / 测试与验证证据
- contract impact explanation when relevant / 必要时说明契约影响

Avoid mixing / 避免在同一 PR 中混合提交：

```text
feature change
+ unrelated refactor
+ documentation sweep
+ release workflow edits
```

除非它们不可分割。

> **English:** Unless they are inseparable.

---

### 5.2 Suggested branch names / 推荐分支命名

Examples / 示例：

```text
fix/checkpoint-summary-output
feat/typescript-boundary-evidence
docs/contributing-guide
test/progress-ci-hermeticity
chore/release-gate-alignment
```

Branch naming is not a hard requirement, but clarity helps review. / 分支命名非强制，但清晰的命名有助于评审。

---

## 6. HarborSpec Contribution Workflow / 贡献工作流

For non-trivial changes, follow this general workflow / 对于非 trivial 变更，请遵循以下通用工作流：

```text
1. Understand the source of truth          / 理解可信来源
2. Determine Contract Impact               / 判断契约影响
3. Update contract sources when needed     / 必要时更新契约源
4. Implement the change                    / 实现变更
5. Update tests / DDT when relevant        / 必要时更新测试与 DDT
6. Refresh generated context when needed   / 必要时刷新派生上下文
7. Run Harbor validation gates             / 运行 Harbor 验证门禁
8. Submit a focused PR                     / 提交聚焦的 PR
```

---

## 7. Contract-First Contribution Rule / 契约优先贡献规则

HarborSpec follows a contract-aware development discipline. / HarborSpec 遵循契约感知的开发规范。

Before modifying any strict, public, or user-visible behavior, decide / 在修改任何严格、公开或用户可见的行为之前，请先判断：

```text
Contract Impact:
- yes
- no
- uncertain
```

If the answer is `yes` or `uncertain`, update the relevant contract source in the same change. / 若答案为 `yes` 或 `uncertain`，请在同一变更中更新相关契约源。

Examples of contract sources / 契约源示例：

- Python docstrings
- JSDoc / TSDoc
- CLI behavior contract / CLI 行为契约
- JSON output shape / JSON 输出结构
- File write targets / 文件写入目标
- Output / exit semantics / 输出与退出语义
- Tests / fixtures / DDT metadata / 测试、固件与 DDT 元数据
- Policy / safety semantics / 策略与安全语义

Do not wait for `harbor checkpoint` to discover an obvious contract sync omission. / 不要等到运行 `harbor checkpoint` 时才发现明显的契约同步遗漏。

---

## 8. Areas That Usually Require Contract Review / 通常需要契约审查的领域

Treat the following as contract-sensitive / 以下领域视为契约敏感区：

- Public CLI command changes / 公开 CLI 命令变更
- CLI flags, args, stdout, stderr, exit code / CLI 标志、参数、标准输出、标准错误、退出码
- Machine-readable JSON output / 机器可读 JSON 输出
- File write behavior / 文件写入行为
- Public API changes / 公开 API 变更
- Parser / serializer / formatter changes / 解析器、序列化器、格式化器变更
- Generated context schema or write behavior / 派生上下文模式或写入行为
- Baseline acceptance semantics / 基线接受语义
- DDT semantics / DDT 语义
- Workspace layout changes / 工作区布局变更
- Agent workflow semantics / Agent 工作流语义

---

## 9. Testing and Validation / 测试与验证

HarborSpec uses `pytest` and Harbor governance gates. / HarborSpec 使用 `pytest` 与 Harbor 治理门禁。

### 9.1 Minimum local validation / 最低本地验证

For most code PRs / 对于大多数代码 PR：

```powershell
pytest
harbor checkpoint --ci --format json --detail summary
harbor stale --ci --format json
harbor doctor --ci --format json
```

---

### 9.2 CI-parity validation / CI 一致性验证

The repository CI runs / 仓库 CI 运行：

```powershell
harbor verify-generated --all --ci --format json
pytest
harbor checkpoint --ci --format json
harbor stale --ci --format json
harbor doctor --ci --format json
```

If your change affects generated context or source truth used by generated views, run `harbor verify-generated --all --ci --format json` before opening a PR. / 若变更影响派生上下文或派生视图所依赖的可信来源，请在提交 PR 前运行该命令。

---

### 9.3 Targeted testing is welcome, but not a replacement for final validation / 定向测试受欢迎，但不能替代最终验证

During development, targeted tests are encouraged / 开发期间鼓励定向测试：

```powershell
pytest tests/test_specific_file.py
```

But before opening a non-trivial PR, broader validation is expected. / 但在提交非 trivial PR 前，期望进行更广泛的验证。

---

## 10. Generated Context Rules / 派生上下文规则

HarborSpec maintains canonical generated context under `.harbor/views/**`. Do not manually edit generated views as project truth. / HarborSpec 在 `.harbor/views/**` 下维护规范的派生上下文。请勿手动编辑派生视图作为项目可信来源。

If your change affects / 若变更影响：

- module responsibilities / 模块职责
- project structure / 项目结构
- public contracts / 公开契约
- tests / DDT / 测试与 DDT
- CLI behavior / CLI 行为
- JSON output / JSON 输出
- generated context logic / 派生上下文逻辑

refresh generated context through Harbor commands. / 请通过 Harbor 命令刷新派生上下文。

### 10.1 Common refresh path / 常用刷新路径

```powershell
harbor finish --sync-context
```

### 10.2 Full refresh path when required / 需要时的完整刷新路径

For broad or release-relevant changes / 对于广泛或发布相关变更：

```powershell
harbor project structure --write
harbor docs --all --write
harbor module seal --all --write
```

Then validate / 然后验证：

```powershell
harbor verify-generated --all --ci --format json
```

---

## 11. What Not to Commit / 不要提交的内容

Do not include local runtime or temporary artifacts unless a maintainer explicitly asks for them. / 除非维护者明确要求，否则不要包含本地运行时或临时产物。

Avoid committing / 避免提交：

```text
.harbor/cache/**
.harbor/state/**
temporary diagnostics / 临时诊断文件
local scratch files / 本地草稿文件
ad-hoc reports / 临时报告
virtual environments / 虚拟环境
```

Use care with / 谨慎提交：

```text
.harbor/reports/**
```

These are usually local diagnostic / evidence artifacts, not regular source changes. / 这些通常是本地诊断或证据产物，非常规源码变更。

---

## 12. Baseline and Diary Boundaries / 基线与决策记忆边界

### 12.1 Do not run `harbor accept` casually / 请勿随意运行 `harbor accept`

`harbor accept` changes the accepted checkpoint baseline. It should only be used after explicit human review and maintainer approval. / `harbor accept` 会改变已接受的检查点基线，仅应在明确的人工审查与维护者批准后方可使用。

If your PR causes checkpoint residuals such as `contract_and_body_changed`, `possible_semantic_drift`, or `untracked_function`, describe them clearly in the PR instead of accepting a new baseline unilaterally. / 若 PR 导致检查点残留（如上述类型），请在 PR 中清晰说明，而非单方面接受新基线。

---

### 12.2 Do not write Diary entries unless requested / 除非被要求，否则不要写入 Diary

Diary entries under `.harbor/diary/**` are source-of-truth decision memory. / `.harbor/diary/**` 下的 Diary 条目是可信来源的决策记忆。

Do not execute `harbor log write` unless maintainers explicitly request it. / 除非维护者明确要求，否则不要执行 `harbor log write`。

If a decision seems worth recording, mention that a Diary Draft may be appropriate. / 若某项决策值得记录，可提及可能需要撰写 Diary Draft。

---

## 13. AI-Assisted Contributions / AI 辅助贡献

HarborSpec welcomes AI-assisted development, but contributors remain responsible for the result. / HarborSpec 欢迎 AI 辅助开发，但贡献者需对结果负责。

If you use an AI coding agent / 若使用 AI 编程 Agent：

- review the diff yourself / 亲自审查 diff
- verify claims about commands actually run / 验证关于实际运行命令的声明
- ensure contracts were not skipped / 确保契约未被跳过
- ensure generated context was not manually edited / 确保派生上下文未被手动编辑
- ensure tests and Harbor gates genuinely passed / 确保测试与 Harbor 门禁真正通过
- avoid submitting large, unfocused AI-generated rewrites / 避免提交大型、无聚焦的 AI 生成重写

A contribution is evaluated by its correctness and maintainability, not by whether AI was involved. / 贡献的评判标准是其正确性与可维护性，而非是否使用了 AI。

---

## 14. Pull Request Checklist / PR 检查清单

Before opening a PR, please confirm / 提交 PR 前，请确认：

- [ ] The PR has one clear purpose. / PR 目的单一明确。
- [ ] I explained the motivation and scope. / 已说明动机与范围。
- [ ] I considered whether the change has Contract Impact. / 已考虑变更是否存在契约影响。
- [ ] If behavior changed, the corresponding contract source was updated. / 若行为变更，相应契约源已更新。
- [ ] Relevant tests were added or updated. / 已添加或更新相关测试。
- [ ] `pytest` was run, or I clearly stated why it was not. / 已运行 `pytest`，或明确说明未运行的原因。
- [ ] Relevant Harbor checks were run. / 已运行相关 Harbor 检查。
- [ ] Generated context was refreshed if needed. / 如需，已刷新派生上下文。
- [ ] I did not manually edit `.harbor/views/**` as source truth. / 未将 `.harbor/views/**` 手动编辑为可信来源。
- [ ] I did not commit `.harbor/cache/**` or `.harbor/state/**`. / 未提交 `.harbor/cache/**` 或 `.harbor/state/**`。
- [ ] I did not run `harbor accept` unless explicitly requested. / 除非明确要求，未运行 `harbor accept`。
- [ ] I did not write Diary entries unless explicitly requested. / 除非明确要求，未写入 Diary 条目。
- [ ] The PR description includes validation commands and observed results. / PR 描述包含验证命令与观察结果。

---

## 15. Suggested PR Description Template / 建议的 PR 描述模板

You may use the following structure / 可使用以下结构：

```markdown
## Summary / 摘要

Describe what changed and why. / 描述变更内容与动机。

## Scope / 范围

- [ ] Bug fix
- [ ] Feature
- [ ] Docs
- [ ] Tests
- [ ] Generated context / governance / 派生上下文与治理
- [ ] CI / release workflow / CI 与发布工作流

## Contract Impact / 契约影响

Contract Impact: yes / no / uncertain

If yes or uncertain, describe / 若为 yes 或 uncertain，请说明：
- affected contract surface / 受影响的契约面
- contract source updated / 已更新的契约源
- breaking-change risk, if any / 可能的破坏性变更风险

## Validation / 验证

Commands actually run / 实际运行的命令：

```text
pytest
harbor checkpoint --ci --format json --detail summary
harbor stale --ci --format json
harbor doctor --ci --format json
```

Observed results / 观察结果：

* ...

## Generated Context / 派生上下文

- [ ] Not affected / 未受影响
- [ ] Refreshed with Harbor commands / 已通过 Harbor 命令刷新
- [ ] Needs maintainer follow-up / 需要维护者跟进

## Remaining Risks / 剩余风险

List any known tradeoffs, follow-ups, or deferred work. / 列出已知的权衡、后续跟进或延期工作。
```

---

## 16. Reporting Bugs / 报告 Bug

A useful bug report should include / 有效的 Bug 报告应包含：

- What command or workflow you ran / 运行的命令或工作流
- What you expected / 预期结果
- What actually happened / 实际发生的情况
- Relevant stdout / stderr / 相关标准输出与标准错误
- OS and Python version / 操作系统与 Python 版本
- HarborSpec version / HarborSpec 版本
- Whether the issue reproduces in a clean checkout, if relevant / 若相关，问题是否在干净克隆中可复现

Please redact secrets and machine-local sensitive data. / 请脱敏处理密钥与机器本地敏感数据。

---

## 17. Feature Requests / 功能请求

A strong feature request explains / 有力的功能请求应说明：

- The problem to solve / 待解决的问题
- Why current HarborSpec behavior is insufficient / 当前 HarborSpec 行为为何不足
- Expected workflow or UX / 预期的工作流或用户体验
- Whether the feature affects / 该功能是否影响：
  - CLI
  - JSON output / JSON 输出
  - generated context / 派生上下文
  - contract / DDT / 契约与 DDT
  - AI agent workflow / AI Agent 工作流
  - CI / release gates / CI 与发布门禁
- Any alternatives considered / 已考虑的替代方案

---

## 18. Documentation Contributions / 文档贡献

Documentation improvements are welcome. / 欢迎文档改进。

When changing documentation / 修改文档时：

- keep terminology consistent with README and AGENTS / 保持术语与 README 和 AGENTS 一致
- do not present generated context as source of truth / 不要将派生上下文呈现为可信来源
- do not claim unsupported TypeScript capabilities / 不要声称不支持的 TypeScript 能力
- keep examples aligned with current command behavior / 保持示例与当前命令行为一致
- update both Chinese and English README only when the change affects both public narratives / 仅当变更影响两种公开叙述时，同时更新中英文 README

---

## 19. Licensing / 许可

HarborSpec is distributed under the Apache-2.0 license. By contributing, you agree that your contribution may be distributed under the repository license. / HarborSpec 基于 Apache-2.0 许可分发。通过提交贡献，你同意你的贡献可在仓库许可下分发。

---

## 20. Thank You / 致谢

Thank you for helping make HarborSpec more reliable, more understandable, and more useful for AI-native software development. / 感谢你帮助 HarborSpec 在 AI 原生软件开发中变得更可靠、更易理解、更有用。

Well-scoped issues, careful bug reports, documentation fixes, tests, and design discussion are all valuable contributions. / 范围明确的 Issue、仔细的 Bug 报告、文档修复、测试与设计讨论都是有价值的贡献。

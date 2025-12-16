下面是一个**可直接复制**的 `project_rules` 通用模板，专门为 Harbor-spec 项目设计。
你在新项目里只需要：**替换占位符**（`<PROJECT_NAME>`、`<LANGUAGE>` 等）+ 适当删减不需要的部分，就能快速得到一份可用的项目级规则。

````markdown
description: Harbor-spec Project Rules for <PROJECT_NAME>
alwaysApply: true
---

# 0. 仓库说明与 Harbor-spec 模式

- 本仓库是 **<PROJECT_NAME>** 项目源码，主要目标：
  - <用 2~3 个 bullet 简要描述项目目标，例如：>
  - - 提供一个用于 XXX 的后端服务；
  - - 或构建一个基于 LLM 的 XXX 工具；
  - - 或实现某个 SDK / 库。
- 本项目在 AI IDE 中启用了 **Harbor-spec 模式**：
  - 通用行为规范见全局 `role_rules`（已在 IDE 中配置）；
  - 本文件是本仓库的 **L1 宪法 / Project Rules**，主要声明：
    - 本仓库的代码分层与依赖边界；
    - 本项目采用的 L3 Docstring / 契约模板；
    - Diary 文件位置与格式；
    - 在本项目中如何按 Harbor-spec 的方式进行 vibe coding 开发。

> 使用约定：  
> - 任何涉及「修改代码行为 / 修改 API 契约 / 调整测试 / 记录演进历史」的操作，  
>   AI 都应按 `role_rules` 触发「确认循环」→ 同步 L3 → 考虑测试与 Diary。

---

# 1. 代码结构与分层（按项目实际填写）

## 1.1 预期目录结构（示意）

```text
<PROJECT_ROOT>/
  <SRC_ROOT>/              # 源码目录，例如 src/ 或 modules/
    ...
  specs/
    DEVELOPMENT_DIARY.md   # 项目级行为变更记录（Diary）
  tests/                   # 测试目录
  ...
````

> 请根据实际情况修改上面的树形结构，只要能让 AI 理解「源码在哪、Diary 在哪、测试在哪」。

## 1.2 分层/模块边界（一般用“洋葱结构”或简单分层）

> 根据实际项目，说明哪些模块是核心、哪些是适配层、哪些是接口层。
> 对 harborflow 这种库型项目，可以写成洋葱架构；
> 对业务项目，可以写“domain / application / infrastructure” 三层。

示例结构（请替换/删改）：

```text
[最外层] <PROJECT_NAME>.api
          ↓  只依赖 service / domain 对外接口，不直接依赖 infra 实现
[中  间] <PROJECT_NAME>.service
          ↓  只依赖 domain；是应用服务层
[内  核] <PROJECT_NAME>.domain
          ↓  只依赖标准库或基础库（如 langgraph 等）
[基础设施] <PROJECT_NAME>.infra
          ↕  提供具体实现（DB / 缓存 / 外部服务适配）
```

依赖约束（示例，可按需修改）：

* `<PROJECT_NAME>.domain`：

  * ✅ 可以依赖：标准库、极少数基础第三方库；
  * ❌ 不依赖：`api` / `service` / `infra`。
* `<PROJECT_NAME>.service`：

  * ✅ 可以依赖：`domain`；
  * ❌ 不直接依赖：`api`（避免循环）；
* `<PROJECT_NAME>.api`：

  * ✅ 可以依赖：`service` + `domain`；
  * ❌ 不直接依赖：`infra`（如 DB 实现）。
* `<PROJECT_NAME>.infra`：

  * ✅ 可以依赖：`domain`；
  * ❌ 不依赖：`api`。

> 当 AI 修改/新增代码时，应自动检查是否违反上述依赖方向，若有违背需在方案中指出。

---

# 2. 本项目的 L3 定义与范围

在本项目中，**下列位置的 Docstring / 注释视为 L3 原子事实（SSOT）**：

* <根据项目填写，典型情况如下：>
* 在 `<SRC_ROOT>` 中：

  * 所有对外暴露的 Public API：

    * 例如：`<PROJECT_NAME>.api` 下的处理函数 / 控制器；
    * 例如：对外可 import 的库接口函数 / 类。
  * 关键领域服务 / 域模型方法：

    * 例如：`<PROJECT_NAME>.domain.*` 中的核心业务方法。
* 若有公共 SDK / 库，可补充：

  * `__init__.py` 中通过 `__all__` 导出的符号的 Docstring。

原则：

* **只要是“对外可见的接口行为”就应有 L3 Docstring，并作为契约单一事实来源**；
* 内部工具函数/私有函数可视情况简化，但当其中封装了关键业务约束时，也建议逐步补齐 L3。

当 AI 修改上述对象的行为 / 逻辑 / 对外使用方式时：

* 必须同步更新对应 Docstring（完整可替换版本）；
* 必须考虑是否需要更新测试与 Diary。

---

# 3. 本项目的 L3 Docstring / 契约模板

> 本节是**项目级的 L3 模板定义**，AI 在创建 / 修改 L3 Docstring 时应优先遵守。
> 若与通用 `role_rules` 中的默认模板冲突，以本节为准。

## 3.1 适用范围

* 适用于本项目中所有 **Public API**：

  * 例如：

    * `api` 层的接口处理函数；
    * `service` 层对外暴露的服务方法；
    * 对外使用的库函数 / 类。
* 对某些“关键 Internal 函数”，可以选择也使用此模板。

> 若某些模块需要不同的模板（如 SDK 与内部服务不同），可在本节下分子小节单独定义。

## 3.2 Python 项目 L3 模板（示例）

> 若项目语言为 Python，请保留并填充此模板；
> 若为其他语言，请改写为对应注释格式（JSDoc、KDoc 等）。

```python
def <function_name>(<params>) -> <ReturnType>:
    """一句话功能概述（让调用方一眼看懂该做什么）。

    功能:
      - 以 1~3 条 bullet 说明该函数的核心行为。

    使用场景:
      - 推荐/典型使用方式：例如在什么业务流程中调用。
      - 不适用或禁止使用的场景（如有）。

    依赖:
      - 关键依赖模块 / 组件 / 外部服务，例如:
        - <PROJECT_NAME>.domain.xxx
        - 外部 API 名称
        - 重要配置项名称

    @harbor.scope: public       # public | internal（按项目约定填写）
    @harbor.idempotency: once   # pure | read-only | once | retriable（按实际语义选择）

    Args:
      <param1> (<type>): 参数的含义、取值范围或约束。
      <param2> (<type>): 如有默认值或特殊含义，在此说明。
      ...

    Returns:
      <ReturnType>: 返回值的结构、语义，以及各字段的含义（如是字典/对象）。

    Raises:
      <ErrorType1>: 在什么条件下会抛出，例如参数非法 / 资源不存在。
      <ErrorType2>: 其它错误类型，逐条列出。
    """
```

> 要求：
>
> * AI 在为本项目生成 / 修改 Docstring 时，应尽量按上述字段结构输出完整版本；
> * 对已有 Docstring，只在**不删除有效信息**的前提下做补充和重构。

## 3.3 其他语言 L3 模板（可选）

> 若项目包含 TypeScript / Java / Go 等多语言，可在此增加对应语言的 L3 模板。
> 例如：JSDoc 模板、KDoc 模板等。

---

# 4. Diary（演进记忆）配置

## 4.1 Diary 文件位置

* 本项目的 Diary 文件为：

```text
specs/DEVELOPMENT_DIARY.md
```

> 若需多仓库共用或模块细分，可在此声明更多 Diary 文件路径并说明各自用途。

## 4.2 Diary 条目推荐格式

AI 在建议新增 Diary 时，应输出如下结构的 Markdown 草稿（用户可直接粘贴）：

```markdown
## YYYY-MM-DD <PROJECT_NAME> <简短变更标题>

- 类型: feature | bugfix | refactor | chore | incident
- 模块: <涉及模块路径，例如 <PROJECT_NAME>.api.user>
- 文件: <相对路径，例如 src/api/user.py>
- 函数/接口: <函数名或 API 标识，如 login_user>
- 摘要: 用一句话概括本次变更做了什么。
- 变更原因:
  - 为什么要改？例如修复 bug / 优化性能 / 对齐上游协议等。
- 具体改动:
  - bullet1（例如“将 DBError 映射为业务错误码 XYZ”）
  - bullet2
- 关联 Issue/PR: #xxx 或 N/A
- 是否可能是 Breaking Change: 是/否（如是，请说明对现有调用方的影响）
```

## 4.3 建议写 Diary 的典型场景

在本项目中，AI 尤其应在以下场景提醒用户写 Diary 并给草稿：

* 对外 API 行为改变：

  * 返回值结构 / 类型 / 语义发生变化；
  * 异常类型或错误码调整；
  * 幂等性 / 重试策略 / 一致性策略改变。
* 影响用户体验或数据的 bugfix：

  * 修复导致 500 / 崩溃 / 数据错乱 / 安全问题的缺陷。
* 重要设计决策：

  * 引入新的模块 / 子系统；
  * 调整系统边界 / 关键依赖。
* 需要团队对齐的 breaking change：

  * 老调用方式将不再支持；
  * 需要迁移步骤或兼容期说明。

---

# 5. 测试与 DDT（Docstring-Driven Testing）约定（可按项目实际调整）

> 若本项目暂未正式启用 DDT，可先将本节作为“建议规范”，后续逐步落实。

## 5.1 测试框架与基本约定

* 测试框架：<如 pytest / unittest / jest / go test 等>。
* 目录结构：`tests/` 下按模块或功能分组。

## 5.2 DDT 意识（与 L3 的关系）

* 对于拥有清晰 L3 Docstring 的 **Public API**：

  * 建议至少有：

    * 1 条正常路径测试；
    * 1 条异常/边界路径测试。
* 当 L3 发生变化时：

  * AI 应提醒用户检查测试是否覆盖新的行为；
  * 在可能时给出“新增/更新哪些测试用例”的建议。

> 若项目使用特定标记（示例）：

```python
@harbor_ddt_target(func="<PROJECT_NAME>.api.login_user", l3_version=1)
def test_login_user_ok():
    ...
```

请在此说明规则，AI 在修改实现 / Docstring 时应同步考虑更新这些标记。

---

# 6. 在本项目中进行 vibe coding 时的默认协作方式

当用户在本仓库中提出以下类型的请求时，AI 应自动按 Harbor-spec 流程处理：

1. **新增功能 / 模块**

   * 起手：用户说明需求、目标模块；
   * AI：先跑「确认循环」，再：

     * 设计或补齐相关 Public API 的 L3 Docstring（用本项目模板）；
     * 然后给出实现骨架 / 代码；
     * 最后给出测试建议与 Diary 建议（视重要性）。

2. **修改行为 / bugfix / 重构**

   * 起手：用户提供发生问题的函数 / 代码片段 / 日志；
   * AI：先从 L3（Docstring）与 Diary 中推导“现在应该是什么”，
     再从实现中找“现在实际上做了什么”，
     最后给出修复方案 + L3 更新 + 测试调整建议 + Diary 草稿（如适用）。

3. **提交前检查 / 发版前 review**

   * 当用户贴出 diff 或说明“准备发版/提 PR”时：

     * AI 应从 Harbor-spec 视角检查：

       * 是否有 Public API 行为变化却未更新 L3；
       * 是否存在明显的 Docstring-实现不一致；
       * 是否存在适合记录在 Diary 中的行为变更；
     * 输出一份“Harbor-spec 视角的 TODO / 风险列表”。

---

# 7. 项目特定约束与补充说明（按需填写）

> 本节用于写**和 Harbor-spec 强相关，但又与具体项目强绑定**的特殊规则，例如：

* 安全 / 合规：

  * 某些模块必须记录所有行为变更到 Diary（例如支付、权限、审计模块）；
  * 某些 API 不允许改变错误码语义，除非明确标记 breaking change。
* 性能 / 可靠性：

  * 某些路径的幂等性 / 重试策略必须在 L3 中明确说明；
  * 某类调用必须在 Docstring 中标注“可能阻塞/耗时”，并在实现中使用异步或队列。
* 团队习惯：

  * 本项目要求所有 Docstring / 注释 / Diary 使用**简体中文**（或规范双语），避免混用英语和中文缩写；
  * 对于重点模块，要求在 Diary 中附上 “影响范围评估”。

> 当 AI 感知到用户的请求触碰以上“特殊规则”时，应在确认循环和最终方案中明确指出这些约束，避免无意违背项目自定义规则。

```

你以后要给其它项目写 `project_rules`，只需要：

- 把 `<PROJECT_NAME>` / 目录结构 / 分层架构 / L3 模板 / Diary 路径 等具体化；  
- 删掉和该项目无关的小节；  
- 保留「L3 定义 + L3 模板 + Diary 规则 + 流程习惯」四大块，就能快速得到一份可用的 Harbor-spec 项目宪法。
```

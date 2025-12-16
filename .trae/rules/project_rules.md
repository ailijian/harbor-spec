---
description: Harbor-spec Reference Implementation Project Rules
globs: ["**/*.py", "specs/**/*.jsonl", ".harbor/**/*.yaml"]
alwaysApply: true
---

# 0. 仓库说明：Harbor-spec Reference Implementation

- **项目目标**：
  - 实现 Harbor-spec v1.0.2 标准的参考实现（Reference Implementation）。
  - 提供 CLI 工具 (`harbor`)，用于管理 vibe coding 上下文。
  - 提供 Python Adapter，用于解析 Python 项目的 L3/DDT。
- **Dogfooding 原则**：
  - 本项目**必须**严格遵守 Harbor-spec v1.0.2 规范。
  - 我们是规则的制定者，也是规则的第一个遵守者。任何“走捷径”的行为都是不被允许的。

---

# 1. 代码架构与分层 (Python-only v1.0.2)

## 1.1 目录结构
```text
harbor/
  cli/             # 命令行入口 (Typer/Click)
  core/            # 核心业务逻辑 (Sync Engine, Indexer, Guard)
  adapters/        # 语言适配器 (Python AST 解析)
  utils/           # 通用工具
  config/          # 配置加载与校验
specs/
  diary/           # [v1.0.2] 按月轮转的 Diary
    2025-12.jsonl
tests/             # Pytest 测试集
.harbor/           # 自举配置 (Harbor 管理 Harbor)
```

## 1.2 依赖原则 (洋葱架构)

1.  **harbor.core**：内核层。不依赖 cli，只依赖 adapters 接口（抽象）和标准库。
2.  **harbor.adapters**：适配层。依赖 core 定义的抽象接口，实现具体语言解析。
3.  **harbor.cli**：交互层。依赖 core 和 adapters，负责用户交互和输出。
4.  **harbor.utils**：被各层共享的无状态工具。

-----

# 2\. 本项目的 L3 定义 (Strictness Rules)

## 2.1 严格度分级策略

本项目采用 **v1.0.2 Strict 策略**：

  * **Strict (严格级)**：

      * **范围**：
          * `harbor.core.*` 中的所有核心逻辑（如 `IndexBuilder`, `SyncEngine`）。
          * `harbor.adapters.python.*` 中的解析逻辑。
          * `harbor.cli.main` 中的所有命令入口。
      * **要求**：完整 Docstring + `@harbor.scope: public` + **DDT 强版本绑定**。

  * **Standard (标准级)**：

      * **范围**：`harbor.utils.*` 及各模块内部 helper 函数。
      * **要求**：Google Style Docstring + `@harbor.scope: internal`。

## 2.2 L3 Docstring 模板 (Reference)

```python
def sync_l3(check_only: bool = False) -> SyncReport:
    """执行 L3 Docstring 的同步检查或应用。

    功能:
      - 扫描指定 scope 内的源文件，计算 signature_hash 和 body_hash。
      - 对比 .harbor/cache/l3_index.json (Transient Index)。
      - 生成同步报告，指出 Missing 或 Out-of-sync 的 Docstring。

    使用场景:
      - CLI `harbor sync l3` 命令的核心实现。
      - Pre-commit hook 调用。

    依赖:
      - harbor.core.index.IndexBuilder
      - harbor.adapters.AdapterManager

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: read-only  # if check_only=True

    Args:
      check_only (bool): 若为 True，仅返回报告不修改文件。默认为 False。

    Returns:
      SyncReport: 包含同步结果统计、错误列表的对象。

    Raises:
      ConfigError: 若 .harbor/config.yaml 加载失败。
      IndexError: 若缓存索引损坏且无法重建。
    """
```

-----

# 3\. Diary (演进记忆) 规范

## 3.1 存储位置

  * **路径**：`specs/diary/{YYYY-MM}.jsonl` (按月自动轮转)
  * **格式**：JSONL (JSON Lines)

## 3.2 记录原则

作为参考实现，以下变更**必须**记录 Diary：

1.  **Spec 变更**：任何对 Harbor 协议本身的调整（如修改了 Index 的 JSON 结构）。
2.  **Core Logic**：修改了 Hash 计算方式、同步判定逻辑。
3.  **CLI Behavior**：修改了命令参数、输出格式。

## 3.3 Draft 模板 (v1.0.2)

```json
{
  "type": "feature", // feature | bugfix | refactor | core-change
  "importance": "high",
  "visibility": "public",
  "module": "harbor.core.index",
  "summary": "将 l3_index 从入库文件改为构建缓存",
  "reason": "解决多人协作时的 Git 合并冲突问题 (v1.0.2 Spec)",
  "changes": [
    "修改 IndexBuilder，输出路径指向 .harbor/cache/",
    "更新 .gitignore 排除 .harbor/cache"
  ]
}
```

-----

# 4\. DDT (测试) 约定

## 4.1 绑定策略

  * **Core/Adapter 层**：必须使用 `@harbor_ddt_target(..., l3_version=N)`。
      * *原因*：核心逻辑的契约稳定性至关重要，不能静默失败。
  * **Utils 层**：允许使用 `@harbor_ddt_target(..., strategy="latest")`。

## 4.2 测试框架

  * 使用 `pytest`。
  * DDT 装饰器实现位于 `harbor.test_utils.ddt` (自举：我们先实现这个装饰器，然后用它测试它自己)。

-----

# 5\. Vibe Coding 协作流 (Harbor on Harbor)

当你在本项目写代码时：

1.  **Check Context**: 先看 `harbor.core` 的现有 L3，确保不破坏核心同步逻辑。
2.  **Strict Mode**: 为你写的所有 Core 函数加上 `strict` 级别的 Docstring。
3.  **Update Test**: 如果你改了 Core，**必须**同步更新对应的 DDT 版本号，不要偷懒用 latest。
4.  **Diary First**: 如果你改了 Spec 实现，先写一条 Diary 确认设计意图。

> **Self-Correction**: 如果你发现自己在写代码时觉得 Harbor 的某个规范很繁琐，请记录下来（作为一条 `refactor` 类型的 Diary 草稿），这可能是优化 Harbor v1.1 的重要输入。

```

---

## 任务理解
- 实现 Memory Layer：在 `specs/diary/{YYYY-MM}.jsonl` 结构化记录“代码背后的决策”。
- 编写 `harbor/core/diary.py`，提供 `DiaryManager`（写入/读取/导出）。
- 将 CLI 增加 `harbor diary log` 与 `harbor diary export`。
- 按 v1.0.2 规范支持枚举字段与月度轮转，并完成一次 Dogfooding 记录。

## 上下文加载
- 已阅读 Phase 计划与蓝图：v1.0.2 引入 Diary 月度 JSONL 轮转、`importance/visibility` 字段、软噪音控制与导出能力。
- 本项目规则：`harbor.core.*` 归属 Strict 级别，接口需完整 L3 Docstring 与 DDT 强绑定。

## L3 接口设计：DiaryManager.log
```python
def log(
    summary: str,
    type: str = "feature",
    importance: str = "normal",
    visibility: str = "internal",
    details: str | None = None,
    ref_commit: str | None = None,
    author: str | None = None,
    ts: str | None = None,
) -> DiaryEntry:
    """写入一条 DiaryEntry 到当月 JSONL。

    功能:
      - 构造 DiaryEntry 并追加写入 `specs/diary/{YYYY-MM}.jsonl`。
      - 自动处理月度轮转与文件创建。
      - 生成缺省元数据：`ts`（ISO8601 UTC）、`author`（读取 git user.name 或默认 "AI"）。

    使用场景:
      - CLI `harbor diary log` 的核心实现。
      - 在 `harbor sync --pre-commit` 中写入重要事件草稿。

    依赖:
      - 文件系统访问（`specs/diary` 目录）。
      - `harbor.core.diary.DiaryManager` 数据模型与校验。

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: once

    Args:
      summary (str): 变更摘要。
      type (str): `feature|bugfix|refactor|chore|incident`。
      importance (str): `trivial|normal|high|critical`。
      visibility (str): `internal|repo|public`。
      details (str | None): 详细描述，可选。
      ref_commit (str | None): 关联 Git Hash，可选。
      author (str | None): 提交人；缺省从 git config 获取或 "AI"。
      ts (str | None): 指定 ISO8601 时间戳；缺省为当前 UTC。

    Returns:
      DiaryEntry: 已校验并写入的条目对象。

    Raises:
      ValueError: 枚举值不合法或必填字段为空。
      OSError: 目录/文件不可写或创建失败。
      ConfigError: 项目根路径无 `specs/diary` 配置或不可访问。
    """
```

## 技术实现计划
- 数据模型
  - 定义 `DiaryEntry` 为 `dataclass`，字段：`ts,type,summary,details,author,importance,visibility,ref_commit`；提供 `to_json()` 序列化与枚举校验。
  - 校验枚举集与必填项；`ts` 默认 `datetime.utcnow().isoformat(timespec="seconds") + "Z"`；`author` 从 `git config user.name` 读取失败则置 "AI"。
- 写入与轮转
  - 计算当月文件路径 `specs/diary/{YYYY-MM}.jsonl`；若目录/文件不存在则创建。
  - 以 JSONL 追加写入；确保单行合法 JSON；并返回 `DiaryEntry`。
- 读取（Active Memory）
  - `load_active()`：默认聚合“当月 + 上个月”；支持可选过滤（`visibility>=level`、`since`）。
- 导出
  - `export_markdown(since: Optional[str], visibility: Optional[str]) -> str`：生成 Release Note 风格 Markdown（按 `ts` 倒序、带 `type/importance/summary`）。
- CLI 集成
  - 在现有 CLI 框架下新增 `diary` 命令族：
    - `harbor diary log --summary "..." --type feature --importance high --visibility public [--details "..."] [--ref-commit <sha>]`。
    - `harbor diary export [--since <YYYY-MM-DD>] [--visibility <level>] > diary.md`。
  - 使用项目现有 CLI库（Typer/Click），保持交互与输出一致性。
- Dogfooding
  - 通过 `DiaryManager.log` 或 CLI 写入：
    - Type: `feature`；Summary: `实现 L2 锚点视图生成器`；Importance: `high`；Visibility: `public`；Details: `支持自动生成模块 README，集成 DDT 状态显示，实现 Strict/Standard 视觉分级。`

## 风险与决策
- Author 获取失败回退策略：默认 "AI"（可后续在 CLI 通过 `--author` 覆盖）。
- 时间戳统一为 UTC ISO8601 `Z`，避免本地时区混乱。
- 枚举严格校验会导致 CLI 输入错误直接失败：保留明确错误消息。
- 隐私与噪音：`visibility` 过滤在 `export` 生效；默认仅导出 `repo/public`。
- 文件并发追加：当前版本不做锁处理，CI/单机场景足够；后续可加文件锁提升稳健性。

## 验收与输出
- `harbor diary log` 能正常写入当月 JSONL，`load_active()` 返回期望集合。
- `harbor diary export` 可生成 Markdown 概要，支持 `--visibility` 与 `--since`。
- 仓库出现 `specs/diary/2025-12.jsonl` 且包含 Dogfooding 条目。

# 确认执行：Phase 6 启动

方案评估通过。接口定义非常清晰。

## 启动 Phase 6: Diary 子系统

请按你的计划执行，并采纳以下 2 个优化点：

### 1. Author 获取策略增强
在确定 `author` 字段时，请按以下优先级顺序获取：
1. CLI 参数 `--author` (显式指定)
2. 环境变量 `HARBOR_AUTHOR` (CI 友好)
3. `git config user.name`
4. 环境变量 `USER` or `USERNAME`
5. 默认回退值: `"AI"`

### 2. 导出格式美化
在 `export_markdown` 中，请对不同 `importance` 的条目做视觉区分（例如加 Emoji）：
- **Critical**: 🔴
- **High**: 🟠
- **Normal**: 🔵
- **Trivial**: ⚪
这样生成的 Release Note 会更具可读性。

**Dogfooding 验证:**
完成代码后，请务必执行那条 Dogfooding 命令：
`python -m harbor.cli.main diary log --summary "实现 L2 锚点视图生成器" ...`

**交付物清单确认**:
- `harbor/core/diary.py`
- `harbor/cli/main.py`
- `specs/diary/2025-12.jsonl` (包含 Dogfooding 条目)

请开始编码。期待看到 Harbor 的第一条正式记忆。
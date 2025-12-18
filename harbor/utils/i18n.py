import os
import locale
from pathlib import Path
from typing import Dict, Any, Optional
import yaml


def get_lang(config_path: Optional[Path] = None) -> str:
    """解析当前语言。

    功能:
      - 读取环境变量与配置文件以确定语言。
      - 回退到系统区域设置与英文。

    使用场景:
      - CLI 提示与用户可见错误的语言选择。

    依赖:
      - yaml.safe_load
      - locale.getdefaultlocale

    @harbor.scope: public
    @harbor.l3_strictness: standard
    @harbor.idempotency: read-only

    Args:
      config_path (Path | None): 指定配置文件路径，未提供时默认使用项目根的 `.harbor/config.yaml`。

    Returns:
      str: 语言代码，`zh` 或 `en`。
    """
    env = (os.environ.get("HARBOR_LANGUAGE") or os.environ.get("HARBOR_LANG") or "").strip().lower()
    if env in ("zh", "en"):
        return env
    cfg_file = config_path or (Path.cwd() / ".harbor" / "config.yaml")
    if cfg_file.exists():
        try:
            data = yaml.safe_load(cfg_file.read_text(encoding="utf-8")) or {}
        except Exception:
            data = {}
        lang = str(data.get("language", "") or "").strip().lower()
        if lang in ("zh", "en"):
            return lang
        if lang == "auto":
            return "en"
        elif lang:
            return "zh" if lang.startswith("zh") else "en"
    return "en"


MESSAGES: Dict[str, Dict[str, str]] = {
    "en": {
        "cli.lock.init": "[Scanning] Initializing...",
        "cli.lock.scanning": "[Scanning] {path}",
        "cli.lock.done": "[Done] {path}",
        "cli.lock.skipped": "[Skipped] {path}",
        "cli.lock.error": "[Error] {path}",
        "cli.lock.summary": "scanned={scanned} updated={updated} skipped={skipped} items={items} db={db}",
        "cli.config.title": "Harbor Config",
        "cli.config.key": "Key",
        "cli.config.value": "Value",
        "cli.config.added": "Added '{path}' to code_roots.",
        "cli.config.removed": "Removed '{path}' from code_roots.",
        "cli.config.nochanges": "No changes. Path not in code_roots.",
        "cli.status.scanning": "[Scanning] Checking file system changes...",
        "cli.status.nochanges": "No changes detected.",
        "cli.status.title": "Harbor Context Status:",
        "cli.status.drift": "Changes to implementation (Drift):",
        "cli.status.contract": "Changes to contract:",
        "cli.status.modified": "Changes (Body + Contract):",
        "cli.status.untracked": "Untracked functions:",
        "cli.status.missing": "Missing functions:",
        "cli.check.title": "Harbor Check Report:",
        "cli.check.ddt": "[DDT] Validation:",
        "cli.check.bindings": "Bindings scanned: {count}",
        "cli.check.nobindings": "No DDT bindings found.",
        "cli.semantic.title": "[Semantic] Audit:",
        "cli.semantic.notargets": "No targets.",
        "cli.docs.nochanges": "No changes needed.",
        "cli.docs.wrote": "Wrote: {path}",
        "cli.log.nochanges": "No changes detected. Nothing to draft.",
        "cli.log.tip1": "[Tip] 'log' analyzes unindexed changes (Drift/Modified).",
        "cli.log.tip2": "If you just ran 'harbor lock', the snapshot matches current code.",
        "cli.log.tip3": "Modify code first, then run 'harbor log' before updating the index.",
        "cli.log.llm_env_hint": "Please set HARBOR_LLM_PROVIDER=openai and HARBOR_LLM_API_KEY in environment, then retry.",
        "cli.log.context_too_long": "Hint: current context may exceed the model limit.",
        "cli.log.ask_simplify": "Use simplified context? [Y]es / [N]o",
        "cli.log.ai_failed": "AI drafting failed: {msg}",
        "cli.log.panel.title": "Diary Draft (AI)",
        "cli.log.panel.summary": "Summary",
        "cli.log.panel.type": "Type",
        "cli.log.panel.importance": "Importance",
        "cli.log.panel.details": "Details",
        "cli.log.ask_save": "Save this entry? [Y]es / [E]dit summary / [N]o",
        "cli.log.discarded": "Discarded.",
        "cli.log.ask_new_summary": "New summary",
        "cli.adopt.table.title": "Decorate Candidates",
        "cli.adopt.table.action": "Action",
        "cli.adopt.table.func": "Func",
        "cli.adopt.table.file": "File",
        "cli.adopt.table.hasdoc": "HasDoc",
        "cli.adopt.table.hasscope": "HasScope",
        "cli.adopt.summary": "Found {total} candidates. {doc_yes} have docstrings, {doc_no} do not.",
        "cli.adopt.planned": "Planned changes to {count} files.",
        "cli.adopt.apply_prompt": "Apply changes to {count} files? [y/N]",
        "cli.adopt.nochanges": "No changes applied.",
        "cli.init.exist": "Config file already exists.",
        "cli.init.detected": "[Harbor] Detected {stacks} project.",
        "cli.init.excludes": "[Harbor] Auto-configured excludes: {keys}{extra}",
        "cli.init.roots": "Auto-detected code roots: {roots}",
        "cli.init.done": "Initialized Harbor in current directory.",
        "cli.init.next": "Run 'harbor lock' to start.",
        "cli.deprecated": "[Deprecated] command \"{old}\" mapped to \"{new}\", please update to v2.0 usage.",
    },
    "zh": {
        "cli.lock.init": "[扫描中] 初始化...",
        "cli.lock.scanning": "[扫描中] {path}",
        "cli.lock.done": "[完成] {path}",
        "cli.lock.skipped": "[跳过] {path}",
        "cli.lock.error": "[错误] {path}",
        "cli.lock.summary": "扫描={scanned} 更新={updated} 跳过={skipped} 项目={items} 库={db}",
        "cli.config.title": "Harbor 配置",
        "cli.config.key": "键",
        "cli.config.value": "值",
        "cli.config.added": "已将 '{path}' 添加到 code_roots。",
        "cli.config.removed": "已从 code_roots 移除 '{path}'。",
        "cli.config.nochanges": "无变更。路径不在 code_roots 中。",
        "cli.status.scanning": "[扫描中] 检查文件系统变化...",
        "cli.status.nochanges": "未检测到变更。",
        "cli.status.title": "Harbor 上下文状态：",
        "cli.status.drift": "实现变更（Drift）：",
        "cli.status.contract": "契约变更：",
        "cli.status.modified": "综合变更（Body + Contract）：",
        "cli.status.untracked": "未跟踪函数：",
        "cli.status.missing": "缺失函数：",
        "cli.check.title": "Harbor 检查报告：",
        "cli.check.ddt": "[DDT] 绑定校验：",
        "cli.check.bindings": "绑定扫描数量：{count}",
        "cli.check.nobindings": "未发现 DDT 绑定。",
        "cli.semantic.title": "[语义] 审计：",
        "cli.semantic.notargets": "无目标。",
        "cli.docs.nochanges": "无需变更。",
        "cli.docs.wrote": "已写入：{path}",
        "cli.log.nochanges": "未检测到变更，无需起草。",
        "cli.log.tip1": "提示：'log' 分析未入库的变更（Drift/Modified）。",
        "cli.log.tip2": "若刚运行过 'harbor lock'，快照与当前代码保持一致。",
        "cli.log.tip3": "先修改代码，再在更新索引前运行 'harbor log'。",
        "cli.log.llm_env_hint": "请在环境中设置 HARBOR_LLM_PROVIDER=openai 与 HARBOR_LLM_API_KEY，再重试。",
        "cli.log.context_too_long": "提示：当前上下文可能超过模型限制。",
        "cli.log.ask_simplify": "是否使用简化上下文继续？ [Y]es / [N]o",
        "cli.log.ai_failed": "AI 起草失败：{msg}",
        "cli.log.panel.title": "Diary 草稿（AI）",
        "cli.log.panel.summary": "摘要",
        "cli.log.panel.type": "类型",
        "cli.log.panel.importance": "重要性",
        "cli.log.panel.details": "详细",
        "cli.log.ask_save": "保存此条目？[Y]es / [E]dit summary / [N]o",
        "cli.log.discarded": "已丢弃。",
        "cli.log.ask_new_summary": "新摘要",
        "cli.adopt.table.title": "装饰候选",
        "cli.adopt.table.action": "操作",
        "cli.adopt.table.func": "函数",
        "cli.adopt.table.file": "文件",
        "cli.adopt.table.hasdoc": "有文档",
        "cli.adopt.table.hasscope": "有 scope",
        "cli.adopt.summary": "找到 {total} 个候选。{doc_yes} 有 docstring，{doc_no} 无。",
        "cli.adopt.planned": "计划变更 {count} 个文件。",
        "cli.adopt.apply_prompt": "应用这些变更到 {count} 个文件？ [y/N]",
        "cli.adopt.nochanges": "未应用任何变更。",
        "cli.init.exist": "配置文件已存在。",
        "cli.init.detected": "[Harbor] 检测到 {stacks} 项目。",
        "cli.init.excludes": "[Harbor] 自动配置排除：{keys}{extra}",
        "cli.init.roots": "自动探测的代码根：{roots}",
        "cli.init.done": "已在当前目录初始化 Harbor。",
        "cli.init.next": "运行 'harbor lock' 开始使用。",
        "cli.deprecated": "[弃用] 命令 \"{old}\" 已映射为 \"{new}\"，请更新为 v2.0 用法。",
    },
}


def t(key: str, **kwargs: Any) -> str:
    """根据当前语言返回文案。

    @harbor.scope: public
    @harbor.l3_strictness: standard
    @harbor.idempotency: read-only

    Args:
      key (str): 文案键或模板。

    Returns:
      str: 本地化后的文案。
    """
    lang = get_lang()
    d = MESSAGES.get(lang) or MESSAGES["en"]
    tpl = d.get(key) or key
    if kwargs:
        try:
            return tpl.format(**kwargs)
        except Exception:
            return tpl
    return tpl

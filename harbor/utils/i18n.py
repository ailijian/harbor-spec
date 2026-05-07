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
        "cli.lock.register_adopted_wrote": "Registered derived adopted_roots ({count}).",
        "cli.lock.register_adopted_hint": "Hint: run 'harbor config adopted --write' to persist derived adopted_roots.",
        "cli.config.title": "Harbor Config",
        "cli.config.key": "Key",
        "cli.config.value": "Value",
        "cli.config.adopt_hint": "Hint: register explicit adopted roots via 'harbor adopt <dir> --yes'.",
        "cli.config.adopted.wrote": "Wrote derived adopted_roots ({count}).",
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
        "cli.start.title": "Harbor Start:",
        "cli.start.clean": "No Harbor changes detected. You can start AI coding.",
        "cli.start.dirty": "Existing Harbor changes detected. Resolve drift or finish the current task before starting a new one.",
        "cli.checkpoint.title": "Harbor Checkpoint:",
        "cli.finish.title": "Harbor Finish:",
        "cli.finish.next_steps": "Next steps:\n  - harbor docs --module <module> --write\n  - harbor log\n  - harbor accept",
        "cli.finish.sync_context.title": "Context Sync:",
        "cli.finish.sync_context.docs": "- Refreshing L2 README for changed modules...",
        "cli.finish.sync_context.capsules": "- Refreshing Module Capsules for changed modules...",
        "cli.finish.sync_context.stale": "- Checking Module Capsule stale status...",
        "cli.finish.sync_context.none": "No changed modules detected. Context sync skipped.",
        "cli.finish.sync_context.next_steps": (
            "Next steps:\n"
            "  - Run `harbor log` if this task involved an important decision or Contract Change.\n"
            "  - Run `harbor accept` when you are ready to accept the new baseline.\n"
            "  - Optionally run `harbor module promote-skill <module>` for high-value modules with up-to-date capsules."
        ),
        "cli.accept.done": "Accepted current Harbor baseline.",
        "cli.check.title": "Harbor Check Report:",
        "cli.check.ddt": "[DDT] Validation:",
        "cli.check.bindings": "Bindings scanned: {count}",
        "cli.check.nobindings": "No DDT bindings found.",
        "cli.semantic.title": "[Semantic] Audit:",
        "cli.semantic.notargets": "No targets.",
        "cli.docs.nochanges": "No changes needed.",
        "cli.docs.wrote": "Wrote: {path}",
        "cli.docs.changed.none": "No changed modules detected. Canonical L2 README files are up to date.",
        "cli.docs.changed.found": "Changed modules detected:",
        "cli.docs.all.none": "No indexed modules found. Nothing to generate.",
        "cli.docs.all.found": "Generating canonical L2 README for all indexed modules:",
        "cli.docs.mode_conflict": "--module, --changed, and --all are mutually exclusive.",
        "cli.docs.preview_only": "Preview only. Use --write to update canonical L2 README files (and optional module README exports).",
        "cli.docs.updated": "Updated:",
        "cli.docs.skipped_unsafe.title": "Skipped unsafe indexed modules:",
        "cli.docs.unsafe_reason.outside_root": "outside repository root",
        "cli.docs.unsafe_reason.traversal": "contains parent traversal",
        "cli.docs.unsafe_reason.invalid": "empty or invalid module",
        "cli.docs.module_unsafe": "Unsafe module is not allowed for explicit --module write: {module} ({reason}).",
        "cli.project.structure.title": "Project structure view:",
        "cli.project.structure.preview_only": "Preview only. Use --write to update {path}.",
        "cli.project.structure.updated": "Updated:",
        "cli.project.structure.no_index": "No indexed modules found. Generated a metadata-only project structure view.",
        "cli.stale.title": "Harbor Stale Check",
        "cli.stale.scope.changed": "changed modules",
        "cli.stale.scope.all": "all indexed modules",
        "cli.stale.scope.module": "module: {module}",
        "cli.stale.none_changed": "No changed modules detected. Derived context views are up to date.",
        "cli.stale.none_all": "No indexed modules found. Nothing to check.",
        "cli.stale.all_up_to_date": "All derived context views are up to date.",
        "cli.stale.l2": "L2 README",
        "cli.stale.l2_export": "Module README Export",
        "cli.stale.capsule": "Module Capsule",
        "cli.stale.up_to_date": "up to date",
        "cli.stale.stale": "stale",
        "cli.stale.unknown": "unknown",
        "cli.stale.disabled": "disabled",
        "cli.stale.reason": "Reason",
        "cli.stale.suggested": "Suggested",
        "cli.stale.mode_conflict": "--module, --changed, and --all are mutually exclusive.",
        "cli.doctor.title": "Harbor Doctor",
        "cli.doctor.scope.changed": "changed modules",
        "cli.doctor.scope.all": "all indexed modules",
        "cli.doctor.scope.module": "module: {module}",
        "cli.doctor.pass": "PASS",
        "cli.doctor.warn": "WARN",
        "cli.doctor.fail": "FAIL",
        "cli.doctor.skip": "SKIP",
        "cli.doctor.config_index": "Config / Index",
        "cli.doctor.workspace_status": "Workspace Status",
        "cli.doctor.ddt_fast": "DDT Fast Check",
        "cli.doctor.derived_views": "Derived Views",
        "cli.doctor.derived_views.legacy_meta_detected": "legacy metadata detected: .harbor/l2_meta.json (read-compatible only)",
        "cli.doctor.derived_views.legacy_meta_canonical": "canonical metadata path: .harbor/views/l2/_meta.json",
        "cli.doctor.skill_refs": "Skill References",
        "cli.doctor.summary.healthy": "Summary:\n- Harbor context looks healthy.",
        "cli.doctor.summary.warnings": "Summary:\n- {count} warnings found.",
        "cli.doctor.no_changes_made": "- No automatic changes were made.",
        "cli.doctor.suggested_next_steps": "Suggested next steps:",
        "cli.doctor.mutually_exclusive": "--module, --changed, and --all are mutually exclusive.",
        "cli.module.inspect.title": "Module inspect: {module}",
        "cli.module.inspect.none": "No indexed records found for module '{module}'.",
        "cli.module.seal.title": "Module seal: {module}",
        "cli.module.seal.preview_only": "Preview only. Use --write to update module capsule files under {path}.",
        "cli.module.seal.updated": "Updated:",
        "cli.module.seal.none": "No indexed records found for module '{module}'. Nothing to seal.",
        "cli.module.seal.changed.none": "No changed modules detected. Module capsules are up to date.",
        "cli.module.seal.changed.found": "Changed modules detected:",
        "cli.module.seal.all.none": "No indexed modules found. Nothing to seal.",
        "cli.module.seal.all.found": "Generating Module Capsules for all indexed modules:",
        "cli.module.seal.batch.updated": "Updated:",
        "cli.module.seal.batch.preview_only": "Preview only. Use --write to update module capsule files under {path}.",
        "cli.module.seal.mode_conflict": "module seal modes are mutually exclusive: choose exactly one of <module>, --changed, or --all.",
        "cli.module.stale.title": "Module Capsule Status: {module}",
        "cli.module.stale.status": "Status",
        "cli.module.stale.fingerprint": "Fingerprint",
        "cli.module.stale.up_to_date": "up to date",
        "cli.module.stale.stale": "stale",
        "cli.module.stale.reason": "Reason",
        "cli.module.stale.suggest": "Suggested",
        "cli.module.stale.none_changed": "No changed modules detected. Module capsules are up to date.",
        "cli.module.stale.none_all": "No indexed modules found. Nothing to check.",
        "cli.module.stale.changed.found": "Checking stale Module Capsules for changed modules:",
        "cli.module.stale.all.found": "Checking stale Module Capsules for all indexed modules:",
        "cli.module.stale.mode_conflict": "module stale modes are mutually exclusive: choose exactly one of <module>, --changed, or --all.",
        "cli.module.promote_skill.generated": "Generated Skill:",
        "cli.module.promote_skill.references": "This skill is a thin entrypoint. It references canonical capsule files:",
        "cli.module.promote_skill.missing_capsule": "Module capsule not found for {module}.",
        "cli.module.promote_skill.stale_capsule": "Module capsule is stale for {module}.",
        "cli.module.promote_skill.stale_hint": "Run:\n  harbor module seal {module} --write\nbefore promoting it to a skill.",
        "cli.module.promote_skill.unknown_module": "No indexed records found for module {module}.",
        "cli.module.promote_skill.unknown_module.hint": "Run harbor module inspect {module} for details.",
        "cli.module.promote_skill.seal_hint": "Run:\n  harbor module seal {module} --write",
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
        "cli.adopt.applied": "Applied changes to {files} files.",
        "cli.adopt.added_config": "Registered '{path}' into code_roots.",
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
        "cli.lock.register_adopted_wrote": "已写入派生的 adopted_roots（{count} 条）。",
        "cli.lock.register_adopted_hint": "提示：运行 'harbor config adopted --write' 可将派生接管目录写入配置。",
        "cli.config.title": "Harbor 配置",
        "cli.config.key": "键",
        "cli.config.value": "值",
        "cli.config.adopt_hint": "提示：通过 'harbor adopt <目录> --yes' 注册明确的接管目录。",
        "cli.config.adopted.wrote": "已写入派生的 adopted_roots（{count} 条）。",
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
        "cli.start.title": "Harbor 开始检查：",
        "cli.start.clean": "未检测到 Harbor 变更。你可以开始 AI coding。",
        "cli.start.dirty": "检测到现有 Harbor 变更。请先解决漂移或完成当前任务，再开启新任务。",
        "cli.checkpoint.title": "Harbor 检查点：",
        "cli.finish.title": "Harbor 收尾检查：",
        "cli.finish.next_steps": "建议下一步：\n  - harbor docs --module <module> --write\n  - harbor log\n  - harbor accept",
        "cli.finish.sync_context.title": "上下文同步：",
        "cli.finish.sync_context.docs": "- 刷新变更模块的 L2 README...",
        "cli.finish.sync_context.capsules": "- 刷新变更模块的 Module Capsule...",
        "cli.finish.sync_context.stale": "- 检查变更模块的 Module Capsule 过时状态...",
        "cli.finish.sync_context.none": "未检测到变更模块。已跳过上下文同步。",
        "cli.finish.sync_context.next_steps": (
            "建议下一步：\n"
            "  - 若本次任务包含重要决策或 Contract Change，请执行 `harbor log`。\n"
            "  - 准备接受新基线时，请执行 `harbor accept`。\n"
            "  - 可选：对高价值且 capsule 已最新的模块执行 `harbor module promote-skill <module>`。"
        ),
        "cli.accept.done": "已接受当前 Harbor 基线。",
        "cli.check.title": "Harbor 检查报告：",
        "cli.check.ddt": "[DDT] 绑定校验：",
        "cli.check.bindings": "绑定扫描数量：{count}",
        "cli.check.nobindings": "未发现 DDT 绑定。",
        "cli.semantic.title": "[语义] 审计：",
        "cli.semantic.notargets": "无目标。",
        "cli.docs.nochanges": "无需变更。",
        "cli.docs.wrote": "已写入：{path}",
        "cli.docs.changed.none": "未检测到变更模块。canonical L2 README 已是最新。",
        "cli.docs.changed.found": "检测到变更模块：",
        "cli.docs.all.none": "未发现可生成的已索引模块。",
        "cli.docs.all.found": "正在为全部已索引模块生成 canonical L2 README：",
        "cli.docs.mode_conflict": "--module、--changed 与 --all 互斥，只能选择一种模式。",
        "cli.docs.preview_only": "仅预览。使用 --write 写入 canonical L2 README（以及可选 module README 导出）。",
        "cli.docs.updated": "已更新：",
        "cli.docs.skipped_unsafe.title": "已跳过不安全的索引模块：",
        "cli.docs.unsafe_reason.outside_root": "位于仓库根之外",
        "cli.docs.unsafe_reason.traversal": "包含父目录穿越",
        "cli.docs.unsafe_reason.invalid": "空或无效模块",
        "cli.docs.module_unsafe": "显式 --module 写入不允许不安全模块：{module}（{reason}）。",
        "cli.project.structure.title": "项目结构视图：",
        "cli.project.structure.preview_only": "仅预览。使用 --write 更新 {path}。",
        "cli.project.structure.updated": "已更新：",
        "cli.project.structure.no_index": "未发现已索引模块。已生成仅包含元信息的项目结构视图。",
        "cli.stale.title": "Harbor 过期检查",
        "cli.stale.scope.changed": "变更模块",
        "cli.stale.scope.all": "全部已索引模块",
        "cli.stale.scope.module": "模块：{module}",
        "cli.stale.none_changed": "未检测到变更模块。派生上下文视图已是最新。",
        "cli.stale.none_all": "未发现已索引模块，无需检查。",
        "cli.stale.all_up_to_date": "所有派生上下文视图均为最新。",
        "cli.stale.l2": "L2 README",
        "cli.stale.l2_export": "Module README 导出",
        "cli.stale.capsule": "Module Capsule",
        "cli.stale.up_to_date": "最新",
        "cli.stale.stale": "过时",
        "cli.stale.unknown": "未知",
        "cli.stale.disabled": "已禁用",
        "cli.stale.reason": "原因",
        "cli.stale.suggested": "建议",
        "cli.stale.mode_conflict": "--module、--changed 与 --all 互斥。",
        "cli.doctor.title": "Harbor Doctor",
        "cli.doctor.scope.changed": "变更模块",
        "cli.doctor.scope.all": "全部已索引模块",
        "cli.doctor.scope.module": "模块：{module}",
        "cli.doctor.pass": "PASS",
        "cli.doctor.warn": "WARN",
        "cli.doctor.fail": "FAIL",
        "cli.doctor.skip": "SKIP",
        "cli.doctor.config_index": "配置 / 索引",
        "cli.doctor.workspace_status": "工作区状态",
        "cli.doctor.ddt_fast": "DDT 快速检查",
        "cli.doctor.derived_views": "派生视图",
        "cli.doctor.derived_views.legacy_meta_detected": "检测到 legacy metadata：.harbor/l2_meta.json（只读兼容）",
        "cli.doctor.derived_views.legacy_meta_canonical": "canonical metadata 路径：.harbor/views/l2/_meta.json",
        "cli.doctor.skill_refs": "Skill 引用",
        "cli.doctor.summary.healthy": "Summary:\n- Harbor 上下文整体健康。",
        "cli.doctor.summary.warnings": "Summary:\n- 发现 {count} 个告警。",
        "cli.doctor.no_changes_made": "- 未执行任何自动变更。",
        "cli.doctor.suggested_next_steps": "建议下一步：",
        "cli.doctor.mutually_exclusive": "--module、--changed 与 --all 互斥。",
        "cli.module.inspect.title": "模块检查：{module}",
        "cli.module.inspect.none": "未找到模块 '{module}' 的已索引记录。",
        "cli.module.seal.title": "模块封装：{module}",
        "cli.module.seal.preview_only": "仅预览。使用 --write 更新 {path} 下的模块胶囊文件。",
        "cli.module.seal.updated": "已更新：",
        "cli.module.seal.none": "未找到模块 '{module}' 的已索引记录，无法生成胶囊。",
        "cli.module.seal.changed.none": "未检测到变更模块。模块胶囊已是最新。",
        "cli.module.seal.changed.found": "检测到变更模块：",
        "cli.module.seal.all.none": "未发现已索引模块，无需生成胶囊。",
        "cli.module.seal.all.found": "正在为全部已索引模块生成 Module Capsule：",
        "cli.module.seal.batch.updated": "已更新：",
        "cli.module.seal.batch.preview_only": "仅预览。使用 --write 更新 {path} 下的模块胶囊文件。",
        "cli.module.seal.mode_conflict": "module seal 模式互斥：<module>、--changed、--all 只能三选一。",
        "cli.module.stale.title": "模块胶囊状态：{module}",
        "cli.module.stale.status": "状态",
        "cli.module.stale.fingerprint": "指纹",
        "cli.module.stale.up_to_date": "最新",
        "cli.module.stale.stale": "过时",
        "cli.module.stale.reason": "原因",
        "cli.module.stale.suggest": "建议",
        "cli.module.stale.none_changed": "未检测到变更模块。模块胶囊已是最新。",
        "cli.module.stale.none_all": "未发现已索引模块，无需检查。",
        "cli.module.stale.changed.found": "正在检查变更模块的 Module Capsule 过时状态：",
        "cli.module.stale.all.found": "正在检查全部已索引模块的 Module Capsule 过时状态：",
        "cli.module.stale.mode_conflict": "module stale 模式互斥：<module>、--changed、--all 只能三选一。",
        "cli.module.promote_skill.generated": "已生成 Skill：",
        "cli.module.promote_skill.references": "该 Skill 是薄入口，引用以下 canonical capsule：",
        "cli.module.promote_skill.missing_capsule": "模块 {module} 的 capsule 不存在。",
        "cli.module.promote_skill.stale_capsule": "模块 {module} 的 capsule 已过时。",
        "cli.module.promote_skill.stale_hint": "请先执行：\n  harbor module seal {module} --write\n再晋升为 skill。",
        "cli.module.promote_skill.unknown_module": "未找到模块 {module} 的已索引记录。",
        "cli.module.promote_skill.unknown_module.hint": "可执行 harbor module inspect {module} 查看详情。",
        "cli.module.promote_skill.seal_hint": "请执行：\n  harbor module seal {module} --write",
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
        "cli.adopt.applied": "已应用对 {files} 个文件的变更。",
        "cli.adopt.added_config": "已将 '{path}' 注册到 code_roots。",
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

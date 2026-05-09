from __future__ import annotations

import locale
import os
import sys
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from rich.console import Console
from rich.prompt import Prompt

from harbor.core.init import Initializer
from harbor.core.init_prompt import Choice, confirm, select_one


STARTER_TEMPLATES: Dict[str, str] = {
    "AGENTS.md": "AGENTS.md",
    ".harbor/rules/role-rules.md": "harbor/rules/role-rules.md",
    ".harbor/rules/project-rules-guide.md": "harbor/rules/project-rules-guide.md",
    ".harbor/policy.yaml": "harbor/policy.yaml",
    ".harbor/safety.yaml": "harbor/safety.yaml",
}

DETAILED_TEMPLATES: Dict[str, str] = {
    ".harbor/rules/glossary.md": "harbor/rules/glossary.md",
    ".harbor/rules/agent-policy.md": "harbor/rules/agent-policy.md",
    ".harbor/rules/contract-rules.md": "harbor/rules/contract-rules.md",
    ".harbor/rules/ddt-rules.md": "harbor/rules/ddt-rules.md",
    ".harbor/rules/runtime-safety.md": "harbor/rules/runtime-safety.md",
    ".harbor/rules/diary-rules.md": "harbor/rules/diary-rules.md",
}

GITIGNORE_SECRETS_START = "# >>> HarborSpec secrets (managed)"
GITIGNORE_SECRETS_END = "# <<< HarborSpec secrets (managed)"
GITIGNORE_RUNTIME_START = "# >>> HarborSpec runtime files (managed)"
GITIGNORE_RUNTIME_END = "# <<< HarborSpec runtime files (managed)"


@dataclass
class InitWizardOptions:
    force: bool = False
    dry_run: bool = False
    language: Optional[str] = None
    project: Optional[str] = None
    governance: Optional[bool] = None
    governance_docs: Optional[bool] = None
    llm: Optional[bool] = None
    update_gitignore: Optional[bool] = None


@dataclass
class InitWizardResult:
    created: List[str] = field(default_factory=list)
    overwritten: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    language: str = "en"
    project: str = "existing"


def _is_tty() -> bool:
    return bool(sys.stdin.isatty() and sys.stdout.isatty())


def _default_language() -> str:
    env = (os.environ.get("HARBOR_LANGUAGE") or os.environ.get("HARBOR_LANG") or "").strip().lower()
    if env in ("zh", "en"):
        return env
    try:
        loc = (locale.getlocale()[0] or "").lower()
    except Exception:
        loc = ""
    if loc:
        return "zh" if loc.startswith("zh") else "en"
    try:
        enc = (locale.getencoding() or "").lower()
    except Exception:
        enc = ""
    if enc.startswith(("gbk", "gb2312", "gb18030", "big5")):
        return "zh"
    return "en"


def _default_project(stacks: List[str], roots: List[str], cwd: Path) -> str:
    if stacks and stacks != ["Python"]:
        return "existing"
    if roots and roots != ["**/*.py"]:
        return "existing"
    entries = [p for p in cwd.iterdir() if p.name not in (".git", ".harbor")]
    return "existing" if entries else "new"


def _mask_key(api_key: str) -> str:
    s = (api_key or "").strip()
    if not s:
        return ""
    if len(s) <= 8:
        return "****"
    return f"{s[:3]}-****{s[-4:]}"


def _load_template_text(template_rel: str) -> str:
    base = resources.files("harbor.templates.init").joinpath("files")
    target = base
    for part in template_rel.split("/"):
        target = target.joinpath(part)
    return target.read_text(encoding="utf-8")


def _write_file_with_policy(path: Path, content: str, *, force: bool, dry_run: bool) -> str:
    existed = path.exists()
    if existed and not force:
        return "skipped"
    if dry_run:
        return "overwritten" if existed else "created"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return "overwritten" if existed else "created"


def _read_env_keys(path: Path) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not path.exists():
        return out
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        out[key.strip()] = value.strip()
    return out


def _append_missing_env_keys(path: Path, kv: Dict[str, str], *, dry_run: bool) -> Tuple[List[str], List[str], bool]:
    existing = _read_env_keys(path)
    missing: List[str] = [k for k, v in kv.items() if v and k not in existing]
    skipped: List[str] = [k for k, v in kv.items() if not v or k in existing]
    created_file = not path.exists()
    if dry_run or not missing:
        return missing, skipped, created_file
    lines: List[str] = []
    if path.exists():
        original = path.read_text(encoding="utf-8")
        lines.append(original.rstrip("\n"))
        if original and not original.endswith("\n"):
            lines.append("")
    else:
        lines.append("# HarborSpec optional LLM config")
    for k in missing:
        lines.append(f"{k}={kv[k]}")
    content = "\n".join(lines).rstrip() + "\n"
    path.write_text(content, encoding="utf-8")
    return missing, skipped, created_file


def _update_managed_block(
    file_path: Path,
    *,
    start_marker: str,
    end_marker: str,
    lines: List[str],
    dry_run: bool,
) -> bool:
    existing = file_path.read_text(encoding="utf-8") if file_path.exists() else ""
    block = "\n".join([start_marker] + lines + [end_marker])
    if start_marker in existing and end_marker in existing:
        start = existing.index(start_marker)
        end = existing.index(end_marker, start) + len(end_marker)
        updated = existing[:start].rstrip("\n") + "\n" + block + "\n" + existing[end:].lstrip("\n")
    else:
        tail = existing.rstrip("\n")
        updated = (tail + "\n\n" if tail else "") + block + "\n"
    if updated == existing:
        return False
    if dry_run:
        return True
    file_path.write_text(updated, encoding="utf-8")
    return True


def _has_env_ignore(file_path: Path) -> bool:
    if not file_path.exists():
        return False
    for raw in file_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line in (".env", "/.env", ".env*", "*.env"):
            return True
    return False


class InitWizard:
    def __init__(
        self,
        *,
        cwd: Optional[Path] = None,
        options: Optional[InitWizardOptions] = None,
        console: Optional[Console] = None,
    ) -> None:
        self.cwd = cwd or Path.cwd()
        self.options = options or InitWizardOptions()
        self.console = console or Console()
        self.interactive = _is_tty()
        self.result = InitWizardResult()

    def _ask_language(self) -> str:
        if self.options.language in ("zh", "en"):
            return self.options.language
        if not self.interactive:
            return _default_language()
        return select_one(
            "选择工作语言 / Choose language:",
            options=[
                Choice(value="zh", label_zh="中文", label_en="Chinese", aliases=["zh", "chinese"]),
                Choice(value="en", label_zh="英文", label_en="English", aliases=["en", "english"]),
            ],
            default="zh",
            language="zh",
            console=self.console,
        )

    def _ask_project(self, stacks: List[str], roots: List[str]) -> str:
        if self.options.project in ("new", "existing"):
            return self.options.project
        default_project = _default_project(stacks, roots, self.cwd)
        if not self.interactive:
            return default_project
        return select_one(
            "你准备如何接入 HarborSpec？\n"
            "How do you want to onboard HarborSpec?",
            options=[
                Choice(
                    value="new",
                    label_zh="新项目",
                    label_en="New project",
                    aliases=["new"],
                    description_zh="从一开始使用 HarborSpec 管理 AI coding 工作流",
                    description_en="Start with HarborSpec from project day one",
                ),
                Choice(
                    value="existing",
                    label_zh="老项目",
                    label_en="Existing project",
                    aliases=["existing", "old"],
                    description_zh="在已有代码库中逐步接入 HarborSpec",
                    description_en="Adopt HarborSpec incrementally in an existing repo",
                ),
            ],
            default=default_project,
            language="zh",
            console=self.console,
        )

    def _ask_yes_no(self, prompt_text: str, default: bool) -> bool:
        return confirm(prompt_text, default=default, language=self.result.language or "en", console=self.console)

    def _emit_detected_summary(self, language: str, stacks: List[str], roots: List[str]) -> None:
        stack_text = ", ".join(stacks) if stacks else ("Python" if language == "en" else "Python")
        root_text = ", ".join(roots) if roots else "**/*.py"
        if language == "zh":
            self.console.print(f"检测到：技术栈 {stack_text}")
            self.console.print(f"默认扫描范围：{root_text}")
            self.console.print("已自动排除：缓存、虚拟环境、构建产物、.git、.harbor 等运行目录")
            self.console.print("完整配置可稍后运行：harbor config list")
            return
        self.console.print(f"Detected stack: {stack_text}")
        self.console.print(f"Default scan roots: {root_text}")
        self.console.print("Auto-excluded: cache, virtual env, build artifacts, .git, .harbor and runtime directories")
        self.console.print("See full config later with: harbor config list")

    def _emit_project_rules_guidance(self, language: str) -> None:
        if language == "zh":
            self.console.print(
                "\n项目规则（Project Rules）未自动生成。\n\n"
                "请让你的 AI coding 工具读取：\n"
                "- .harbor/rules/project-rules-guide.md\n\n"
                "建议提示词：\n"
                "\"请根据 .harbor/rules/project-rules-guide.md、当前项目结构、README、测试入口和主要代码目录，"
                "生成 .harbor/rules/project-rules.md。要求不要重复 AGENTS.md，不要覆盖 Harbor machine policy，只描述本项目专属规则。\""
            )
            return
        self.console.print(
            "\nProject Rules were not auto-generated.\n\n"
            "To create project-specific rules, ask your AI coding tool to read:\n"
            "- .harbor/rules/project-rules-guide.md\n\n"
            "Suggested prompt:\n"
            "\"Please generate .harbor/rules/project-rules.md from .harbor/rules/project-rules-guide.md, "
            "current project structure, README, test entrypoints, and core code directories. "
            "Do not duplicate AGENTS.md and do not override Harbor machine policy.\""
        )

    def _emit_ide_guidance(self, language: str) -> None:
        if language == "zh":
            self.console.print(
                "\nAI IDE 接入说明：\n"
                "- AGENTS.md：适合 AGENTS-compatible / Codex-style 工具读取\n"
                "- .harbor/rules/role-rules.md：可复制或引用到 TRAE / IDE role rules\n"
                "- Cursor：可根据 role-rules 手动创建 .cursor/rules/harbor.mdc\n"
                "- Claude Code：可根据 AGENTS.md 手动创建 CLAUDE.md\n"
                "- GitHub Copilot：可根据 AGENTS.md 手动创建 .github/copilot-instructions.md"
            )
            return
        self.console.print(
            "\nAI IDE integration guidance:\n"
            "- AGENTS.md: best for AGENTS-compatible / Codex-style tools\n"
            "- .harbor/rules/role-rules.md: copy or reference in TRAE / IDE role rules\n"
            "- Cursor: create .cursor/rules/harbor.mdc from role-rules\n"
            "- Claude Code: create CLAUDE.md from AGENTS.md\n"
            "- GitHub Copilot: create .github/copilot-instructions.md from AGENTS.md"
        )

    def _emit_next_steps(self, language: str, project: str) -> None:
        if project == "new":
            if language == "zh":
                self.console.print(
                    "\nHarborSpec 已为你的新项目准备就绪。\n\n"
                    "建议下一步：\n"
                    "1. 打开你的 AI coding 工具并让它遵循：\n"
                    "   - AGENTS.md\n"
                    "   - .harbor/rules/role-rules.md\n"
                    "2. 如需项目专属规则，请让 AI 工具生成：\n"
                    "   - .harbor/rules/project-rules.md\n"
                    "   参考：.harbor/rules/project-rules-guide.md\n"
                    "3. 开始首个 AI coding 任务：\n"
                    "   harbor start\n"
                    "4. 完成一个有意义的 AI coding 单元后：\n"
                    "   harbor finish --sync-context\n"
                    "   harbor doctor\n"
                    "5. 人工复核后再执行：\n"
                    "   harbor accept\n"
                    "当首批模块稳定后，可生成项目结构：\n"
                    "   harbor project structure --write"
                )
            else:
                self.console.print(
                    "\nHarborSpec is ready for your new project.\n\n"
                    "Next steps:\n"
                    "1. Open your AI coding tool and tell it to follow:\n"
                    "   - AGENTS.md\n"
                    "   - .harbor/rules/role-rules.md\n"
                    "2. If you need project-specific rules, ask your AI coding tool to generate:\n"
                    "   - .harbor/rules/project-rules.md\n"
                    "   Use: .harbor/rules/project-rules-guide.md\n"
                    "3. Start your first AI coding task:\n"
                    "   harbor start\n"
                    "4. After AI completes a meaningful unit of work:\n"
                    "   harbor finish --sync-context\n"
                    "   harbor doctor\n"
                    "5. After human review:\n"
                    "   harbor accept\n"
                    "When your first modules exist, you may generate project context:\n"
                    "   harbor project structure --write"
                )
            return
        if language == "zh":
            self.console.print(
                "\nHarborSpec 已准备好检查你的已有项目。\n\n"
                "建议下一步：\n"
                "1. 查看探测到的扫描根：\n"
                "   harbor config list\n"
                "2. 生成项目结构视图：\n"
                "   harbor project structure --write\n"
                "3. 运行首次 checkpoint：\n"
                "   harbor checkpoint\n"
                "4. 如果噪音太多，收窄 code_roots 或 exclude_paths。\n"
                "5. 可选逐步接管已有代码：\n"
                "   harbor adopt <path> --strategy safe --dry-run\n"
                "6. 如需项目专属规则，让 AI 工具生成：\n"
                "   .harbor/rules/project-rules.md\n"
                "   参考：.harbor/rules/project-rules-guide.md\n"
                "7. 人工复核后接受基线：\n"
                "   harbor accept"
            )
        else:
            self.console.print(
                "\nHarborSpec is ready to inspect your existing project.\n\n"
                "Recommended next steps:\n"
                "1. Review detected scan roots:\n"
                "   harbor config list\n"
                "2. Generate project structure view:\n"
                "   harbor project structure --write\n"
                "3. Run first checkpoint:\n"
                "   harbor checkpoint\n"
                "4. If there is too much noise, narrow code_roots or exclude_paths.\n"
                "5. Optionally adopt existing code gradually:\n"
                "   harbor adopt <path> --strategy safe --dry-run\n"
                "6. If you need project-specific rules, ask your AI coding tool to generate:\n"
                "   .harbor/rules/project-rules.md\n"
                "   Use: .harbor/rules/project-rules-guide.md\n"
                "7. After human review, accept the baseline:\n"
                "   harbor accept"
            )

    def run(self) -> InitWizardResult:
        init = Initializer(cwd=self.cwd)
        stacks, roots, excludes = init.autodetect()
        detect_warnings = list(init.last_warnings)

        language = self._ask_language()
        project = self._ask_project(stacks, roots)
        self.result.language = language
        self.result.project = project
        self._emit_detected_summary(language, stacks, roots)
        for warn in detect_warnings:
            if language == "zh":
                self.console.print(f"警告：{warn}")
            else:
                self.console.print(f"Warning: {warn}")

        use_detected = self._ask_yes_no("使用这些扫描范围吗？[Y/n] / Use detected scan roots?", True)
        if not use_detected and self.interactive:
            entered = Prompt.ask("输入自定义 roots（逗号分隔）/ Custom roots (comma-separated)", default=",".join(roots))
            custom = [x.strip() for x in entered.split(",") if x.strip()]
            if custom:
                roots = custom

        # write config
        config_target = init.config_path
        if self.options.dry_run:
            if config_target.exists() and not self.options.force:
                self.result.skipped.append(".harbor/config/harbor.yaml")
            else:
                self.result.created.append(".harbor/config/harbor.yaml")
        else:
            path = init.write_config(roots, force=self.options.force, exclude_paths=excludes, language=language)
            if path.exists():
                if config_target.exists() and not self.options.force:
                    # best effort; actual write_config handles this branch
                    pass
                self.result.created.append(".harbor/config/harbor.yaml")

        governance = self.options.governance if self.options.governance is not None else self._ask_yes_no(
            "是否生成 Harbor governance starter files？[Y/n]", True
        )
        if governance:
            for target_rel, source_rel in STARTER_TEMPLATES.items():
                target = self.cwd / target_rel
                action = _write_file_with_policy(
                    target,
                    _load_template_text(source_rel),
                    force=self.options.force,
                    dry_run=self.options.dry_run,
                )
                if action == "created":
                    self.result.created.append(target_rel)
                elif action == "overwritten":
                    self.result.overwritten.append(target_rel)
                else:
                    self.result.skipped.append(target_rel)
            self._emit_project_rules_guidance(language)

        governance_docs = self.options.governance_docs if self.options.governance_docs is not None else self._ask_yes_no(
            "是否生成详细 Harbor governance docs？[y/N]",
            False,
        )
        if governance_docs:
            for target_rel, source_rel in DETAILED_TEMPLATES.items():
                target = self.cwd / target_rel
                action = _write_file_with_policy(
                    target,
                    _load_template_text(source_rel),
                    force=self.options.force,
                    dry_run=self.options.dry_run,
                )
                if action == "created":
                    self.result.created.append(target_rel)
                elif action == "overwritten":
                    self.result.overwritten.append(target_rel)
                else:
                    self.result.skipped.append(target_rel)

        show_guide = self._ask_yes_no("是否输出 AI IDE 接入说明？[Y/n]", True)
        if show_guide:
            self._emit_ide_guidance(language)

        llm_enabled = self.options.llm if self.options.llm is not None else self._ask_yes_no(
            "是否配置可选 LLM semantic audit？[y/N]",
            False,
        )
        llm_kv: Dict[str, str] = {}
        if llm_enabled:
            if language == "zh":
                self.console.print("HarborSpec 核心检查不依赖 LLM。LLM 仅用于可选语义审计。")
            else:
                self.console.print("HarborSpec core checks do not require an LLM. LLM is optional for semantic audit.")
            provider = "openai"
            base_url = "https://api.openai.com/v1"
            api_key = ""
            if self.interactive:
                provider = select_one(
                    "请选择 LLM 服务商（使用 ↑/↓ 选择，Enter 确认；也可输入编号或名称）："
                    if language == "zh"
                    else "Choose LLM provider (use ↑/↓ and Enter, or type number/name):",
                    options=[
                        Choice(value="openai", label_zh="OpenAI", label_en="OpenAI", aliases=["openai"]),
                        Choice(value="deepseek", label_zh="DeepSeek", label_en="DeepSeek", aliases=["deepseek"]),
                        Choice(
                            value="custom",
                            label_zh="OpenAI-compatible 自定义 endpoint",
                            label_en="OpenAI-compatible custom endpoint",
                            aliases=["custom", "openai-compatible", "compatible"],
                        ),
                    ],
                    default="openai",
                    aliases={"1": "openai", "2": "deepseek", "3": "custom"},
                    language=language,
                    console=self.console,
                )
                if provider == "deepseek":
                    provider = "deepseek"
                    base_url = "https://api.deepseek.com/v1"
                elif provider == "custom":
                    provider = "custom"
                    base_url = Prompt.ask("HARBOR_LLM_BASE_URL")
                api_key = Prompt.ask("HARBOR_LLM_API_KEY", password=True, default="")
            else:
                provider = (os.environ.get("HARBOR_LLM_PROVIDER") or "openai").strip().lower()
                base_url = (os.environ.get("HARBOR_LLM_BASE_URL") or base_url).strip()
                api_key = (os.environ.get("HARBOR_LLM_API_KEY") or "").strip()
            llm_kv = {
                "HARBOR_LLM_PROVIDER": provider,
                "HARBOR_LLM_API_KEY": api_key,
                "HARBOR_LLM_BASE_URL": base_url,
                "HARBOR_LANGUAGE": language,
            }
            env_path = self.cwd / ".env"
            added, skipped, _ = _append_missing_env_keys(env_path, llm_kv, dry_run=self.options.dry_run)
            if added:
                self.result.notes.append(".env updated with missing HARBOR_* keys only")
            if "HARBOR_LLM_API_KEY" in added and api_key:
                self.result.notes.append(f"HARBOR_LLM_API_KEY={_mask_key(api_key)}")
            if skipped:
                self.result.notes.append(f".env skipped existing keys: {', '.join(sorted(skipped))}")
            if self.options.dry_run:
                self.result.notes.append("dry-run: .env write preview only")

        update_gitignore = self.options.update_gitignore if self.options.update_gitignore is not None else self._ask_yes_no(
            "是否更新 .gitignore 以忽略 Harbor runtime files？[Y/n]",
            True,
        )
        gitignore_path = self.cwd / ".gitignore"
        if update_gitignore and not self.options.dry_run and not gitignore_path.exists():
            gitignore_path.write_text("", encoding="utf-8")
        if update_gitignore:
            changed_runtime = _update_managed_block(
                gitignore_path,
                start_marker=GITIGNORE_RUNTIME_START,
                end_marker=GITIGNORE_RUNTIME_END,
                lines=[
                    ".harbor/cache/",
                    ".harbor/state/",
                    ".harbor/exports/",
                    ".harbor/reports/tmp/",
                    ".harbor/reports/local/",
                ],
                dry_run=self.options.dry_run,
            )
            if changed_runtime:
                self.result.notes.append("updated .gitignore runtime managed block")
            env_ignored = _has_env_ignore(gitignore_path)
            if llm_enabled and not env_ignored:
                add_env = self._ask_yes_no("`.env` 当前未在 .gitignore 中，是否追加？[Y/n]", True)
                if add_env:
                    changed_secret = _update_managed_block(
                        gitignore_path,
                        start_marker=GITIGNORE_SECRETS_START,
                        end_marker=GITIGNORE_SECRETS_END,
                        lines=[".env"],
                        dry_run=self.options.dry_run,
                    )
                    if changed_secret:
                        self.result.notes.append("updated .gitignore secrets managed block")
                else:
                    self.result.notes.append("warning: .env is not ignored by .gitignore")

        if self.options.dry_run:
            self.console.print("dry-run：未写入任何文件。" if language == "zh" else "dry-run: no files were written.")
        if self.result.created:
            self.console.print("已创建：" if language == "zh" else "Created:")
            for x in self.result.created:
                self.console.print(f"- {x}")
        if self.result.overwritten:
            self.console.print("已覆盖：" if language == "zh" else "Overwritten:")
            for x in self.result.overwritten:
                self.console.print(f"- {x}")
        if self.result.skipped:
            self.console.print("已跳过：" if language == "zh" else "Skipped:")
            for x in self.result.skipped:
                self.console.print(f"- {x}")
        for note in self.result.notes:
            self.console.print(f"- {note}")
        self._emit_next_steps(language, project)
        return self.result

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from rich.console import Console
from rich.prompt import Prompt


@dataclass
class Choice:
    value: str
    label_zh: str
    label_en: str
    aliases: List[str] = field(default_factory=list)
    description_zh: str = ""
    description_en: str = ""


def _is_interactive(interactive: Optional[bool]) -> bool:
    if interactive is not None:
        return interactive
    if os.environ.get("CI", "").strip().lower() in {"1", "true", "yes"}:
        return False
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return False
    return bool(sys.stdin.isatty() and sys.stdout.isatty())


def _choice_label(choice: Choice, language: str) -> str:
    return choice.label_zh if language == "zh" else choice.label_en


def _try_arrow_select(
    *,
    title: str,
    options: List[Choice],
    default: Optional[str],
    language: str,
) -> Optional[str]:
    try:
        from prompt_toolkit.shortcuts import radiolist_dialog
    except Exception:
        return None
    values = [(opt.value, _choice_label(opt, language)) for opt in options]
    result = radiolist_dialog(title=title, text=title, values=values, default=default or options[0].value).run()
    if isinstance(result, str) and result:
        return result
    return None


def select_one(
    title: str,
    options: List[Choice],
    default: str | None = None,
    aliases: Dict[str, str] | None = None,
    language: str = "en",
    *,
    console: Optional[Console] = None,
    interactive: Optional[bool] = None,
) -> str:
    if not options:
        raise ValueError("select_one requires at least one option")
    c = console or Console()
    merged_aliases: Dict[str, str] = {}
    for idx, opt in enumerate(options, start=1):
        merged_aliases[str(idx)] = opt.value
        merged_aliases[opt.value.lower()] = opt.value
        for alias in opt.aliases:
            merged_aliases[alias.lower()] = opt.value
    for k, v in (aliases or {}).items():
        merged_aliases[k.lower()] = v
    selected_default = default if default is not None else options[0].value
    if selected_default not in {x.value for x in options}:
        selected_default = options[0].value

    can_interactive = _is_interactive(interactive)
    if can_interactive:
        val = _try_arrow_select(title=title, options=options, default=selected_default, language=language)
        if val in {x.value for x in options}:
            return val

    c.print(title)
    for idx, opt in enumerate(options, start=1):
        label = _choice_label(opt, language)
        desc = opt.description_zh if language == "zh" else opt.description_en
        if desc:
            c.print(f"{idx}. {label} - {desc}")
        else:
            c.print(f"{idx}. {label}")

    default_idx = "1"
    for idx, opt in enumerate(options, start=1):
        if opt.value == selected_default:
            default_idx = str(idx)
            break
    valid_tip = "/".join(str(i) for i in range(1, len(options) + 1))
    while True:
        raw = Prompt.ask(">", default=default_idx).strip().lower()
        if raw in merged_aliases:
            return merged_aliases[raw]
        if language == "zh":
            c.print(f"无效输入：{raw}。可选：{valid_tip} 或名称别名。")
        else:
            c.print(f"Invalid input: {raw}. Available: {valid_tip} or option aliases.")


def confirm(
    title: str,
    default: bool = True,
    language: str = "en",
    *,
    console: Optional[Console] = None,
    interactive: Optional[bool] = None,
) -> bool:
    if not _is_interactive(interactive):
        return default
    c = console or Console()
    default_token = "Y" if default else "N"
    while True:
        raw = Prompt.ask(title, default=default_token).strip().lower()
        if raw in {"y", "yes"}:
            return True
        if raw in {"n", "no"}:
            return False
        if language == "zh":
            c.print("请输入 y 或 n。")
        else:
            c.print("Please enter y or n.")

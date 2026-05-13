from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

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


def _title_with_marker(title: str) -> str:
    title_text = title.strip()
    if title_text.startswith("◇"):
        return title_text
    return f"◇ {title_text}"


def _detect_console_encoding(console: Console) -> str:
    stream = getattr(console, "file", None)
    for candidate in (
        getattr(stream, "encoding", None),
        getattr(sys.stdout, "encoding", None),
    ):
        if isinstance(candidate, str) and candidate.strip():
            return candidate
    return "utf-8"


def _safe_console_print(console: Console, text: str) -> None:
    try:
        console.print(text)
        return
    except UnicodeEncodeError:
        pass

    encoding = _detect_console_encoding(console)
    safe_text = text.encode(encoding, errors="replace").decode(encoding, errors="replace")
    try:
        console.print(safe_text)
        return
    except UnicodeEncodeError:
        pass

    stream = getattr(console, "file", None)
    if stream is not None and hasattr(stream, "write"):
        stream.write(f"{safe_text}\n")
        flush = getattr(stream, "flush", None)
        if callable(flush):
            flush()
        return
    sys.stdout.write(f"{safe_text}\n")
    sys.stdout.flush()


def _render_inline_options(
    *,
    console: Console,
    title: str,
    options: List[Choice],
    language: str,
    selected_idx: int,
) -> None:
    _safe_console_print(console, _title_with_marker(title))
    for idx, opt in enumerate(options):
        marker = "❯" if idx == selected_idx else " "
        _safe_console_print(console, f"  {marker} {_choice_label(opt, language)}")


def _try_arrow_select(
    *,
    title: str,
    options: List[Choice],
    default: Optional[str],
    language: str,
    aliases: Dict[str, str],
    console: Console,
) -> Optional[str]:
    try:
        from prompt_toolkit.application import Application
        from prompt_toolkit.formatted_text import FormattedText
        from prompt_toolkit.key_binding import KeyBindings
        from prompt_toolkit.layout import HSplit, Layout, Window
        from prompt_toolkit.layout.controls import FormattedTextControl
    except Exception:
        return None

    values = [x.value for x in options]
    if not values:
        return None
    default_idx = values.index(default) if default in values else 0
    selected_idx = default_idx
    typed = ""
    error_msg = ""
    result: Optional[str] = None

    def _render() -> FormattedText:
        rows: List[Tuple[str, str]] = [("", _title_with_marker(title)), ("", "\n")]
        for idx, opt in enumerate(options):
            marker = "❯" if idx == selected_idx else " "
            rows.append(("", f"  {marker} {_choice_label(opt, language)}"))
            rows.append(("", "\n"))
        if language == "zh":
            hint = "↑/↓ 选择 + Enter 确认；也可直接输入别名/值后回车"
        else:
            hint = "↑/↓ + Enter; or type alias/value and press Enter"
        rows.append(("class:hint", hint))
        rows.append(("", "\n"))
        rows.append(("", f"> {typed}"))
        if error_msg:
            rows.append(("", "\n"))
            rows.append(("class:error", error_msg))
        return FormattedText(rows)

    kb = KeyBindings()

    @kb.add("up")
    def _up(event) -> None:
        nonlocal selected_idx
        selected_idx = (selected_idx - 1) % len(options)
        event.app.invalidate()

    @kb.add("down")
    def _down(event) -> None:
        nonlocal selected_idx
        selected_idx = (selected_idx + 1) % len(options)
        event.app.invalidate()

    @kb.add("c-c")
    def _ctrl_c(event) -> None:
        event.app.exit(exception=KeyboardInterrupt())

    @kb.add("enter")
    def _enter(event) -> None:
        nonlocal typed, error_msg, result
        raw = typed.strip().lower()
        if raw:
            mapped = aliases.get(raw)
            if mapped in values:
                result = mapped
                event.app.exit(result=result)
                return
            if language == "zh":
                error_msg = f"无效输入：{raw}"
            else:
                error_msg = f"Invalid input: {raw}"
            typed = ""
            event.app.invalidate()
            return
        result = options[selected_idx].value
        event.app.exit(result=result)

    @kb.add("backspace")
    def _backspace(event) -> None:
        nonlocal typed, error_msg
        if typed:
            typed = typed[:-1]
            error_msg = ""
            event.app.invalidate()

    @kb.add("escape")
    def _escape(event) -> None:
        nonlocal typed, error_msg
        typed = ""
        error_msg = ""
        event.app.invalidate()

    @kb.add("<any>")
    def _append_char(event) -> None:
        nonlocal typed, error_msg
        data = event.data or ""
        if len(data) == 1 and data.isprintable():
            typed += data
            error_msg = ""
            event.app.invalidate()

    try:
        app = Application(
            layout=Layout(HSplit([Window(content=FormattedTextControl(_render), always_hide_cursor=True)])),
            key_bindings=kb,
            full_screen=False,
            mouse_support=False,
        )
        app_result = app.run()
    except KeyboardInterrupt:
        raise
    except Exception:
        return None
    if isinstance(app_result, str) and app_result in values:
        return app_result
    if isinstance(result, str) and result in values:
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
        val = _try_arrow_select(
            title=title,
            options=options,
            default=selected_default,
            language=language,
            aliases=merged_aliases,
            console=c,
        )
        if val in {x.value for x in options}:
            return val

    _safe_console_print(c, _title_with_marker(title))
    for idx, opt in enumerate(options, start=1):
        label = _choice_label(opt, language)
        desc = opt.description_zh if language == "zh" else opt.description_en
        if desc:
            _safe_console_print(c, f"{idx}. {label} - {desc}")
        else:
            _safe_console_print(c, f"{idx}. {label}")

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
            _safe_console_print(c, f"无效输入：{raw}。可选：{valid_tip} 或名称别名。")
        else:
            _safe_console_print(c, f"Invalid input: {raw}. Available: {valid_tip} or option aliases.")


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
    selected = select_one(
        title,
        options=[
            Choice(value="yes", label_zh="是", label_en="Yes", aliases=["y", "yes", "是", "对", "true", "1"]),
            Choice(value="no", label_zh="否", label_en="No", aliases=["n", "no", "否", "错", "false", "2"]),
        ],
        default="yes" if default else "no",
        language=language,
        console=console or Console(),
        interactive=interactive,
    )
    return selected == "yes"

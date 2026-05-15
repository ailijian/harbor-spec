from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator, Optional

from rich.console import Console
from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn


def detect_console_encoding(console: Console) -> str:
    stream = getattr(console, "file", None)
    for candidate in (
        getattr(stream, "encoding", None),
        getattr(sys.stdout, "encoding", None),
    ):
        if isinstance(candidate, str) and candidate.strip():
            return candidate
    return "utf-8"


def safe_console_print(console: Console, text: object) -> None:
    rendered = str(text)
    try:
        console.print(rendered)
        return
    except UnicodeEncodeError:
        pass

    encoding = detect_console_encoding(console)
    safe_text = rendered.encode(encoding, errors="replace").decode(encoding, errors="replace")
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


def _truthy_env(value: object) -> bool:
    if not isinstance(value, str):
        return False
    normalized = value.strip().lower()
    return normalized not in ("", "0", "false", "no", "off")


def is_ci_environment(env: Optional[dict] = None) -> bool:
    source = env if env is not None else os.environ
    for key in ("CI", "GITHUB_ACTIONS", "TF_BUILD", "BUILD_BUILDID", "TEAMCITY_VERSION"):
        if _truthy_env(source.get(key)):
            return True
    return False


def should_render_progress(
    *,
    output_format: str = "text",
    ci: bool = False,
    stream: object = None,
    env: Optional[dict] = None,
    interactive: Optional[bool] = None,
) -> bool:
    if str(output_format or "text") != "text":
        return False
    if ci or is_ci_environment(env):
        return False
    if interactive is not None:
        return bool(interactive)

    target_stream = stream if stream is not None else sys.stderr
    isatty = getattr(target_stream, "isatty", None)
    if not callable(isatty):
        return False
    try:
        return bool(isatty())
    except Exception:
        return False


@dataclass
class _NoOpBatchProgress:
    def update(self, *, description: Optional[str] = None, advance: int = 0, total: Optional[int] = None) -> None:
        return None


class _RichBatchProgress:
    def __init__(self, progress: Progress, task_id: int):
        self._progress = progress
        self._task_id = task_id

    def update(self, *, description: Optional[str] = None, advance: int = 0, total: Optional[int] = None) -> None:
        kwargs = {}
        if description is not None:
            kwargs["description"] = description
        if advance:
            kwargs["advance"] = advance
        if total is not None:
            kwargs["total"] = total
        if kwargs:
            self._progress.update(self._task_id, **kwargs)


class CLIProgressReporter:
    def __init__(self, *, console: Optional[Console] = None, enabled: bool = False):
        self.console = console if console is not None else Console(stderr=True)
        self.enabled = enabled

    def phase(self, *, current: int, total: int, label: str) -> None:
        if not self.enabled:
            return
        safe_console_print(self.console, f"[progress] Phase {current}/{total}: {label}")

    @contextmanager
    def status(self, text: str, *, spinner: str = "dots") -> Iterator[None]:
        if not self.enabled:
            yield
            return
        with self.console.status(f"[bold blue]{text}", spinner=spinner):
            yield

    @contextmanager
    def batch(self, description: str, *, total: int = 0) -> Iterator[object]:
        if not self.enabled:
            yield _NoOpBatchProgress()
            return
        with Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=self.console,
            transient=True,
        ) as progress:
            task_id = progress.add_task(description, total=total)
            yield _RichBatchProgress(progress, task_id)


def build_cli_progress(
    *,
    output_format: str = "text",
    ci: bool = False,
    console: Optional[Console] = None,
    stream: object = None,
    env: Optional[dict] = None,
    interactive: Optional[bool] = None,
) -> CLIProgressReporter:
    target_console = console if console is not None else Console(stderr=True)
    enabled = should_render_progress(
        output_format=output_format,
        ci=ci,
        stream=stream if stream is not None else getattr(target_console, "file", None),
        env=env,
        interactive=interactive,
    )
    return CLIProgressReporter(console=target_console, enabled=enabled)

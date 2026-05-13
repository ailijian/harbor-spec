from __future__ import annotations

import sys

from rich.console import Console


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

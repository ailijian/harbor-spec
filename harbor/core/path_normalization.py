from __future__ import annotations

import re
from pathlib import Path
from typing import Optional


_WINDOWS_ABS_PATH_RE = re.compile(r"(?i)^[a-z]:[\\/]")


def normalize_path_separators(path_text: str | Path) -> str:
    return str(path_text or "").strip().replace("\\", "/")


def looks_like_absolute_path(path_text: str | Path) -> bool:
    normalized = normalize_path_separators(path_text)
    return bool(_WINDOWS_ABS_PATH_RE.match(normalized)) or normalized.startswith("//") or normalized.startswith("/")


def repo_relative_path(path_text: str | Path, *, repo_root: Path) -> Optional[str]:
    raw = str(path_text or "").strip()
    if not raw:
        return None

    root = repo_root.resolve()
    normalized = normalize_path_separators(raw)
    if not normalized:
        return None

    candidate = Path(raw)
    if candidate.is_absolute():
        try:
            rel = candidate.resolve().relative_to(root).as_posix()
            return rel or None
        except Exception:
            pass

    if not looks_like_absolute_path(normalized):
        return normalized.strip("/") or None

    root_text = root.as_posix().rstrip("/")
    path_text_norm = normalized.rstrip("/")
    case_sensitive = not _WINDOWS_ABS_PATH_RE.match(path_text_norm) and not path_text_norm.startswith("//")
    rel = _strip_root_prefix(path_text_norm, root_text, case_sensitive=case_sensitive)
    return rel or None


def sanitize_path_for_display(path_text: str | Path, *, repo_root: Path) -> str:
    raw = str(path_text or "").strip()
    if not raw:
        return ""
    rel = repo_relative_path(raw, repo_root=repo_root)
    if rel:
        return rel

    normalized = normalize_path_separators(raw).rstrip("/")
    if looks_like_absolute_path(normalized):
        base = Path(normalized).name or Path(normalized.rstrip("/")).name
        return base or normalized
    return normalized.strip("/")


def _strip_root_prefix(path_text: str, root_text: str, *, case_sensitive: bool) -> Optional[str]:
    normalized_path = path_text.rstrip("/")
    normalized_root = root_text.rstrip("/")
    if not normalized_root:
        return None

    path_cmp = normalized_path if case_sensitive else normalized_path.lower()
    root_cmp = normalized_root if case_sensitive else normalized_root.lower()
    if path_cmp == root_cmp:
        return ""
    prefix = root_cmp + "/"
    if not path_cmp.startswith(prefix):
        return None
    rel = normalized_path[len(normalized_root) :].lstrip("/")
    return rel or ""

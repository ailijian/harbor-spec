from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

from harbor.core.l2 import collect_all_indexed_modules, collect_modules_from_paths


_STATUS_REPORT_BUCKETS = (
    "drift",
    "modified",
    "contract_changed",
    "contract_gap",
    "skipped_no_contract",
    "contract_parse_error",
    "unsupported_syntax_advisory",
    "untracked",
    "missing",
)

_GENERATOR_INTEGRITY_FILES = {
    "harbor/core/l2.py",
    "harbor/core/module_capsule.py",
    "harbor/core/stale.py",
    "harbor/core/readonly_index.py",
    "harbor/core/context_integrity.py",
}


def collect_changed_paths_from_status(report) -> List[str]:
    changed_paths: List[str] = []
    for bucket in _STATUS_REPORT_BUCKETS:
        for entry in list(getattr(report, bucket, []) or []):
            raw_path = str(getattr(entry, "file_path", "") or "").strip()
            if raw_path:
                changed_paths.append(raw_path)
    return changed_paths


def normalize_changed_path(path: str | Path, *, repo_root: Optional[Path] = None) -> Optional[str]:
    root = (repo_root or Path.cwd()).resolve()
    raw = str(path or "").strip()
    if not raw:
        return None

    normalized = raw.replace("\\", "/")
    if re.match(r"(?i)^[a-z]:/", normalized) or normalized.startswith("//"):
        marker = f"/{root.name.lower()}/"
        lower = normalized.lower()
        idx = lower.find(marker)
        if idx == -1:
            return None
        rel = normalized[idx + len(marker) :].strip("/")
        return rel or None

    candidate = Path(normalized)
    absolute_candidate = candidate if candidate.is_absolute() else (root / candidate)
    try:
        rel = absolute_candidate.resolve().relative_to(root).as_posix()
    except Exception:
        return None
    return rel or None


def expand_modules_with_indexed_parents(
    modules: Sequence[str],
    *,
    indexed_modules: Optional[Iterable[str]] = None,
) -> List[str]:
    normalized_modules: List[str] = []
    seen = set()
    for module in modules:
        text = str(module or "").strip().replace("\\", "/").strip("/")
        if not text or text in seen:
            continue
        seen.add(text)
        normalized_modules.append(text)
    if not normalized_modules:
        return []

    indexed = indexed_modules if indexed_modules is not None else collect_all_indexed_modules()
    indexed_set = {str(module or "").strip().replace("\\", "/").strip("/") for module in indexed}
    indexed_set.discard("")
    if not indexed_set:
        return sorted(normalized_modules)

    expanded = set(normalized_modules)
    for module in normalized_modules:
        parts = [part for part in module.split("/") if part]
        for depth in range(1, len(parts)):
            parent = "/".join(parts[:depth])
            if parent in indexed_set:
                expanded.add(parent)
    return sorted(expanded)


def collect_changed_modules_from_status(
    report,
    *,
    repo_root: Optional[Path] = None,
    indexed_modules: Optional[Iterable[str]] = None,
    include_indexed_parents: bool = True,
) -> List[str]:
    normalized_paths = [
        rel
        for rel in (
            normalize_changed_path(path, repo_root=repo_root)
            for path in collect_changed_paths_from_status(report)
        )
        if rel
    ]
    modules = collect_modules_from_paths(normalized_paths)
    if include_indexed_parents:
        return expand_modules_with_indexed_parents(modules, indexed_modules=indexed_modules)
    return modules


def detect_generator_integrity_changes(
    paths: Sequence[str | Path],
    *,
    repo_root: Optional[Path] = None,
) -> List[str]:
    matched = {
        rel
        for rel in (
            normalize_changed_path(path, repo_root=repo_root)
            for path in list(paths or [])
        )
        if rel in _GENERATOR_INTEGRITY_FILES
    }
    return sorted(matched)

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from harbor.adapters.base import ContractSource, ContractSourceKind, SourceConfidence


_TAG_RE = re.compile(r"@([A-Za-z_][\w\.-]*)")
_HIGH_CONFIDENCE_TAG_PREFIXES = ("param", "returns", "return", "throws")


def extract_adjacent_tsdoc(
    source: str,
    symbol_lineno: int,
    file_path: str,
) -> Optional[ContractSource]:
    lines = source.splitlines()
    symbol_index = max(symbol_lineno - 1, 0)
    i = symbol_index - 1
    if i < 0:
        return None

    # Walk upward and allow only empty lines or comments between symbol and block comment.
    while i >= 0:
        stripped = lines[i].strip()
        if not stripped:
            i -= 1
            continue
        if stripped.startswith("//"):
            i -= 1
            continue
        if "*/" not in stripped:
            return None
        break

    if i < 0:
        return None

    end_line = i + 1
    start_idx = _find_block_comment_start(lines, i)
    if start_idx is None:
        return None
    if "/**" not in lines[start_idx]:
        return None

    start_line = start_idx + 1
    text = "\n".join(lines[start_idx:end_line]).strip()
    confidence, tags = _classify_comment(text)
    metadata: Dict[str, Any] = {
        "tags": tags,
        "tag_counts": {tag: tags.count(tag) for tag in sorted(set(tags))},
    }
    return ContractSource(
        kind=ContractSourceKind.TSDOC,
        text=text,
        confidence=confidence,
        location=f"{file_path}:{start_line}",
        metadata=metadata,
    )


def _find_block_comment_start(lines: List[str], end_index: int) -> Optional[int]:
    i = end_index
    while i >= 0:
        line = lines[i]
        if "/**" in line:
            return i
        if "/*" in line:
            return i
        i -= 1
    return None


def _classify_comment(text: str) -> tuple[SourceConfidence, List[str]]:
    tags = [tag.lower() for tag in _TAG_RE.findall(text)]
    if any(_is_high_confidence_tag(tag) for tag in tags):
        return "high", tags
    return "medium", tags


def _is_high_confidence_tag(tag: str) -> bool:
    if tag.startswith("harbor."):
        return True
    return any(tag == prefix for prefix in _HIGH_CONFIDENCE_TAG_PREFIXES)

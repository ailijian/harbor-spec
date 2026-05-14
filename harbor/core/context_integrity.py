from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from harbor import __version__ as HARBOR_VERSION
except Exception:
    try:
        from importlib.metadata import version

        HARBOR_VERSION = version("harbor-spec")
    except Exception:
        HARBOR_VERSION = "unknown"


DEFAULT_STALE_POLICY = "advisory"
DEFAULT_GENERATOR_NAME = "harbor-spec"
DEFAULT_SCHEMA_VERSION = 1
FRONTMATTER_FIELDS = [
    "generated_by",
    "harbor_version",
    "view_type",
    "module",
    "generated_at",
    "generation_command",
    "stale_policy",
    "source_path_count",
    "source_paths_truncated",
    "source_paths",
    "source_fingerprint",
    "contract_fingerprint",
    "generator_fingerprint",
    "view_fingerprint",
    "fingerprint",
]


def _normalize_rel_path(value: str) -> str:
    return str(value or "").replace("\\", "/").strip("/")


def _looks_like_windows_absolute_path(path_text: str) -> bool:
    normalized = str(path_text or "").strip().replace("\\", "/")
    return bool(normalized) and (bool(normalized[:2].endswith(":")) and normalized[2:3] == "/" or normalized.startswith("//"))


def _as_repo_relative(path_text: str, repo_root: Path) -> str:
    raw = str(path_text or "").strip()
    if not raw:
        return ""
    normalized = raw.replace("\\", "/")
    if _looks_like_windows_absolute_path(normalized):
        marker = f"/{repo_root.name.lower()}/"
        lower = normalized.lower()
        idx = lower.find(marker)
        if idx == -1:
            return ""
        return _normalize_rel_path(normalized[idx + len(marker) :])
    path_obj = Path(normalized)
    if path_obj.is_absolute():
        try:
            return path_obj.resolve().relative_to(repo_root.resolve()).as_posix()
        except Exception:
            return ""
    return _normalize_rel_path(normalized)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _json_stable_hash(payload: Any) -> str:
    stable = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(stable.encode("utf-8")).hexdigest()


def _normalized_source_content_for_fingerprint(path: Path) -> bytes:
    """Return fingerprint input bytes with cross-platform text newline normalization.

    Text source files are decoded as UTF-8 and normalized to LF-only newlines before
    hashing so generated-context integrity stays deterministic across Windows and
    Unix-style working trees. Payloads that cannot be decoded as UTF-8 remain
    byte-preserving for fingerprinting.
    """

    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return normalized.encode("utf-8")


def compute_source_fingerprint(source_paths: List[str], *, repo_root: Optional[Path] = None) -> str:
    """Compute a deterministic generated-context source fingerprint.

    Behavior:
      - Hashes repo-relative source paths in deterministic sorted order.
      - Normalizes platform line endings for UTF-8 text sources before hashing.
      - Preserves raw bytes for payloads that cannot be decoded as UTF-8.
      - Keeps the existing `missing:<rel>` fallback for missing source files.
      - Keeps the existing deterministic fallback for unreadable source files.

    Args:
      source_paths (List[str]): Source paths that contribute to generated context.
      repo_root (Optional[Path]): Repository root used to resolve relative paths.

    Returns:
      str: Stable `sha256:` fingerprint for generated-context source truth.

    Side Effects:
      - Reads source files from disk.

    Idempotency:
      - Deterministic for the same logical source content and path set across platforms.
      - Does not change the existing fallback semantics for missing or unreadable files.
    """

    root = (repo_root or Path.cwd()).resolve()
    normalized = sorted({_as_repo_relative(path, root) for path in source_paths if _as_repo_relative(path, root)})
    rows: List[Dict[str, str]] = []
    for rel in normalized:
        abs_path = (root / rel).resolve()
        if not abs_path.exists() or not abs_path.is_file():
            rows.append({"path": rel, "content": f"missing:{rel}"})
            continue
        try:
            content = _normalized_source_content_for_fingerprint(abs_path)
        except Exception:
            rows.append({"path": rel, "content": f"missing:{rel}"})
            continue
        content_sha = hashlib.sha256(content).hexdigest()
        rows.append({"path": rel, "content": content_sha})
    return _json_stable_hash(rows)


def compute_contract_fingerprint(contract_records: List[Dict[str, Any]]) -> str:
    stable_rows: List[Dict[str, Any]] = []
    for row in contract_records or []:
        if not isinstance(row, dict):
            continue
        stable_rows.append(
            {
                "symbol": str(row.get("symbol") or row.get("id") or row.get("qualified_name") or ""),
                "file": _normalize_rel_path(str(row.get("file") or "")),
                "scope": str(row.get("scope") or ""),
                "strictness": str(row.get("strictness") or ""),
            }
        )
    stable_rows = sorted(stable_rows, key=lambda item: (item["symbol"], item["file"], item["scope"], item["strictness"]))
    return _json_stable_hash(stable_rows)


def compute_generator_fingerprint(
    *,
    view_type: str,
    harbor_version: Optional[str] = None,
    generator_name: str = DEFAULT_GENERATOR_NAME,
    schema_version: int = DEFAULT_SCHEMA_VERSION,
) -> str:
    payload = {
        "view_type": str(view_type or ""),
        "harbor_version": str(harbor_version or HARBOR_VERSION),
        "generator_name": str(generator_name or DEFAULT_GENERATOR_NAME),
        "schema_version": int(schema_version),
    }
    return _json_stable_hash(payload)


def build_context_integrity_metadata(
    *,
    view_type: str,
    module: Optional[str],
    generation_command: str,
    source_paths: List[str],
    contract_records: Optional[List[Dict[str, Any]]] = None,
    repo_root: Optional[Path] = None,
    stale_policy: str = DEFAULT_STALE_POLICY,
    generator_name: str = DEFAULT_GENERATOR_NAME,
    schema_version: int = DEFAULT_SCHEMA_VERSION,
    max_source_paths: int = 120,
    include_view_fingerprint: bool = False,
) -> Dict[str, Any]:
    root = (repo_root or Path.cwd()).resolve()
    normalized = sorted({_as_repo_relative(path, root) for path in source_paths if _as_repo_relative(path, root)})
    source_path_count = len(normalized)
    shown_paths = normalized[: max(1, int(max_source_paths))]
    metadata: Dict[str, Any] = {
        "generated_by": DEFAULT_GENERATOR_NAME,
        "harbor_version": str(HARBOR_VERSION),
        "view_type": str(view_type or ""),
        "generated_at": _now_iso(),
        "generation_command": str(generation_command or ""),
        "stale_policy": str(stale_policy or DEFAULT_STALE_POLICY),
        "source_path_count": source_path_count,
        "source_paths_truncated": source_path_count > len(shown_paths),
        "source_paths": shown_paths,
        "source_fingerprint": compute_source_fingerprint(normalized, repo_root=root),
        "contract_fingerprint": compute_contract_fingerprint(contract_records or []),
        "generator_fingerprint": compute_generator_fingerprint(
            view_type=view_type,
            harbor_version=HARBOR_VERSION,
            generator_name=generator_name,
            schema_version=schema_version,
        ),
    }
    mod = _normalize_rel_path(module or "")
    if mod:
        metadata["module"] = mod
    if include_view_fingerprint:
        metadata["view_fingerprint"] = ""
    return metadata


def _yaml_quote(text: str) -> str:
    return json.dumps(str(text or ""), ensure_ascii=False)


def _render_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    return _yaml_quote(str(value))


def render_frontmatter(metadata: Dict[str, Any]) -> str:
    lines: List[str] = ["---"]
    for key in FRONTMATTER_FIELDS:
        if key not in metadata:
            continue
        value = metadata.get(key)
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {_yaml_quote(str(item))}")
            continue
        lines.append(f"{key}: {_render_scalar(value)}")
    lines.append("---")
    return "\n".join(lines)


def _decode_scalar(text: str) -> Optional[Any]:
    raw = (text or "").strip()
    if raw == "":
        return ""
    if raw in ("true", "false"):
        return raw == "true"
    if raw.isdigit() or (raw.startswith("-") and raw[1:].isdigit()):
        try:
            return int(raw)
        except Exception:
            return None
    if raw.startswith('"') and raw.endswith('"'):
        try:
            return json.loads(raw)
        except Exception:
            return None
    if raw.startswith("'") and raw.endswith("'"):
        return raw[1:-1]
    if ":" in raw:
        return None
    return raw


def parse_frontmatter(markdown: str) -> Optional[Dict[str, Any]]:
    header, _ = split_frontmatter(markdown)
    return header


def split_frontmatter(markdown: str) -> Tuple[Optional[Dict[str, Any]], str]:
    text = (markdown or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None, text

    end_idx = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break
    if end_idx < 0:
        return None, text

    payload = lines[1:end_idx]
    body = "\n".join(lines[end_idx + 1 :]).lstrip("\n")
    parsed: Dict[str, Any] = {}
    idx = 0
    while idx < len(payload):
        row = payload[idx]
        if not row.strip():
            idx += 1
            continue
        if row.startswith(" ") or row.startswith("\t"):
            return None, text
        if ":" not in row:
            return None, text
        key, value = row.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            return None, text
        if value == "":
            items: List[str] = []
            idx += 1
            while idx < len(payload):
                item_row = payload[idx]
                if not item_row.strip():
                    idx += 1
                    continue
                if not item_row.startswith("  - "):
                    break
                item_raw = item_row[4:].strip()
                item_val = _decode_scalar(item_raw)
                if not isinstance(item_val, str):
                    return None, text
                items.append(item_val)
                idx += 1
            parsed[key] = items
            continue
        scalar = _decode_scalar(value)
        if scalar is None:
            return None, text
        if isinstance(scalar, (dict, list)):
            return None, text
        parsed[key] = scalar
        idx += 1
    return parsed, body


def strip_frontmatter(markdown: str) -> str:
    _, body = split_frontmatter(markdown)
    return body


def _normalize_body_for_compare(text: str) -> str:
    lines: List[str] = []
    for raw in (text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if raw.startswith("Generated At: "):
            continue
        lines.append(raw.rstrip())
    return "\n".join(lines).strip()


def content_without_generated_at_for_compare(markdown: str) -> str:
    metadata, body = split_frontmatter(markdown)
    if metadata is None:
        return _normalize_body_for_compare(markdown)
    copied = dict(metadata)
    copied.pop("generated_at", None)
    return (render_frontmatter(copied) + "\n\n" + _normalize_body_for_compare(body)).strip()


def merge_generated_at(previous_markdown: str, new_metadata: Dict[str, Any], new_body: str) -> Dict[str, Any]:
    merged = dict(new_metadata)
    old_meta, old_body = split_frontmatter(previous_markdown)
    if not old_meta:
        return merged
    required_keys = ["source_fingerprint", "contract_fingerprint", "generator_fingerprint"]
    if any(str(old_meta.get(key) or "") != str(merged.get(key) or "") for key in required_keys):
        return merged
    if _normalize_body_for_compare(old_body) != _normalize_body_for_compare(new_body):
        return merged
    old_generated_at = str(old_meta.get("generated_at") or "").strip()
    if old_generated_at:
        merged["generated_at"] = old_generated_at
    return merged


def compose_markdown_with_frontmatter(previous_markdown: str, metadata: Dict[str, Any], body: str) -> str:
    merged = merge_generated_at(previous_markdown, metadata, body)
    fm = render_frontmatter(merged)
    return f"{fm}\n\n{body.rstrip()}\n"


def extract_integrity_fingerprints(markdown: str) -> Dict[str, str]:
    meta = parse_frontmatter(markdown) or {}
    result = {
        "source_fingerprint": str(meta.get("source_fingerprint") or "").strip(),
        "contract_fingerprint": str(meta.get("contract_fingerprint") or "").strip(),
        "generator_fingerprint": str(meta.get("generator_fingerprint") or "").strip(),
        "view_fingerprint": str(meta.get("view_fingerprint") or "").strip(),
        "fingerprint": str(meta.get("fingerprint") or "").strip(),
    }
    if not result["view_fingerprint"] and result["fingerprint"]:
        result["view_fingerprint"] = result["fingerprint"]
    return result

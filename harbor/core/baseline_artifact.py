from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:
    from harbor import __version__ as HARBOR_VERSION
except Exception:
    try:
        from importlib.metadata import version

        HARBOR_VERSION = version("harbor-spec")
    except Exception:
        try:
            init_py = Path(__file__).resolve().parents[1] / "__init__.py"
            match = re.search(
                r'__version__\s*=\s*["\']([^"\']+)["\']',
                init_py.read_text(encoding="utf-8"),
            )
            HARBOR_VERSION = match.group(1) if match else "unknown"
        except Exception:
            HARBOR_VERSION = "unknown"

ACCEPTED_CHECKPOINT_BASELINE_PATH = Path(".harbor") / "baseline" / "accepted-checkpoint.json"
CHECKPOINT_BASELINE_SCHEMA_VERSION = "1.0"
CHECKPOINT_BASELINE_KIND = "accepted_checkpoint_baseline"

_HEX_64_RE = re.compile(r"^[0-9a-f]{64}$")


class BaselineArtifactError(ValueError):
    """Base error for accepted checkpoint baseline artifact validation."""


class AcceptedBaselineMissingError(BaselineArtifactError):
    """Raised when the accepted checkpoint baseline artifact is missing."""


class AcceptedBaselineInvalidError(BaselineArtifactError):
    """Raised when the accepted checkpoint baseline artifact is invalid."""


def normalize_baseline_item_path(file_path: str, *, project_root: Optional[Path] = None) -> str:
    """Normalize one baseline item path into repo-relative POSIX format."""
    raw = str(file_path or "").strip()
    if not raw:
        raise AcceptedBaselineInvalidError("baseline item file_path must not be empty")

    normalized = raw.replace("\\", "/")
    if normalized.startswith("/"):
        raise AcceptedBaselineInvalidError("baseline item file_path must be repo-relative")
    if re.match(r"^[a-zA-Z]:/", normalized):
        root = (project_root or Path.cwd()).resolve()
        candidate = Path(normalized)
        try:
            normalized = candidate.resolve().relative_to(root).as_posix()
        except Exception as exc:
            raise AcceptedBaselineInvalidError("baseline item file_path must stay within repo root") from exc
    if normalized.startswith("../") or "/../" in normalized or normalized == "..":
        raise AcceptedBaselineInvalidError("baseline item file_path must stay within repo root")
    while "./" in normalized:
        normalized = normalized.replace("./", "")
    return normalized.strip("/")


def build_checkpoint_baseline_artifact(
    *,
    items: Iterable[Dict[str, Any]],
    accepted_at: Optional[str] = None,
    accepted_by: str = "harbor accept",
    harbor_version: Optional[str] = None,
    git_head: Optional[str] = None,
) -> Dict[str, Any]:
    """Build the accepted checkpoint baseline artifact payload."""
    normalized_items = _normalize_items(items)
    artifact: Dict[str, Any] = {
        "schema_version": CHECKPOINT_BASELINE_SCHEMA_VERSION,
        "kind": CHECKPOINT_BASELINE_KIND,
        "accepted_at": accepted_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "accepted_by": str(accepted_by or "harbor accept"),
        "harbor_version": str(harbor_version or HARBOR_VERSION or "unknown"),
        "baseline": {
            "items": normalized_items,
        },
    }
    git_head_text = str(git_head or "").strip()
    if git_head_text:
        artifact["git_head"] = git_head_text
    _validate_artifact(artifact)
    return artifact


def load_checkpoint_baseline_artifact(
    path: Optional[Path] = None,
    *,
    project_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Load and validate the accepted checkpoint baseline artifact from disk."""
    root = (project_root or Path.cwd()).resolve()
    target_path = _resolve_artifact_path(path, project_root=root)
    if not target_path.exists():
        raise AcceptedBaselineMissingError(f"accepted checkpoint baseline artifact missing: {target_path.as_posix()}")
    try:
        payload = json.loads(target_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise AcceptedBaselineInvalidError(f"failed to read baseline artifact: {target_path.as_posix()}") from exc
    _validate_artifact(payload, project_root=root)
    return payload


def write_checkpoint_baseline_artifact(
    artifact: Dict[str, Any],
    path: Optional[Path] = None,
    *,
    project_root: Optional[Path] = None,
) -> Path:
    """Validate and write the accepted checkpoint baseline artifact."""
    root = (project_root or Path.cwd()).resolve()
    _validate_artifact(artifact, project_root=root)
    target_path = _resolve_artifact_path(path, project_root=root)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target_path


def _resolve_artifact_path(path: Optional[Path], *, project_root: Path) -> Path:
    candidate = Path(path) if path is not None else ACCEPTED_CHECKPOINT_BASELINE_PATH
    if not candidate.is_absolute():
        candidate = project_root / candidate
    return candidate.resolve()


def _normalize_items(items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    seen_ids = set()
    seen_targets = set()
    for item in items:
        row = {
            "id": _require_text(item, "id"),
            "target_id": _require_text(item, "target_id"),
            "func_id": _require_text(item, "func_id"),
            "language": _require_text(item, "language").lower(),
            "symbol_kind": _require_text(item, "symbol_kind").lower(),
            "file_path": normalize_baseline_item_path(_require_text(item, "file_path")),
            "body_hash": _normalize_hash(item.get("body_hash"), field_name="body_hash"),
            "contract_hash": _normalize_hash(item.get("contract_hash"), field_name="contract_hash"),
            "contract_presence": _normalize_contract_presence(item.get("contract_presence")),
            "contract_required": _require_bool(item, "contract_required"),
        }
        if row["id"] in seen_ids:
            raise AcceptedBaselineInvalidError(f"duplicate baseline item id: {row['id']}")
        if row["target_id"] in seen_targets:
            raise AcceptedBaselineInvalidError(f"duplicate baseline item target_id: {row['target_id']}")
        seen_ids.add(row["id"])
        seen_targets.add(row["target_id"])
        normalized.append(row)
    return sorted(normalized, key=lambda item: (item["file_path"], item["target_id"], item["func_id"]))


def _validate_artifact(payload: Dict[str, Any], project_root: Optional[Path] = None) -> None:
    if not isinstance(payload, dict):
        raise AcceptedBaselineInvalidError("baseline artifact payload must be an object")
    schema_version = str(payload.get("schema_version") or "").strip()
    if schema_version != CHECKPOINT_BASELINE_SCHEMA_VERSION:
        raise AcceptedBaselineInvalidError(f"unsupported baseline artifact schema_version: {schema_version or '<empty>'}")
    kind = str(payload.get("kind") or "").strip()
    if kind != CHECKPOINT_BASELINE_KIND:
        raise AcceptedBaselineInvalidError(f"unsupported baseline artifact kind: {kind or '<empty>'}")
    if not str(payload.get("accepted_at") or "").strip():
        raise AcceptedBaselineInvalidError("baseline artifact accepted_at must not be empty")
    if not str(payload.get("accepted_by") or "").strip():
        raise AcceptedBaselineInvalidError("baseline artifact accepted_by must not be empty")
    if not str(payload.get("harbor_version") or "").strip():
        raise AcceptedBaselineInvalidError("baseline artifact harbor_version must not be empty")
    baseline = payload.get("baseline")
    if not isinstance(baseline, dict):
        raise AcceptedBaselineInvalidError("baseline artifact baseline must be an object")
    items = baseline.get("items")
    if not isinstance(items, list):
        raise AcceptedBaselineInvalidError("baseline artifact baseline.items must be a list")
    normalized = _normalize_items(items)
    if project_root is not None:
        for item in normalized:
            item["file_path"] = normalize_baseline_item_path(item["file_path"], project_root=project_root)
    payload["baseline"] = {"items": normalized}


def _require_text(item: Dict[str, Any], field_name: str) -> str:
    value = str(item.get(field_name) or "").strip()
    if not value:
        raise AcceptedBaselineInvalidError(f"baseline item {field_name} must not be empty")
    return value


def _require_bool(item: Dict[str, Any], field_name: str) -> bool:
    value = item.get(field_name)
    if not isinstance(value, bool):
        raise AcceptedBaselineInvalidError(f"baseline item {field_name} must be boolean")
    return value


def _normalize_hash(value: Any, *, field_name: str) -> str:
    text = str(value or "").strip().lower()
    if text and not _HEX_64_RE.match(text):
        raise AcceptedBaselineInvalidError(f"baseline item {field_name} must be empty or a sha256 hex digest")
    return text


def _normalize_contract_presence(value: Any) -> str:
    presence = str(value or "").strip().lower()
    allowed = {"present", "missing", "malformed", "non_contract_doc", "unsupported_syntax"}
    if presence not in allowed:
        raise AcceptedBaselineInvalidError("baseline item contract_presence is invalid")
    return presence

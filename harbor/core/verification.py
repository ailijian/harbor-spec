from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

import yaml


_WINDOWS_ABS_RE = re.compile(r"^[a-zA-Z]:[\\/]")
_WINDOWS_UNC_RE = re.compile(r"^[\\/]{2}[^\\/]+[\\/][^\\/]+")

TYPESCRIPT_DDT_PREVIEW_SCHEMA_VERSION = "1.0"
DEFAULT_TYPESCRIPT_DDT_PREVIEW_BINDINGS_FILE = ".harbor/ddt/typescript-bindings.yaml"
TYPESCRIPT_DDT_PREVIEW_STRATEGIES: Tuple[str, ...] = (
    "preview_reference",
    "preview_strict",
)


def _to_bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return default


def _looks_like_windows_absolute_path(value: Any) -> bool:
    raw = str(value or "").strip()
    if not raw:
        return False
    normalized = raw.replace("\\", "/")
    return bool(_WINDOWS_ABS_RE.match(raw)) or bool(_WINDOWS_UNC_RE.match(raw)) or normalized.startswith("//")


def normalize_repo_relative_path(value: Any, *, repo_root: Path, field_name: str) -> str:
    """Normalize one repo-local path into stable POSIX-style relative form.

    Behavior:
      - Accepts relative paths written with Windows or POSIX separators.
      - Rejects empty, absolute, or repo-escaping paths.
      - Returns a normalized repo-relative path using `/` separators.

    Args:
      value (Any): User-provided path-like value.
      repo_root (Path): Repository root used as the trust boundary.
      field_name (str): Logical field name used in error messages.

    Returns:
      str: Normalized repo-relative POSIX path.

    Raises:
      ValueError: If the path is empty, absolute, or escapes the repo root.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: deterministic
    """
    root = Path(repo_root).resolve()
    raw = str(value or "").strip()
    if not raw:
        raise ValueError(f"Invalid repo-relative path for '{field_name}': empty value is not allowed.")
    if _looks_like_windows_absolute_path(raw):
        raise ValueError(
            f"Invalid repo-relative path for '{field_name}': '{raw}' must stay repo-local."
        )

    normalized = raw.replace("\\", "/")
    candidate = Path(normalized)
    if candidate.is_absolute():
        raise ValueError(
            f"Invalid repo-relative path for '{field_name}': '{raw}' must stay repo-local."
        )

    resolved = (root / candidate).resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(
            f"Invalid repo-relative path for '{field_name}': '{raw}' escapes repo root '{root.as_posix()}'."
        ) from exc
    return relative.as_posix()


def resolve_repo_local_file(value: Any, *, repo_root: Path, field_name: str) -> Path:
    """Resolve a repo-local file path under the repository trust boundary.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: deterministic
    """
    relative = normalize_repo_relative_path(value, repo_root=repo_root, field_name=field_name)
    return (Path(repo_root).resolve() / Path(relative)).resolve()


@dataclass(frozen=True)
class VerificationTargetRef:
    target_id: Optional[str] = None
    func_id: Optional[str] = None

    def __post_init__(self) -> None:
        target_id = str(self.target_id or "").strip() or None
        func_id = str(self.func_id or "").strip() or None
        if target_id is None and func_id is None:
            raise ValueError("VerificationTargetRef requires target_id or func_id.")
        object.__setattr__(self, "target_id", target_id)
        object.__setattr__(self, "func_id", func_id)

    def primary_anchor(self) -> str:
        """Return the preferred stable anchor for verification binding identity."""
        return str(self.target_id or self.func_id or "")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize verification target identity into a stable dictionary.

        Behavior:
          - Preserves additive verification identity fields.
          - Keeps `target_id` and `func_id` layered instead of merging them into comparison hashes.

        Returns:
          Dict[str, Any]: Stable JSON-friendly verification target payload.

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: deterministic
        """
        return {
            "target_id": self.target_id,
            "func_id": self.func_id,
            "primary_anchor": self.primary_anchor(),
        }


@dataclass(frozen=True)
class VerificationTestAsset:
    path: str
    label: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize verification test asset metadata into a stable dictionary.

        Behavior:
          - Preserves normalized repo-relative path text.
          - Keeps label metadata additive and optional.

        Returns:
          Dict[str, Any]: Stable JSON-friendly verification test asset payload.

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: deterministic
        """
        return {
            "path": self.path,
            "label": self.label,
        }


@dataclass(frozen=True)
class VerificationBinding:
    binding_id: str
    language: str
    target_ref: VerificationTargetRef
    target_id: Optional[str]
    func_id: Optional[str]
    binding_kind: str
    test_asset: VerificationTestAsset
    strategy: str
    version_ref: Optional[str] = None
    status: Optional[str] = None
    reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize verification binding metadata into a stable dictionary.

        Behavior:
          - Preserves verification metadata as additive governance evidence.
          - Does not emit contract comparison hashes or public-boundary evidence fields.

        Returns:
          Dict[str, Any]: Stable JSON-friendly verification binding payload.

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: deterministic
        """
        return {
            "binding_id": self.binding_id,
            "language": self.language,
            "target_ref": self.target_ref.to_dict(),
            "target_id": self.target_id,
            "func_id": self.func_id,
            "binding_kind": self.binding_kind,
            "test_asset": self.test_asset.to_dict(),
            "strategy": self.strategy,
            "version_ref": self.version_ref,
            "status": self.status,
            "reason": self.reason,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_legacy_ddt_binding(cls, binding: object) -> "VerificationBinding":
        func_id = str(getattr(binding, "func_id", "") or "").strip() or None
        explicit_target_id = str(getattr(binding, "target_id", "") or "").strip() or None
        target_id = explicit_target_id
        if target_id is None and func_id and ":" in func_id:
            prefix = func_id.split(":", 1)[0].lower()
            if prefix in {"python", "typescript"}:
                target_id = func_id
        strategy = str(getattr(binding, "strategy", "") or "strict").strip() or "strict"
        l3_version = getattr(binding, "l3_version", None)
        test_name = str(getattr(binding, "test_name", "") or "").strip() or None
        file_path = str(getattr(binding, "file_path", "") or "").strip()
        binding_id = f"legacy-ddt:{func_id or target_id or test_name or 'binding'}:{test_name or 'unnamed'}"
        version_ref = f"l3:{int(l3_version)}" if isinstance(l3_version, int) else None
        return cls(
            binding_id=binding_id,
            language="python" if func_id and not str(func_id).startswith("typescript:") else "typescript",
            target_ref=VerificationTargetRef(target_id=target_id, func_id=func_id),
            target_id=target_id,
            func_id=func_id,
            binding_kind="ddt",
            test_asset=VerificationTestAsset(path=file_path, label=test_name),
            strategy=strategy,
            version_ref=version_ref,
            status="legacy_compatible",
            reason=None,
            metadata={
                "source": "legacy_ddt_binding",
                "l3_version": l3_version,
            },
        )


@dataclass(frozen=True)
class TypeScriptDDTPreviewConfig:
    enabled: bool = False
    bindings_file: str = DEFAULT_TYPESCRIPT_DDT_PREVIEW_BINDINGS_FILE
    require_contract_source: bool = True
    require_public_boundary: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize normalized preview config into a stable dictionary.

        Behavior:
          - Preserves additive preview config defaults.
          - Keeps preview disabled unless explicitly enabled upstream.

        Returns:
          Dict[str, Any]: Stable JSON-friendly preview config payload.

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: deterministic
        """
        return {
            "enabled": self.enabled,
            "bindings_file": self.bindings_file,
            "require_contract_source": self.require_contract_source,
            "require_public_boundary": self.require_public_boundary,
        }


@dataclass(frozen=True)
class TypeScriptDDTPreviewSidecar:
    schema_version: str
    bindings: Tuple[VerificationBinding, ...]
    source_path: Path

    def to_dict(self) -> Dict[str, Any]:
        """Serialize parsed preview sidecar data into a stable dictionary.

        Behavior:
          - Preserves frozen sidecar schema_version and normalized source path.
          - Emits parsed bindings without adding validator findings or explainability state.

        Returns:
          Dict[str, Any]: Stable JSON-friendly sidecar payload.

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: deterministic
        """
        return {
            "schema_version": self.schema_version,
            "source_path": self.source_path.as_posix(),
            "bindings": [binding.to_dict() for binding in self.bindings],
        }


def resolve_typescript_ddt_preview_config(config: Optional[Mapping[str, Any]]) -> TypeScriptDDTPreviewConfig:
    """Resolve additive TypeScript DDT preview config with safe disabled defaults.

    Behavior:
      - Reads `verification.typescript_ddt_preview`.
      - Keeps preview disabled unless explicitly enabled.
      - Leaves legacy DDT / checkpoint behavior untouched when unset.

    Args:
      config (Optional[Mapping[str, Any]]): Loaded Harbor config mapping.

    Returns:
      TypeScriptDDTPreviewConfig: Normalized preview foundation config.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: deterministic
    """
    cfg = dict(config or {})
    verification_cfg = cfg.get("verification")
    if not isinstance(verification_cfg, Mapping):
        verification_cfg = {}
    preview_cfg = verification_cfg.get("typescript_ddt_preview")
    if not isinstance(preview_cfg, Mapping):
        preview_cfg = {}
    bindings_file = str(
        preview_cfg.get("bindings_file") or DEFAULT_TYPESCRIPT_DDT_PREVIEW_BINDINGS_FILE
    ).strip() or DEFAULT_TYPESCRIPT_DDT_PREVIEW_BINDINGS_FILE
    return TypeScriptDDTPreviewConfig(
        enabled=_to_bool(preview_cfg.get("enabled"), default=False),
        bindings_file=bindings_file.replace("\\", "/"),
        require_contract_source=_to_bool(preview_cfg.get("require_contract_source"), default=True),
        require_public_boundary=_to_bool(preview_cfg.get("require_public_boundary"), default=False),
    )


def load_typescript_ddt_preview_sidecar(
    repo_root: Path,
    config: TypeScriptDDTPreviewConfig,
) -> Optional[TypeScriptDDTPreviewSidecar]:
    """Load the TypeScript DDT preview sidecar only when preview is explicitly enabled.

    Behavior:
      - Returns `None` without touching the sidecar when preview is disabled.
      - Resolves `bindings_file` within the repo boundary.
      - Parses the frozen MVP sidecar schema into `VerificationBinding` items.
      - Leaves validator findings and explainability for later phases.

    Args:
      repo_root (Path): Repository root used to resolve repo-local paths.
      config (TypeScriptDDTPreviewConfig): Normalized preview config.

    Returns:
      Optional[TypeScriptDDTPreviewSidecar]: Parsed sidecar when enabled, otherwise `None`.

    Raises:
      ValueError: If schema shape, paths, or strategy values violate the frozen foundation contract.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: read-only
    """
    if not config.enabled:
        return None

    source_path = resolve_repo_local_file(
        config.bindings_file,
        repo_root=repo_root,
        field_name="verification.typescript_ddt_preview.bindings_file",
    )
    if not source_path.exists():
        return TypeScriptDDTPreviewSidecar(
            schema_version=TYPESCRIPT_DDT_PREVIEW_SCHEMA_VERSION,
            bindings=(),
            source_path=source_path,
        )

    payload = yaml.safe_load(source_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, Mapping):
        raise ValueError("TypeScript DDT preview sidecar must be a YAML mapping.")

    allowed_top_level_keys = {"schema_version", "bindings"}
    unknown_top_level_keys = sorted(set(payload.keys()) - allowed_top_level_keys)
    if unknown_top_level_keys:
        raise ValueError(
            f"Unknown TypeScript DDT preview sidecar keys: {', '.join(unknown_top_level_keys)}"
        )

    schema_version = str(payload.get("schema_version") or "").strip()
    if schema_version != TYPESCRIPT_DDT_PREVIEW_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported TypeScript DDT preview schema_version '{schema_version}'."
        )

    raw_bindings = payload.get("bindings")
    if raw_bindings is None:
        raw_bindings = []
    if not isinstance(raw_bindings, list):
        raise ValueError("TypeScript DDT preview sidecar 'bindings' must be a list.")

    bindings: List[VerificationBinding] = []
    for index, raw_binding in enumerate(raw_bindings):
        bindings.append(
            _parse_typescript_ddt_preview_binding(
                raw_binding,
                repo_root=Path(repo_root).resolve(),
                field_prefix=f"bindings[{index}]",
            )
        )

    return TypeScriptDDTPreviewSidecar(
        schema_version=schema_version,
        bindings=tuple(bindings),
        source_path=source_path,
    )


def _parse_typescript_ddt_preview_binding(
    raw_binding: Any,
    *,
    repo_root: Path,
    field_prefix: str,
) -> VerificationBinding:
    if not isinstance(raw_binding, Mapping):
        raise ValueError(f"{field_prefix} must be a mapping.")

    allowed_binding_keys = {
        "binding_id",
        "target_id",
        "test_asset",
        "strategy",
        "contract_expectation",
        "note",
    }
    unknown_binding_keys = sorted(set(raw_binding.keys()) - allowed_binding_keys)
    if unknown_binding_keys:
        raise ValueError(
            f"{field_prefix} contains unknown keys: {', '.join(unknown_binding_keys)}"
        )

    binding_id = str(raw_binding.get("binding_id") or "").strip()
    target_id = str(raw_binding.get("target_id") or "").strip()
    strategy = str(raw_binding.get("strategy") or "").strip()
    if not binding_id:
        raise ValueError(f"{field_prefix}.binding_id is required.")
    if not target_id:
        raise ValueError(f"{field_prefix}.target_id is required.")
    if strategy not in TYPESCRIPT_DDT_PREVIEW_STRATEGIES:
        raise ValueError(
            f"{field_prefix}.strategy must be one of {', '.join(TYPESCRIPT_DDT_PREVIEW_STRATEGIES)}."
        )

    raw_test_asset = raw_binding.get("test_asset")
    if not isinstance(raw_test_asset, Mapping):
        raise ValueError(f"{field_prefix}.test_asset must be a mapping.")

    allowed_test_asset_keys = {"path", "label"}
    unknown_test_asset_keys = sorted(set(raw_test_asset.keys()) - allowed_test_asset_keys)
    if unknown_test_asset_keys:
        raise ValueError(
            f"{field_prefix}.test_asset contains unknown keys: {', '.join(unknown_test_asset_keys)}"
        )

    test_asset_path = normalize_repo_relative_path(
        raw_test_asset.get("path"),
        repo_root=repo_root,
        field_name=f"{field_prefix}.test_asset.path",
    )
    test_asset_label = str(raw_test_asset.get("label") or "").strip() or None
    contract_expectation = str(raw_binding.get("contract_expectation") or "").strip() or None
    note = str(raw_binding.get("note") or "").strip() or None

    return VerificationBinding(
        binding_id=binding_id,
        language="typescript",
        target_ref=VerificationTargetRef(target_id=target_id, func_id=None),
        target_id=target_id,
        func_id=None,
        binding_kind="ddt_preview",
        test_asset=VerificationTestAsset(path=test_asset_path, label=test_asset_label),
        strategy=strategy,
        version_ref=None,
        status="preview_declared",
        reason=None,
        metadata={
            "contract_expectation": contract_expectation,
            "note": note,
        },
    )

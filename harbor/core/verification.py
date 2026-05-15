from __future__ import annotations

from collections import Counter
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import yaml

from harbor.adapters.base import ContractSubject
from harbor.adapters.typescript.adapter import TypeScriptAdapter
from harbor.core.utils import resolve_code_roots


_WINDOWS_ABS_RE = re.compile(r"^[a-zA-Z]:[\\/]")
_WINDOWS_UNC_RE = re.compile(r"^[\\/]{2}[^\\/]+[\\/][^\\/]+")

TYPESCRIPT_DDT_PREVIEW_SCHEMA_VERSION = "1.0"
DEFAULT_TYPESCRIPT_DDT_PREVIEW_BINDINGS_FILE = ".harbor/ddt/typescript-bindings.yaml"
TYPESCRIPT_DDT_PREVIEW_STRATEGIES: Tuple[str, ...] = (
    "preview_reference",
    "preview_strict",
)
_PREVIEW_FINDING_PRIORITY: Dict[str, int] = {
    "binding_schema_invalid": 0,
    "duplicate_binding_id": 1,
    "target_not_found": 2,
    "test_asset_missing": 3,
    "contract_source_missing": 4,
    "public_boundary_unconfirmed": 5,
    "preview_valid": 6,
}
_PUBLIC_BOUNDARY_CONFIRMED_STATES = {
    "direct_export_only",
    "re_exported_surface",
    "package_export_surface",
    "configured_entrypoint_surface",
}


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


@dataclass(frozen=True)
class TypeScriptDDTPreviewFinding:
    status: str
    reason: str
    binding_id: Optional[str] = None
    target_id: Optional[str] = None
    test_asset_path: Optional[str] = None
    test_asset_label: Optional[str] = None
    target_file_path: Optional[str] = None
    language: str = "typescript"
    symbol_kind: Optional[str] = None
    adapter: str = "typescript"
    bindings_file: Optional[str] = None
    contract_source_kinds: Optional[Tuple[str, ...]] = None
    source_confidence_summary: Optional[str] = None
    public_boundary_state: Optional[str] = None
    public_boundary_confidence: Optional[str] = None
    public_boundary_evidence_kinds: Optional[Tuple[str, ...]] = None
    public_boundary_reason: Optional[str] = None
    boundary_preset_mode: Optional[str] = None
    preview: bool = True
    advisory: bool = True
    blocking: bool = False

    def dedupe_key(self) -> Tuple[str, str, str, str, str]:
        return (
            str(self.status or "").strip(),
            str(self.binding_id or "").strip(),
            str(self.target_id or "").strip(),
            str(self.test_asset_path or "").strip(),
            str(self.reason or "").strip(),
        )

    def sort_key(self) -> Tuple[int, str, str, str, str]:
        return (
            _PREVIEW_FINDING_PRIORITY.get(str(self.status or ""), 99),
            str(self.binding_id or "").strip(),
            str(self.target_id or "").strip(),
            str(self.test_asset_path or "").strip(),
            str(self.reason or "").strip(),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize one TypeScript DDT preview finding into a stable dictionary.

        Behavior:
          - Emits stable preview-only, advisory-first metadata.
          - Mirrors `status` into `category` for compatibility with existing `harbor next` consumers.
          - Keeps preview findings outside checkpoint blocking semantics.

        Returns:
          Dict[str, Any]: Stable JSON-friendly preview finding payload.

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: deterministic
        """
        payload: Dict[str, Any] = {
            "status": self.status,
            "category": self.status,
            "reason": self.reason,
            "language": self.language,
            "adapter": self.adapter,
            "preview": self.preview,
            "advisory": self.advisory,
            "blocking": self.blocking,
        }
        if self.binding_id:
            payload["binding_id"] = self.binding_id
        if self.target_id:
            payload["target_id"] = self.target_id
        if self.test_asset_path:
            payload["test_asset_path"] = self.test_asset_path
        if self.test_asset_label:
            payload["test_asset_label"] = self.test_asset_label
        if self.target_file_path:
            payload["target_file_path"] = self.target_file_path
        if self.symbol_kind:
            payload["symbol_kind"] = self.symbol_kind
        if self.bindings_file:
            payload["bindings_file"] = self.bindings_file
        if self.contract_source_kinds:
            payload["contract_source_kinds"] = list(self.contract_source_kinds)
        if self.source_confidence_summary:
            payload["source_confidence_summary"] = self.source_confidence_summary
        if self.public_boundary_state:
            payload["public_boundary_state"] = self.public_boundary_state
        if self.public_boundary_confidence:
            payload["public_boundary_confidence"] = self.public_boundary_confidence
        if self.public_boundary_evidence_kinds:
            payload["public_boundary_evidence_kinds"] = list(self.public_boundary_evidence_kinds)
        if self.public_boundary_reason:
            payload["public_boundary_reason"] = self.public_boundary_reason
        if self.boundary_preset_mode:
            payload["boundary_preset_mode"] = self.boundary_preset_mode
        return payload


@dataclass(frozen=True)
class TypeScriptDDTPreviewReport:
    bindings_file: str
    bindings_count: int
    valid_count: int
    advisory_count: int
    findings: Tuple[TypeScriptDDTPreviewFinding, ...]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the preview validator report into a stable dictionary.

        Behavior:
          - Emits additive preview-only summary and finding details.
          - Keeps preview report separate from `ci_failures` and checkpoint exit semantics.

        Returns:
          Dict[str, Any]: Stable JSON-friendly preview report payload.

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: deterministic
        """
        return {
            "bindings_file": self.bindings_file,
            "bindings_count": self.bindings_count,
            "valid_count": self.valid_count,
            "advisory_count": self.advisory_count,
            "findings": [finding.to_dict() for finding in self.findings],
        }

    def to_summary_dict(self) -> Dict[str, Any]:
        """Serialize the lightweight preview summary without full finding rows.

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: deterministic
        """
        return {
            "bindings_file": self.bindings_file,
            "bindings_count": self.bindings_count,
            "valid_count": self.valid_count,
            "advisory_count": self.advisory_count,
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


def validate_typescript_ddt_preview(
    repo_root: Path,
    config: Optional[Mapping[str, Any]] = None,
) -> Optional[TypeScriptDDTPreviewReport]:
    """Validate TypeScript DDT preview bindings in advisory-only mode.

    Behavior:
      - Returns `None` when preview is disabled.
      - Reads the frozen sidecar schema and validates structure, references, and minimal semantics.
      - Emits deterministic, deduped, non-blocking findings.
      - Never changes checkpoint `ci_failures`, exit code, or baseline adjudication semantics.

    Args:
      repo_root (Path): Repository root.
      config (Optional[Mapping[str, Any]]): Workspace config mapping.

    Returns:
      Optional[TypeScriptDDTPreviewReport]: Preview validator report when enabled, otherwise `None`.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: read-only
    """
    preview_config = resolve_typescript_ddt_preview_config(config)
    if not preview_config.enabled:
        return None

    try:
        bindings_file = normalize_repo_relative_path(
            preview_config.bindings_file,
            repo_root=repo_root,
            field_name="verification.typescript_ddt_preview.bindings_file",
        )
    except ValueError as exc:
        return _build_typescript_ddt_preview_report(
            bindings_file=str(preview_config.bindings_file or DEFAULT_TYPESCRIPT_DDT_PREVIEW_BINDINGS_FILE),
            bindings_count=0,
            findings=[
                _preview_finding(
                    status="binding_schema_invalid",
                    reason=str(exc),
                    bindings_file=str(preview_config.bindings_file or DEFAULT_TYPESCRIPT_DDT_PREVIEW_BINDINGS_FILE),
                )
            ],
        )

    source_path = (Path(repo_root).resolve() / bindings_file).resolve()
    if not source_path.exists():
        return _build_typescript_ddt_preview_report(bindings_file=bindings_file, bindings_count=0, findings=[])

    try:
        payload = yaml.safe_load(source_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        return _build_typescript_ddt_preview_report(
            bindings_file=bindings_file,
            bindings_count=0,
            findings=[
                _preview_finding(
                    status="binding_schema_invalid",
                    reason=f"Failed to parse TypeScript DDT preview sidecar YAML: {str(exc)}",
                    bindings_file=bindings_file,
                )
            ],
        )

    if not isinstance(payload, Mapping):
        return _build_typescript_ddt_preview_report(
            bindings_file=bindings_file,
            bindings_count=0,
            findings=[
                _preview_finding(
                    status="binding_schema_invalid",
                    reason="TypeScript DDT preview sidecar must be a YAML mapping.",
                    bindings_file=bindings_file,
                )
            ],
        )

    allowed_top_level_keys = {"schema_version", "bindings"}
    unknown_top_level_keys = sorted(set(payload.keys()) - allowed_top_level_keys)
    if unknown_top_level_keys:
        return _build_typescript_ddt_preview_report(
            bindings_file=bindings_file,
            bindings_count=0,
            findings=[
                _preview_finding(
                    status="binding_schema_invalid",
                    reason=(
                        "Unknown TypeScript DDT preview sidecar keys: "
                        + ", ".join(unknown_top_level_keys)
                    ),
                    bindings_file=bindings_file,
                )
            ],
        )

    schema_version = str(payload.get("schema_version") or "").strip()
    if schema_version != TYPESCRIPT_DDT_PREVIEW_SCHEMA_VERSION:
        return _build_typescript_ddt_preview_report(
            bindings_file=bindings_file,
            bindings_count=0,
            findings=[
                _preview_finding(
                    status="binding_schema_invalid",
                    reason=f"Unsupported TypeScript DDT preview schema_version '{schema_version}'.",
                    bindings_file=bindings_file,
                )
            ],
        )

    raw_bindings = payload.get("bindings")
    if raw_bindings is None:
        raw_bindings = []
    if not isinstance(raw_bindings, list):
        return _build_typescript_ddt_preview_report(
            bindings_file=bindings_file,
            bindings_count=0,
            findings=[
                _preview_finding(
                    status="binding_schema_invalid",
                    reason="TypeScript DDT preview sidecar 'bindings' must be a list.",
                    bindings_file=bindings_file,
                )
            ],
        )

    parsed_bindings: List[VerificationBinding] = []
    findings: List[TypeScriptDDTPreviewFinding] = []
    for index, raw_binding in enumerate(raw_bindings):
        parsed, binding_findings = _parse_preview_binding_for_validation(
            raw_binding,
            repo_root=Path(repo_root).resolve(),
            field_prefix=f"bindings[{index}]",
            bindings_file=bindings_file,
        )
        findings.extend(binding_findings)
        if parsed is not None:
            parsed_bindings.append(parsed)

    duplicate_ids = {
        binding_id
        for binding_id, count in Counter(binding.binding_id for binding in parsed_bindings).items()
        if count > 1
    }
    subjects_by_target = _collect_typescript_preview_subjects(
        repo_root=Path(repo_root).resolve(),
        config=config,
    )

    for binding in parsed_bindings:
        if binding.binding_id in duplicate_ids:
            findings.append(
                _preview_finding(
                    status="duplicate_binding_id",
                    reason=f"Duplicate TypeScript DDT preview binding_id '{binding.binding_id}' was declared.",
                    binding=binding,
                    bindings_file=bindings_file,
                )
            )
            continue

        subject = subjects_by_target.get(str(binding.target_id or ""))
        binding_findings = _validate_preview_binding_against_subject(
            binding=binding,
            subject=subject,
            repo_root=Path(repo_root).resolve(),
            preview_config=preview_config,
            bindings_file=bindings_file,
        )
        findings.extend(binding_findings)

    return _build_typescript_ddt_preview_report(
        bindings_file=bindings_file,
        bindings_count=len(raw_bindings),
        findings=findings,
    )


def _parse_preview_binding_for_validation(
    raw_binding: Any,
    *,
    repo_root: Path,
    field_prefix: str,
    bindings_file: str,
) -> Tuple[Optional[VerificationBinding], List[TypeScriptDDTPreviewFinding]]:
    findings: List[TypeScriptDDTPreviewFinding] = []
    if not isinstance(raw_binding, Mapping):
        findings.append(
            _preview_finding(
                status="binding_schema_invalid",
                reason=f"{field_prefix} must be a mapping.",
                bindings_file=bindings_file,
            )
        )
        return None, findings

    binding_id = str(raw_binding.get("binding_id") or "").strip() or None
    target_id = str(raw_binding.get("target_id") or "").strip() or None

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
        findings.append(
            _preview_finding(
                status="binding_schema_invalid",
                reason=f"{field_prefix} contains unknown keys: {', '.join(unknown_binding_keys)}",
                binding_id=binding_id,
                target_id=target_id,
                bindings_file=bindings_file,
            )
        )
        return None, findings

    if not binding_id:
        findings.append(
            _preview_finding(
                status="binding_schema_invalid",
                reason=f"{field_prefix}.binding_id is required.",
                target_id=target_id,
                bindings_file=bindings_file,
            )
        )
        return None, findings
    if not target_id:
        findings.append(
            _preview_finding(
                status="binding_schema_invalid",
                reason=f"{field_prefix}.target_id is required.",
                binding_id=binding_id,
                bindings_file=bindings_file,
            )
        )
        return None, findings

    strategy = str(raw_binding.get("strategy") or "").strip()
    if strategy not in TYPESCRIPT_DDT_PREVIEW_STRATEGIES:
        findings.append(
            _preview_finding(
                status="binding_schema_invalid",
                reason=(
                    f"{field_prefix}.strategy must be one of "
                    f"{', '.join(TYPESCRIPT_DDT_PREVIEW_STRATEGIES)}."
                ),
                binding_id=binding_id,
                target_id=target_id,
                bindings_file=bindings_file,
            )
        )
        return None, findings

    raw_test_asset = raw_binding.get("test_asset")
    if not isinstance(raw_test_asset, Mapping):
        findings.append(
            _preview_finding(
                status="binding_schema_invalid",
                reason=f"{field_prefix}.test_asset must be a mapping.",
                binding_id=binding_id,
                target_id=target_id,
                bindings_file=bindings_file,
            )
        )
        return None, findings

    allowed_test_asset_keys = {"path", "label"}
    unknown_test_asset_keys = sorted(set(raw_test_asset.keys()) - allowed_test_asset_keys)
    if unknown_test_asset_keys:
        findings.append(
            _preview_finding(
                status="binding_schema_invalid",
                reason=(
                    f"{field_prefix}.test_asset contains unknown keys: "
                    f"{', '.join(unknown_test_asset_keys)}"
                ),
                binding_id=binding_id,
                target_id=target_id,
                bindings_file=bindings_file,
            )
        )
        return None, findings

    try:
        test_asset_path = normalize_repo_relative_path(
            raw_test_asset.get("path"),
            repo_root=repo_root,
            field_name=f"{field_prefix}.test_asset.path",
        )
    except ValueError as exc:
        findings.append(
            _preview_finding(
                status="binding_schema_invalid",
                reason=str(exc),
                binding_id=binding_id,
                target_id=target_id,
                bindings_file=bindings_file,
            )
        )
        return None, findings

    test_asset_label = str(raw_test_asset.get("label") or "").strip() or None
    contract_expectation = str(raw_binding.get("contract_expectation") or "").strip() or None
    note = str(raw_binding.get("note") or "").strip() or None
    return (
        VerificationBinding(
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
        ),
        findings,
    )


def _collect_typescript_preview_subjects(
    *,
    repo_root: Path,
    config: Optional[Mapping[str, Any]],
) -> Dict[str, ContractSubject]:
    cfg = dict(config or {})
    code_roots = list(cfg.get("code_roots") or ["harbor/**"])
    languages_cfg = cfg.get("languages")
    if not isinstance(languages_cfg, Mapping):
        languages_cfg = {}
    typescript_cfg = languages_cfg.get("typescript")
    if not isinstance(typescript_cfg, Mapping):
        typescript_cfg = {}
    adapter = TypeScriptAdapter(config=typescript_cfg)
    subjects: Dict[str, ContractSubject] = {}
    for path in adapter.discover_files(resolve_code_roots(code_roots, repo_root=repo_root)):
        try:
            parsed = adapter.parse_file(path)
        except Exception:
            continue
        for subject in parsed:
            target_id = str(getattr(subject, "target_id", "") or "").strip()
            if target_id:
                subjects[target_id] = subject
                relative_target_id = _make_repo_relative_target_id(subject, repo_root=repo_root)
                if relative_target_id:
                    subjects[relative_target_id] = subject
    return subjects


def _validate_preview_binding_against_subject(
    *,
    binding: VerificationBinding,
    subject: Optional[ContractSubject],
    repo_root: Path,
    preview_config: TypeScriptDDTPreviewConfig,
    bindings_file: str,
) -> List[TypeScriptDDTPreviewFinding]:
    if subject is None or str(getattr(subject, "language", "") or "").strip().lower() != "typescript":
        return [
            _preview_finding(
                status="target_not_found",
                reason=f"TypeScript target '{binding.target_id}' was not found in the current workspace scan.",
                binding=binding,
                bindings_file=bindings_file,
            )
        ]

    findings: List[TypeScriptDDTPreviewFinding] = []
    test_asset_path = (repo_root / binding.test_asset.path).resolve()
    common_kwargs = _subject_preview_metadata(subject, repo_root=repo_root)
    if not test_asset_path.exists():
        findings.append(
            _preview_finding(
                status="test_asset_missing",
                reason=f"Preview test asset '{binding.test_asset.path}' does not exist.",
                binding=binding,
                bindings_file=bindings_file,
                **common_kwargs,
            )
        )

    contract_presence = str(getattr(subject, "contract_presence", "") or "").strip().lower()
    if preview_config.require_contract_source and contract_presence != "present":
        findings.append(
            _preview_finding(
                status="contract_source_missing",
                reason="Required TypeScript contract source is missing or not contract-like for preview validation.",
                binding=binding,
                bindings_file=bindings_file,
                **common_kwargs,
            )
        )

    public_boundary_state = str(getattr(subject, "metadata", {}).get("public_boundary_state", "") or "").strip()
    if preview_config.require_public_boundary and public_boundary_state not in _PUBLIC_BOUNDARY_CONFIRMED_STATES:
        findings.append(
            _preview_finding(
                status="public_boundary_unconfirmed",
                reason="TypeScript public boundary is not confirmed strongly enough for preview validation.",
                binding=binding,
                bindings_file=bindings_file,
                **common_kwargs,
            )
        )

    if findings:
        return findings

    return [
        _preview_finding(
            status="preview_valid",
            reason="TypeScript DDT preview binding is declared, resolved, and currently advisory-valid.",
            binding=binding,
            bindings_file=bindings_file,
            **common_kwargs,
        )
    ]


def _subject_preview_metadata(subject: ContractSubject, *, repo_root: Path) -> Dict[str, Any]:
    metadata = dict(getattr(subject, "metadata", {}) or {})
    target_file_path = str(getattr(subject, "file_path", "") or "").strip() or None
    if target_file_path:
        try:
            target_file_path = Path(target_file_path).resolve().relative_to(repo_root).as_posix()
        except Exception:
            target_file_path = Path(target_file_path).name or target_file_path
    return {
        "target_file_path": target_file_path,
        "symbol_kind": str(getattr(subject, "symbol_kind", "") or "").strip() or None,
        "contract_source_kinds": tuple(
            str(getattr(getattr(source, "kind", None), "value", getattr(source, "kind", "")) or "").strip().lower()
            for source in list(getattr(subject, "contract_sources", ()) or ())
            if str(getattr(getattr(source, "kind", None), "value", getattr(source, "kind", "")) or "").strip()
        )
        or None,
        "source_confidence_summary": _strongest_contract_confidence(subject),
        "public_boundary_state": str(metadata.get("public_boundary_state") or "").strip() or None,
        "public_boundary_confidence": str(metadata.get("public_boundary_confidence") or "").strip() or None,
        "public_boundary_evidence_kinds": tuple(
            str(value or "").strip()
            for value in list(metadata.get("public_boundary_evidence_kinds") or [])
            if str(value or "").strip()
        )
        or None,
        "public_boundary_reason": str(metadata.get("public_boundary_reason") or "").strip() or None,
        "boundary_preset_mode": str(metadata.get("boundary_preset_mode") or "").strip() or None,
    }


def _strongest_contract_confidence(subject: ContractSubject) -> Optional[str]:
    priorities = {"high": 3, "medium": 2, "low": 1}
    strongest: Optional[str] = None
    best = 0
    for source in list(getattr(subject, "contract_sources", ()) or ()):
        confidence = str(getattr(source, "confidence", "") or "").strip().lower()
        score = priorities.get(confidence, 0)
        if score > best:
            strongest = confidence
            best = score
    return strongest


def _make_repo_relative_target_id(subject: ContractSubject, *, repo_root: Path) -> Optional[str]:
    file_path = str(getattr(subject, "file_path", "") or "").strip()
    symbol_kind = str(getattr(subject, "symbol_kind", "") or "").strip()
    qualified_name = str(getattr(subject, "qualified_name", "") or "").strip()
    language = str(getattr(subject, "language", "") or "").strip()
    if not all((file_path, symbol_kind, qualified_name, language)):
        return None
    try:
        relative_path = Path(file_path).resolve().relative_to(repo_root).as_posix()
    except Exception:
        return None
    return ContractSubject.make_target_id(
        language=language,
        file_path=relative_path,
        symbol_kind=symbol_kind,
        qualified_name=qualified_name,
    )


def _preview_finding(
    *,
    status: str,
    reason: str,
    binding: Optional[VerificationBinding] = None,
    binding_id: Optional[str] = None,
    target_id: Optional[str] = None,
    bindings_file: Optional[str] = None,
    **kwargs: Any,
) -> TypeScriptDDTPreviewFinding:
    effective_binding_id = str(binding_id or getattr(binding, "binding_id", "") or "").strip() or None
    effective_target_id = str(target_id or getattr(binding, "target_id", "") or "").strip() or None
    test_asset = getattr(binding, "test_asset", None)
    test_asset_path = str(getattr(test_asset, "path", "") or "").strip() or None
    test_asset_label = str(getattr(test_asset, "label", "") or "").strip() or None
    return TypeScriptDDTPreviewFinding(
        status=status,
        reason=str(reason or "").strip(),
        binding_id=effective_binding_id,
        target_id=effective_target_id,
        test_asset_path=test_asset_path,
        test_asset_label=test_asset_label,
        bindings_file=str(bindings_file or "").strip() or None,
        **kwargs,
    )


def _dedupe_preview_findings(
    findings: Iterable[TypeScriptDDTPreviewFinding],
) -> Tuple[TypeScriptDDTPreviewFinding, ...]:
    selected: Dict[Tuple[str, str, str, str, str], TypeScriptDDTPreviewFinding] = {}
    passthrough: List[TypeScriptDDTPreviewFinding] = []
    for finding in findings:
        key = finding.dedupe_key()
        if not any(key):
            passthrough.append(finding)
            continue
        prev = selected.get(key)
        if prev is None or finding.sort_key() < prev.sort_key():
            selected[key] = finding
    merged = passthrough + list(selected.values())
    return tuple(sorted(merged, key=lambda item: item.sort_key()))


def _build_typescript_ddt_preview_report(
    *,
    bindings_file: str,
    bindings_count: int,
    findings: Sequence[TypeScriptDDTPreviewFinding],
) -> TypeScriptDDTPreviewReport:
    deduped = _dedupe_preview_findings(findings)
    valid_count = sum(1 for item in deduped if item.status == "preview_valid")
    advisory_count = sum(1 for item in deduped if item.status != "preview_valid")
    return TypeScriptDDTPreviewReport(
        bindings_file=bindings_file,
        bindings_count=int(bindings_count),
        valid_count=valid_count,
        advisory_count=advisory_count,
        findings=deduped,
    )

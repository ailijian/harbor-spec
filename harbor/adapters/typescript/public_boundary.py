from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Iterable, List, Literal, Mapping, Optional, Sequence, Tuple


PublicBoundaryConfidence = Literal["high", "medium", "low"]


class PublicBoundaryEvidenceKind(str, Enum):
    DIRECT_EXPORT = "direct_export"
    DEFAULT_EXPORT = "default_export"
    NAMED_RE_EXPORT = "named_re_export"
    STAR_RE_EXPORT = "star_re_export"
    PACKAGE_EXPORT = "package_export"
    CONFIGURED_ENTRYPOINT = "configured_entrypoint"
    DECLARATION_SURFACE_PREVIEW = "declaration_surface_preview"


class PublicBoundaryState(str, Enum):
    DIRECT_EXPORT_ONLY = "direct_export_only"
    RE_EXPORTED_SURFACE = "re_exported_surface"
    PACKAGE_EXPORT_SURFACE = "package_export_surface"
    CONFIGURED_ENTRYPOINT_SURFACE = "configured_entrypoint_surface"
    DECLARATION_SURFACE_PREVIEW = "declaration_surface_preview"
    INTERNAL_OR_UNCONFIRMED = "internal_or_unconfirmed"
    UNKNOWN = "unknown"


PUBLIC_BOUNDARY_PRESET_MODES = {
    "legacy_exported",
    "package_public",
    "custom_entrypoints",
}

CONTRACT_REQUIRED_STRATEGIES = {
    "legacy_exported",
    "confirmed_boundary_advisory",
    "confirmed_boundary_policy_preview",
}


@dataclass(frozen=True)
class PublicBoundaryEvidence:
    kind: PublicBoundaryEvidenceKind
    confidence: PublicBoundaryConfidence = "low"
    source_file: Optional[str] = None
    source_ref: Optional[str] = None
    resolved_target: Optional[str] = None
    reason: Optional[str] = None

    def sort_key(self) -> Tuple[str, int, str, str, str, str]:
        return (
            self.kind.value,
            _confidence_sort_key(self.confidence),
            str(self.source_file or ""),
            str(self.source_ref or ""),
            str(self.resolved_target or ""),
            str(self.reason or ""),
        )

    def dedupe_key(self) -> Tuple[str, str, str, str]:
        return (
            self.kind.value,
            str(self.source_file or ""),
            str(self.source_ref or ""),
            str(self.resolved_target or ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize one public-boundary evidence item into stable JSON metadata.

        Behavior:
          - Returns a JSON-compatible mapping for additive explainability output.
          - Preserves stable keys:
            `kind`, `confidence`, `source_file`, `source_ref`, `resolved_target`, `reason`.
          - Keeps public-boundary evidence separate from contract-source semantics.

        Returns:
          Dict[str, Any]: Deterministic JSON-ready evidence payload.

        Side Effects:
          - Writes no files.

        Idempotency:
          - Deterministic for the same evidence item.

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: deterministic
        """
        return {
            "kind": self.kind.value,
            "confidence": self.confidence,
            "source_file": self.source_file,
            "source_ref": self.source_ref,
            "resolved_target": self.resolved_target,
            "reason": self.reason,
        }


def normalize_public_boundary_evidence_items(
    items: Iterable[PublicBoundaryEvidence | Mapping[str, Any]],
) -> Tuple[PublicBoundaryEvidence, ...]:
    normalized: List[PublicBoundaryEvidence] = []
    for item in list(items or ()):
        evidence = _coerce_public_boundary_evidence(item)
        if evidence is not None:
            normalized.append(evidence)
    selected: Dict[Tuple[str, str, str, str], PublicBoundaryEvidence] = {}
    for evidence in sorted(normalized, key=lambda value: value.sort_key()):
        key = evidence.dedupe_key()
        if key not in selected:
            selected[key] = evidence
    return tuple(sorted(selected.values(), key=lambda value: value.sort_key()))


def build_public_boundary_metadata(
    *,
    evidence_items: Iterable[PublicBoundaryEvidence | Mapping[str, Any]],
    preset_mode: str,
    is_exported: bool,
) -> Dict[str, Any]:
    normalized_items = normalize_public_boundary_evidence_items(evidence_items)
    kinds = _boundary_evidence_kinds(normalized_items)
    state = _resolve_boundary_state(normalized_items, is_exported=is_exported)
    confidence = _resolve_boundary_confidence(normalized_items)
    reason = _resolve_boundary_reason(
        normalized_items=normalized_items,
        state=state,
        is_exported=is_exported,
    )
    return {
        "public_boundary_state": state,
        "public_boundary_confidence": confidence,
        "public_boundary_evidence_kinds": kinds,
        "public_boundary_evidence_items": [item.to_dict() for item in normalized_items],
        "public_boundary_reason": reason,
        "boundary_preset_mode": normalize_public_boundary_preset_mode(preset_mode),
    }


def initial_public_boundary_evidence_for_symbol(
    *,
    is_exported: bool,
    export_mode: str,
    source_file: str,
    source_ref: str,
    resolved_target: str,
) -> Tuple[PublicBoundaryEvidence, ...]:
    if not is_exported:
        return ()
    kind = (
        PublicBoundaryEvidenceKind.DEFAULT_EXPORT
        if str(export_mode or "").strip().lower() == "default"
        else PublicBoundaryEvidenceKind.DIRECT_EXPORT
    )
    reason = (
        "Target is exported as the default symbol from its declaring source file."
        if kind == PublicBoundaryEvidenceKind.DEFAULT_EXPORT
        else "Target is exported directly from its declaring source file."
    )
    return normalize_public_boundary_evidence_items(
        [
            PublicBoundaryEvidence(
                kind=kind,
                confidence="low",
                source_file=source_file,
                source_ref=source_ref,
                resolved_target=resolved_target,
                reason=reason,
            )
        ]
    )


def normalize_typescript_governance_config(config: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    cfg = dict(config or {})
    public_boundary = cfg.get("public_boundary")
    if not isinstance(public_boundary, Mapping):
        public_boundary = {}

    raw_entrypoints = public_boundary.get("entrypoints")
    if isinstance(raw_entrypoints, Sequence) and not isinstance(raw_entrypoints, (str, bytes)):
        entrypoints = [str(value).strip() for value in raw_entrypoints if str(value or "").strip()]
    else:
        entrypoints = []

    raw_source_mappings = public_boundary.get("source_mappings")
    source_mappings: Dict[str, str] = {}
    if isinstance(raw_source_mappings, Mapping):
        for key, value in raw_source_mappings.items():
            key_text = str(key or "").strip()
            value_text = str(value or "").strip()
            if key_text and value_text:
                source_mappings[key_text] = value_text

    return {
        "public_boundary": {
            "mode": normalize_public_boundary_preset_mode(public_boundary.get("mode")),
            "follow_re_exports": _to_bool(public_boundary.get("follow_re_exports"), default=True),
            "read_package_exports": _to_bool(public_boundary.get("read_package_exports"), default=True),
            "use_tsconfig_paths": _to_bool(public_boundary.get("use_tsconfig_paths"), default=True),
            "declaration_surface_preview": _to_bool(
                public_boundary.get("declaration_surface_preview"),
                default=False,
            ),
            "entrypoints": entrypoints,
            "source_mappings": source_mappings,
        },
        "contract_required_strategy": normalize_contract_required_strategy(
            cfg.get("contract_required_strategy")
        ),
    }


def normalize_public_boundary_preset_mode(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in PUBLIC_BOUNDARY_PRESET_MODES:
        return text
    return "legacy_exported"


def normalize_contract_required_strategy(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in CONTRACT_REQUIRED_STRATEGIES:
        return text
    return "legacy_exported"


def _coerce_public_boundary_evidence(
    item: PublicBoundaryEvidence | Mapping[str, Any],
) -> Optional[PublicBoundaryEvidence]:
    if isinstance(item, PublicBoundaryEvidence):
        return item
    if not isinstance(item, Mapping):
        return None
    raw_kind = str(item.get("kind") or "").strip()
    if not raw_kind:
        return None
    try:
        kind = PublicBoundaryEvidenceKind(raw_kind)
    except ValueError:
        return None
    confidence = _normalize_boundary_confidence(item.get("confidence"))
    return PublicBoundaryEvidence(
        kind=kind,
        confidence=confidence,
        source_file=_optional_text(item.get("source_file")),
        source_ref=_optional_text(item.get("source_ref")),
        resolved_target=_optional_text(item.get("resolved_target")),
        reason=_optional_text(item.get("reason")),
    )


def _boundary_evidence_kinds(items: Sequence[PublicBoundaryEvidence]) -> List[str]:
    seen = set()
    values: List[str] = []
    for item in items:
        kind = item.kind.value
        if kind in seen:
            continue
        seen.add(kind)
        values.append(kind)
    return values


def _resolve_boundary_state(
    items: Sequence[PublicBoundaryEvidence],
    *,
    is_exported: bool,
) -> str:
    kinds = {item.kind for item in items}
    if PublicBoundaryEvidenceKind.CONFIGURED_ENTRYPOINT in kinds:
        return PublicBoundaryState.CONFIGURED_ENTRYPOINT_SURFACE.value
    if PublicBoundaryEvidenceKind.PACKAGE_EXPORT in kinds:
        return PublicBoundaryState.PACKAGE_EXPORT_SURFACE.value
    if (
        PublicBoundaryEvidenceKind.NAMED_RE_EXPORT in kinds
        or PublicBoundaryEvidenceKind.STAR_RE_EXPORT in kinds
    ):
        return PublicBoundaryState.RE_EXPORTED_SURFACE.value
    if PublicBoundaryEvidenceKind.DECLARATION_SURFACE_PREVIEW in kinds:
        return PublicBoundaryState.DECLARATION_SURFACE_PREVIEW.value
    if (
        PublicBoundaryEvidenceKind.DIRECT_EXPORT in kinds
        or PublicBoundaryEvidenceKind.DEFAULT_EXPORT in kinds
    ):
        return PublicBoundaryState.DIRECT_EXPORT_ONLY.value
    if not is_exported:
        return PublicBoundaryState.INTERNAL_OR_UNCONFIRMED.value
    return PublicBoundaryState.UNKNOWN.value


def _resolve_boundary_confidence(
    items: Sequence[PublicBoundaryEvidence],
) -> Optional[PublicBoundaryConfidence]:
    best: Optional[PublicBoundaryConfidence] = None
    best_score = 0
    for item in items:
        score = _confidence_score(item.confidence)
        if score > best_score:
            best = item.confidence
            best_score = score
    return best


def _resolve_boundary_reason(
    *,
    normalized_items: Sequence[PublicBoundaryEvidence],
    state: str,
    is_exported: bool,
) -> str:
    if normalized_items:
        preferred_kinds = _preferred_reason_kinds(state)
        preferred = _select_preferred_reason_item(normalized_items, preferred_kinds)
        if preferred and preferred.reason:
            return preferred.reason
        first = _select_preferred_reason_item(normalized_items, None)
        if first and first.reason:
            return first.reason
        if state == PublicBoundaryState.DIRECT_EXPORT_ONLY.value:
            return "Target has direct export evidence only; broader public boundary is not yet confirmed."
        if state == PublicBoundaryState.RE_EXPORTED_SURFACE.value:
            return "Target has re-export evidence and may participate in a broader public surface."
        if state == PublicBoundaryState.PACKAGE_EXPORT_SURFACE.value:
            return "Target is confirmed by package export evidence."
        if state == PublicBoundaryState.CONFIGURED_ENTRYPOINT_SURFACE.value:
            return "Target is confirmed by configured entrypoint evidence."
        if state == PublicBoundaryState.DECLARATION_SURFACE_PREVIEW.value:
            return "Target only has declaration surface preview evidence."
    if not is_exported:
        return "Target is internal or has no confirmed public boundary evidence."
    return "No confirmed public boundary evidence is available beyond legacy exported semantics."


def _preferred_reason_kinds(state: str) -> Optional[Tuple[PublicBoundaryEvidenceKind, ...]]:
    if state == PublicBoundaryState.CONFIGURED_ENTRYPOINT_SURFACE.value:
        return (PublicBoundaryEvidenceKind.CONFIGURED_ENTRYPOINT,)
    if state == PublicBoundaryState.PACKAGE_EXPORT_SURFACE.value:
        return (PublicBoundaryEvidenceKind.PACKAGE_EXPORT,)
    if state == PublicBoundaryState.RE_EXPORTED_SURFACE.value:
        return (
            PublicBoundaryEvidenceKind.NAMED_RE_EXPORT,
            PublicBoundaryEvidenceKind.STAR_RE_EXPORT,
        )
    if state == PublicBoundaryState.DECLARATION_SURFACE_PREVIEW.value:
        return (PublicBoundaryEvidenceKind.DECLARATION_SURFACE_PREVIEW,)
    if state == PublicBoundaryState.DIRECT_EXPORT_ONLY.value:
        return (
            PublicBoundaryEvidenceKind.DEFAULT_EXPORT,
            PublicBoundaryEvidenceKind.DIRECT_EXPORT,
        )
    return None


def _select_preferred_reason_item(
    items: Sequence[PublicBoundaryEvidence],
    preferred_kinds: Optional[Tuple[PublicBoundaryEvidenceKind, ...]],
) -> Optional[PublicBoundaryEvidence]:
    candidates = list(items)
    if preferred_kinds is not None:
        candidates = [item for item in candidates if item.kind in preferred_kinds]
    if not candidates:
        return None
    ordered = sorted(
        candidates,
        key=lambda item: (
            -_confidence_score(item.confidence),
            item.kind.value,
            str(item.source_file or ""),
            str(item.source_ref or ""),
            str(item.resolved_target or ""),
        ),
    )
    return ordered[0]


def _normalize_boundary_confidence(value: Any) -> PublicBoundaryConfidence:
    text = str(value or "").strip().lower()
    if text == "high":
        return "high"
    if text == "medium":
        return "medium"
    return "low"


def _confidence_sort_key(value: PublicBoundaryConfidence) -> int:
    return -_confidence_score(value)


def _confidence_score(value: PublicBoundaryConfidence) -> int:
    if value == "high":
        return 3
    if value == "medium":
        return 2
    return 1


def _to_bool(value: Any, *, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return default


def _optional_text(value: Any) -> Optional[str]:
    text = str(value or "").strip()
    return text or None

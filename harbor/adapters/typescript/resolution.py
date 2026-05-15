from __future__ import annotations

import json
import re
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Set, Tuple

from harbor.adapters.typescript.public_boundary import (
    PublicBoundaryEvidence,
    PublicBoundaryEvidenceKind,
    normalize_public_boundary_evidence_items,
)
from harbor.adapters.typescript.symbols import TypeScriptSymbol

_EXCLUDED_DIRS = {
    "node_modules",
    "dist",
    "build",
    "coverage",
    ".next",
    ".nuxt",
    "out",
    ".vite",
    ".turbo",
    "storybook-static",
}

_NAMED_RE_EXPORT_RE = re.compile(
    r"export\s*\{(?P<specifiers>[^}]*)\}\s*from\s*[\"'](?P<module>[^\"']+)[\"']",
    re.MULTILINE,
)
_STAR_RE_EXPORT_RE = re.compile(
    r"export\s*\*\s*from\s*[\"'](?P<module>[^\"']+)[\"']",
    re.MULTILINE,
)
_JS_LIKE_SUFFIXES = {".js", ".mjs", ".cjs"}
_PACKAGE_EXPORT_PREFERENCE = ("source", "types", "import", "default", "require", "node")


@dataclass(frozen=True)
class ReExportRule:
    source_file: str
    target_file: str
    imported_name: str
    exported_name: str
    module_specifier: str
    source_ref: str
    lineno: int
    evidence_kind: PublicBoundaryEvidenceKind

    def propagate(self, name: str) -> Optional[str]:
        if self.evidence_kind == PublicBoundaryEvidenceKind.STAR_RE_EXPORT:
            if name == "default":
                return None
            return name
        if self.imported_name != name:
            return None
        return self.exported_name


@dataclass(frozen=True)
class PackageExportEntry:
    export_key: str
    raw_target: str
    source_file: Optional[str]


@dataclass
class PackageContext:
    package_root: Path
    package_json_path: Optional[Path]
    tsconfig_base_dir: Optional[Path]
    tsconfig_paths: Dict[str, List[str]]
    re_export_rules_by_target: Dict[str, Tuple[ReExportRule, ...]]
    package_exports: Tuple[PackageExportEntry, ...]


class TypeScriptBoundaryResolver:
    def __init__(self, config: Optional[Mapping[str, object]] = None) -> None:
        self._config = dict(config or {})

    def collect_evidence(
        self,
        *,
        file_path: str,
        symbol: TypeScriptSymbol,
        target_id: str,
    ) -> Tuple[PublicBoundaryEvidence, ...]:
        initial_names = _initial_export_names(symbol)
        if not initial_names:
            return ()

        context = self._context_for(Path(file_path))
        origin = Path(file_path).resolve().as_posix()
        reachable = {origin: set(initial_names)}
        evidence: List[PublicBoundaryEvidence] = []

        if bool(self._config.get("follow_re_exports", True)):
            re_export_evidence, reachable = self._trace_re_export_chain(
                context=context,
                origin=origin,
                initial_names=initial_names,
                target_id=target_id,
            )
            evidence.extend(re_export_evidence)

        evidence.extend(
            self._configured_entrypoint_evidence(
                context=context,
                reachable=reachable,
                target_id=target_id,
            )
        )

        if bool(self._config.get("read_package_exports", True)):
            evidence.extend(
                self._package_export_evidence(
                    context=context,
                    reachable=reachable,
                    target_id=target_id,
                )
            )

        return normalize_public_boundary_evidence_items(evidence)

    def _context_for(self, file_path: Path) -> PackageContext:
        package_root = _find_package_root(file_path)

        tsconfig_base_dir, tsconfig_paths = _load_tsconfig_paths(package_root)
        rules = self._build_re_export_rules(
            package_root=package_root,
            tsconfig_base_dir=tsconfig_base_dir,
            tsconfig_paths=tsconfig_paths,
        )
        package_json_path = package_root / "package.json"
        package_exports = _load_package_exports(
            package_root=package_root,
            package_json_path=package_json_path if package_json_path.exists() else None,
            source_mappings=self._config.get("source_mappings") or {},
        )
        return PackageContext(
            package_root=package_root,
            package_json_path=package_json_path if package_json_path.exists() else None,
            tsconfig_base_dir=tsconfig_base_dir,
            tsconfig_paths=tsconfig_paths,
            re_export_rules_by_target=rules,
            package_exports=package_exports,
        )

    def _build_re_export_rules(
        self,
        *,
        package_root: Path,
        tsconfig_base_dir: Optional[Path],
        tsconfig_paths: Mapping[str, Sequence[str]],
    ) -> Dict[str, Tuple[ReExportRule, ...]]:
        by_target: Dict[str, List[ReExportRule]] = {}
        for source_file in _iter_project_typescript_files(package_root):
            try:
                content = source_file.read_text(encoding="utf-8")
            except OSError:
                continue

            rules: List[ReExportRule] = []
            for match in _NAMED_RE_EXPORT_RE.finditer(content):
                module_specifier = str(match.group("module") or "").strip()
                resolved = _resolve_module_specifier(
                    module_specifier,
                    from_file=source_file,
                    package_root=package_root,
                    use_tsconfig_paths=bool(self._config.get("use_tsconfig_paths", True)),
                    tsconfig_base_dir=tsconfig_base_dir,
                    tsconfig_paths=tsconfig_paths,
                )
                if resolved is None:
                    continue
                specifiers_text = str(match.group("specifiers") or "")
                line_no = _to_lineno(content, match.start())
                for specifier in _split_named_specifiers(specifiers_text):
                    imported_name, exported_name = _parse_named_specifier(specifier)
                    if not imported_name or not exported_name:
                        continue
                    source_ref = (
                        imported_name
                        if imported_name == exported_name
                        else f"{imported_name} as {exported_name}"
                    )
                    rules.append(
                        ReExportRule(
                            source_file=source_file.resolve().as_posix(),
                            target_file=resolved,
                            imported_name=imported_name,
                            exported_name=exported_name,
                            module_specifier=module_specifier,
                            source_ref=source_ref,
                            lineno=line_no,
                            evidence_kind=PublicBoundaryEvidenceKind.NAMED_RE_EXPORT,
                        )
                    )
            for match in _STAR_RE_EXPORT_RE.finditer(content):
                module_specifier = str(match.group("module") or "").strip()
                resolved = _resolve_module_specifier(
                    module_specifier,
                    from_file=source_file,
                    package_root=package_root,
                    use_tsconfig_paths=bool(self._config.get("use_tsconfig_paths", True)),
                    tsconfig_base_dir=tsconfig_base_dir,
                    tsconfig_paths=tsconfig_paths,
                )
                if resolved is None:
                    continue
                rules.append(
                    ReExportRule(
                        source_file=source_file.resolve().as_posix(),
                        target_file=resolved,
                        imported_name="*",
                        exported_name="*",
                        module_specifier=module_specifier,
                        source_ref="*",
                        lineno=_to_lineno(content, match.start()),
                        evidence_kind=PublicBoundaryEvidenceKind.STAR_RE_EXPORT,
                    )
                )
            for rule in rules:
                by_target.setdefault(rule.target_file, []).append(rule)

        return {
            key: tuple(sorted(value, key=lambda item: (item.source_file, item.lineno, item.source_ref)))
            for key, value in by_target.items()
        }

    def _trace_re_export_chain(
        self,
        *,
        context: PackageContext,
        origin: str,
        initial_names: Set[str],
        target_id: str,
    ) -> Tuple[Tuple[PublicBoundaryEvidence, ...], Dict[str, Set[str]]]:
        evidence: List[PublicBoundaryEvidence] = []
        reachable: Dict[str, Set[str]] = {origin: set(initial_names)}
        queue: deque[Tuple[str, str]] = deque(
            (origin, name) for name in sorted(initial_names)
        )

        while queue:
            current_file, current_name = queue.popleft()
            for rule in context.re_export_rules_by_target.get(current_file, ()):
                propagated_name = rule.propagate(current_name)
                if not propagated_name:
                    continue
                evidence.append(
                    PublicBoundaryEvidence(
                        kind=rule.evidence_kind,
                        confidence="medium",
                        source_file=rule.source_file,
                        source_ref=rule.source_ref,
                        resolved_target=target_id,
                        reason=_build_re_export_reason(rule),
                    )
                )
                exported_names = reachable.setdefault(rule.source_file, set())
                if propagated_name not in exported_names:
                    exported_names.add(propagated_name)
                    queue.append((rule.source_file, propagated_name))

        return normalize_public_boundary_evidence_items(evidence), reachable

    def _configured_entrypoint_evidence(
        self,
        *,
        context: PackageContext,
        reachable: Mapping[str, Set[str]],
        target_id: str,
    ) -> Tuple[PublicBoundaryEvidence, ...]:
        evidence: List[PublicBoundaryEvidence] = []
        for entrypoint in list(self._config.get("entrypoints") or []):
            resolved = _resolve_entrypoint_path(str(entrypoint), package_root=context.package_root)
            if resolved is None:
                continue
            exported_names = reachable.get(resolved)
            if not exported_names:
                continue
            evidence.append(
                PublicBoundaryEvidence(
                    kind=PublicBoundaryEvidenceKind.CONFIGURED_ENTRYPOINT,
                    confidence="medium",
                    source_file=resolved,
                    source_ref=str(entrypoint),
                    resolved_target=target_id,
                    reason=(
                        f"Target is reachable from configured entrypoint '{entrypoint}'."
                    ),
                )
            )
        return normalize_public_boundary_evidence_items(evidence)

    def _package_export_evidence(
        self,
        *,
        context: PackageContext,
        reachable: Mapping[str, Set[str]],
        target_id: str,
    ) -> Tuple[PublicBoundaryEvidence, ...]:
        if context.package_json_path is None:
            return ()
        evidence: List[PublicBoundaryEvidence] = []
        for export_entry in context.package_exports:
            if not export_entry.source_file:
                continue
            exported_names = reachable.get(export_entry.source_file)
            if not exported_names:
                continue
            reason = (
                f"Package export '{export_entry.export_key}' maps to '{export_entry.raw_target}' "
                f"and resolves to a source entrypoint that exposes this target."
            )
            evidence.append(
                PublicBoundaryEvidence(
                    kind=PublicBoundaryEvidenceKind.PACKAGE_EXPORT,
                    confidence="high",
                    source_file=context.package_json_path.as_posix(),
                    source_ref=export_entry.export_key,
                    resolved_target=target_id,
                    reason=reason,
                )
            )
        return normalize_public_boundary_evidence_items(evidence)


def _find_package_root(file_path: Path) -> Path:
    start = file_path.resolve()
    first_tsconfig_parent: Optional[Path] = None
    fallback_root: Optional[Path] = None
    for parent in (start.parent, *start.parents):
        if (parent / "package.json").exists():
            return parent
        if first_tsconfig_parent is None and (parent / "tsconfig.json").exists():
            first_tsconfig_parent = parent
        if fallback_root is None and ((parent / ".harbor").exists() or (parent / "src").exists()):
            fallback_root = parent
        if parent.name.lower() in {"src", "lib"}:
            fallback_root = parent.parent if parent.parent != parent else parent
    return first_tsconfig_parent or fallback_root or start.parent


def _iter_project_typescript_files(package_root: Path) -> List[Path]:
    files: List[Path] = []
    for path in package_root.rglob("*.ts"):
        if path.name.endswith(".d.ts"):
            continue
        if any(part in _EXCLUDED_DIRS for part in path.parts):
            continue
        files.append(path.resolve())
    return sorted(files)


def _load_tsconfig_paths(package_root: Path) -> Tuple[Optional[Path], Dict[str, List[str]]]:
    tsconfig_path = _find_first_parent_file(package_root, "tsconfig.json")
    if tsconfig_path is None:
        candidate = package_root / "tsconfig.json"
        tsconfig_path = candidate if candidate.exists() else None
    if tsconfig_path is None:
        return None, {}
    try:
        payload = json.loads(tsconfig_path.read_text(encoding="utf-8"))
    except Exception:
        return None, {}
    compiler_options = payload.get("compilerOptions") if isinstance(payload, dict) else {}
    if not isinstance(compiler_options, dict):
        compiler_options = {}
    base_url = str(compiler_options.get("baseUrl") or ".").strip() or "."
    raw_paths = compiler_options.get("paths")
    path_map: Dict[str, List[str]] = {}
    if isinstance(raw_paths, dict):
        for key, value in raw_paths.items():
            key_text = str(key or "").strip()
            if not key_text:
                continue
            values: List[str] = []
            if isinstance(value, list):
                values = [str(item).strip() for item in value if str(item or "").strip()]
            elif isinstance(value, str) and value.strip():
                values = [value.strip()]
            if values:
                path_map[key_text] = values
    return (tsconfig_path.parent / base_url).resolve(), path_map


def _find_first_parent_file(start: Path, filename: str) -> Optional[Path]:
    for parent in (start, *start.parents):
        candidate = parent / filename
        if candidate.exists():
            return candidate
    return None


def _resolve_module_specifier(
    module_specifier: str,
    *,
    from_file: Path,
    package_root: Path,
    use_tsconfig_paths: bool,
    tsconfig_base_dir: Optional[Path],
    tsconfig_paths: Mapping[str, Sequence[str]],
) -> Optional[str]:
    specifier = str(module_specifier or "").strip()
    if not specifier:
        return None

    candidates: List[Path] = []
    if specifier.startswith("."):
        candidates.extend(_module_candidates(from_file.parent / specifier))
    else:
        if use_tsconfig_paths and tsconfig_base_dir is not None:
            candidates.extend(
                _tsconfig_path_candidates(
                    specifier,
                    base_dir=tsconfig_base_dir,
                    tsconfig_paths=tsconfig_paths,
                )
            )
        if not candidates:
            candidates.extend(_module_candidates(package_root / specifier))

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate.resolve().as_posix()
    return None


def _module_candidates(base: Path) -> List[Path]:
    base = base.resolve()
    candidates: List[Path] = []
    if base.suffix == ".ts":
        candidates.append(base)
    elif base.suffix in _JS_LIKE_SUFFIXES:
        candidates.append(base.with_suffix(".ts"))
    elif base.suffix:
        candidates.append(base)
        candidates.append(base.with_suffix(".ts"))
    else:
        candidates.append(base.with_suffix(".ts"))
        candidates.append((base / "index.ts").resolve())
    return _dedupe_paths(candidates)


def _tsconfig_path_candidates(
    specifier: str,
    *,
    base_dir: Path,
    tsconfig_paths: Mapping[str, Sequence[str]],
) -> List[Path]:
    resolved: List[Path] = []
    for pattern, replacements in tsconfig_paths.items():
        wildcard_value = _extract_wildcard(pattern, specifier)
        if wildcard_value is None:
            continue
        for replacement in replacements:
            mapped = replacement.replace("*", wildcard_value) if "*" in replacement else replacement
            resolved.extend(_module_candidates((base_dir / mapped).resolve()))
    return _dedupe_paths(resolved)


def _extract_wildcard(pattern: str, value: str) -> Optional[str]:
    if "*" not in pattern:
        return "" if pattern == value else None
    prefix, suffix = pattern.split("*", 1)
    if not value.startswith(prefix):
        return None
    if suffix and not value.endswith(suffix):
        return None
    return value[len(prefix) : len(value) - len(suffix) if suffix else len(value)]


def _split_named_specifiers(raw: str) -> List[str]:
    return [chunk.strip() for chunk in str(raw or "").replace("\n", " ").split(",") if chunk.strip()]


def _parse_named_specifier(specifier: str) -> Tuple[str, str]:
    parts = [part.strip() for part in str(specifier or "").split(" as ")]
    if len(parts) == 1:
        name = parts[0]
        return name, name
    if len(parts) == 2:
        return parts[0], parts[1]
    return "", ""


def _build_re_export_reason(rule: ReExportRule) -> str:
    file_name = Path(rule.source_file).name
    if rule.evidence_kind == PublicBoundaryEvidenceKind.STAR_RE_EXPORT:
        return (
            f"Target is re-exported via export * from '{file_name}' "
            f"using module '{rule.module_specifier}'."
        )
    if rule.imported_name == "default":
        return (
            f"Target default export is re-exported from '{file_name}' as '{rule.exported_name}'."
        )
    if rule.imported_name != rule.exported_name:
        return (
            f"Target is re-exported from '{file_name}' as '{rule.exported_name}' "
            f"via local name '{rule.imported_name}'."
        )
    return f"Target is re-exported from '{file_name}' as '{rule.exported_name}'."


def _load_package_exports(
    *,
    package_root: Path,
    package_json_path: Optional[Path],
    source_mappings: Mapping[str, object],
) -> Tuple[PackageExportEntry, ...]:
    if package_json_path is None:
        return ()
    try:
        payload = json.loads(package_json_path.read_text(encoding="utf-8"))
    except Exception:
        return ()
    exports_block = payload.get("exports") if isinstance(payload, dict) else None
    normalized = _normalize_exports_block(exports_block)
    results: List[PackageExportEntry] = []
    for export_key, raw_target in normalized:
        resolved_source = _map_package_export_to_source(
            raw_target,
            package_root=package_root,
            source_mappings=source_mappings,
        )
        results.append(
            PackageExportEntry(
                export_key=export_key,
                raw_target=raw_target,
                source_file=resolved_source,
            )
        )
    return tuple(results)


def _normalize_exports_block(exports_block: object) -> List[Tuple[str, str]]:
    if isinstance(exports_block, str) and exports_block.strip():
        return [(".", exports_block.strip())]
    if not isinstance(exports_block, dict):
        return []
    results: List[Tuple[str, str]] = []
    for key, value in exports_block.items():
        key_text = str(key or "").strip() or "."
        resolved = _coerce_export_target(value)
        if resolved:
            results.append((key_text, resolved))
    return results


def _coerce_export_target(value: object) -> Optional[str]:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if not isinstance(value, dict):
        return None
    for key in _PACKAGE_EXPORT_PREFERENCE:
        nested = value.get(key)
        if isinstance(nested, str) and nested.strip():
            return nested.strip()
    for nested in value.values():
        if isinstance(nested, str) and nested.strip():
            return nested.strip()
    return None


def _map_package_export_to_source(
    raw_target: str,
    *,
    package_root: Path,
    source_mappings: Mapping[str, object],
) -> Optional[str]:
    target_text = str(raw_target or "").strip()
    if not target_text:
        return None
    mapping = _match_source_mapping(target_text, source_mappings)
    mapped_target = mapping or _default_source_mapping(target_text)
    if mapped_target is None:
        mapped_target = target_text
    for candidate in _module_candidates(package_root / mapped_target.lstrip("./")):
        if candidate.exists() and candidate.is_file():
            return candidate.resolve().as_posix()
    return None


def _match_source_mapping(raw_target: str, source_mappings: Mapping[str, object]) -> Optional[str]:
    normalized_target = raw_target.replace("\\", "/").strip()
    comparable_keys = {
        normalized_target,
        normalized_target.lstrip("./"),
    }
    for key, value in source_mappings.items():
        key_text = str(key or "").replace("\\", "/").strip()
        if key_text not in comparable_keys and key_text.lstrip("./") not in comparable_keys:
            continue
        value_text = str(value or "").strip()
        if value_text:
            return value_text
    return None


def _default_source_mapping(raw_target: str) -> Optional[str]:
    normalized = raw_target.replace("\\", "/").strip()
    trimmed = normalized.lstrip("./")
    if not trimmed:
        return None
    candidate = trimmed
    if candidate.startswith("dist/"):
        candidate = "src/" + candidate[len("dist/") :]
    elif "/dist/" in candidate:
        candidate = candidate.replace("/dist/", "/src/", 1)
    if Path(candidate).suffix in _JS_LIKE_SUFFIXES:
        candidate = str(Path(candidate).with_suffix(".ts")).replace("\\", "/")
    return candidate


def _resolve_entrypoint_path(entrypoint: str, *, package_root: Path) -> Optional[str]:
    value = str(entrypoint or "").strip()
    if not value:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = package_root / value
    for candidate in _module_candidates(path):
        if candidate.exists() and candidate.is_file():
            return candidate.resolve().as_posix()
    return None


def _initial_export_names(symbol: TypeScriptSymbol) -> Set[str]:
    if not symbol.is_exported:
        return set()
    if str(symbol.export_mode or "").strip().lower() == "default":
        return {"default"}
    if symbol.symbol_kind == "method" and symbol.class_name:
        return {symbol.class_name}
    return {str(symbol.name or "").strip()} if str(symbol.name or "").strip() else set()


def _dedupe_paths(paths: Sequence[Path]) -> List[Path]:
    seen: Set[str] = set()
    ordered: List[Path] = []
    for path in paths:
        key = path.resolve().as_posix()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(path.resolve())
    return ordered


def _to_lineno(source: str, offset: int) -> int:
    return source.count("\n", 0, offset) + 1

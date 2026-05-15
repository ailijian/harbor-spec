from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple, Union

from harbor.adapters.base import ContractSource, ContractSourceKind, ContractSubject
from harbor.adapters.typescript.jsdoc import extract_adjacent_tsdoc
from harbor.adapters.typescript.hashing import normalized_sha256
from harbor.adapters.typescript.parser import TypeScriptLightweightParser
from harbor.adapters.typescript.public_boundary import (
    build_public_boundary_metadata,
    initial_public_boundary_evidence_for_symbol,
    normalize_typescript_governance_config,
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


def _to_posix_path(path: Union[str, Path]) -> str:
    if isinstance(path, Path):
        return path.as_posix()
    return path.strip().replace("\\", "/")


class TypeScriptAdapter:
    language = "typescript"

    def __init__(self, config: Mapping[str, Any] | None = None) -> None:
        governance = normalize_typescript_governance_config(config)
        self._typescript_config = dict(config or {})
        self._public_boundary_config = dict(governance["public_boundary"])
        self._contract_required_strategy = str(governance["contract_required_strategy"])

    def discover_files(self, roots: Sequence[Path]) -> List[Path]:
        discovered: Dict[str, Path] = {}
        for root in roots:
            if root.is_file():
                self._collect_file(root, discovered)
                continue
            if not root.exists():
                continue
            for path in root.rglob("*.ts"):
                self._collect_file(path, discovered)
        return [discovered[key] for key in sorted(discovered.keys())]

    def parse_file(self, path: Union[str, Path]) -> List[ContractSubject]:
        file_path = Path(path)
        source = file_path.read_text(encoding="utf-8")
        parser = TypeScriptLightweightParser()
        symbols = parser.parse(source)
        normalized_path = _to_posix_path(file_path)

        subjects: List[ContractSubject] = []
        for symbol in symbols:
            tsdoc_source = extract_adjacent_tsdoc(
                source=source,
                symbol_lineno=symbol.lineno,
                file_path=normalized_path,
            )
            contract_required, required_reason = _is_contract_required(symbol, normalized_path)
            unsupported_for_symbol = any(f"`{symbol.name}`" in msg for msg in parser.diagnostics)
            contract_sources = _collect_contract_sources(
                symbol=symbol,
                file_path=normalized_path,
                tsdoc_source=tsdoc_source,
            )
            contract_presence = _resolve_contract_presence(
                symbol=symbol,
                contract_sources=contract_sources,
                tsdoc_confidence=tsdoc_source.confidence if tsdoc_source else None,
                unsupported_for_symbol=unsupported_for_symbol,
            )
            target_id = ContractSubject.make_target_id(
                language="typescript",
                file_path=normalized_path,
                symbol_kind=symbol.symbol_kind,
                qualified_name=symbol.qualified_name,
            )
            boundary_evidence = initial_public_boundary_evidence_for_symbol(
                is_exported=bool(symbol.is_exported),
                export_mode=str(symbol.export_mode or ""),
                source_file=normalized_path,
                source_ref=str(symbol.qualified_name or symbol.name or ""),
                resolved_target=target_id,
            )
            metadata = {
                "export_kind": symbol.export_kind,
                "export_mode": symbol.export_mode,
                "parser_backend": "lightweight",
                "public_surface_evidence": symbol.public_surface_evidence,
                "data_contract_kind": symbol.data_contract_kind,
                "schema_source_kind": symbol.schema_source_kind,
                "contract_required_strategy": self._contract_required_strategy,
            }
            metadata.update(
                build_public_boundary_metadata(
                    evidence_items=boundary_evidence,
                    preset_mode=self._public_boundary_config.get("mode", "legacy_exported"),
                    is_exported=bool(symbol.is_exported),
                )
            )
            if symbol.class_name:
                metadata["class_name"] = symbol.class_name
            if parser.diagnostics:
                metadata["diagnostics"] = tuple(parser.diagnostics)
            metadata["jsdoc_confidence"] = tsdoc_source.confidence if tsdoc_source else None
            metadata["contract_required_reason"] = required_reason

            subjects.append(
                ContractSubject(
                    target_id=target_id,
                    legacy_func_id=target_id,
                    language="typescript",
                    symbol_kind=symbol.symbol_kind,
                    qualified_name=symbol.qualified_name,
                    file_path=normalized_path,
                    lineno=symbol.lineno,
                    end_lineno=symbol.end_lineno,
                    visibility=symbol.visibility,
                    strictness=None,
                    signature_text=symbol.signature_text,
                    signature_hash=normalized_sha256(symbol.signature_text),
                    body_hash=normalized_sha256(symbol.body_text) if symbol.body_text else None,
                    contract_hash=_contract_hash_for_sources(contract_sources),
                    contract_presence=contract_presence,
                    contract_required=contract_required,
                    metadata=metadata,
                    contract_sources=tuple(contract_sources),
                )
            )
        return subjects

    def _collect_file(self, path: Path, discovered: Dict[str, Path]) -> None:
        if not path.exists() or not path.is_file():
            return
        name = path.name
        if not name.endswith(".ts"):
            return
        if name.endswith(".d.ts"):
            return
        if any(part in _EXCLUDED_DIRS for part in path.parts):
            return
        discovered[path.resolve().as_posix()] = path.resolve()


def _is_contract_required(symbol: TypeScriptSymbol, normalized_path: str) -> Tuple[bool, str]:
    path_lower = normalized_path.lower()
    if _is_test_file(path_lower):
        return False, "test_file"
    if _is_script_file(path_lower):
        return False, "script_file"
    if symbol.symbol_kind in {"interface", "type_alias"}:
        return False, "advisory_data_contract_target"
    if symbol.schema_source_kind == "z.object" or symbol.schema_source_kind == "z.enum":
        return False, "advisory_schema_target"
    if symbol.symbol_kind == "class":
        return False, "public_surface_target"
    if symbol.is_exported and symbol.visibility == "public":
        return True, "exported_public_symbol"
    return False, "internal_helper_or_non_exported"


def _is_test_file(path_lower: str) -> bool:
    if "/tests/fixtures/" in path_lower:
        return False
    return (
        path_lower.startswith("tests/")
        or "/tests/" in path_lower
        or path_lower.endswith(".test.ts")
        or path_lower.endswith(".spec.ts")
        or "__tests__" in path_lower
    )


def _is_script_file(path_lower: str) -> bool:
    return "/scripts/" in path_lower or path_lower.endswith("/script.ts")


def _resolve_contract_presence(
    *,
    symbol: TypeScriptSymbol,
    contract_sources: Iterable[ContractSource],
    tsdoc_confidence: Union[str, None],
    unsupported_for_symbol: bool,
) -> str:
    if symbol.symbol_kind in {"interface", "type_alias"}:
        return "present"
    if symbol.schema_source_kind in {"z.object", "z.enum"}:
        return "present"
    if tsdoc_confidence == "high":
        return "present"
    if tsdoc_confidence == "medium":
        return "non_contract_doc"
    if unsupported_for_symbol:
        return "unsupported_syntax"
    return "missing"


def _collect_contract_sources(
    *,
    symbol: TypeScriptSymbol,
    file_path: str,
    tsdoc_source: ContractSource | None,
) -> List[ContractSource]:
    sources: List[ContractSource] = []
    if tsdoc_source is not None:
        sources.append(tsdoc_source)

    if symbol.symbol_kind == "interface":
        sources.append(
            ContractSource(
                kind=ContractSourceKind.TYPESCRIPT_INTERFACE,
                text=symbol.signature_text,
                fingerprint=normalized_sha256(symbol.signature_text),
                confidence="high",
                location=f"{file_path}:{symbol.lineno}",
                metadata={"data_contract_kind": symbol.data_contract_kind},
            )
        )
    elif symbol.symbol_kind == "type_alias":
        sources.append(
            ContractSource(
                kind=ContractSourceKind.TYPESCRIPT_TYPE,
                text=symbol.signature_text,
                fingerprint=normalized_sha256(symbol.signature_text),
                confidence="high",
                location=f"{file_path}:{symbol.lineno}",
                metadata={"data_contract_kind": symbol.data_contract_kind},
            )
        )
    elif symbol.schema_source_kind in {"z.object", "z.enum"}:
        sources.append(
            ContractSource(
                kind=ContractSourceKind.ZOD_SCHEMA,
                text=symbol.signature_text,
                fingerprint=normalized_sha256(symbol.signature_text),
                confidence="high",
                location=f"{file_path}:{symbol.lineno}",
                metadata={"schema_source_kind": symbol.schema_source_kind},
            )
        )
    return sources


def _contract_hash_for_sources(contract_sources: Iterable[ContractSource]) -> str | None:
    bundle: List[str] = []
    for source in contract_sources:
        if source.kind in {ContractSourceKind.TSDOC, ContractSourceKind.JSDOC} and source.confidence != "high":
            continue
        bundle.append(f"{source.kind.value}|{source.confidence}|{source.fingerprint}")
    if not bundle:
        return None
    return normalized_sha256("\n".join(sorted(bundle)))

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Sequence, Tuple, Union

from harbor.adapters.base import ContractSubject
from harbor.adapters.typescript.jsdoc import extract_adjacent_tsdoc
from harbor.adapters.typescript.hashing import normalized_sha256
from harbor.adapters.typescript.parser import TypeScriptLightweightParser
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
            contract_source = extract_adjacent_tsdoc(
                source=source,
                symbol_lineno=symbol.lineno,
                file_path=normalized_path,
            )
            contract_required, required_reason = _is_contract_required(symbol, normalized_path)
            unsupported_for_symbol = any(f"`{symbol.name}`" in msg for msg in parser.diagnostics)
            contract_presence = _resolve_contract_presence(
                contract_source_confidence=contract_source.confidence if contract_source else None,
                unsupported_for_symbol=unsupported_for_symbol,
            )
            target_id = ContractSubject.make_target_id(
                language="typescript",
                file_path=normalized_path,
                symbol_kind=symbol.symbol_kind,
                qualified_name=symbol.qualified_name,
            )
            metadata = {
                "export_kind": symbol.export_kind,
                "parser_backend": "lightweight",
            }
            if symbol.class_name:
                metadata["class_name"] = symbol.class_name
            if parser.diagnostics:
                metadata["diagnostics"] = tuple(parser.diagnostics)
            metadata["jsdoc_confidence"] = contract_source.confidence if contract_source else None
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
                    contract_hash=None,
                    contract_presence=contract_presence,
                    contract_required=contract_required,
                    metadata=metadata,
                    contract_sources=(contract_source,) if contract_source else (),
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
    contract_source_confidence: Union[str, None],
    unsupported_for_symbol: bool,
) -> str:
    if contract_source_confidence == "high":
        return "present"
    if contract_source_confidence == "medium":
        return "non_contract_doc"
    if unsupported_for_symbol:
        return "unsupported_syntax"
    return "missing"

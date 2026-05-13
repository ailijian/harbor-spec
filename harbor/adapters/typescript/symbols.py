from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TypeScriptSymbol:
    name: str
    symbol_kind: str  # function | method | interface | type_alias | class | const
    qualified_name: str
    export_kind: str
    is_exported: bool
    lineno: int
    end_lineno: int
    signature_text: str
    body_text: Optional[str]
    visibility: str = "public"
    class_name: Optional[str] = None
    export_mode: str = "named"
    public_surface_evidence: Optional[str] = None
    data_contract_kind: Optional[str] = None
    schema_source_kind: Optional[str] = None

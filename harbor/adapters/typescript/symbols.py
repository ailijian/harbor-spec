from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TypeScriptSymbol:
    name: str
    symbol_kind: str  # function | method
    qualified_name: str
    export_kind: str
    is_exported: bool
    lineno: int
    end_lineno: int
    signature_text: str
    body_text: Optional[str]
    visibility: str = "public"
    class_name: Optional[str] = None

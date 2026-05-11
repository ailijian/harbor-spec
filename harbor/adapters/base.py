from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Protocol, Sequence, Tuple


class ContractSourceKind(str, Enum):
    DOCSTRING = "docstring"
    JSDOC = "jsdoc"
    TSDOC = "tsdoc"
    TYPE_HINT = "type_hint"
    TYPESCRIPT_SIGNATURE = "typescript_signature"
    TYPESCRIPT_INTERFACE = "typescript_interface"
    TYPESCRIPT_TYPE = "typescript_type"
    ZOD_SCHEMA = "zod_schema"
    JSON_SCHEMA = "json_schema"
    ROUTE_SCHEMA = "route_schema"
    TEST = "test"
    FIXTURE = "fixture"
    SNAPSHOT = "snapshot"
    PUBLIC_BEHAVIOR = "public_behavior"
    OTHER = "other"


SourceConfidence = Literal["high", "medium", "low"]


@dataclass(frozen=True)
class ContractSource:
    kind: ContractSourceKind
    text: str
    fingerprint: str = ""
    confidence: SourceConfidence = "medium"
    location: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", self.compute_fingerprint(self.text))

    @staticmethod
    def compute_fingerprint(text: str) -> str:
        normalized = text.replace("\r\n", "\n").strip()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize contract source into a JSON-friendly dictionary.

        @harbor.scope: public
        @harbor.l3_strictness: strict

        Returns:
          Dict[str, Any]: Stable dictionary payload for additive JSON output.
        """
        return {
            "kind": self.kind.value,
            "text": self.text,
            "fingerprint": self.fingerprint,
            "confidence": self.confidence,
            "location": self.location,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class ContractSubject:
    target_id: str
    language: str
    symbol_kind: str
    qualified_name: str
    file_path: str
    lineno: int
    legacy_func_id: Optional[str] = None
    end_lineno: Optional[int] = None
    visibility: Optional[str] = None
    strictness: Optional[str] = None
    signature_text: Optional[str] = None
    signature_hash: Optional[str] = None
    body_hash: Optional[str] = None
    contract_hash: Optional[str] = None
    contract_presence: Optional[str] = None
    contract_required: Optional[bool] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    contract_sources: Tuple[ContractSource, ...] = field(default_factory=tuple)

    @staticmethod
    def make_target_id(
        language: str, file_path: str, symbol_kind: str, qualified_name: str
    ) -> str:
        normalized_file_path = file_path.strip().replace("\\", "/")
        return f"{language}:{normalized_file_path}:{symbol_kind}:{qualified_name}"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize contract subject into a JSON-friendly dictionary.

        @harbor.scope: public
        @harbor.l3_strictness: strict

        Returns:
          Dict[str, Any]: Stable dictionary payload for additive JSON output.
        """
        return {
            "target_id": self.target_id,
            "legacy_func_id": self.legacy_func_id,
            "language": self.language,
            "symbol_kind": self.symbol_kind,
            "qualified_name": self.qualified_name,
            "file_path": self.file_path,
            "lineno": self.lineno,
            "end_lineno": self.end_lineno,
            "visibility": self.visibility,
            "strictness": self.strictness,
            "signature_text": self.signature_text,
            "signature_hash": self.signature_hash,
            "body_hash": self.body_hash,
            "contract_hash": self.contract_hash,
            "contract_presence": self.contract_presence,
            "contract_required": self.contract_required,
            "metadata": dict(self.metadata),
            "contract_sources": [source.to_dict() for source in self.contract_sources],
        }


class LanguageAdapter(Protocol):
    language: str

    def discover_files(self, roots: Sequence[Path]) -> List[Path]:
        ...

    def parse_file(self, path: Path) -> List[ContractSubject]:
        ...

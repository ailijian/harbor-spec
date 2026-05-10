from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from harbor.adapters.python.parser import FunctionContract


_TO_DICT_RE = re.compile(r"(^|[_\.])(to_dict|report_to_dict)$", re.IGNORECASE)
_WRITE_RE = re.compile(r"(^|[_\.])write_[a-z0-9_]*$", re.IGNORECASE)


@dataclass
class ContractPresence:
    presence: Literal["present", "missing", "empty", "non_contract_doc", "malformed"]
    required: bool
    sources: list[str]
    reason: str


def is_contract_required(contract: FunctionContract, file_path: str) -> bool:
    name = str(getattr(contract, "name", "") or "").strip()
    scope = str(getattr(contract, "scope", "") or "").strip().lower()
    strictness = str(getattr(contract, "strictness", "") or "").strip().lower()
    rel = str(file_path or "").replace("\\", "/").strip().lower()

    # Internal helpers and test utilities are opt-out by default.
    if rel.startswith("tests/") or "/tests/" in rel:
        return False
    if strictness == "light":
        return False
    if name.startswith("_") and strictness != "strict":
        return False

    if scope == "public":
        return True
    if strictness == "strict":
        return True
    if rel.startswith("harbor/cli/"):
        return True
    if rel in {
        "harbor/core/l2.py",
        "harbor/core/module_capsule.py",
        "harbor/core/project_structure.py",
    }:
        return True
    if _TO_DICT_RE.search(name):
        return True
    if _WRITE_RE.search(name):
        return True
    return False


def evaluate_contract_presence(contract: FunctionContract, file_path: str) -> ContractPresence:
    required = is_contract_required(contract, file_path)
    doc = contract.docstring
    sources: list[str] = []

    if contract.contract_hash:
        sources.append("docstring_hash")
    if doc is not None:
        stripped = doc.strip()
        if stripped:
            sources.append("docstring")
        else:
            return ContractPresence(
                presence="empty",
                required=required,
                sources=sources,
                reason="Docstring exists but is empty.",
            )

    if not sources:
        return ContractPresence(
            presence="missing",
            required=required,
            sources=[],
            reason="No contract source found.",
        )

    if "docstring" in sources and doc is not None and not _looks_like_contract_doc(doc):
        return ContractPresence(
            presence="non_contract_doc",
            required=required,
            sources=sources,
            reason="Docstring exists but lacks contract-like sections.",
        )

    return ContractPresence(
        presence="present",
        required=required,
        sources=sources,
        reason="Contract source found.",
    )


def _looks_like_contract_doc(doc: str) -> bool:
    text = (doc or "").lower()
    return any(token in text for token in ("args:", "returns:", "raises:", "@harbor."))


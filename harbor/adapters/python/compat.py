from __future__ import annotations

from harbor.adapters.base import ContractSource
from harbor.adapters.base import ContractSourceKind
from harbor.adapters.base import ContractSubject
from harbor.adapters.python.parser import FunctionContract


def _normalize_posix_path(file_path: str) -> str:
    return file_path.strip().replace("\\", "/")


def function_contract_to_subject(contract: FunctionContract, file_path: str) -> ContractSubject:
    normalized_file_path = _normalize_posix_path(file_path)
    symbol_kind = "method" if contract.is_method else "function"
    contract_sources = ()

    if contract.docstring and contract.docstring.strip():
        confidence = "high" if contract.contract_hash else "medium"
        contract_sources = (
            ContractSource(
                kind=ContractSourceKind.DOCSTRING,
                text=contract.docstring,
                fingerprint=ContractSource.compute_fingerprint(contract.docstring),
                confidence=confidence,
                location=f"{normalized_file_path}:{contract.lineno}",
                metadata={"docstring_raw_hash": contract.docstring_raw_hash},
            ),
        )

    return ContractSubject(
        target_id=ContractSubject.make_target_id(
            language="python",
            file_path=normalized_file_path,
            symbol_kind=symbol_kind,
            qualified_name=contract.qualified_name,
        ),
        legacy_func_id=contract.id,
        language="python",
        symbol_kind=symbol_kind,
        qualified_name=contract.qualified_name,
        file_path=normalized_file_path,
        lineno=contract.lineno,
        end_lineno=None,
        visibility=contract.scope or "unknown",
        strictness=contract.strictness,
        signature_text=None,
        signature_hash=contract.signature_hash,
        body_hash=None,
        contract_hash=contract.contract_hash,
        contract_presence=contract.contract_presence,
        contract_required=contract.contract_required,
        metadata={
            "name": contract.name,
            "parent_class": contract.parent_class,
            "is_method": contract.is_method,
            "docstring_raw_hash": contract.docstring_raw_hash,
        },
        contract_sources=contract_sources,
    )

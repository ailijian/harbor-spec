from __future__ import annotations

from dataclasses import replace
from typing import Any, Dict, Iterable, Optional

from harbor.adapters.base import ContractSource, ContractSubject
from harbor.adapters.python.compat import function_contract_to_subject
from harbor.adapters.python.parser import FunctionContract


def _source_kinds(contract_sources: Iterable[ContractSource]) -> list[str]:
    return [source.kind.value for source in contract_sources]


def _source_fingerprints(contract_sources: Iterable[ContractSource]) -> list[str]:
    return [source.fingerprint for source in contract_sources]


def _source_confidence_summary(contract_sources: Iterable[ContractSource]) -> Optional[str]:
    confidences = sorted({str(source.confidence or "").strip() for source in contract_sources if str(source.confidence or "").strip()})
    if not confidences:
        return None
    if len(confidences) == 1:
        return confidences[0]
    return ",".join(confidences)


def _default_name(qualified_name: str) -> str:
    text = str(qualified_name or "").strip()
    if not text:
        return ""
    return text.rsplit(".", 1)[-1]


def contract_subject_to_index_entry(subject: ContractSubject) -> Dict[str, Any]:
    entry_id = str(subject.legacy_func_id or subject.target_id or "").strip()
    metadata = dict(subject.metadata or {})
    if subject.language == "python":
        meta = {
            "name": metadata.get("name") or _default_name(subject.qualified_name),
            "scope": metadata.get("scope") or subject.visibility,
            "strictness": subject.strictness,
            "lineno": subject.lineno,
            "qualified_name": subject.qualified_name,
            "docstring_raw_hash": metadata.get("docstring_raw_hash"),
            "target_id": subject.target_id,
            "func_id": subject.legacy_func_id or subject.target_id,
            "legacy_func_id": subject.legacy_func_id,
            "language": subject.language,
            "symbol_kind": subject.symbol_kind,
            "file_path": subject.file_path,
            "end_lineno": subject.end_lineno,
            "visibility": subject.visibility,
            "contract_presence": subject.contract_presence,
            "contract_required": subject.contract_required,
            "contract_source_kinds": _source_kinds(subject.contract_sources),
            "contract_source_fingerprints": _source_fingerprints(subject.contract_sources),
            "source_confidence_summary": _source_confidence_summary(subject.contract_sources),
        }
    else:
        meta = dict(metadata)
        meta.setdefault("name", _default_name(subject.qualified_name))
        meta["target_id"] = subject.target_id
        meta["func_id"] = subject.legacy_func_id or subject.target_id
        meta["legacy_func_id"] = subject.legacy_func_id
        meta["language"] = subject.language
        meta["symbol_kind"] = subject.symbol_kind
        meta["qualified_name"] = subject.qualified_name
        meta["file_path"] = subject.file_path
        meta["lineno"] = subject.lineno
        meta["end_lineno"] = subject.end_lineno
        meta["visibility"] = subject.visibility
        meta["strictness"] = subject.strictness
        meta["contract_presence"] = subject.contract_presence
        meta["contract_required"] = subject.contract_required
        meta["contract_source_kinds"] = _source_kinds(subject.contract_sources)
        meta["contract_source_fingerprints"] = _source_fingerprints(subject.contract_sources)
        meta["source_confidence_summary"] = _source_confidence_summary(subject.contract_sources)

    return {
        "id": entry_id,
        "file_path": subject.file_path,
        "signature_hash": subject.signature_hash,
        "body_hash": subject.body_hash,
        "contract_hash": subject.contract_hash,
        "meta": meta,
    }


def function_contract_to_index_entry(
    contract: FunctionContract,
    *,
    file_path: str,
    body_hash: Optional[str],
) -> Dict[str, Any]:
    subject = replace(
        function_contract_to_subject(contract, file_path),
        body_hash=body_hash,
    )
    return contract_subject_to_index_entry(subject)


def index_entry_to_cache_item(entry_obj: Dict[str, Any]) -> Dict[str, Any]:
    meta = dict(entry_obj.get("meta") or {})
    item: Dict[str, Any] = {
        "id": entry_obj.get("id"),
        "qualified_name": meta.get("qualified_name"),
        "name": meta.get("name"),
        "signature_hash": entry_obj.get("signature_hash"),
        "body_hash": entry_obj.get("body_hash"),
        "contract_hash": entry_obj.get("contract_hash"),
        "docstring_raw_hash": meta.get("docstring_raw_hash"),
        "scope": meta.get("scope"),
        "strictness": meta.get("strictness"),
        "lineno": meta.get("lineno"),
    }
    additive_fields = (
        "target_id",
        "func_id",
        "legacy_func_id",
        "language",
        "symbol_kind",
        "file_path",
        "end_lineno",
        "visibility",
        "contract_presence",
        "contract_required",
        "contract_source_kinds",
        "contract_source_fingerprints",
        "source_confidence_summary",
        "public_boundary_state",
        "public_boundary_confidence",
        "public_boundary_evidence_kinds",
        "public_boundary_evidence_items",
        "public_boundary_reason",
        "boundary_preset_mode",
    )
    for key in additive_fields:
        value = meta.get(key)
        if value is not None:
            item[key] = value
    return item

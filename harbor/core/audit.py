from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Literal, Mapping, Optional, Sequence, Tuple

from dotenv import load_dotenv

try:
    from openai import OpenAI  # type: ignore
except Exception:
    OpenAI = None  # type: ignore

from harbor.adapters.base import ContractSource, ContractSourceKind, ContractSubject
from harbor.adapters.python.parser import FunctionContract
from harbor.adapters.typescript.adapter import TypeScriptAdapter
from harbor.core.contract_presence import evaluate_contract_presence
from harbor.core.utils import find_function_node, resolve_code_roots


_PYTHON_BEHAVIOR_EVIDENCE_KINDS = {"docstring"}
_TYPESCRIPT_BEHAVIOR_EVIDENCE_KINDS = {"jsdoc", "tsdoc"}
_TYPESCRIPT_AUXILIARY_EVIDENCE_KINDS = {
    "typescript_interface",
    "typescript_type",
    "zod_schema",
}
_TYPESCRIPT_PREVIEW_SYMBOL_KINDS = {"function", "method", "const"}
_TYPESCRIPT_PREVIEW_FINDING_PRIORITY: Dict[str, int] = {
    "preview_error": 0,
    "preview_mismatch": 1,
    "preview_ineligible": 2,
    "preview_ok": 3,
}


@dataclass(frozen=True)
class AuditEvidence:
    kind: str
    text: str
    confidence: str = "medium"
    location: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize one audit evidence row into a stable dictionary.

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: deterministic
        """
        return {
            "kind": self.kind,
            "text": self.text,
            "confidence": self.confidence,
            "location": self.location,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class AuditSubject:
    language: str
    subject_id: str
    target_id: Optional[str]
    func_id: Optional[str]
    qualified_name: str
    symbol_kind: str
    source_path: str
    source_excerpt: str
    contract_evidence: Tuple[AuditEvidence, ...] = field(default_factory=tuple)
    public_boundary_context: Dict[str, Any] = field(default_factory=dict)
    preview_only: bool = False
    notes: Tuple[str, ...] = field(default_factory=tuple)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize one audit subject into a stable dictionary.

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: deterministic
        """
        return {
            "language": self.language,
            "subject_id": self.subject_id,
            "target_id": self.target_id,
            "func_id": self.func_id,
            "qualified_name": self.qualified_name,
            "symbol_kind": self.symbol_kind,
            "source_path": self.source_path,
            "source_excerpt": self.source_excerpt,
            "contract_evidence": [item.to_dict() for item in self.contract_evidence],
            "public_boundary_context": dict(self.public_boundary_context),
            "preview_only": self.preview_only,
            "notes": list(self.notes),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class AuditPromptContext:
    language: str
    subject_id: str
    target_id: Optional[str]
    qualified_name: str
    symbol_kind: str
    source_path: str
    source_excerpt: str
    contract_text: str
    contract_evidence_kinds: Tuple[str, ...] = field(default_factory=tuple)
    public_boundary_context: Dict[str, Any] = field(default_factory=dict)
    preview_only: bool = False
    notes: Tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize one prompt context into a stable dictionary.

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: deterministic
        """
        return {
            "language": self.language,
            "subject_id": self.subject_id,
            "target_id": self.target_id,
            "qualified_name": self.qualified_name,
            "symbol_kind": self.symbol_kind,
            "source_path": self.source_path,
            "source_excerpt": self.source_excerpt,
            "contract_text": self.contract_text,
            "contract_evidence_kinds": list(self.contract_evidence_kinds),
            "public_boundary_context": dict(self.public_boundary_context),
            "preview_only": self.preview_only,
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class AuditEligibility:
    eligible: bool
    reason: str
    notes: Tuple[str, ...] = field(default_factory=tuple)
    evidence_kinds: Tuple[str, ...] = field(default_factory=tuple)
    preview_only: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize one eligibility evaluation into a stable dictionary.

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: deterministic
        """
        return {
            "eligible": self.eligible,
            "reason": self.reason,
            "notes": list(self.notes),
            "evidence_kinds": list(self.evidence_kinds),
            "preview_only": self.preview_only,
        }


@dataclass
class AuditResult:
    status: Literal["OK", "MISMATCH", "ERROR", "CONTRACT_GAP", "SKIPPED_NO_CONTRACT", "NOT_SUPPORTED"]
    reason: Optional[str]
    provider: str
    func_id: str
    prompt: Optional[str] = None
    raw_output: Optional[str] = None
    target_id: Optional[str] = None
    language: Optional[str] = None
    symbol_kind: Optional[str] = None
    preview: bool = False
    eligibility_reason: Optional[str] = None
    evidence_kinds: Tuple[str, ...] = field(default_factory=tuple)
    qualified_name: Optional[str] = None
    file_path: Optional[str] = None
    llm_called: bool = False


@dataclass(frozen=True)
class TypeScriptSemanticAuditPreviewConfig:
    enabled: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize normalized TypeScript semantic-audit preview config.

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: deterministic
        """
        return {"enabled": self.enabled}


@dataclass(frozen=True)
class TypeScriptSemanticAuditPreviewFinding:
    status: str
    reason: str
    target_id: Optional[str] = None
    qualified_name: Optional[str] = None
    file_path: Optional[str] = None
    symbol_kind: Optional[str] = None
    eligibility_reason: Optional[str] = None
    evidence_kinds: Tuple[str, ...] = field(default_factory=tuple)
    contract_source_kinds: Tuple[str, ...] = field(default_factory=tuple)
    source_confidence_summary: Optional[str] = None
    public_boundary_state: Optional[str] = None
    public_boundary_confidence: Optional[str] = None
    public_boundary_evidence_kinds: Tuple[str, ...] = field(default_factory=tuple)
    public_boundary_reason: Optional[str] = None
    boundary_preset_mode: Optional[str] = None
    preview: bool = True
    eligible: bool = False
    advisory: bool = True
    blocking: bool = False
    llm_called: bool = False
    language: str = "typescript"

    def dedupe_key(self) -> Tuple[str, str, str, str]:
        return (
            str(self.status or "").strip(),
            str(self.target_id or "").strip(),
            str(self.eligibility_reason or "").strip(),
            str(self.reason or "").strip(),
        )

    def sort_key(self) -> Tuple[int, str, str, str]:
        return (
            _TYPESCRIPT_PREVIEW_FINDING_PRIORITY.get(str(self.status or ""), 99),
            str(self.target_id or "").strip(),
            str(self.qualified_name or "").strip(),
            str(self.reason or "").strip(),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize one TypeScript semantic-audit preview finding.

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: deterministic
        """
        payload: Dict[str, Any] = {
            "status": self.status,
            "category": self.status,
            "reason": self.reason,
            "language": self.language,
            "preview": self.preview,
            "eligible": self.eligible,
            "advisory": self.advisory,
            "blocking": self.blocking,
            "llm_called": self.llm_called,
        }
        if self.target_id:
            payload["target_id"] = self.target_id
        if self.qualified_name:
            payload["qualified_name"] = self.qualified_name
        if self.file_path:
            payload["file_path"] = self.file_path
        if self.symbol_kind:
            payload["symbol_kind"] = self.symbol_kind
        if self.eligibility_reason:
            payload["eligibility_reason"] = self.eligibility_reason
        if self.evidence_kinds:
            payload["evidence_kinds"] = list(self.evidence_kinds)
        if self.contract_source_kinds:
            payload["contract_source_kinds"] = list(self.contract_source_kinds)
        if self.source_confidence_summary:
            payload["source_confidence_summary"] = self.source_confidence_summary
        if self.public_boundary_state:
            payload["public_boundary_state"] = self.public_boundary_state
        if self.public_boundary_confidence:
            payload["public_boundary_confidence"] = self.public_boundary_confidence
        if self.public_boundary_evidence_kinds:
            payload["public_boundary_evidence_kinds"] = list(self.public_boundary_evidence_kinds)
        if self.public_boundary_reason:
            payload["public_boundary_reason"] = self.public_boundary_reason
        if self.boundary_preset_mode:
            payload["boundary_preset_mode"] = self.boundary_preset_mode
        return payload


@dataclass(frozen=True)
class TypeScriptSemanticAuditPreviewReport:
    provider: str
    model: str
    targets_count: int
    eligible_count: int
    previewed_count: int
    ineligible_count: int
    advisory_count: int
    findings: Tuple[TypeScriptSemanticAuditPreviewFinding, ...]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the TypeScript semantic-audit preview report.

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: deterministic
        """
        return {
            "provider": self.provider,
            "model": self.model,
            "targets_count": self.targets_count,
            "eligible_count": self.eligible_count,
            "previewed_count": self.previewed_count,
            "ineligible_count": self.ineligible_count,
            "advisory_count": self.advisory_count,
            "findings": [item.to_dict() for item in self.findings],
        }

    def to_summary_dict(self) -> Dict[str, Any]:
        """Serialize the compact preview summary without finding rows.

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: deterministic
        """
        return {
            "provider": self.provider,
            "model": self.model,
            "targets_count": self.targets_count,
            "eligible_count": self.eligible_count,
            "previewed_count": self.previewed_count,
            "ineligible_count": self.ineligible_count,
            "advisory_count": self.advisory_count,
        }


class LLMProvider:
    name: str

    def infer(self, prompt: str) -> str:  # type: ignore[override]
        raise NotImplementedError


class MockProvider(LLMProvider):
    name = "mock"
    model = "n/a"

    def infer(self, prompt: str) -> str:
        return "[OK]"


class OpenAIProvider(LLMProvider):
    def __init__(self, provider_name: str, api_key: str, base_url: str, model: str) -> None:
        self.name = provider_name
        self.model = model
        if OpenAI is None:
            raise RuntimeError("openai library not available")
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def infer(self, prompt: str) -> str:
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a code auditor. Be precise and deterministic."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
                response_format={"type": "json_object"},
            )
            txt = (resp.choices[0].message.content or "").strip()
            return txt or "[ERROR]: empty response"
        except Exception as exc:
            return f"[ERROR]: {str(exc)}"


PROMPT_TEMPLATES = {
    "en": (
        "You are a code auditor. Check if the implementation matches the docstring contract.\n"
        "Docstring:\n"
        "{doc}\n"
        "Code:\n"
        "{code}\n"
        "Focus on: Args, Returns, Raises.\n"
        "Return ONLY a JSON object with keys 'status' and optional 'reason'.\n"
        "Examples: {{\"status\":\"OK\"}} or {{\"status\":\"MISMATCH\",\"reason\":\"...\"}}"
    ),
    "zh": (
        "你是一名代码审计专家。请检查下方的代码实现是否严格符合 Docstring 契约。\n"
        "Docstring:\n"
        "{doc}\n"
        "Code:\n"
        "{code}\n"
        "请重点关注: 参数(Args), 返回值(Returns), 异常(Raises)。\n"
        "只返回一个 JSON 对象，包含 'status' 和可选 'reason' 字段，且不要输出任何其他文本。\n"
        "示例: {{\"status\":\"OK\"}} 或 {{\"status\":\"MISMATCH\",\"reason\":\"原因\"}}"
    ),
}

PREVIEW_PROMPT_TEMPLATES = {
    "en": (
        "You are a code auditor. Check if the implementation matches the contract evidence.\n"
        "Contract Evidence:\n"
        "{contract}\n"
        "Code:\n"
        "{code}\n"
        "Focus on behavior, arguments, returns, raises, and observable semantics.\n"
        "Return ONLY a JSON object with keys 'status' and optional 'reason'.\n"
        "Examples: {{\"status\":\"OK\"}} or {{\"status\":\"MISMATCH\",\"reason\":\"...\"}}"
    ),
    "zh": (
        "你是一名代码审计专家。请检查下方代码实现是否符合给定契约证据。\n"
        "Contract Evidence:\n"
        "{contract}\n"
        "Code:\n"
        "{code}\n"
        "请重点关注行为、参数、返回值、异常和可观察语义。\n"
        "只返回一个 JSON 对象，包含 'status' 和可选 'reason' 字段，且不要输出任何其他文本。\n"
        "示例: {{\"status\":\"OK\"}} 或 {{\"status\":\"MISMATCH\",\"reason\":\"原因\"}}"
    ),
}


def resolve_provider() -> LLMProvider:
    load_dotenv()
    provider_name = (os.getenv("HARBOR_LLM_PROVIDER") or "mock").strip().lower()
    if provider_name != "mock":
        api_key = os.getenv("HARBOR_LLM_API_KEY") or ""
        base_url = os.getenv("HARBOR_LLM_BASE_URL") or "https://api.openai.com/v1"
        model = os.getenv("HARBOR_LLM_MODEL") or "gpt-4o-mini"
        if not api_key:
            return MockProvider()
        try:
            return OpenAIProvider(
                provider_name=provider_name,
                api_key=api_key,
                base_url=base_url,
                model=model,
            )
        except Exception:
            return MockProvider()
    return MockProvider()


def resolve_typescript_semantic_audit_preview_config(
    config: Optional[Mapping[str, Any]],
) -> TypeScriptSemanticAuditPreviewConfig:
    """Resolve additive TypeScript semantic-audit preview config.

    Behavior:
      - Reads `verification.semantic_audit.typescript_preview`.
      - Keeps preview disabled unless explicitly enabled.
      - Leaves Python semantic audit behavior unchanged when unset.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: deterministic
    """
    cfg = dict(config or {})
    verification_cfg = cfg.get("verification")
    if not isinstance(verification_cfg, Mapping):
        verification_cfg = {}
    semantic_cfg = verification_cfg.get("semantic_audit")
    if not isinstance(semantic_cfg, Mapping):
        semantic_cfg = {}
    typescript_preview_cfg = semantic_cfg.get("typescript_preview")
    if not isinstance(typescript_preview_cfg, Mapping):
        typescript_preview_cfg = {}
    return TypeScriptSemanticAuditPreviewConfig(
        enabled=_to_bool(typescript_preview_cfg.get("enabled"), default=False)
    )


class SemanticGuard:
    def build_prompt(self, contract: FunctionContract, source_code: str) -> str:
        doc = contract.docstring or ""
        lines = source_code.replace("\r\n", "\n").strip()
        lang = (os.getenv("HARBOR_LANGUAGE") or "en").strip().lower()
        tmpl = PROMPT_TEMPLATES.get(lang, PROMPT_TEMPLATES["en"])
        return tmpl.format(doc=doc, code=lines)

    def build_prompt_from_context(self, context: AuditPromptContext) -> str:
        contract = context.contract_text.strip()
        code = context.source_excerpt.replace("\r\n", "\n").strip()
        lang = (os.getenv("HARBOR_LANGUAGE") or "en").strip().lower()
        tmpl = PREVIEW_PROMPT_TEMPLATES.get(lang, PREVIEW_PROMPT_TEMPLATES["en"])
        return tmpl.format(contract=contract, code=code)

    def audit(
        self,
        contract: FunctionContract,
        source_text: str,
        provider: LLMProvider,
        file_path: str = "",
    ) -> AuditResult:
        if _is_typescript_target(contract):
            inferred_file = file_path or str(getattr(contract, "file_path", "") or "").strip()
            return AuditResult(
                status="SKIPPED_NO_CONTRACT",
                reason=(
                    "TypeScript semantic audit preview requires unified TypeScript contract evidence; "
                    "legacy FunctionContract targets are ineligible."
                ),
                provider=provider.name,
                func_id=str(contract.id),
                prompt=None,
                raw_output=None,
                target_id=str(contract.id),
                language="typescript",
                symbol_kind="function",
                preview=True,
                eligibility_reason="legacy_typescript_target",
                evidence_kinds=tuple(),
                qualified_name=str(contract.qualified_name or contract.id),
                file_path=inferred_file or None,
                llm_called=False,
            )
        subject = build_python_audit_subject(contract, source_text, file_path=file_path)
        return self.audit_subject(subject, provider)

    def audit_subject(self, subject: AuditSubject, provider: LLMProvider) -> AuditResult:
        eligibility = evaluate_audit_eligibility(subject)
        if not eligibility.eligible:
            return _ineligible_audit_result(subject, provider, eligibility)
        prompt_context = build_audit_prompt_context(subject, eligibility)
        prompt = self._build_subject_prompt(subject, prompt_context)
        try:
            output = provider.infer(prompt).strip()
        except Exception as exc:
            return AuditResult(
                status="ERROR",
                reason=str(exc),
                provider=provider.name,
                func_id=str(subject.func_id or subject.subject_id),
                prompt=prompt,
                raw_output=None,
                target_id=subject.target_id,
                language=subject.language,
                symbol_kind=subject.symbol_kind,
                preview=subject.preview_only,
                eligibility_reason=eligibility.reason,
                evidence_kinds=eligibility.evidence_kinds,
                qualified_name=subject.qualified_name,
                file_path=subject.source_path,
                llm_called=True,
            )
        return _parse_audit_output(
            output=output,
            prompt=prompt,
            provider=provider,
            subject=subject,
            eligibility=eligibility,
        )

    def _build_subject_prompt(
        self,
        subject: AuditSubject,
        prompt_context: AuditPromptContext,
    ) -> str:
        legacy_docstring = str(subject.metadata.get("legacy_docstring") or "").strip()
        if subject.language == "python" and legacy_docstring:
            contract = FunctionContract(
                id=str(subject.func_id or subject.subject_id),
                name=str(subject.qualified_name.split(".")[-1] or subject.subject_id),
                qualified_name=subject.qualified_name,
                signature_hash=str(subject.metadata.get("signature_hash") or ""),
                docstring=legacy_docstring,
                docstring_raw_hash=None,
                contract_hash=str(subject.metadata.get("contract_hash") or "") or None,
                lineno=int(subject.metadata.get("lineno") or 0),
                col_offset=0,
            )
            return self.build_prompt(contract, subject.source_excerpt)
        return self.build_prompt_from_context(prompt_context)


def build_python_audit_subject(
    contract: FunctionContract,
    source_text: str,
    *,
    file_path: str = "",
) -> AuditSubject:
    """Adapt the existing Python semantic-audit path to the unified subject model.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: read-only
    """
    inferred_file = file_path or _infer_file_path_from_contract(contract)
    presence = evaluate_contract_presence(contract, inferred_file)
    contract.contract_presence = presence.presence
    contract.contract_required = presence.required
    contract.contract_sources = presence.sources
    node = find_function_node(source_text, contract.lineno, contract.name)
    code_seg = _slice_source_excerpt(
        source_text,
        start_lineno=getattr(node, "lineno", None) if node is not None else contract.lineno,
        end_lineno=getattr(node, "end_lineno", None) if node is not None else None,
    )
    evidence: List[AuditEvidence] = []
    if str(contract.docstring or "").strip():
        evidence.append(
            AuditEvidence(
                kind="docstring",
                text=str(contract.docstring or ""),
                confidence="high",
                location=f"{inferred_file}:{int(contract.lineno or 0)}" if inferred_file else None,
            )
        )
    symbol_kind = "method" if bool(getattr(contract, "is_method", False)) else "function"
    return AuditSubject(
        language="python",
        subject_id=str(contract.id),
        target_id=None,
        func_id=str(contract.id),
        qualified_name=str(contract.qualified_name or contract.id),
        symbol_kind=symbol_kind,
        source_path=str(inferred_file or ""),
        source_excerpt=code_seg or source_text.replace("\r\n", "\n").strip(),
        contract_evidence=tuple(evidence),
        public_boundary_context={},
        preview_only=False,
        notes=(str(presence.reason or ""),),
        metadata={
            "contract_presence": presence.presence,
            "contract_required": bool(presence.required),
            "contract_sources": list(presence.sources),
            "legacy_docstring": str(contract.docstring or ""),
            "signature_hash": str(contract.signature_hash or ""),
            "contract_hash": str(contract.contract_hash or ""),
            "lineno": int(contract.lineno or 0),
            "scope": str(getattr(contract, "scope", "") or ""),
            "strictness": str(getattr(contract, "strictness", "") or ""),
        },
    )


def build_typescript_audit_subject(
    subject: ContractSubject,
    *,
    repo_root: Path,
) -> AuditSubject:
    """Adapt one TypeScript `ContractSubject` into the unified audit subject model.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: read-only
    """
    source_path = _normalize_subject_source_path(str(getattr(subject, "file_path", "") or ""), repo_root=repo_root)
    absolute_source_path = _resolve_subject_source_path(str(getattr(subject, "file_path", "") or ""), repo_root=repo_root)
    source_text = absolute_source_path.read_text(encoding="utf-8")
    source_excerpt = _slice_source_excerpt(
        source_text,
        start_lineno=getattr(subject, "lineno", None),
        end_lineno=getattr(subject, "end_lineno", None),
    )
    evidence = tuple(_audit_evidence_from_contract_source(item) for item in list(subject.contract_sources or ()))
    metadata = dict(getattr(subject, "metadata", {}) or {})
    public_boundary_context = {
        "public_boundary_state": str(metadata.get("public_boundary_state") or "").strip() or None,
        "public_boundary_confidence": str(metadata.get("public_boundary_confidence") or "").strip() or None,
        "public_boundary_evidence_kinds": tuple(
            str(value or "").strip()
            for value in list(metadata.get("public_boundary_evidence_kinds") or [])
            if str(value or "").strip()
        ),
        "public_boundary_reason": str(metadata.get("public_boundary_reason") or "").strip() or None,
        "boundary_preset_mode": str(metadata.get("boundary_preset_mode") or "").strip() or None,
    }
    return AuditSubject(
        language="typescript",
        subject_id=str(subject.target_id or subject.legacy_func_id or ""),
        target_id=str(subject.target_id or "") or None,
        func_id=str(subject.legacy_func_id or "") or None,
        qualified_name=str(subject.qualified_name or subject.target_id or ""),
        symbol_kind=str(subject.symbol_kind or ""),
        source_path=source_path,
        source_excerpt=source_excerpt,
        contract_evidence=evidence,
        public_boundary_context={k: v for k, v in public_boundary_context.items() if v not in (None, (), [], "")},
        preview_only=True,
        notes=tuple(
            item
            for item in [
                str(metadata.get("contract_required_reason") or "").strip() or None,
                str(_typescript_ineligibility_hint(subject) or "").strip() or None,
            ]
            if item
        ),
        metadata={
            "contract_presence": str(getattr(subject, "contract_presence", "") or ""),
            "contract_required": bool(getattr(subject, "contract_required", False)),
            "source_confidence_summary": str(_strongest_subject_confidence(subject) or ""),
            "contract_source_kinds": tuple(
                evidence_item.kind
                for evidence_item in evidence
                if str(evidence_item.kind or "").strip()
            ),
            "public_boundary_state": str(metadata.get("public_boundary_state") or ""),
            "public_boundary_confidence": str(metadata.get("public_boundary_confidence") or ""),
            "public_boundary_evidence_kinds": tuple(
                str(value or "").strip()
                for value in list(metadata.get("public_boundary_evidence_kinds") or [])
                if str(value or "").strip()
            ),
            "public_boundary_reason": str(metadata.get("public_boundary_reason") or ""),
            "boundary_preset_mode": str(metadata.get("boundary_preset_mode") or ""),
        },
    )


def build_audit_prompt_context(
    subject: AuditSubject,
    eligibility: AuditEligibility,
) -> AuditPromptContext:
    """Build the unified prompt context consumed by semantic-audit providers.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: deterministic
    """
    evidence_rows: List[str] = []
    for item in list(subject.contract_evidence or ()):
        label = str(item.kind or "").strip()
        confidence = str(item.confidence or "").strip()
        prefix = f"[{label}"
        if confidence:
            prefix += f":{confidence}"
        prefix += "]"
        evidence_rows.append(f"{prefix}\n{str(item.text or '').strip()}")
    contract_text = "\n\n".join(row for row in evidence_rows if row.strip()).strip()
    return AuditPromptContext(
        language=subject.language,
        subject_id=subject.subject_id,
        target_id=subject.target_id,
        qualified_name=subject.qualified_name,
        symbol_kind=subject.symbol_kind,
        source_path=subject.source_path,
        source_excerpt=subject.source_excerpt,
        contract_text=contract_text,
        contract_evidence_kinds=eligibility.evidence_kinds,
        public_boundary_context=dict(subject.public_boundary_context),
        preview_only=subject.preview_only,
        notes=tuple(eligibility.notes),
    )


def evaluate_audit_eligibility(subject: AuditSubject) -> AuditEligibility:
    """Evaluate whether a subject may enter semantic audit.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: deterministic
    """
    evidence_kinds = tuple(
        str(item.kind or "").strip().lower()
        for item in list(subject.contract_evidence or ())
        if str(item.kind or "").strip()
    )
    if not str(subject.source_excerpt or "").strip():
        return AuditEligibility(
            eligible=False,
            reason="source_excerpt_missing",
            notes=("No source excerpt could be extracted for semantic audit.",),
            evidence_kinds=evidence_kinds,
            preview_only=subject.preview_only,
        )
    if str(subject.language or "").strip().lower() == "typescript":
        return _evaluate_typescript_audit_eligibility(subject, evidence_kinds=evidence_kinds)
    return _evaluate_python_audit_eligibility(subject, evidence_kinds=evidence_kinds)


def build_typescript_semantic_audit_preview(
    repo_root: Path,
    status_report: object,
    *,
    config: Optional[Mapping[str, Any]] = None,
    provider: Optional[LLMProvider] = None,
    guard: Optional[SemanticGuard] = None,
) -> Optional[TypeScriptSemanticAuditPreviewReport]:
    """Build the additive TypeScript semantic-audit preview report.

    Behavior:
      - Returns `None` when preview is disabled.
      - Reuses unified audit subject/prompt/eligibility logic.
      - Keeps all findings advisory-only and non-blocking.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: read-only
    """
    preview_config = resolve_typescript_semantic_audit_preview_config(config)
    if not preview_config.enabled:
        return None
    effective_provider = provider or resolve_provider()
    effective_guard = guard or SemanticGuard()
    subjects = _collect_typescript_subjects(repo_root=Path(repo_root).resolve(), config=config)
    findings: List[TypeScriptSemanticAuditPreviewFinding] = []
    eligible_count = 0
    previewed_count = 0
    targets = _collect_typescript_preview_targets(status_report)
    for entry in targets:
        subject = _resolve_typescript_subject_for_entry(entry, subjects=subjects)
        if subject is None:
            findings.append(
                TypeScriptSemanticAuditPreviewFinding(
                    status="preview_ineligible",
                    reason="TypeScript target could not be resolved for semantic audit preview.",
                    target_id=str(getattr(entry, "target_id", "") or getattr(entry, "id", "") or "") or None,
                    qualified_name=str(getattr(entry, "name", "") or "") or None,
                    file_path=str(getattr(entry, "file_path", "") or "") or None,
                    symbol_kind=str(getattr(entry, "symbol_kind", "") or "") or None,
                    eligibility_reason="target_not_resolved",
                    evidence_kinds=tuple(
                        str(value or "").strip()
                        for value in list(getattr(entry, "contract_source_kinds", []) or [])
                        if str(value or "").strip()
                    ),
                    contract_source_kinds=tuple(
                        str(value or "").strip()
                        for value in list(getattr(entry, "contract_source_kinds", []) or [])
                        if str(value or "").strip()
                    ),
                    source_confidence_summary=str(getattr(entry, "source_confidence_summary", "") or "") or None,
                    public_boundary_state=str(getattr(entry, "public_boundary_state", "") or "") or None,
                    public_boundary_confidence=str(getattr(entry, "public_boundary_confidence", "") or "") or None,
                    public_boundary_evidence_kinds=tuple(
                        str(value or "").strip()
                        for value in list(getattr(entry, "public_boundary_evidence_kinds", []) or [])
                        if str(value or "").strip()
                    ),
                    public_boundary_reason=str(getattr(entry, "public_boundary_reason", "") or "") or None,
                    boundary_preset_mode=str(getattr(entry, "boundary_preset_mode", "") or "") or None,
                    eligible=False,
                    llm_called=False,
                )
            )
            continue
        audit_subject = build_typescript_audit_subject(subject, repo_root=Path(repo_root).resolve())
        eligibility = evaluate_audit_eligibility(audit_subject)
        if eligibility.eligible:
            eligible_count += 1
        result = effective_guard.audit_subject(audit_subject, effective_provider)
        if result.llm_called:
            previewed_count += 1
        findings.append(
            _semantic_preview_finding_from_result(
                result=result,
                audit_subject=audit_subject,
                eligibility=eligibility,
            )
        )
    deduped = _dedupe_typescript_preview_findings(findings)
    ineligible_count = sum(1 for item in deduped if not item.eligible)
    advisory_count = sum(1 for item in deduped if item.status != "preview_ok")
    return TypeScriptSemanticAuditPreviewReport(
        provider=str(getattr(effective_provider, "name", "mock") or "mock"),
        model=str(getattr(effective_provider, "model", "n/a") or "n/a"),
        targets_count=len(targets),
        eligible_count=eligible_count,
        previewed_count=previewed_count,
        ineligible_count=ineligible_count,
        advisory_count=advisory_count,
        findings=deduped,
    )


def _to_bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return default


def _audit_evidence_from_contract_source(source: ContractSource) -> AuditEvidence:
    kind_value = getattr(source.kind, "value", str(source.kind or "other"))
    return AuditEvidence(
        kind=str(kind_value or "other").strip().lower(),
        text=str(source.text or ""),
        confidence=str(source.confidence or "medium"),
        location=source.location,
        metadata=dict(source.metadata or {}),
    )


def _collect_typescript_preview_targets(status_report: object) -> List[object]:
    rows: List[object] = []
    seen: set[str] = set()
    for bucket_name in (
        "drift",
        "modified",
        "contract_changed",
        "contract_gap",
        "skipped_no_contract",
        "unsupported_syntax_advisory",
    ):
        for entry in list(getattr(status_report, bucket_name, []) or []):
            language = str(getattr(entry, "language", "") or "").strip().lower()
            file_path = str(getattr(entry, "file_path", "") or "").strip().lower()
            if language != "typescript" and not (file_path.endswith(".ts") and not file_path.endswith(".d.ts")):
                continue
            key = str(getattr(entry, "target_id", "") or getattr(entry, "id", "") or "").strip()
            if not key:
                key = f"{bucket_name}:{file_path}:{str(getattr(entry, 'name', '') or '').strip()}"
            if key in seen:
                continue
            seen.add(key)
            rows.append(entry)
    rows.sort(
        key=lambda item: (
            str(getattr(item, "target_id", "") or getattr(item, "id", "") or "").strip(),
            str(getattr(item, "file_path", "") or "").strip(),
            str(getattr(item, "name", "") or "").strip(),
        )
    )
    return rows


def _collect_typescript_subjects(
    *,
    repo_root: Path,
    config: Optional[Mapping[str, Any]],
) -> Dict[str, ContractSubject]:
    cfg = dict(config or {})
    code_roots = list(cfg.get("code_roots") or ["harbor/**"])
    languages_cfg = cfg.get("languages")
    if not isinstance(languages_cfg, Mapping):
        languages_cfg = {}
    typescript_cfg = languages_cfg.get("typescript")
    if not isinstance(typescript_cfg, Mapping):
        typescript_cfg = {}
    adapter = TypeScriptAdapter(config=typescript_cfg)
    subjects: Dict[str, ContractSubject] = {}
    for path in adapter.discover_files(resolve_code_roots(code_roots, repo_root=repo_root)):
        try:
            parsed = adapter.parse_file(path)
        except Exception:
            continue
        for subject in parsed:
            target_id = str(getattr(subject, "target_id", "") or "").strip()
            if target_id:
                subjects[target_id] = subject
            legacy_func_id = str(getattr(subject, "legacy_func_id", "") or "").strip()
            if legacy_func_id:
                subjects[legacy_func_id] = subject
            try:
                rel_path = Path(str(getattr(subject, "file_path", "") or "")).resolve().relative_to(repo_root).as_posix()
            except Exception:
                rel_path = str(getattr(subject, "file_path", "") or "").replace("\\", "/")
            if rel_path:
                rel_target_id = ContractSubject.make_target_id(
                    language="typescript",
                    file_path=rel_path,
                    symbol_kind=str(getattr(subject, "symbol_kind", "") or ""),
                    qualified_name=str(getattr(subject, "qualified_name", "") or ""),
                )
                subjects[rel_target_id] = subject
    return subjects


def _resolve_typescript_subject_for_entry(
    entry: object,
    *,
    subjects: Mapping[str, ContractSubject],
) -> Optional[ContractSubject]:
    for candidate in (
        str(getattr(entry, "target_id", "") or "").strip(),
        str(getattr(entry, "id", "") or "").strip(),
    ):
        if candidate and candidate in subjects:
            return subjects[candidate]
    return None


def _evaluate_python_audit_eligibility(
    subject: AuditSubject,
    *,
    evidence_kinds: Tuple[str, ...],
) -> AuditEligibility:
    presence = str(subject.metadata.get("contract_presence") or "").strip().lower()
    required = bool(subject.metadata.get("contract_required", False))
    if presence == "present":
        return AuditEligibility(
            eligible=True,
            reason="eligible_contract_present",
            notes=tuple(subject.notes),
            evidence_kinds=evidence_kinds,
            preview_only=subject.preview_only,
        )
    if required:
        return AuditEligibility(
            eligible=False,
            reason="required_contract_missing",
            notes=tuple(subject.notes) or ("Required contract source is missing.",),
            evidence_kinds=evidence_kinds,
            preview_only=subject.preview_only,
        )
    return AuditEligibility(
        eligible=False,
        reason="contract_not_required",
        notes=tuple(subject.notes) or ("No contract is required for this target.",),
        evidence_kinds=evidence_kinds,
        preview_only=subject.preview_only,
    )


def _evaluate_typescript_audit_eligibility(
    subject: AuditSubject,
    *,
    evidence_kinds: Tuple[str, ...],
) -> AuditEligibility:
    symbol_kind = str(subject.symbol_kind or "").strip().lower()
    if symbol_kind not in _TYPESCRIPT_PREVIEW_SYMBOL_KINDS:
        return AuditEligibility(
            eligible=False,
            reason="non_function_symbol",
            notes=(
                "TypeScript semantic audit preview only evaluates function-like targets.",
            ),
            evidence_kinds=evidence_kinds,
            preview_only=True,
        )
    behavior_evidence = [
        item
        for item in list(subject.contract_evidence or ())
        if item.kind in _TYPESCRIPT_BEHAVIOR_EVIDENCE_KINDS and str(item.confidence or "").strip().lower() == "high"
    ]
    if behavior_evidence:
        return AuditEligibility(
            eligible=True,
            reason="eligible_behavior_contract_present",
            notes=tuple(subject.notes),
            evidence_kinds=evidence_kinds,
            preview_only=True,
        )
    if any(item.kind in _TYPESCRIPT_AUXILIARY_EVIDENCE_KINDS for item in list(subject.contract_evidence or ())):
        return AuditEligibility(
            eligible=False,
            reason="auxiliary_evidence_only",
            notes=(
                "Found only interface/type/Zod evidence; function-level preview requires behavior contract evidence such as JSDoc/TSDoc.",
            ),
            evidence_kinds=evidence_kinds,
            preview_only=True,
        )
    presence = str(subject.metadata.get("contract_presence") or "").strip().lower()
    if presence == "non_contract_doc":
        return AuditEligibility(
            eligible=False,
            reason="behavior_contract_low_confidence",
            notes=(
                "A nearby TypeScript doc comment exists, but its confidence is not high enough to qualify as behavior contract evidence.",
            ),
            evidence_kinds=evidence_kinds,
            preview_only=True,
        )
    if presence == "unsupported_syntax":
        return AuditEligibility(
            eligible=False,
            reason="unsupported_syntax",
            notes=(
                "TypeScript semantic audit preview could not derive stable behavior evidence from the current parser result.",
            ),
            evidence_kinds=evidence_kinds,
            preview_only=True,
        )
    return AuditEligibility(
        eligible=False,
        reason="behavior_contract_missing",
        notes=(
            "TypeScript semantic audit preview requires behavior contract evidence such as JSDoc/TSDoc.",
        ),
        evidence_kinds=evidence_kinds,
        preview_only=True,
    )


def _ineligible_audit_result(
    subject: AuditSubject,
    provider: LLMProvider,
    eligibility: AuditEligibility,
) -> AuditResult:
    status = "SKIPPED_NO_CONTRACT"
    if subject.language == "python" and bool(subject.metadata.get("contract_required", False)):
        status = "CONTRACT_GAP"
    return AuditResult(
        status=status,
        reason=_eligibility_message(subject, eligibility),
        provider=provider.name,
        func_id=str(subject.func_id or subject.subject_id),
        prompt=None,
        raw_output=None,
        target_id=subject.target_id,
        language=subject.language,
        symbol_kind=subject.symbol_kind,
        preview=subject.preview_only,
        eligibility_reason=eligibility.reason,
        evidence_kinds=eligibility.evidence_kinds,
        qualified_name=subject.qualified_name,
        file_path=subject.source_path,
        llm_called=False,
    )


def _parse_audit_output(
    *,
    output: str,
    prompt: str,
    provider: LLMProvider,
    subject: AuditSubject,
    eligibility: AuditEligibility,
) -> AuditResult:
    common_kwargs = {
        "provider": provider.name,
        "func_id": str(subject.func_id or subject.subject_id),
        "prompt": prompt,
        "raw_output": output,
        "target_id": subject.target_id,
        "language": subject.language,
        "symbol_kind": subject.symbol_kind,
        "preview": subject.preview_only,
        "eligibility_reason": eligibility.reason,
        "evidence_kinds": eligibility.evidence_kinds,
        "qualified_name": subject.qualified_name,
        "file_path": subject.source_path,
        "llm_called": True,
    }
    try:
        text = output
        if "```" in text:
            text = text.replace("```json", "").replace("```", "").strip()
        key_pos = text.find("\"status\"")
        if key_pos != -1:
            start = text.rfind("{", 0, key_pos)
            end = text.find("}", key_pos)
            candidate = text[start : end + 1] if start != -1 and end != -1 and end > start else text
        else:
            candidate = text
        obj = json.loads(candidate)
        if isinstance(obj, dict):
            state = str(obj.get("status", "")).strip().upper()
            reason = obj.get("reason")
            if state == "OK":
                return AuditResult(status="OK", reason=None, **common_kwargs)
            if state == "MISMATCH":
                return AuditResult(status="MISMATCH", reason=(reason or "mismatch"), **common_kwargs)
            if state == "ERROR":
                return AuditResult(status="ERROR", reason=(reason or "error"), **common_kwargs)
    except Exception:
        pass
    upper = output.upper()
    if upper.startswith("[ERROR]"):
        reason = output.split("]", 1)[1].strip(": ").strip()
        return AuditResult(status="ERROR", reason=reason or "error", **common_kwargs)
    if upper.startswith("[MISMATCH]"):
        reason = output.split("]", 1)[1].strip(": ").strip()
        return AuditResult(status="MISMATCH", reason=reason or "mismatch", **common_kwargs)
    if "[OK]" in upper:
        return AuditResult(status="OK", reason=None, **common_kwargs)
    return AuditResult(status="ERROR", reason="unrecognized output", **common_kwargs)


def _semantic_preview_finding_from_result(
    *,
    result: AuditResult,
    audit_subject: AuditSubject,
    eligibility: AuditEligibility,
) -> TypeScriptSemanticAuditPreviewFinding:
    status = "preview_ok"
    if result.status == "MISMATCH":
        status = "preview_mismatch"
    elif result.status == "ERROR":
        status = "preview_error"
    elif result.status in {"CONTRACT_GAP", "SKIPPED_NO_CONTRACT", "NOT_SUPPORTED"}:
        status = "preview_ineligible"
    metadata = dict(audit_subject.metadata or {})
    return TypeScriptSemanticAuditPreviewFinding(
        status=status,
        reason=str(result.reason or _eligibility_message(audit_subject, eligibility) or "").strip(),
        target_id=audit_subject.target_id,
        qualified_name=audit_subject.qualified_name,
        file_path=audit_subject.source_path,
        symbol_kind=audit_subject.symbol_kind,
        eligibility_reason=result.eligibility_reason or eligibility.reason,
        evidence_kinds=tuple(result.evidence_kinds or eligibility.evidence_kinds),
        contract_source_kinds=tuple(
            str(value or "").strip()
            for value in list(metadata.get("contract_source_kinds") or [])
            if str(value or "").strip()
        ),
        source_confidence_summary=str(metadata.get("source_confidence_summary") or "") or None,
        public_boundary_state=str(metadata.get("public_boundary_state") or "") or None,
        public_boundary_confidence=str(metadata.get("public_boundary_confidence") or "") or None,
        public_boundary_evidence_kinds=tuple(
            str(value or "").strip()
            for value in list(metadata.get("public_boundary_evidence_kinds") or [])
            if str(value or "").strip()
        ),
        public_boundary_reason=str(metadata.get("public_boundary_reason") or "") or None,
        boundary_preset_mode=str(metadata.get("boundary_preset_mode") or "") or None,
        eligible=eligibility.eligible,
        llm_called=bool(result.llm_called),
    )


def _dedupe_typescript_preview_findings(
    findings: Iterable[TypeScriptSemanticAuditPreviewFinding],
) -> Tuple[TypeScriptSemanticAuditPreviewFinding, ...]:
    selected: Dict[Tuple[str, str, str, str], TypeScriptSemanticAuditPreviewFinding] = {}
    for finding in findings:
        key = finding.dedupe_key()
        previous = selected.get(key)
        if previous is None or finding.sort_key() < previous.sort_key():
            selected[key] = finding
    return tuple(sorted(selected.values(), key=lambda item: item.sort_key()))


def _eligibility_message(subject: AuditSubject, eligibility: AuditEligibility) -> str:
    if subject.language == "python":
        if eligibility.reason == "required_contract_missing":
            return "No contract source found; semantic comparison skipped."
        if eligibility.reason == "contract_not_required":
            return "No contract required for this target; semantic comparison skipped."
    if eligibility.notes:
        return " ".join(part.strip() for part in eligibility.notes if str(part or "").strip()).strip()
    if eligibility.reason == "non_function_symbol":
        return "TypeScript semantic audit preview only evaluates function-like targets."
    if eligibility.reason == "auxiliary_evidence_only":
        return "Found only interface/type/Zod evidence; function-level preview requires behavior contract evidence such as JSDoc/TSDoc."
    if eligibility.reason == "behavior_contract_low_confidence":
        return "A nearby TypeScript doc comment exists, but its confidence is not high enough to qualify as behavior contract evidence."
    if eligibility.reason == "unsupported_syntax":
        return "TypeScript semantic audit preview could not derive stable behavior evidence from the current parser result."
    if eligibility.reason == "behavior_contract_missing":
        return "TypeScript semantic audit preview requires behavior contract evidence such as JSDoc/TSDoc."
    if eligibility.reason == "source_excerpt_missing":
        return "No source excerpt could be extracted for semantic audit."
    return "Semantic audit eligibility was not satisfied."


def _slice_source_excerpt(
    source_text: str,
    *,
    start_lineno: Optional[int],
    end_lineno: Optional[int],
) -> str:
    lines = source_text.replace("\r\n", "\n").split("\n")
    start = int(start_lineno or 0)
    end = int(end_lineno or 0)
    if start > 0 and end >= start:
        return "\n".join(lines[start - 1 : end]).strip()
    if start > 0:
        return "\n".join(lines[start - 1 :]).strip()
    return source_text.replace("\r\n", "\n").strip()


def _resolve_subject_source_path(file_path: str, *, repo_root: Path) -> Path:
    candidate = Path(str(file_path or "").replace("\\", "/"))
    if candidate.is_absolute():
        return candidate.resolve()
    return (Path(repo_root).resolve() / candidate).resolve()


def _normalize_subject_source_path(file_path: str, *, repo_root: Path) -> str:
    resolved = _resolve_subject_source_path(file_path, repo_root=repo_root)
    try:
        return resolved.relative_to(Path(repo_root).resolve()).as_posix()
    except Exception:
        return resolved.as_posix()


def _strongest_subject_confidence(subject: ContractSubject) -> Optional[str]:
    priority = {"high": 3, "medium": 2, "low": 1}
    strongest: Optional[str] = None
    best = 0
    for source in list(getattr(subject, "contract_sources", ()) or ()):
        confidence = str(getattr(source, "confidence", "") or "").strip().lower()
        score = priority.get(confidence, 0)
        if score > best:
            strongest = confidence
            best = score
    return strongest


def _typescript_ineligibility_hint(subject: ContractSubject) -> Optional[str]:
    symbol_kind = str(getattr(subject, "symbol_kind", "") or "").strip().lower()
    metadata = dict(getattr(subject, "metadata", {}) or {})
    if symbol_kind in {"interface", "type_alias"}:
        return "Data-contract evidence is advisory-only and does not independently qualify for function-level preview."
    if str(metadata.get("schema_source_kind") or "").strip() in {"z.object", "z.enum"}:
        return "Zod evidence is advisory-only and does not independently qualify for function-level preview."
    return None


def _infer_file_path_from_contract(contract: FunctionContract) -> str:
    qualified_name = str(getattr(contract, "qualified_name", "") or "").strip()
    if not qualified_name:
        return ""
    parts = [item for item in qualified_name.split(".") if item]
    if not parts:
        return ""
    if bool(getattr(contract, "is_method", False)) and len(parts) >= 3:
        module_parts = parts[:-2]
    else:
        module_parts = parts[:-1]
    if not module_parts:
        return ""
    return f"{'/'.join(module_parts)}.py"


def _is_typescript_target(contract: FunctionContract) -> bool:
    ident = str(getattr(contract, "id", "") or "").strip().lower()
    if ident.startswith("typescript:"):
        return True
    file_path = str(getattr(contract, "file_path", "") or "").strip().lower()
    return file_path.endswith(".ts")

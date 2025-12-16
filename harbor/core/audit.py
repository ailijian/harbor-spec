from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional, Literal, List
from dotenv import load_dotenv
try:
    from openai import OpenAI  # type: ignore
except Exception:
    OpenAI = None  # type: ignore

from harbor.adapters.python.parser import FunctionContract, PythonAdapter
from harbor.core.utils import find_function_node


@dataclass
class AuditResult:
    status: Literal["OK", "MISMATCH", "ERROR"]
    reason: Optional[str]
    provider: str
    func_id: str


class LLMProvider:
    name: str

    def infer(self, prompt: str) -> str:  # type: ignore[override]
        raise NotImplementedError


class MockProvider(LLMProvider):
    name = "mock"

    def infer(self, prompt: str) -> str:
        return "[OK]"


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, api_key: str, base_url: str, model: str) -> None:
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
            )
            txt = (resp.choices[0].message.content or "").strip()
            return txt or "[ERROR]: empty response"
        except Exception as e:
            return f"[ERROR]: {str(e)}"


def resolve_provider() -> LLMProvider:
    load_dotenv()
    prov = (os.getenv("HARBOR_LLM_PROVIDER") or "mock").strip().lower()
    if prov == "openai":
        api_key = os.getenv("HARBOR_LLM_API_KEY") or ""
        base_url = os.getenv("HARBOR_LLM_BASE_URL") or "https://api.openai.com/v1"
        model = os.getenv("HARBOR_LLM_MODEL") or "gpt-4o-mini"
        if not api_key:
            return MockProvider()
        try:
            return OpenAIProvider(api_key=api_key, base_url=base_url, model=model)
        except Exception:
            return MockProvider()
    return MockProvider()


class SemanticGuard:
    def build_prompt(self, contract: FunctionContract, source_code: str) -> str:
        doc = contract.docstring or ""
        lines = source_code.replace("\r\n", "\n").strip()
        return (
            "You are a code auditor. Check if the implementation matches the docstring contract.\n"
            "Docstring:\n"
            f"{doc}\n"
            "Code:\n"
            f"{lines}\n"
            "Focus on: Args, Returns, Raises.\n"
            "If mismatch, output [MISMATCH]: reason. Else output [OK]."
        )

    def audit(self, contract: FunctionContract, source_text: str, provider: LLMProvider) -> AuditResult:
        node = find_function_node(source_text, contract.lineno, contract.name)
        code_seg = ""
        if node is not None:
            try:
                start = getattr(node, "lineno", 0)
                end = getattr(node, "end_lineno", 0)
                lines = source_text.split("\n")
                code_seg = "\n".join(lines[start - 1 : end])
            except Exception:
                code_seg = source_text
        prompt = self.build_prompt(contract, code_seg or source_text)
        try:
            out = provider.infer(prompt).strip()
        except Exception as e:
            return AuditResult(status="ERROR", reason=str(e), provider=provider.name, func_id=contract.id)
        up = out.upper()
        if up.startswith("[MISMATCH]"):
            reason = out.split("]", 1)[1].strip(": ").strip()
            return AuditResult(status="MISMATCH", reason=reason or "mismatch", provider=provider.name, func_id=contract.id)
        if "[OK]" in up:
            return AuditResult(status="OK", reason=None, provider=provider.name, func_id=contract.id)
        return AuditResult(status="ERROR", reason="unrecognized output", provider=provider.name, func_id=contract.id)

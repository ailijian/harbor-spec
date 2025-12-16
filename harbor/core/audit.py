from __future__ import annotations

import os
from dataclasses import dataclass
import json
import re
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
    prompt: Optional[str] = None
    raw_output: Optional[str] = None


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
        except Exception as e:
            return f"[ERROR]: {str(e)}"

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


def resolve_provider() -> LLMProvider:
    load_dotenv()
    prov = (os.getenv("HARBOR_LLM_PROVIDER") or "mock").strip().lower()
    if prov != "mock":
        api_key = os.getenv("HARBOR_LLM_API_KEY") or ""
        base_url = os.getenv("HARBOR_LLM_BASE_URL") or "https://api.openai.com/v1"
        model = os.getenv("HARBOR_LLM_MODEL") or "gpt-4o-mini"
        if not api_key:
            return MockProvider()
        try:
            return OpenAIProvider(provider_name=prov, api_key=api_key, base_url=base_url, model=model)
        except Exception:
            return MockProvider()
    return MockProvider()


class SemanticGuard:
    def build_prompt(self, contract: FunctionContract, source_code: str) -> str:
        doc = contract.docstring or ""
        lines = source_code.replace("\r\n", "\n").strip()
        lang = (os.getenv("HARBOR_LANGUAGE") or "en").strip().lower()
        tmpl = PROMPT_TEMPLATES.get(lang, PROMPT_TEMPLATES["en"])
        return tmpl.format(doc=doc, code=lines)

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
            return AuditResult(status="ERROR", reason=str(e), provider=provider.name, func_id=contract.id, prompt=prompt, raw_output=None)
        try:
            txt = out
            if "```" in txt:
                txt = txt.replace("```json", "").replace("```", "").strip()
            k = txt.find("\"status\"")
            if k != -1:
                s = txt.rfind("{", 0, k)
                e = txt.find("}", k)
                candidate = txt[s : e + 1] if s != -1 and e != -1 and e > s else txt
            else:
                candidate = txt
            obj = json.loads(candidate)
            if isinstance(obj, dict):
                st = str(obj.get("status", "")).strip().upper()
                rs = obj.get("reason")
                if st == "OK":
                    return AuditResult(status="OK", reason=None, provider=provider.name, func_id=contract.id, prompt=prompt, raw_output=out)
                if st == "MISMATCH":
                    return AuditResult(status="MISMATCH", reason=(rs or "mismatch"), provider=provider.name, func_id=contract.id, prompt=prompt, raw_output=out)
                if st == "ERROR":
                    return AuditResult(status="ERROR", reason=(rs or "error"), provider=provider.name, func_id=contract.id, prompt=prompt, raw_output=out)
        except Exception:
            pass
        up = out.upper()
        if up.startswith("[ERROR]"):
            reason = out.split("]", 1)[1].strip(": ").strip()
            return AuditResult(status="ERROR", reason=reason or "error", provider=provider.name, func_id=contract.id, prompt=prompt, raw_output=out)
        if up.startswith("[MISMATCH]"):
            reason = out.split("]", 1)[1].strip(": ").strip()
            return AuditResult(status="MISMATCH", reason=reason or "mismatch", provider=provider.name, func_id=contract.id, prompt=prompt, raw_output=out)
        if "[OK]" in up:
            return AuditResult(status="OK", reason=None, provider=provider.name, func_id=contract.id, prompt=prompt, raw_output=out)
        return AuditResult(status="ERROR", reason="unrecognized output", provider=provider.name, func_id=contract.id, prompt=prompt, raw_output=out)

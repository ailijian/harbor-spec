from __future__ import annotations

import os
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from harbor.core.sync import SyncEngine, StatusEntry
from harbor.core.diary import DiaryManager
from harbor.core.audit import LLMProvider, resolve_provider
from harbor.adapters.python.parser import PythonAdapter, FunctionContract
from harbor.core.utils import find_function_node


class LLMNotConfiguredError(RuntimeError):
    pass


@dataclass
class DraftResult:
    summary: str
    type: str
    importance: str
    details: str


class DiaryDrafter:
    def __init__(
        self,
        sync_engine: Optional[SyncEngine] = None,
        adapter: Optional[PythonAdapter] = None,
        provider: Optional[LLMProvider] = None,
        diary_manager: Optional[DiaryManager] = None,
        max_context_chars: Optional[int] = None,
    ) -> None:
        """AI 辅助生成 Diary 草稿。

        功能:
          - 汇总 Harbor 当前的 Drift/Modified 变更。
          - 提取受影响函数的源码片段，构建上下文。
          - 调用 LLM 生成结构化草稿（summary/type/importance/details）。

        使用场景:
          - CLI `harbor diary draft`。

        依赖:
          - harbor.core.sync.SyncEngine
          - harbor.adapters.python.PythonAdapter
          - harbor.core.audit.LLMProvider
          - harbor.core.diary.DiaryManager

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: read-only

        Args:
          sync_engine: 变更检测引擎实例，缺省自动创建。
          adapter: Python 解析器实例，缺省自动创建。
          provider: LLM 提供者实例，缺省从环境解析。
          diary_manager: 日志管理器实例，缺省自动创建。
        max_context_chars: 上下文截断上限（字符数）。缺省不限制。

        Raises:
          RuntimeError: 当 LLM 未配置或解析失败。
        """
        self.eng = sync_engine or SyncEngine()
        self.adapter = adapter or PythonAdapter()
        self.provider = provider
        self.diary = diary_manager or DiaryManager()
        self.max_context_chars = max_context_chars
        self.last_prompt: Optional[str] = None
        self.last_output: Optional[str] = None

    def generate_draft(self, limit: Optional[int] = None) -> Optional[Dict]:
        rep = self.eng.check_status()
        targets: List[StatusEntry] = []
        targets.extend(rep.drift)
        targets.extend(rep.modified)
        if not targets:
            return None
        prov = self.provider or resolve_provider()
        if getattr(prov, "name", "mock") == "mock":
            raise LLMNotConfiguredError("LLM 未配置。请设置 HARBOR_LLM_PROVIDER 与 HARBOR_LLM_API_KEY 后重试。")
        ctx = self._extract_code_context(targets, limit=limit)
        prompt = self._build_prompt(ctx)
        self.last_prompt = prompt
        out = prov.infer(prompt).strip()
        self.last_output = out
        obj = self._safe_json_parse(out)
        if not isinstance(obj, dict):
            obj = self._kv_fallback_parse(out)
        if not isinstance(obj, dict):
            raise RuntimeError("AI 输出不可解析为 JSON。")
        summary = str(obj.get("summary", "")).strip()
        typ = str(obj.get("type", "")).strip()
        imp = str(obj.get("importance", "")).strip()
        details = str(obj.get("details", "")).strip()
        if not summary:
            raise RuntimeError("AI 输出缺少 summary。")
        if not typ:
            typ = "chore"
        if not imp:
            imp = "normal"
        return {"summary": summary, "type": typ, "importance": imp, "details": details}

    def _extract_code_context(self, entries: List[StatusEntry], limit: Optional[int] = None) -> str:
        parts: List[str] = []
        total = 0
        max_chars = self.max_context_chars if limit is None else limit
        for e in entries:
            fp = Path(e.file_path)
            try:
                src = fp.read_text(encoding="utf-8")
            except Exception:
                continue
            contracts = list(self.adapter.parse_file(e.file_path))
            matched: Optional[FunctionContract] = None
            for fc in contracts:
                if fc.id == e.id:
                    matched = fc
                    break
            seg = ""
            if matched is not None:
                node = find_function_node(src, matched.lineno, matched.name)
                if node is not None:
                    start = getattr(node, "lineno", 1)
                    end = getattr(node, "end_lineno", None)
                    lines = src.replace("\r\n", "\n").split("\n")
                    if isinstance(end, int) and end >= start:
                        seg = "\n".join(lines[start - 1 : end])
                    else:
                        seg = "\n".join(lines[start - 1 :])
                else:
                    seg = src
            else:
                seg = src
            trimmed = self._trim_segment(seg, limit=2000)
            header = f"### file: {e.file_path}\n### func: {e.id}\n### change: {e.change_type}\n"
            block = f"{header}{trimmed}\n---\n"
            if isinstance(max_chars, int):
                if total + len(block) > max_chars:
                    parts.append(block[: max(0, max_chars - total)])
                    break
            parts.append(block)
            total += len(block)
        return "\n".join(parts).strip()

    def _trim_segment(self, code: str, limit: int = 2000) -> str:
        txt = code.strip()
        if len(txt) <= limit:
            return txt
        lines = txt.split("\n")
        head = "\n".join(lines[:20])
        tail = "\n".join(lines[-20:]) if len(lines) > 40 else ""
        return f"{head}\n...\n{tail}".strip()

    def _build_prompt(self, code_context: str) -> str:
        lang = (os.getenv("HARBOR_LANGUAGE") or "zh").strip().lower()
        base = (
            "You are a technical writer for a software project.\n"
            "Analyze the following code changes and generate a structured diary entry.\n\n"
            "Allowed Types: feature, bugfix, refactor, chore, incident\n"
            "Allowed Importance: trivial, normal, high, critical\n"
            "Allowed Visibility: internal, repo, public\n\n"
            "Changes:\n"
            f"{code_context}\n\n"
            "Return ONLY a single strict JSON object with these keys, no code fences, no commentary:\n"
            "- summary: (string, max 50 chars, Chinese)\n"
            "- type: (enum above)\n"
            "- importance: (enum above)\n"
            "- details: (string, markdown supported, explain WHY and WHAT, Chinese)\n"
        )
        if lang == "en":
            base = base.replace("Chinese", "English")
        return base

    def _safe_json_parse(self, text: str) -> Optional[Dict]:
        t = text.strip()
        if "```" in t:
            t = t.replace("```json", "").replace("```", "").strip()
        stack: List[int] = []
        for i, ch in enumerate(t):
            if ch == "{":
                stack.append(i)
            elif ch == "}":
                if stack:
                    st = stack.pop()
                    candidate = t[st : i + 1]
                    try:
                        obj = json.loads(candidate)
                        if isinstance(obj, dict):
                            return obj
                    except Exception:
                        pass
        # fallback: naive slice
        s = t.find("{")
        e = t.rfind("}")
        if s != -1 and e != -1 and e > s:
            candidate = t[s : e + 1]
            try:
                obj = json.loads(candidate)
                if isinstance(obj, dict):
                    return obj
            except Exception:
                # final fallback: convert single quotes to double quotes if it looks like JSON
                cleaned = candidate.replace("'", '"')
                try:
                    obj2 = json.loads(cleaned)
                    if isinstance(obj2, dict):
                        return obj2
                except Exception:
                    return None
        return None

    def _kv_fallback_parse(self, text: str) -> Optional[Dict]:
        lines = [x.strip() for x in text.replace("\r\n", "\n").split("\n") if x.strip()]
        data: Dict[str, str] = {}
        keys = {"summary", "type", "importance", "details"}
        buf_details: List[str] = []
        capturing_details = False
        for ln in lines:
            s = ln
            if capturing_details:
                buf_details.append(s)
                continue
            if ":" in s or "：" in s:
                sep = ":" if ":" in s else "："
                k, v = s.split(sep, 1)
                k2 = k.strip().lower()
                v2 = v.strip().strip("'\"")
                if k2 in keys:
                    if k2 == "details":
                        data[k2] = v2
                        capturing_details = True
                    else:
                        data[k2] = v2
        if buf_details and not data.get("details"):
            data["details"] = "\n".join(buf_details).strip()
        if not data:
            return None
        return data

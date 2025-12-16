from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional

import pytest

from harbor.core.sync import StatusEntry, StatusReport
from harbor.core.drafting import DiaryDrafter, LLMNotConfiguredError
from harbor.core.audit import LLMProvider, MockProvider


@dataclass
class _EngStub:
    rep: StatusReport

    def check_status(self) -> StatusReport:
        return self.rep


class _OKProvider(LLMProvider):
    name = "ok"
    model = "test"

    def infer(self, prompt: str) -> str:
        obj = {
            "summary": "测试草稿",
            "type": "refactor",
            "importance": "normal",
            "details": "这是一条由测试生成的草稿。",
        }
        return json.dumps(obj, ensure_ascii=False)


def _rep_with(entries: List[StatusEntry]) -> StatusReport:
    return StatusReport(drift=entries, modified=entries, contract_changed=[], untracked=[], missing=[], counts={"drift": len(entries), "modified": len(entries), "contract_changed": 0, "untracked": 0, "missing": 0})


def test_generate_draft_returns_none_when_no_changes():
    rep = StatusReport(drift=[], modified=[], contract_changed=[], untracked=[], missing=[], counts={"drift": 0, "modified": 0, "contract_changed": 0, "untracked": 0, "missing": 0})
    eng = _EngStub(rep=rep)
    drafter = DiaryDrafter(sync_engine=eng, provider=_OKProvider())
    assert drafter.generate_draft() is None


def test_raise_when_llm_not_configured(tmp_path: Path):
    f = tmp_path / "foo.py"
    f.write_text("def foo():\n    return 1\n", encoding="utf-8")
    entry = StatusEntry(id="x.foo", name="foo", file_path=f.as_posix(), change_type="Modified", details="Body + Contract changed")
    rep = _rep_with([entry])
    eng = _EngStub(rep=rep)
    with pytest.raises(LLMNotConfiguredError):
        DiaryDrafter(sync_engine=eng, provider=MockProvider()).generate_draft()


def test_generate_draft_parses_json(tmp_path: Path):
    f = tmp_path / "bar.py"
    f.write_text("def bar():\n    return 2\n", encoding="utf-8")
    entry = StatusEntry(id="x.bar", name="bar", file_path=f.as_posix(), change_type="Drift", details="Body changed, Contract static")
    rep = _rep_with([entry])
    eng = _EngStub(rep=rep)
    drafter = DiaryDrafter(sync_engine=eng, provider=_OKProvider())
    res: Optional[Dict] = drafter.generate_draft()
    assert isinstance(res, dict)
    assert res.get("summary") == "测试草稿"
    assert res.get("type") == "refactor"
    assert res.get("importance") == "normal"
    assert "草稿" in (res.get("details") or "")


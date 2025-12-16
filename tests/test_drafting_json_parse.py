from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Dict

from harbor.core.drafting import DiaryDrafter


def _parse(txt: str) -> Optional[Dict]:
    # 访问受保护方法需通过实例
    d = DiaryDrafter()
    return d._safe_json_parse(txt)  # type: ignore


def test_parse_with_code_fence():
    obj = {
        "summary": "围栏JSON",
        "type": "feature",
        "importance": "high",
        "details": "包含代码围栏的返回",
    }
    txt = "```json\n" + json.dumps(obj, ensure_ascii=False) + "\n```"
    res = _parse(txt)
    assert isinstance(res, dict)
    assert res.get("summary") == "围栏JSON"


def test_parse_with_noise_prefix_suffix():
    obj = {
        "summary": "噪声JSON",
        "type": "refactor",
        "importance": "normal",
        "details": "前后噪声",
    }
    raw = json.dumps(obj, ensure_ascii=False)
    txt = "Note: output below\n" + raw + "\nThanks."
    res = _parse(txt)
    assert isinstance(res, dict)
    assert res.get("type") == "refactor"


def test_parse_single_quotes_fallback():
    txt = "{'summary':'单引号','type':'bugfix','importance':'critical','details':'修复'}"
    res = _parse(txt)
    assert isinstance(res, dict)
    assert res.get("importance") == "critical"

def test_kv_fallback_lines_parse():
    from harbor.core.drafting import DiaryDrafter
    d = DiaryDrafter()
    txt = "summary: 行级键值\n type: refactor\n importance: normal\n details: 说明第一行\n后续说明第二行"
    res = d._kv_fallback_parse(txt)  # type: ignore
    assert isinstance(res, dict)
    assert res.get("summary") == "行级键值"
    assert res.get("type") == "refactor"
    assert "说明" in (res.get("details") or "")

def test_nested_brace_with_code_fence():
    obj = {
        "summary": "嵌套包裹",
        "type": "feature",
        "importance": "normal",
        "details": "外层存在多余大括号与代码围栏",
    }
    inner = json.dumps(obj, ensure_ascii=False)
    txt = "{\n```json\n" + inner + "\n```\n"
    res = _parse(txt)
    assert isinstance(res, dict)
    assert res.get("summary") == "嵌套包裹"

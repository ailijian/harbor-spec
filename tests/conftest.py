from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture(autouse=True)
def _isolate_harbor_language_env(monkeypatch):
    """避免外部 CI/发布环境变量污染测试语言分支。"""
    monkeypatch.delenv("HARBOR_LANGUAGE", raising=False)
    monkeypatch.delenv("HARBOR_LANG", raising=False)

import json
import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import pytest

from harbor.cli.main import main


@pytest.fixture(autouse=True)
def _force_en_locale(monkeypatch):
    monkeypatch.setenv("HARBOR_LANGUAGE", "en")


def _write_index(tmp_path: Path) -> None:
    idx = tmp_path / ".harbor" / "cache" / "l3_index.json"
    idx.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "files": {
            "harbor/core/sync.py": {
                "items": [
                    {
                        "id": "harbor.core.sync.SyncEngine.check_status",
                        "qualified_name": "SyncEngine.check_status",
                        "scope": "public",
                        "strictness": "standard",
                    }
                ]
            },
            "harbor/core/l2.py": {
                "items": [
                    {
                        "id": "harbor.core.l2.L2Generator.generate",
                        "qualified_name": "L2Generator.generate",
                        "scope": "public",
                        "strictness": "standard",
                    }
                ]
            },
        }
    }
    idx.write_text(json.dumps(payload), encoding="utf-8")


def run_cmd(argv):
    buf = StringIO()
    with redirect_stdout(buf):
        sys.argv = ["harbor"] + argv
        main()
    return buf.getvalue()


def test_module_promote_skill_is_recognized(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    out = run_cmd(["module", "promote-skill", "harbor/unknown"])
    assert "No indexed records found for module harbor/unknown." in out
    assert "Run harbor module inspect harbor/unknown for details." in out


def test_module_promote_skill_missing_capsule(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    out = run_cmd(["module", "promote-skill", "harbor/core"])
    assert "Module capsule not found for harbor/core." in out
    assert "harbor module seal harbor/core --write" in out
    assert not (tmp_path / ".agents" / "skills").exists()


def test_module_promote_skill_stale_capsule(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    run_cmd(["module", "seal", "harbor/core", "--write"])
    card = tmp_path / "docs" / "harbor" / "modules" / "harbor" / "core" / "module-card.md"
    card.write_text(card.read_text(encoding="utf-8").replace("fingerprint:", "fingerprint: deadbeef"), encoding="utf-8")
    out = run_cmd(["module", "promote-skill", "harbor/core"])
    assert "Module capsule is stale for harbor/core." in out
    assert "harbor module seal harbor/core --write" in out
    assert not (tmp_path / ".agents" / "skills").exists()


def test_module_promote_skill_up_to_date_generates_skill(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    run_cmd(["module", "seal", "harbor/core", "--write"])
    out = run_cmd(["module", "promote-skill", "harbor/core"])
    skill = tmp_path / ".agents" / "skills" / "harbor-debug-harbor-core" / "SKILL.md"
    assert "Generated Skill:" in out
    assert "- .agents/skills/harbor-debug-harbor-core/SKILL.md" in out
    assert "This skill is a thin entrypoint. It references:" in out
    assert "docs/harbor/modules/harbor/core/module-card.md" in out
    assert "docs/harbor/modules/harbor/core/review-checklist.md" in out
    assert "docs/harbor/modules/harbor/core/debug-playbook.md" in out
    assert skill.exists()
    assert not (tmp_path / ".harbor" / "module-map.yaml").exists()

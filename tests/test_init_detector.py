from pathlib import Path
import os

from harbor.core.init import ProjectDetector


def test_gitignore_mapping(tmp_path: Path):
    (tmp_path / ".gitignore").write_text("tmp/\n*.log\n!keep.log\n", encoding="utf-8")
    old = Path.cwd()
    try:
        os.chdir(tmp_path)
        det = ProjectDetector(cwd=tmp_path)
        stacks, roots, excludes = det.detect()
        assert "tmp/**" in excludes
        assert "*.log" in excludes
        assert not any(x.startswith("!keep") for x in excludes)
        assert roots  # fallback present
    finally:
        os.chdir(old)


def test_mixed_stack_rules(tmp_path: Path):
    (tmp_path / "requirements.txt").write_text("flask\n", encoding="utf-8")
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    old = Path.cwd()
    try:
        os.chdir(tmp_path)
        det = ProjectDetector(cwd=tmp_path)
        stacks, roots, excludes = det.detect()
        assert any("Python" in s for s in stacks)
        assert any("Node" in s for s in stacks)
        assert "node_modules/**" in excludes
        assert ".venv/**" in excludes or "venv/**" in excludes
        assert roots  # fallback present
    finally:
        os.chdir(old)


def test_django_detection(tmp_path: Path):
    (tmp_path / "manage.py").write_text("", encoding="utf-8")
    old = Path.cwd()
    try:
        os.chdir(tmp_path)
        det = ProjectDetector(cwd=tmp_path)
        stacks, roots, excludes = det.detect()
        assert any("Django" in s for s in stacks)
        assert any(r in roots for r in ["**/apps", "**/views.py", "**/models.py"])
        assert ".venv/**" in excludes or "venv/**" in excludes
    finally:
        os.chdir(old)


def test_python_project_excludes_do_not_contain_py_globs(tmp_path: Path):
    (tmp_path / "requirements.txt").write_text("pytest\n", encoding="utf-8")
    (tmp_path / ".gitignore").write_text("*.py\n**/*.py\n", encoding="utf-8")
    det = ProjectDetector(cwd=tmp_path)
    _, roots, excludes = det.detect()
    assert "**/*.py" in roots
    assert "*.py" not in excludes
    assert "**/*.py" not in excludes


def test_excludes_do_not_override_code_roots(tmp_path: Path):
    (tmp_path / "go.mod").write_text("module demo\n", encoding="utf-8")
    (tmp_path / ".gitignore").write_text("./**\n", encoding="utf-8")
    det = ProjectDetector(cwd=tmp_path)
    _, roots, excludes = det.detect()
    assert "." in roots
    assert all(x not in excludes for x in ["./**", "**"])
    assert any("overlaps code_roots" in w for w in det.last_warnings)


def test_gitignore_py_pattern_is_skipped_with_warning(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\nversion='0.1.0'\n", encoding="utf-8")
    (tmp_path / ".gitignore").write_text("*.py\n", encoding="utf-8")
    det = ProjectDetector(cwd=tmp_path)
    _, _, excludes = det.detect()
    assert "*.py" not in excludes
    assert any("exclude Python sources" in w for w in det.last_warnings)

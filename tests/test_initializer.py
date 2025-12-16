from pathlib import Path

from harbor.core.init import Initializer


def test_detect_src_layout(tmp_path: Path):
    (tmp_path / "src").mkdir()
    init = Initializer(cwd=tmp_path)
    roots = init.detect_code_roots()
    assert roots == ["src/**"]


def test_detect_package_layout(tmp_path: Path):
    pkg1 = tmp_path / "pkg1"
    pkg2 = tmp_path / "pkg2"
    pkg1.mkdir()
    pkg2.mkdir()
    (pkg1 / "__init__.py").write_text("", encoding="utf-8")
    (pkg2 / "__init__.py").write_text("", encoding="utf-8")
    init = Initializer(cwd=tmp_path)
    roots = sorted(init.detect_code_roots())
    assert roots == ["pkg1/**", "pkg2/**"]


def test_detect_script_layout(tmp_path: Path):
    (tmp_path / "main.py").write_text("print('ok')", encoding="utf-8")
    init = Initializer(cwd=tmp_path)
    roots = init.detect_code_roots()
    assert roots == ["*.py"]


def test_detect_fallback(tmp_path: Path):
    init = Initializer(cwd=tmp_path)
    roots = init.detect_code_roots()
    assert roots == ["**/*.py"]


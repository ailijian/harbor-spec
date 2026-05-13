import os
import subprocess
import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import pytest

import harbor.cli.main as cli_main
from harbor.cli.main import main
from harbor.core.doctor import DoctorCheckResult, DoctorReport, PASS
from harbor.core.stale import ModuleStaleSummary, ViewStaleResult


def run_cmd(argv):
    buf = StringIO()
    with redirect_stdout(buf):
        sys.argv = ["harbor"] + argv
        main()
    return buf.getvalue()


def run_cmd_with_code(argv):
    buf = StringIO()
    code = 0
    with redirect_stdout(buf):
        sys.argv = ["harbor"] + argv
        try:
            main()
        except SystemExit as ex:
            code = ex.code if isinstance(ex.code, int) else 1
    return code, buf.getvalue()


def _write_subprocess_workspace(tmp_path: Path) -> None:
    cfg = tmp_path / ".harbor" / "config" / "harbor.yaml"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text("code_roots:\n- src/**\n- tests/**\nexclude_paths: []\nlanguage: zh\n", encoding="utf-8")

    src_dir = tmp_path / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "app.py").write_text("def run() -> str:\n    return 'ok'\n", encoding="utf-8")


def _run_real_cli(tmp_path: Path, argv):
    repo_root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env["HARBOR_LANGUAGE"] = "zh"
    env.pop("PYTHONIOENCODING", None)
    env.pop("PYTHONUTF8", None)
    env["PYTHONPATH"] = str(repo_root) if not env.get("PYTHONPATH") else str(repo_root) + os.pathsep + env["PYTHONPATH"]
    return subprocess.run(
        [sys.executable, "-X", "utf8=0", "-m", "harbor.cli.main", *argv],
        cwd=tmp_path,
        capture_output=True,
        encoding="utf-8",
        text=True,
        env=env,
        check=False,
    )


def test_env_language_overrides_config(tmp_path: Path):
    cfg_dir = tmp_path / ".harbor"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "config.yaml").write_text(
        "schema_version: '1.0.2'\nprofile: enforce_l3\ncode_roots:\n  - harbor/**\nexclude_paths:\n  - .git/**\nlanguage: en\n",
        encoding="utf-8",
    )
    old = Path.cwd()
    old_env = os.environ.get("HARBOR_LANGUAGE")
    try:
        os.environ["HARBOR_LANGUAGE"] = "zh"
        os.chdir(tmp_path)
        out = run_cmd(["config", "list"])
        assert "Harbor 配置" in out
        assert "language" in out
        assert "en" in out  # 配置仍显示 en，但输出语言为中文
    finally:
        if old_env is None:
            os.environ.pop("HARBOR_LANGUAGE", None)
        else:
            os.environ["HARBOR_LANGUAGE"] = old_env
        os.chdir(old)


def test_env_language_controls_ci_text(monkeypatch):
    monkeypatch.setattr(
        cli_main,
        "check_module_derived_views_stale",
        lambda module: ModuleStaleSummary(
            module=module,
            l2_readme=ViewStaleResult("L2 README", "up_to_date", None, None),
            l2_readme_export=ViewStaleResult("L2 README Export", "up_to_date", None, None),
            module_capsule=ViewStaleResult("Module Capsule", "up_to_date", None, None),
        ),
    )
    monkeypatch.setattr(
        cli_main,
        "build_doctor_report",
        lambda scope, modules: DoctorReport(scope=scope, checks=[DoctorCheckResult("Config / Index", PASS, ["ok"], [])]),
    )

    class _FakeSyncEngine:
        def check_status(self):
            return type(
                "StatusReport",
                (),
                {"drift": [], "modified": [], "contract_changed": [], "untracked": [], "missing": [], "counts": {}},
            )()

    class _FakeDDTScanner:
        def scan_tests(self):
            return []

    class _FakeDDTValidator:
        def validate(self, bindings):
            return type("DDTReport", (), {"valid": [], "violations": [], "counts": {}})()

    monkeypatch.setattr(cli_main, "SyncEngine", _FakeSyncEngine)
    monkeypatch.setattr(cli_main, "DDTScanner", _FakeDDTScanner)
    monkeypatch.setattr(cli_main, "DDTValidator", _FakeDDTValidator)

    monkeypatch.setenv("HARBOR_LANGUAGE", "zh")
    _, zh_checkpoint = run_cmd_with_code(["checkpoint", "--ci"])
    _, zh_stale = run_cmd_with_code(["stale", "--module", "harbor/core", "--ci"])
    _, zh_doctor = run_cmd_with_code(["doctor", "--module", "harbor/core", "--ci"])
    zh_text = "\n".join([zh_checkpoint, zh_stale, zh_doctor])
    assert "CI 模式已启用" in zh_text
    assert "CI 门禁：" in zh_text
    assert "建议下一步：" in zh_text

    monkeypatch.setenv("HARBOR_LANGUAGE", "en")
    _, en_checkpoint = run_cmd_with_code(["checkpoint", "--ci"])
    _, en_stale = run_cmd_with_code(["stale", "--module", "harbor/core", "--ci"])
    _, en_doctor = run_cmd_with_code(["doctor", "--module", "harbor/core", "--ci"])
    en_text = "\n".join([en_checkpoint, en_stale, en_doctor])
    assert "CI mode enabled" in en_text
    assert "CI gate" in en_text
    assert "Suggested next steps" in en_text


@pytest.mark.skipif(os.name != "nt", reason="Windows-specific CLI encoding behavior")
def test_real_cli_stale_zh_subprocess_output_is_utf8_readable(tmp_path: Path):
    _write_subprocess_workspace(tmp_path)

    proc = _run_real_cli(tmp_path, ["stale", "--module", "harbor/core"])

    assert proc.returncode == 0
    assert "Traceback" not in proc.stderr
    assert "Harbor 过期检查" in proc.stdout
    assert "模块：harbor/core" in proc.stdout
    assert "未知" in proc.stdout
    assert "原因:" in proc.stdout


@pytest.mark.skipif(os.name != "nt", reason="Windows-specific CLI encoding behavior")
def test_real_cli_doctor_zh_subprocess_output_is_utf8_readable(tmp_path: Path):
    _write_subprocess_workspace(tmp_path)

    proc = _run_real_cli(tmp_path, ["doctor", "--module", "harbor/core"])

    assert proc.returncode == 0
    assert "Traceback" not in proc.stderr
    assert "Harbor Doctor" in proc.stdout
    assert "模块：harbor/core" in proc.stdout
    assert "工作区状态" in proc.stdout

import json
import os
import shutil
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


def _contains_cjk(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def _with_repo_pythonpath(env):
    updated = dict(env)
    existing = updated.get("PYTHONPATH")
    repo_root = str(REPO_ROOT)
    updated["PYTHONPATH"] = repo_root if not existing else repo_root + os.pathsep + existing
    return updated


@lru_cache(maxsize=1)
def _require_windows_powershell_51() -> str:
    if sys.platform != "win32":
        pytest.skip("Windows PowerShell 5.1 regression coverage only runs on Windows")

    powershell = shutil.which("powershell.exe") or shutil.which("powershell")
    if not powershell:
        pytest.skip("powershell.exe is not available")

    probe = subprocess.run(
        [powershell, "-NoProfile", "-NonInteractive", "-Command", "$PSVersionTable.PSVersion.ToString()"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    version = probe.stdout.strip()
    if not version.startswith("5.1"):
        pytest.skip(f"Expected Windows PowerShell 5.1, got {version or 'unknown'}")
    return powershell


@lru_cache(maxsize=None)
def _cached_canonical_json_payload(command: tuple[str, ...], require_cjk: bool):
    env = _with_repo_pythonpath(os.environ)
    env["HARBOR_LANGUAGE"] = "zh"
    env["PYTHONIOENCODING"] = "utf-8"
    env.pop("PYTHONUTF8", None)
    proc = subprocess.run(
        [sys.executable, "-m", "harbor.cli.main", *command],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=False,
    )
    payload = json.loads(proc.stdout)
    if require_cjk:
        assert _contains_cjk(proc.stdout)
    return proc.returncode, payload


def _canonical_json_payload(command, *, require_cjk: bool):
    return _cached_canonical_json_payload(tuple(command), require_cjk)


def _ps_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _run_powershell_json_capture_cases(cases, tmp_path: Path):
    powershell = _require_windows_powershell_51()
    env = _with_repo_pythonpath(os.environ)
    env["HARBOR_LANGUAGE"] = "zh"
    env.pop("PYTHONIOENCODING", None)
    env["PYTHONUTF8"] = "0"

    script_blocks = []
    result_paths = {}
    for index, case in enumerate(cases):
        name = case["name"]
        mode = case["mode"]
        command = case["command"]
        normalized_path = tmp_path / f"{name}-normalized.json"
        raw_path = tmp_path / f"{name}-raw.json"
        exit_code_path = tmp_path / f"{name}-exit-code.txt"
        result_paths[name] = {
            "normalized": normalized_path,
            "exit_code": exit_code_path,
            "require_cjk": case["require_cjk"],
        }
        quoted_command = ", ".join(_ps_quote(item) for item in [sys.executable, "-m", "harbor.cli.main", *command])
        quoted_normalized = _ps_quote(str(normalized_path))
        quoted_raw = _ps_quote(str(raw_path))
        quoted_exit_code = _ps_quote(str(exit_code_path))
        save_text = (
            f"[System.IO.File]::WriteAllText({quoted_normalized}, $text, "
            "[System.Text.UTF8Encoding]::new($false))"
        )
        script_blocks.append(
            f"""
$cmd{index} = @({quoted_command})
if ({_ps_quote(mode)} -eq 'direct') {{
    $text = [string]::Join("`n", @(& $cmd{index}[0] $cmd{index}[1..($cmd{index}.Length - 1)]))
}} elseif ({_ps_quote(mode)} -eq 'redirect') {{
    & $cmd{index}[0] $cmd{index}[1..($cmd{index}.Length - 1)] > {quoted_raw}
    $text = Get-Content -Path {quoted_raw} -Raw
}} elseif ({_ps_quote(mode)} -eq 'out-file') {{
    & $cmd{index}[0] $cmd{index}[1..($cmd{index}.Length - 1)] | Out-File -FilePath {quoted_raw} -Encoding utf8
    $text = Get-Content -Path {quoted_raw} -Raw
}} else {{
    throw "unsupported mode: {mode}"
}}
$exitCode = $LASTEXITCODE
$null = $text | ConvertFrom-Json
Set-Content -Path {quoted_exit_code} -Value $exitCode -Encoding ascii
{save_text}
"""
        )
    script = f"""
$ErrorActionPreference = 'Stop'
$enc = [System.Text.Encoding]::GetEncoding(936)
$OutputEncoding = $enc
try {{ [Console]::OutputEncoding = $enc }} catch {{}}
try {{ [Console]::InputEncoding = $enc }} catch {{}}
chcp 936 > $null
{"".join(script_blocks)}
"""
    subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    results = {}
    for name, paths in result_paths.items():
        normalized_text = paths["normalized"].read_text(encoding="utf-8")
        if paths["require_cjk"]:
            assert _contains_cjk(normalized_text)
        exit_code = int(paths["exit_code"].read_text(encoding="ascii").strip())
        results[name] = (exit_code, json.loads(normalized_text))
    return results


def test_windows_powershell_51_checkpoint_json_round_trip(tmp_path: Path):
    command = ["checkpoint", "--ci", "--format", "json"]
    cases = [
        {"name": "checkpoint-direct", "mode": "direct", "command": command, "require_cjk": True},
        {"name": "checkpoint-redirect", "mode": "redirect", "command": command, "require_cjk": True},
        {"name": "checkpoint-out-file", "mode": "out-file", "command": command, "require_cjk": True},
    ]
    expected = _canonical_json_payload(command, require_cjk=True)
    results = _run_powershell_json_capture_cases(cases, tmp_path)
    assert results["checkpoint-direct"] == expected
    assert results["checkpoint-redirect"] == expected
    assert results["checkpoint-out-file"] == expected


def test_windows_powershell_51_ci_json_gate_commands_round_trip(tmp_path: Path):
    stale_command = ["stale", "--ci", "--format", "json"]
    doctor_command = ["doctor", "--ci", "--format", "json"]
    cases = [
        {"name": "stale-direct", "mode": "direct", "command": stale_command, "require_cjk": False},
        {"name": "doctor-direct", "mode": "direct", "command": doctor_command, "require_cjk": False},
    ]
    results = _run_powershell_json_capture_cases(cases, tmp_path)
    assert results["stale-direct"] == _canonical_json_payload(stale_command, require_cjk=False)
    assert results["doctor-direct"] == _canonical_json_payload(doctor_command, require_cjk=False)

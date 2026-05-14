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


def _read_case_diagnostic(path: Path) -> dict:
    if not path.exists():
        return {"diagnostic_missing": True, "diagnostic_path": str(path)}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:  # pragma: no cover - defensive diagnostics path
        return {
            "diagnostic_path": str(path),
            "diagnostic_read_error": str(exc),
            "diagnostic_raw": path.read_text(encoding="utf-8-sig", errors="replace"),
        }


def _format_case_diagnostic(paths: dict) -> str:
    return json.dumps(_read_case_diagnostic(paths["diagnostic"]), ensure_ascii=False, indent=2)


def _all_case_diagnostics(result_paths: dict) -> str:
    payload = {
        name: _read_case_diagnostic(paths["diagnostic"])
        for name, paths in result_paths.items()
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _full_stderr_from_paths(paths: dict) -> str:
    diagnostic = _read_case_diagnostic(paths["diagnostic"])
    stderr_full_text = diagnostic.get("stderr_full_text", "")
    return stderr_full_text if isinstance(stderr_full_text, str) else str(stderr_full_text)


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
        stderr_path = tmp_path / f"{name}-stderr.txt"
        diagnostic_path = tmp_path / f"{name}-diagnostic.json"
        exit_code_path = tmp_path / f"{name}-exit-code.txt"
        result_paths[name] = {
            "normalized": normalized_path,
            "raw": raw_path,
            "stderr": stderr_path,
            "diagnostic": diagnostic_path,
            "exit_code": exit_code_path,
            "require_cjk": case["require_cjk"],
        }
        quoted_command = ", ".join(_ps_quote(item) for item in [sys.executable, "-m", "harbor.cli.main", *command])
        quoted_normalized = _ps_quote(str(normalized_path))
        quoted_raw = _ps_quote(str(raw_path))
        quoted_stderr = _ps_quote(str(stderr_path))
        quoted_diagnostic = _ps_quote(str(diagnostic_path))
        quoted_exit_code = _ps_quote(str(exit_code_path))
        script_blocks.append(
            f"""
$cmd{index} = @({quoted_command})
$text = $null
$nativeExitCode = $null
$nativeSuccess = $false
$textForWrite = ""
$previousErrorActionPreference = $ErrorActionPreference
Remove-Item -LiteralPath {quoted_raw}, {quoted_stderr}, {quoted_normalized}, {quoted_diagnostic}, {quoted_exit_code} -Force -ErrorAction SilentlyContinue
try {{
    $ErrorActionPreference = 'Continue'
    if ({_ps_quote(mode)} -eq 'direct') {{
        $text = [string]::Join("`n", @(& $cmd{index}[0] $cmd{index}[1..($cmd{index}.Length - 1)] 2> {quoted_stderr}))
        $nativeExitCode = $LASTEXITCODE
        $nativeSuccess = $?
    }} elseif ({_ps_quote(mode)} -eq 'redirect') {{
        & $cmd{index}[0] $cmd{index}[1..($cmd{index}.Length - 1)] > {quoted_raw} 2> {quoted_stderr}
        $nativeExitCode = $LASTEXITCODE
        $nativeSuccess = $?
        $text = Get-Content -LiteralPath {quoted_raw} -Raw -ErrorAction SilentlyContinue
    }} elseif ({_ps_quote(mode)} -eq 'out-file') {{
        & $cmd{index}[0] $cmd{index}[1..($cmd{index}.Length - 1)] 2> {quoted_stderr} | Out-File -FilePath {quoted_raw} -Encoding utf8
        $nativeExitCode = $LASTEXITCODE
        $nativeSuccess = $?
        $text = Get-Content -LiteralPath {quoted_raw} -Raw -ErrorAction SilentlyContinue
    }} else {{
        throw "unsupported mode: {mode}"
    }}
}} finally {{
    $ErrorActionPreference = $previousErrorActionPreference
}}
$textForWrite = if ($null -eq $text) {{ "" }} else {{ [string]$text }}
if ({_ps_quote(mode)} -eq 'direct') {{
    [System.IO.File]::WriteAllText({quoted_raw}, $textForWrite, [System.Text.UTF8Encoding]::new($false))
}}
$rawExists = Test-Path -LiteralPath {quoted_raw}
$rawLength = if ($rawExists) {{ [System.IO.FileInfo]::new({quoted_raw}).Length }} else {{ 0 }}
$rawHeadHex = if ($rawExists -and $rawLength -gt 0) {{
    $rawBytes = [System.IO.File]::ReadAllBytes({quoted_raw})
    $rawCount = [Math]::Min(128, $rawBytes.Length)
    [System.BitConverter]::ToString($rawBytes[0..($rawCount - 1)])
}} else {{
    ""
}}
$stderrExists = Test-Path -LiteralPath {quoted_stderr}
$stderrLength = if ($stderrExists) {{ [System.IO.FileInfo]::new({quoted_stderr}).Length }} else {{ 0 }}
$stderrPreview = if ($stderrExists) {{
    $stderrText = Get-Content -LiteralPath {quoted_stderr} -Raw -ErrorAction SilentlyContinue
    if ($null -eq $stderrText) {{
        ""
    }} else {{
        $stderrText.Substring(0, [Math]::Min(240, $stderrText.Length))
    }}
}} else {{
    ""
}}
$stderrFullText = if ($stderrExists) {{
    $stderrText = Get-Content -LiteralPath {quoted_stderr} -Raw -ErrorAction SilentlyContinue
    if ($null -eq $stderrText) {{
        ""
    }} else {{
        $stderrText.Substring(0, [Math]::Min(20000, $stderrText.Length))
    }}
}} else {{
    ""
}}
$textIsNull = $null -eq $text
$textLength = if ($textIsNull) {{ 0 }} else {{ $text.Length }}
$textPreview = if ($textIsNull) {{
    ""
}} else {{
    $text.Substring(0, [Math]::Min(120, $text.Length))
}}
$convertFromJsonOk = $false
$convertFromJsonError = ""
try {{
    $null = $text | ConvertFrom-Json
    $convertFromJsonOk = $true
}} catch {{
    $convertFromJsonError = $_.Exception.Message
}}
$diagnostic = [ordered]@{{
    case_name = {_ps_quote(name)}
    mode = {_ps_quote(mode)}
    native_exit_code = $nativeExitCode
    native_success = $nativeSuccess
    raw_exists = $rawExists
    raw_length = $rawLength
    raw_head_hex = $rawHeadHex
    stderr_exists = $stderrExists
    stderr_length = $stderrLength
    stderr_preview = $stderrPreview
    stderr_full_text = $stderrFullText
    text_is_null = $textIsNull
    text_length = $textLength
    text_preview = $textPreview
    convert_from_json_ok = $convertFromJsonOk
    convert_from_json_error = $convertFromJsonError
}}
[System.IO.File]::WriteAllText(
    {quoted_diagnostic},
    ($diagnostic | ConvertTo-Json -Depth 4),
    [System.Text.UTF8Encoding]::new($false)
)
[System.IO.File]::WriteAllText({quoted_normalized}, $textForWrite, [System.Text.UTF8Encoding]::new($false))
Set-Content -LiteralPath {quoted_exit_code} -Value ([string]$nativeExitCode) -Encoding ascii
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
    proc = subprocess.run(
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
        check=False,
    )
    if proc.returncode != 0:
        pytest.fail(
            "PowerShell capture script failed.\n"
            f"returncode={proc.returncode}\n"
            f"stdout:\n{proc.stdout}\n"
            f"stderr:\n{proc.stderr}\n"
            f"diagnostics:\n{_all_case_diagnostics(result_paths)}"
        )
    results = {}
    for name, paths in result_paths.items():
        normalized_text = paths["normalized"].read_text(encoding="utf-8")
        diagnostic_message = _format_case_diagnostic(paths)
        full_stderr = _full_stderr_from_paths(paths)
        if not normalized_text:
            pytest.fail(
                f"{name} produced empty normalized text.\n"
                f"Diagnostic JSON:\n{diagnostic_message}\n"
                f"Full stderr:\n{full_stderr}"
            )
        if paths["require_cjk"]:
            assert _contains_cjk(normalized_text), (
                f"{name} normalized text missing CJK characters.\n"
                f"Diagnostic JSON:\n{diagnostic_message}\n"
                f"Full stderr:\n{full_stderr}"
            )
        exit_code = int(paths["exit_code"].read_text(encoding="ascii").strip())
        try:
            payload = json.loads(normalized_text)
        except json.JSONDecodeError as exc:
            pytest.fail(
                f"{name} normalized text failed json.loads(): {exc}\n"
                f"Diagnostic JSON:\n{diagnostic_message}\n"
                f"Full stderr:\n{full_stderr}"
            )
        results[name] = (exit_code, payload)
    return results


def test_windows_powershell_51_checkpoint_json_round_trip(tmp_path: Path):
    command = ["checkpoint", "--ci", "--format", "json"]
    # GitHub Windows runner 的 host encoding 可能无法直接承载本地化 JSON 文本；
    # 阻断断言聚焦于 redirect / out-file round-trip 后的 payload 等价性，而不是原始文本必须含 CJK。
    cases = [
        {"name": "checkpoint-redirect", "mode": "redirect", "command": command, "require_cjk": False},
        {"name": "checkpoint-out-file", "mode": "out-file", "command": command, "require_cjk": False},
    ]
    expected = _canonical_json_payload(command, require_cjk=True)
    results = _run_powershell_json_capture_cases(cases, tmp_path)
    assert results["checkpoint-redirect"] == expected
    assert results["checkpoint-out-file"] == expected


def test_windows_powershell_51_ci_json_gate_commands_round_trip(tmp_path: Path):
    stale_command = ["stale", "--ci", "--format", "json"]
    doctor_command = ["doctor", "--ci", "--format", "json"]
    cases = [
        {"name": "stale-redirect", "mode": "redirect", "command": stale_command, "require_cjk": False},
        {"name": "doctor-redirect", "mode": "redirect", "command": doctor_command, "require_cjk": False},
    ]
    results = _run_powershell_json_capture_cases(cases, tmp_path)
    assert results["stale-redirect"] == _canonical_json_payload(stale_command, require_cjk=False)
    assert results["doctor-redirect"] == _canonical_json_payload(doctor_command, require_cjk=False)

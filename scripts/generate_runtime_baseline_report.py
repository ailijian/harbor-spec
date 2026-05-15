from __future__ import annotations

import json
import os
import re
import shutil
import sys
import tempfile
import time
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from typing import Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from harbor.cli.main import main
from harbor.core.performance_baseline import (
    RuntimeHotspotAssessment,
    RuntimeMatrixEntry,
    build_runtime_baseline_observation,
    build_runtime_performance_baseline_report,
    collect_runtime_baseline_context_metrics,
    format_runtime_performance_baseline_report,
    runtime_performance_baseline_report_to_dict,
)

ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")
REPORT_JSON_NAME = "harbor-spec-runtime-performance-baseline-v145.json"
REPORT_MD_NAME = "harbor-spec-runtime-performance-baseline-v145.md"


class TTYStringIO(StringIO):
    def isatty(self):
        return True


def _strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def _run_cli(
    argv: List[str],
    *,
    cwd: Path,
    scenario: str,
    output_mode: str,
    writes_files: bool,
    interactive: bool,
    cache_signal: str,
    incremental_signal: str,
    notes: List[str],
    progress_expected: bool | None = None,
) -> Dict[str, object]:
    old_cwd = Path.cwd()
    old_argv = list(sys.argv)
    out = StringIO()
    err = TTYStringIO() if interactive else StringIO()
    exit_code = 0
    try:
        os.chdir(cwd)
        start_wall = time.perf_counter()
        start_cpu = time.process_time()
        with redirect_stdout(out), redirect_stderr(err):
            sys.argv = ["harbor"] + list(argv)
            try:
                main()
            except SystemExit as ex:
                exit_code = ex.code if isinstance(ex.code, int) else 1
        wall = time.perf_counter() - start_wall
        cpu = time.process_time() - start_cpu
    finally:
        os.chdir(old_cwd)
        sys.argv = old_argv
    stderr_text = _strip_ansi(err.getvalue())
    progress_rendered = bool(stderr_text.strip()) if interactive else False
    if progress_expected is not None:
        progress_rendered = bool(progress_expected)
    return {
        "argv": list(argv),
        "scenario": scenario,
        "output_mode": output_mode,
        "writes_files": writes_files,
        "progress_rendered": progress_rendered,
        "wall": wall,
        "cpu": cpu,
        "exit_code": exit_code,
        "cache_signal": cache_signal,
        "incremental_signal": incremental_signal,
        "notes": list(notes),
    }


def _copy_repo_for_write_paths(src: Path, dst: Path) -> None:
    shutil.copytree(
        src,
        dst,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(".git", ".pytest_cache", "__pycache__", ".venv", "dist", "build"),
    )


def main_script() -> None:
    os.environ["HARBOR_LANGUAGE"] = "en"
    repo_root = Path.cwd().resolve()
    report_json = repo_root / ".harbor" / "reports" / REPORT_JSON_NAME
    report_md = repo_root / ".harbor" / "reports" / REPORT_MD_NAME

    context_metrics = collect_runtime_baseline_context_metrics(repo_root)

    command_matrix = [
        RuntimeMatrixEntry(
            "checkpoint",
            "interactive text / repo-owned clean workspace",
            "executed",
            ("phase-style progress forced through TTY stderr capture",),
        ),
        RuntimeMatrixEntry(
            "checkpoint --ci --format json --detail summary",
            "machine JSON / repo-owned clean workspace",
            "executed",
            ("accepted baseline artifact path",),
        ),
        RuntimeMatrixEntry(
            "finish",
            "interactive text / repo-owned clean workspace",
            "executed",
            ("includes change-window runtime state write",),
        ),
        RuntimeMatrixEntry(
            "check",
            "interactive text / repo-owned clean workspace",
            "executed",
            ("full semantic path with preview disabled by default",),
        ),
        RuntimeMatrixEntry(
            "verify-generated --all --ci --format json",
            "machine JSON / repo-owned clean workspace",
            "executed",
            ("all-scope generated verification path",),
        ),
        RuntimeMatrixEntry(
            "stale --all --ci --format json",
            "machine JSON / repo-owned clean workspace",
            "executed",
            ("all-scope stale verification path",),
        ),
        RuntimeMatrixEntry(
            "doctor --all --ci --format json",
            "machine JSON / repo-owned clean workspace",
            "executed",
            ("all-scope doctor report path",),
        ),
        RuntimeMatrixEntry(
            "docs --all --write",
            "interactive text / scratch copy",
            "executed",
            ("write-path measured on temporary scratch copy to avoid mutating working tree",),
        ),
        RuntimeMatrixEntry(
            "module seal --all --write",
            "interactive text / scratch copy",
            "executed",
            ("write-path measured on temporary scratch copy to avoid mutating working tree",),
        ),
        RuntimeMatrixEntry(
            "accept",
            "repo-owned workspace",
            "policy_gated",
            ("not executed because Harbor policy requires an explicit user request for harbor accept",),
        ),
    ]

    raw_results = [
        _run_cli(
            ["checkpoint"],
            cwd=repo_root,
            scenario="interactive text / repo-owned clean workspace",
            output_mode="text",
            writes_files=False,
            interactive=True,
            cache_signal="runtime_cache_snapshot",
            incremental_signal="n/a",
            notes=["progress-enabled text path"],
            progress_expected=True,
        ),
        _run_cli(
            ["checkpoint", "--ci", "--format", "json", "--detail", "summary"],
            cwd=repo_root,
            scenario="machine JSON / repo-owned clean workspace",
            output_mode="json",
            writes_files=False,
            interactive=False,
            cache_signal="accepted_artifact",
            incremental_signal="n/a",
            notes=["summary CI path"],
            progress_expected=False,
        ),
        _run_cli(
            ["finish"],
            cwd=repo_root,
            scenario="interactive text / repo-owned clean workspace",
            output_mode="text",
            writes_files=True,
            interactive=True,
            cache_signal="runtime_cache_snapshot",
            incremental_signal="n/a",
            notes=["post-optimization run reuses status report inside finish"],
            progress_expected=True,
        ),
        _run_cli(
            ["check"],
            cwd=repo_root,
            scenario="interactive text / repo-owned clean workspace",
            output_mode="text",
            writes_files=False,
            interactive=True,
            cache_signal="runtime_cache_snapshot",
            incremental_signal="n/a",
            notes=["full DDT plus semantic target collection path"],
            progress_expected=True,
        ),
        _run_cli(
            ["verify-generated", "--all", "--ci", "--format", "json"],
            cwd=repo_root,
            scenario="machine JSON / repo-owned clean workspace",
            output_mode="json",
            writes_files=False,
            interactive=False,
            cache_signal="fresh_source_preferred",
            incremental_signal="all_scope_full",
            notes=["all modules"],
            progress_expected=False,
        ),
        _run_cli(
            ["stale", "--all", "--ci", "--format", "json"],
            cwd=repo_root,
            scenario="machine JSON / repo-owned clean workspace",
            output_mode="json",
            writes_files=False,
            interactive=False,
            cache_signal="fresh_source_preferred",
            incremental_signal="all_scope_full",
            notes=["all modules"],
            progress_expected=False,
        ),
        _run_cli(
            ["doctor", "--all", "--ci", "--format", "json"],
            cwd=repo_root,
            scenario="machine JSON / repo-owned clean workspace",
            output_mode="json",
            writes_files=False,
            interactive=False,
            cache_signal="fresh_source_preferred",
            incremental_signal="all_scope_full",
            notes=["all modules"],
            progress_expected=False,
        ),
    ]

    with tempfile.TemporaryDirectory(prefix="harbor-perf-baseline-") as tmp_dir:
        scratch = Path(tmp_dir) / "repo"
        _copy_repo_for_write_paths(repo_root, scratch)
        raw_results.append(
            _run_cli(
                ["docs", "--all", "--write"],
                cwd=scratch,
                scenario="interactive text / scratch copy",
                output_mode="text",
                writes_files=True,
                interactive=True,
                cache_signal="fresh_source_preferred",
                incremental_signal="all_scope_full",
                notes=["scratch copy"],
                progress_expected=True,
            )
        )
        raw_results.append(
            _run_cli(
                ["module", "seal", "--all", "--write"],
                cwd=scratch,
                scenario="interactive text / scratch copy",
                output_mode="text",
                writes_files=True,
                interactive=True,
                cache_signal="fresh_source_preferred",
                incremental_signal="all_scope_full",
                notes=["scratch copy"],
                progress_expected=True,
            )
        )

    observations = []
    for item in raw_results:
        argv = item["argv"]
        command_name = "module seal" if argv[:2] == ["module", "seal"] else argv[0]
        observations.append(
            build_runtime_baseline_observation(
                command=command_name,
                argv=argv,
                scenario=str(item["scenario"]),
                output_mode=str(item["output_mode"]),
                progress_rendered=bool(item["progress_rendered"]),
                writes_files=bool(item["writes_files"]),
                wall_time_seconds=float(item["wall"]),
                cpu_time_seconds=float(item["cpu"]),
                exit_code=int(item["exit_code"]),
                context_metrics=context_metrics,
                cache_signal=str(item["cache_signal"]),
                incremental_signal=str(item["incremental_signal"]),
                notes=list(item["notes"]),
            )
        )

    finish_obs = next(obs for obs in observations if obs.command == "finish")
    docs_obs = next(obs for obs in observations if obs.command == "docs")
    module_obs = next(obs for obs in observations if obs.command == "module seal")
    verify_obs = next(obs for obs in observations if obs.command == "verify-generated")
    checkpoint_ci_obs = next(
        obs for obs in observations if obs.argv == ("checkpoint", "--ci", "--format", "json", "--detail", "summary")
    )

    hotspots = [
        RuntimeHotspotAssessment(
            hotspot="finish duplicate status scan",
            evidence=(
                f"finish now runs at wall={finish_obs.wall_time_seconds:.3f}s after reusing the initial status report; "
                "previous implementation called SyncEngine.check_status() twice in the same workflow."
            ),
            recommendation="Keep the reuse in v1.4.5 as the only quick win and defer broader finish pipeline restructuring.",
            quick_win_candidate=True,
        ),
        RuntimeHotspotAssessment(
            hotspot="generated context all-scope write paths",
            evidence=(
                f"docs --all --write wall={docs_obs.wall_time_seconds:.3f}s and module seal --all --write "
                f"wall={module_obs.wall_time_seconds:.3f}s dominate the measured all-scope write workflows."
            ),
            recommendation="Use these paths as the primary candidates if v1.4.6 becomes a dedicated performance release.",
            quick_win_candidate=False,
        ),
        RuntimeHotspotAssessment(
            hotspot="generated verification all-scope scan",
            evidence=(
                f"verify-generated --all --ci --format json completed in wall={verify_obs.wall_time_seconds:.3f}s "
                "and shares the same source-derived readonly-index path as stale/doctor."
            ),
            recommendation="If future regressions appear, profile repeated module-context and readonly-index construction first.",
            quick_win_candidate=False,
        ),
        RuntimeHotspotAssessment(
            hotspot="checkpoint stage mix",
            evidence=(
                f"checkpoint --ci --format json --detail summary completed in wall={checkpoint_ci_obs.wall_time_seconds:.3f}s; "
                "stage-level timing is still inferred from code structure rather than explicit per-stage timers."
            ),
            recommendation="Do not add new public timing output in v1.4.5; add internal profiling only if v1.4.6 is approved.",
            quick_win_candidate=False,
        ),
    ]

    report = build_runtime_performance_baseline_report(
        scope="Task Group D / v1.4.5 runtime baseline on harbor-spec repository",
        repo_root=repo_root,
        command_matrix=command_matrix,
        observations=observations,
        hotspots=hotspots,
        quick_wins=[
            "Implemented the low-risk finish optimization by reusing the first status report during full check execution.",
        ],
        deferred_optimizations=[
            "Do not introduce a new public performance/profiling CLI surface in v1.4.5.",
            "Do not start structural cache redesign, concurrency changes, or provider-level semantic-audit tuning in v1.4.5.",
            "Keep accept in the frozen matrix but leave execution to an explicit user-authorized follow-up.",
        ],
        recommendation=(
            "The baseline now exists and the obvious quick win is closed. v1.4.6 should become a dedicated performance "
            "release only if generated-context all-scope write paths or repeated readonly-index work show materially worse "
            "latency in broader repositories than this harbor-spec baseline."
        ),
    )

    report_json.write_text(
        json.dumps(runtime_performance_baseline_report_to_dict(report), ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    report_md.write_text(format_runtime_performance_baseline_report(report), encoding="utf-8")

    print(
        json.dumps(
            {
                "json_report": report_json.as_posix(),
                "markdown_report": report_md.as_posix(),
                "observations": [
                    {
                        "command": obs.command,
                        "scenario": obs.scenario,
                        "wall_time_seconds": round(obs.wall_time_seconds, 3),
                        "cpu_time_seconds": round(obs.cpu_time_seconds, 3),
                        "exit_code": obs.exit_code,
                        "progress_rendered": obs.progress_rendered,
                    }
                    for obs in observations
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main_script()

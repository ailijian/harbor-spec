from pathlib import Path
from types import SimpleNamespace

from harbor.core import performance_baseline


def test_collect_runtime_baseline_context_metrics_aggregates_repo_counts(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(
        performance_baseline,
        "SyncEngine",
        lambda: SimpleNamespace(
            collect_current_snapshot=lambda: {
                "harbor/cli/main.py": {"a": {}, "b": {}},
                "harbor/core/sync.py": {"c": {}},
            },
            check_status=lambda: SimpleNamespace(),
        ),
    )
    monkeypatch.setattr(
        performance_baseline,
        "collect_all_indexed_modules",
        lambda prefer_fresh_source=False: ["harbor/cli", "harbor/core"],
    )
    monkeypatch.setattr(
        performance_baseline,
        "DDTScanner",
        lambda: SimpleNamespace(scan_tests=lambda: [object(), object(), object()]),
    )
    monkeypatch.setattr(
        performance_baseline,
        "load_workspace_config",
        lambda repo_root: {"config": {"languages": {"typescript": {"enabled": True}}}},
    )
    monkeypatch.setattr(
        performance_baseline,
        "validate_typescript_ddt_preview",
        lambda repo_root, config: SimpleNamespace(bindings_count=4),
    )
    monkeypatch.setattr(
        performance_baseline,
        "build_typescript_semantic_audit_preview",
        lambda repo_root, status_report, config=None: SimpleNamespace(targets_count=5),
    )

    metrics = performance_baseline.collect_runtime_baseline_context_metrics(tmp_path)

    assert metrics.scan_file_count == 2
    assert metrics.indexed_target_count == 3
    assert metrics.module_count == 2
    assert metrics.ddt_binding_count == 3
    assert metrics.preview_binding_count == 4
    assert metrics.preview_audit_target_count == 5


def test_runtime_performance_baseline_report_to_dict_and_markdown():
    context_metrics = performance_baseline.RuntimeBaselineContextMetrics(
        scan_file_count=12,
        indexed_target_count=34,
        module_count=5,
        ddt_binding_count=8,
        preview_binding_count=2,
        preview_audit_target_count=None,
    )
    observation = performance_baseline.build_runtime_baseline_observation(
        command="checkpoint",
        argv=("checkpoint", "--ci", "--format", "json", "--detail", "summary"),
        scenario="repo-owned clean workspace",
        output_mode="json",
        progress_rendered=False,
        writes_files=False,
        wall_time_seconds=0.8123,
        cpu_time_seconds=0.6012,
        exit_code=0,
        context_metrics=context_metrics,
        cache_signal="accepted_artifact",
        incremental_signal="n/a",
        notes=("machine-readable route",),
    )
    report = performance_baseline.build_runtime_performance_baseline_report(
        scope="Task Group D / v1.4.5",
        repo_root=Path("E:/project/harbor-spec"),
        command_matrix=[
            performance_baseline.RuntimeMatrixEntry(
                command="checkpoint --ci --format json --detail summary",
                scenario="repo-owned clean workspace",
                status="executed",
                notes=("summary CI path",),
            ),
            performance_baseline.RuntimeMatrixEntry(
                command="accept",
                scenario="repo-owned workspace",
                status="policy_gated",
                notes=("requires explicit user request",),
            ),
        ],
        observations=[observation],
        hotspots=[
            performance_baseline.RuntimeHotspotAssessment(
                hotspot="finish duplicate status scan",
                evidence="finish called status twice before optimization",
                recommendation="reuse the first status report inside finish",
                quick_win_candidate=True,
            )
        ],
        quick_wins=["Reuse finish status snapshot for semantic-audit target collection."],
        deferred_optimizations=["Do not start structural cache redesign in v1.4.5."],
        recommendation="Use this baseline to decide whether v1.4.6 should become a performance-focused release.",
        generated_at="2026-05-15T14:00:00Z",
    )

    payload = performance_baseline.runtime_performance_baseline_report_to_dict(report)
    rendered = performance_baseline.format_runtime_performance_baseline_report(report)

    assert payload["title"] == "Harbor-spec Runtime Performance Baseline Report"
    assert payload["observations"][0]["cache_signal"] == "accepted_artifact"
    assert payload["command_matrix"][1]["status"] == "policy_gated"
    assert "## Command Matrix" in rendered
    assert "checkpoint" in rendered
    assert "finish duplicate status scan" in rendered

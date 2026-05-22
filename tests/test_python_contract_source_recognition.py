from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import textwrap

from harbor.core.ci import build_checkpoint_ci_result, checkpoint_ci_result_to_dict
from harbor.core.contract_impact import ContractImpactLevel, ContractImpactReport
from harbor.core.index import IndexBuilder
from harbor.core.readonly_index import _load_existing_db_index, load_readonly_index
from harbor.core.sync import SyncEngine


def _write_workspace_config(tmp_path: Path, *, code_root: str) -> None:
    cfg = tmp_path / ".harbor" / "config" / "harbor.yaml"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(
        textwrap.dedent(
            f"""
            code_roots:
              - {code_root}
            exclude_paths: []
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")


def _empty_ddt_report():
    return SimpleNamespace(valid=[], violations=[], advisory=[], counts={"valid": 0, "violations": 0, "advisory": 0})


def _no_contract_impact_report() -> ContractImpactReport:
    return ContractImpactReport(
        level=ContractImpactLevel.NO_CONTRACT_IMPACT,
        categories=[],
        findings=[],
        summary_counts={
            ContractImpactLevel.NO_CONTRACT_IMPACT.value: 0,
            ContractImpactLevel.POSSIBLE_CONTRACT_IMPACT.value: 0,
            ContractImpactLevel.CONFIRMED_CONTRACT_IMPACT.value: 0,
            ContractImpactLevel.UNKNOWN.value: 0,
        },
        notable_findings=[],
    )


def test_python_behavior_docstring_change_is_not_false_drift(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_workspace_config(tmp_path, code_root="backend/**")
    target = tmp_path / "backend" / "app" / "cli.py"
    _write_file(
        target,
        """
        def main(argv=None):
            \"\"\"Execute the CLI entrypoint.

            Behavior:
              - Dispatches the `api` command.

            @harbor.scope: public
            @harbor.l3_strictness: strict
            \"\"\"
            if argv == ["api"]:
                return 0
            return 1
        """,
    )

    engine = SyncEngine()
    baseline_snapshot = engine.collect_current_snapshot()
    baseline_item = baseline_snapshot["backend/app/cli.py"]["backend.app.cli.main"]

    _write_file(
        target,
        """
        def main(argv=None):
            \"\"\"Execute the CLI entrypoint.

            Behavior:
              - Dispatches the `api` command.
              - Dispatches the `worker review-job-segment` command.

            @harbor.scope: public
            @harbor.l3_strictness: strict
            \"\"\"
            if argv == ["api"]:
                return 0
            if argv == ["worker", "review-job-segment"]:
                return 0
            return 1
        """,
    )

    current_snapshot = engine.collect_current_snapshot()
    current_item = current_snapshot["backend/app/cli.py"]["backend.app.cli.main"]
    report = engine.check_status(
        baseline_snapshot=baseline_snapshot,
        baseline_source="accepted_artifact",
    )

    assert baseline_item["contract_hash"] != current_item["contract_hash"]
    assert baseline_item["contract_source_fingerprints"] != current_item["contract_source_fingerprints"]
    assert report.counts["drift"] == 0
    assert report.counts["modified"] == 1
    assert report.modified[0].id == "backend.app.cli.main"


def test_checkpoint_full_json_exposes_python_contract_source_fingerprint(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_workspace_config(tmp_path, code_root="backend/**")
    target = tmp_path / "backend" / "app" / "cli.py"
    _write_file(
        target,
        """
        def main(argv=None):
            \"\"\"Execute the CLI entrypoint.

            Behavior:
              - Dispatches the `api` command.

            @harbor.scope: public
            @harbor.l3_strictness: strict
            \"\"\"
            if argv == ["api"]:
                return 0
            return 1
        """,
    )

    engine = SyncEngine()
    baseline_snapshot = engine.collect_current_snapshot()

    _write_file(
        target,
        """
        def main(argv=None):
            \"\"\"Execute the CLI entrypoint.

            Behavior:
              - Dispatches the `api` command.
              - Dispatches the `worker review-job-segment` command.

            @harbor.scope: public
            @harbor.l3_strictness: strict
            \"\"\"
            if argv == ["api"]:
                return 0
            if argv == ["worker", "review-job-segment"]:
                return 0
            return 1
        """,
    )

    report = engine.check_status(
        baseline_snapshot=baseline_snapshot,
        baseline_source="accepted_artifact",
    )
    payload = checkpoint_ci_result_to_dict(
        build_checkpoint_ci_result(
            status_report=report,
            ddt_report=_empty_ddt_report(),
            contract_impact_report=_no_contract_impact_report(),
            baseline_source="accepted_artifact",
            baseline_path=".harbor/baseline/accepted-checkpoint.json",
            baseline_found=True,
        )
    )

    row = payload["ci_failures"][0]
    assert row["category"] == "contract_and_body_changed"
    assert row["func_id"] == "backend.app.cli.main"
    assert row["contract_source_kinds"] == ["docstring"]
    assert len(row["contract_source_fingerprints"]) == 1


def test_behavior_only_docstring_is_present_in_readonly_index_for_required_python_target(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_workspace_config(tmp_path, code_root="harbor/**")
    _write_file(
        tmp_path / "harbor" / "cli" / "main.py",
        """
        def main(argv=None):
            \"\"\"Execute the CLI entrypoint.

            Behavior:
              - Dispatches the CLI command.
            \"\"\"
            return 0
        """,
    )

    payload = load_readonly_index(repo_root=tmp_path, prefer_fresh_source=True)
    item = payload["files"]["harbor/cli/main.py"]["items"][0]

    assert item["contract_presence"] == "present"
    assert item["contract_required"] is True
    assert item["contract_source_kinds"] == ["docstring"]
    assert len(item["contract_source_fingerprints"]) == 1


def test_python_db_readonly_fallback_keeps_contract_source_metadata(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_workspace_config(tmp_path, code_root="backend/**")
    _write_file(
        tmp_path / "backend" / "app" / "cli.py",
        """
        def main(argv=None):
            \"\"\"Execute the CLI entrypoint.

            Behavior:
              - Dispatches the `api` command.

            @harbor.scope: public
            @harbor.l3_strictness: strict
            \"\"\"
            return 0
        """,
    )

    cache_dir = tmp_path / ".harbor" / "cache"
    builder = IndexBuilder(code_roots=[str(tmp_path / "backend")], cache_dir=cache_dir)
    builder.build(incremental=False)

    payload = _load_existing_db_index(repo_root=tmp_path)
    assert payload is not None
    item = payload["files"]["backend/app/cli.py"]["items"][0]

    assert item["contract_presence"] == "present"
    assert item["contract_required"] is True
    assert item["contract_source_kinds"] == ["docstring"]
    assert len(item["contract_source_fingerprints"]) == 1

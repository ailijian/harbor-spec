from pathlib import Path

import pytest
import yaml

from harbor.core.workspace import (
    HarborWorkspacePaths,
    build_workspace_paths,
    load_workspace_config,
    load_workspace_paths,
    parse_workspace_export_options,
    write_workspace_config,
)
from harbor.core.project_structure import (
    ProjectMetadata,
    ProjectStructureContext,
    write_project_structure,
)


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


def test_default_paths() -> None:
    repo = Path.cwd().resolve()
    paths = build_workspace_paths(repo, config={})
    assert isinstance(paths, HarborWorkspacePaths)
    assert paths.workspace_root == (repo / ".harbor").resolve()
    assert paths.views_root == (repo / ".harbor" / "views").resolve()
    assert paths.project_structure_path == (repo / ".harbor" / "views" / "project-structure.md").resolve()
    assert paths.modules_view_root == (repo / ".harbor" / "views" / "modules").resolve()
    assert paths.l2_view_root == (repo / ".harbor" / "views" / "l2").resolve()
    assert paths.diary_root == (repo / ".harbor" / "diary").resolve()
    assert paths.reports_root == (repo / ".harbor" / "reports").resolve()
    assert paths.state_root == (repo / ".harbor" / "state").resolve()
    assert paths.cache_root == (repo / ".harbor" / "cache").resolve()


def test_new_config_read(tmp_path: Path) -> None:
    new_cfg = tmp_path / ".harbor" / "config" / "harbor.yaml"
    _write_yaml(new_cfg, {"workspace": {"root": ".harbor"}, "views": {"canonical_root": ".harbor/views-new"}})
    _write_yaml(tmp_path / ".harbor" / "config.yaml", {"views": {"canonical_root": ".harbor/views-legacy"}})

    loaded = load_workspace_config(tmp_path)
    assert loaded["source_path"] == new_cfg
    assert loaded["config"]["views"]["canonical_root"] == ".harbor/views-new"

    paths = load_workspace_paths(tmp_path)
    assert paths.views_root == (tmp_path / ".harbor" / "views-new").resolve()


def test_legacy_config_read(tmp_path: Path) -> None:
    legacy_cfg = tmp_path / ".harbor" / "config.yaml"
    _write_yaml(legacy_cfg, {"workspace": {"root": ".harbor-legacy"}, "reports": {"root": ".harbor/reports-legacy"}})

    loaded = load_workspace_config(tmp_path)
    assert loaded["source_path"] == legacy_cfg
    assert loaded["config"]["workspace"]["root"] == ".harbor-legacy"

    paths = load_workspace_paths(tmp_path)
    assert paths.workspace_root == (tmp_path / ".harbor-legacy").resolve()
    assert paths.reports_root == (tmp_path / ".harbor" / "reports-legacy").resolve()


def test_single_write_new_config_target(tmp_path: Path) -> None:
    target = write_workspace_config(tmp_path, {"schema_version": "1.0.2"})
    assert target == (tmp_path / ".harbor" / "config" / "harbor.yaml")
    assert target.exists()
    assert not (tmp_path / ".harbor" / "config.yaml").exists()


def test_export_options_parsing() -> None:
    options = parse_workspace_export_options(
        {
            "views": {"export": {"docs": {"enabled": True, "root": "docs/harbor-export"}}},
            "l2": {"export": {"module_readme": {"enabled": False}}},
        }
    )
    assert options["views"]["docs"]["enabled"] is True
    assert options["views"]["docs"]["root"] == "docs/harbor-export"
    assert options["l2"]["module_readme"]["enabled"] is False


def test_write_path_cannot_escape_repo_root(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="escapes repo root"):
        build_workspace_paths(
            tmp_path,
            config={
                "workspace": {"root": ".harbor"},
                "views": {"canonical_root": "../outside"},
            },
        )


def test_windows_posix_path_normalization(tmp_path: Path) -> None:
    paths = build_workspace_paths(
        tmp_path,
        config={
            "workspace": {"root": r".\.harbor"},
            "views": {"canonical_root": r".\.harbor\views"},
            "reports": {"root": "./.harbor/reports-posix"},
            "state": {"root": ".harbor/state-posix"},
        },
    )
    assert paths.workspace_root == (tmp_path / ".harbor").resolve()
    assert paths.views_root == (tmp_path / ".harbor" / "views").resolve()
    assert paths.reports_root == (tmp_path / ".harbor" / "reports-posix").resolve()
    assert paths.state_root == (tmp_path / ".harbor" / "state-posix").resolve()


def test_project_structure_docs_export_root_cannot_escape_repo_root(tmp_path: Path) -> None:
    cfg = {
        "views": {
            "export": {
                "docs": {
                    "enabled": True,
                    "root": "../outside-docs",
                }
            }
        }
    }
    write_workspace_config(tmp_path, cfg)

    context = ProjectStructureContext(
        metadata=ProjectMetadata(name="harbor-spec", version="1.3.0", description="desc", entrypoint="harbor.cli.main:main"),
        modules=[],
        supporting_areas=[],
        key_areas=[],
        has_indexed_modules=False,
        discovery_mode="filesystem fallback",
        contract_aware="no",
        has_real_index_records=False,
    )

    with pytest.raises(ValueError, match="views.export.docs.root"):
        write_project_structure(context, tmp_path)

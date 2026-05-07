from pathlib import Path
import subprocess

from harbor.core.workspace import build_workspace_paths


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _gitignore_entries() -> set[str]:
    text = (_repo_root() / ".gitignore").read_text(encoding="utf-8")
    entries = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        entries.add(line)
    return entries


def _is_ignored(path: str) -> bool:
    repo = _repo_root()
    result = subprocess.run(
        ["git", "check-ignore", path],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def test_gitignore_does_not_use_broad_harbor_ignore() -> None:
    entries = _gitignore_entries()
    assert ".harbor/" not in entries


def test_gitignore_ignores_required_local_runtime_paths() -> None:
    entries = _gitignore_entries()
    assert ".harbor/state/" in entries
    assert ".harbor/cache/" in entries
    assert ".harbor/exports/" in entries


def test_project_structure_canonical_path_is_harbor_views() -> None:
    repo = _repo_root().resolve()
    paths = build_workspace_paths(repo, config={})
    relative = paths.project_structure_path.relative_to(repo).as_posix()
    assert relative == ".harbor/views/project-structure.md"


def test_docs_design_paths_are_trackable() -> None:
    assert _is_ignored("docs/design/harbor-workspace-layout-v1.md") is False
    assert _is_ignored("docs/design/context-routing-v1.md") is False


def test_docs_harbor_project_structure_remains_non_canonical_export_target() -> None:
    assert _is_ignored("docs/harbor/project-structure.md") is True


def test_harbor_canonical_and_runtime_ignore_policy() -> None:
    assert _is_ignored(".harbor/views/project-structure.md") is False
    assert _is_ignored(".harbor/state/example.json") is True
    assert _is_ignored(".harbor/cache/example.tmp") is True
    assert _is_ignored(".harbor/exports/example.md") is True

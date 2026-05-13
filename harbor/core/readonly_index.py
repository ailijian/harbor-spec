from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict

from harbor.adapters.registry import AdapterRegistry
from harbor.core.index import process_file_worker
from harbor.core.index_entry import index_entry_to_cache_item
from harbor.core.storage import HarborDB
from harbor.core.utils import discover_indexable_files
from harbor.core.workspace import load_workspace_config

_TRANSIENT_INDEX_CACHE: Dict[str, Dict[str, Any]] = {}


def load_readonly_index(
    index_path: Path | None = None,
    *,
    repo_root: Path | None = None,
    prefer_fresh_source: bool = False,
) -> Dict[str, Any]:
    """Load a read-only Harbor index snapshot for analysis paths.

    Behavior:
      - Uses the repo-local runtime cache snapshot when available by default.
      - When `prefer_fresh_source=True`, prefers a transient source-derived scan
        before any runtime cache snapshot so generated-context and stale checks
        can use the same source-of-truth input as clean CI.
      - Generated-context writers and stale validators can use
        `prefer_fresh_source=True` to bypass `.harbor/cache/l3_index.json`
        whenever transient source-derived records are available.
      - Fresh/source fallback remains read-only: it may read cache or database
        snapshots only when source-derived records are unavailable.
      - Remains read-only and never writes cache snapshots or database state.

    Args:
      index_path (Path | None): Optional explicit cache snapshot path.
      repo_root (Path | None): Repository root used for path resolution.
      prefer_fresh_source (bool): Prefer transient source-derived records over
        runtime cache snapshots when possible.

    Returns:
      Dict[str, Any]: JSON-compatible readonly index payload.

    Side Effects:
      - Reads workspace config, source files, or runtime cache state.
      - Writes no files.

    Idempotency:
      - Deterministic for the same repository state and arguments.

    Security:
      - Must not write cache state or mutate source files.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: read-only
    """
    root = (repo_root or Path.cwd()).resolve()
    target = _resolve_index_path(index_path, repo_root=root)
    if prefer_fresh_source:
        transient_payload = _build_transient_index(root)
        if transient_payload.get("files"):
            return transient_payload
        if target.exists():
            try:
                return json.loads(target.read_text(encoding="utf-8"))
            except Exception:
                pass
        db_payload = _load_existing_db_index(repo_root=root)
        if db_payload is not None:
            return db_payload
        return transient_payload
    if target.exists():
        try:
            return json.loads(target.read_text(encoding="utf-8"))
        except Exception:
            pass
    # Prefer a fresh source scan over runtime DB state so CI/view checks do not
    # depend on test-populated caches that are not source of truth.
    transient_payload = _build_transient_index(root)
    if transient_payload.get("files"):
        return transient_payload
    db_payload = _load_existing_db_index(repo_root=root)
    if db_payload is not None:
        return db_payload
    return transient_payload


def _resolve_index_path(index_path: Path | None, *, repo_root: Path) -> Path:
    candidate = Path(index_path) if index_path is not None else (Path(".harbor") / "cache" / "l3_index.json")
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    return candidate.resolve()


def _build_transient_index(repo_root: Path) -> Dict[str, Any]:
    loaded = load_workspace_config(repo_root)
    config = loaded.get("config") or {}
    code_roots = list(config.get("code_roots") or ["**/*.py"])
    exclude_paths = list(config.get("exclude_paths") or [])
    registry = AdapterRegistry.from_config(config)
    cache_key = json.dumps(
        {
            "repo_root": repo_root.as_posix(),
            "code_roots": code_roots,
            "exclude_paths": exclude_paths,
            "enabled_languages": registry.get_enabled_languages(),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    cached = _TRANSIENT_INDEX_CACHE.get(cache_key)
    if cached is not None:
        return copy.deepcopy(cached)

    files: Dict[str, Any] = {}
    for source_path in discover_indexable_files(
        code_roots,
        exclude_paths,
        registry=registry,
        repo_root=repo_root,
    ):
        try:
            rel = source_path.resolve().relative_to(repo_root).as_posix()
        except Exception:
            rel = source_path.resolve().as_posix()
        _, mtime, items, _ = process_file_worker(str(source_path))
        files[rel] = {
            "mtime": mtime,
            "file_hash": "",
            "items": [index_entry_to_cache_item(item) for item in items],
        }

    payload: Dict[str, Any] = {
        "meta": {"schema_version": "1.0.2", "source": "transient_filesystem"},
        "files": files,
    }
    _TRANSIENT_INDEX_CACHE[cache_key] = copy.deepcopy(payload)
    return payload


def _load_existing_db_index(*, repo_root: Path) -> Dict[str, Any] | None:
    db_path = (repo_root / ".harbor" / "cache" / "harbor.db").resolve()
    if not db_path.exists():
        return None

    db = HarborDB(db_path=db_path, project_root=repo_root)
    try:
        files: Dict[str, Any] = {}
        for fp, mtime in db.get_all_files():
            items = []
            for it in db.get_file_entries(fp):
                meta = it.get("meta", {}) or {}
                items.append(
                    {
                        "id": it.get("id"),
                        "qualified_name": meta.get("qualified_name"),
                        "name": meta.get("name"),
                        "signature_hash": it.get("signature_hash"),
                        "body_hash": it.get("body_hash"),
                        "contract_hash": it.get("contract_hash"),
                        "docstring_raw_hash": meta.get("docstring_raw_hash"),
                        "scope": meta.get("scope"),
                        "strictness": meta.get("strictness"),
                        "lineno": meta.get("lineno"),
                    }
                )
            files[fp] = {"mtime": mtime, "file_hash": "", "items": items}
        if not files:
            return None
        return {"meta": {"schema_version": "1.0.2", "source": "existing_harbor_db"}, "files": files}
    finally:
        db.conn.close()

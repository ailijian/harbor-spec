import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, TextColumn, BarColumn, MofNCompleteColumn, TimeElapsedColumn
import json
from rich.panel import Panel
from rich.prompt import Prompt

from harbor.utils.i18n import t, get_lang

from harbor.core.index import IndexBuilder
from harbor.core.sync import SyncEngine
from harbor.core.ddt import DDTScanner, DDTValidator
from harbor.core.l2 import L2Generator, collect_all_indexed_modules, collect_modules_from_paths
from harbor.core.module_capsule import (
    check_module_capsule_stale,
    collect_module_context,
    preview_module_capsule,
    resolve_module_capsule_paths,
    write_module_capsule,
)
from harbor.core.module_skill import (
    check_capsule_ready_for_skill,
    write_module_skill,
)
from harbor.core.project_structure import (
    collect_project_structure_context,
    generate_project_structure_markdown,
    write_project_structure,
)
from harbor.core.stale import (
    check_module_derived_views_stale,
    format_stale_summary,
    stale_report_to_dict,
)
from harbor.core.doctor import (
    build_doctor_report,
    format_doctor_report,
)
from harbor.core.workspace_inspect import (
    build_workspace_inspect_report,
    format_workspace_inspect_report,
    workspace_inspect_report_to_dict,
)
from harbor.core.diary import DiaryManager
from harbor.core.audit import SemanticGuard, resolve_provider
from harbor.core.drafting import DiaryDrafter, LLMNotConfiguredError
from harbor.core.init import Initializer
from harbor.core.decorator import DecoratorEngine
from harbor.core.workspace import load_workspace_config, load_workspace_paths, write_workspace_config


def main():
    """Harbor CLI 入口。

    功能:
      - 提供 `harbor` 命令的子命令入口：`init/status/lock/check/log/adopt/unadopt/docs/config`。
      - 解析参数并委派到对应子系统。
      - adopt：在应用装饰变更后，将接管目录注册到 `.harbor/config.yaml` 的 `code_roots`。
      - unadopt：从 `.harbor/config.yaml` 的 `code_roots` 中移除接管目录。

    使用场景:
      - 开发者在本地与 CI 中调用 Harbor 管理上下文。

    依赖:
      - harbor.core.index.IndexBuilder
      - harbor.core.sync.SyncEngine
      - harbor.core.ddt.DDTScanner/DDTValidator
      - harbor.core.l2.L2Generator
      - harbor.core.diary.DiaryManager
      - harbor.core.audit.SemanticGuard
      - harbor.utils.i18n.t/get_lang

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: once

    Args:
      None

    Returns:
      None

    Raises:
      RuntimeError: 当关键子系统初始化失败时。
    """
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    def _map_argv(argv):
        if not argv:
            return argv, None
        tokens = list(argv)
        dep = None
        if tokens[0] == "build-index":
            tokens[0] = "lock"
            dep = "build-index"
        elif tokens[0] == "audit":
            dep = "audit"
            tokens[0] = "check"
        elif tokens[0] == "diary":
            if len(tokens) >= 2:
                subc = tokens[1]
                dep = f"diary {subc}"
                if subc == "draft":
                    tokens = ["log"] + tokens[2:]
                elif subc == "log":
                    tokens = ["log"] + tokens[2:]
                elif subc == "export":
                    tokens = ["log", "--export"] + tokens[2:]
        elif tokens[0] == "gen":
            if len(tokens) >= 2 and tokens[1] == "l2":
                tokens = ["docs"] + tokens[2:]
                dep = "gen l2"
        elif tokens[0] == "decorate":
            tokens[0] = "adopt"
            dep = "decorate"
        elif tokens[0] == "ddt":
            if len(tokens) >= 2 and tokens[1] == "validate":
                tokens = ["check", "--fast"] + tokens[2:]
                dep = "ddt validate"
        elif tokens[0] == "st":
            tokens[0] = "status"
        elif tokens[0] == "conf":
            tokens[0] = "config"
        elif tokens[0] == "commit":
            tokens[0] = "lock"
        return tokens, dep

    argv_mapped, deprecated = _map_argv(sys.argv[1:])

    parser = argparse.ArgumentParser(prog="harbor", description="Harbor-spec CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_lock = sub.add_parser("lock", help="Lock current L3 contract snapshot into cache")
    p_lock.add_argument("--no-incremental", action="store_true")
    p_lock.add_argument("--code-root", action="append", default=None)
    p_lock.add_argument("--cache-dir", type=str, default=None)
    p_lock.add_argument("--no-register-adopted", action="store_true")
    p_lock.add_argument("--register-scan", action="store_true")

    p_config = sub.add_parser("config", help="Manage Harbor config")
    p_cfg_sub = p_config.add_subparsers(dest="cfg_cmd", required=True)
    p_cfg_list = p_cfg_sub.add_parser("list", help="List current config values")
    p_cfg_add = p_cfg_sub.add_parser("add", help="Add a path to code_roots")
    p_cfg_add.add_argument("path", type=str)
    p_cfg_remove = p_cfg_sub.add_parser("remove", help="Remove a path from code_roots")
    p_cfg_remove.add_argument("path", type=str)
    p_cfg_adopted = p_cfg_sub.add_parser("adopted", help="Show or write derived adopted roots")
    p_cfg_adopted.add_argument("--write", action="store_true")
    p_cfg_adopted.add_argument("--min-count", type=int, default=5)

    p_status = sub.add_parser("status", help="Show Harbor context status (no implicit index update)")
    p_start = sub.add_parser(
        "start",
        help="Workflow facade: run status before AI coding",
        description="Workflow facade command: run status before AI coding.",
    )
    p_checkpoint = sub.add_parser(
        "checkpoint",
        help="Workflow facade: status + check --fast",
        description="Workflow facade command: run status + check --fast.",
    )
    p_finish = sub.add_parser(
        "finish",
        help="Workflow facade: status + check + next steps",
        description="Workflow facade command: run status + check and print guided next steps.",
    )
    p_finish.add_argument(
        "--sync-context",
        action="store_true",
        help="Run finish checks and sync derived context views for changed modules",
    )
    p_accept = sub.add_parser(
        "accept",
        help="Workflow facade alias for lock",
        description="Workflow facade command: semantic alias of harbor lock.",
    )

    p_adopt = sub.add_parser("adopt", help="Adopt legacy code into Harbor governance")
    p_adopt.add_argument("path", type=str)
    p_adopt.add_argument("--strategy", type=str, choices=["safe", "aggressive"], default="safe")
    p_adopt.add_argument("--yes", action="store_true")
    p_adopt.add_argument("--dry-run", action="store_true")
    p_unadopt = sub.add_parser("unadopt", help="Remove adopted directory from Harbor code_roots")
    p_unadopt.add_argument("path", type=str)

    p_check = sub.add_parser("check", help="Run semantic and DDT checks")
    p_check.add_argument("--fast", action="store_true")
    p_check.add_argument("--module", type=str, default=None)
    p_check.add_argument("--func", type=str, default=None)
    p_check.add_argument("--diff-only", action="store_true", default=True)
    p_check.add_argument("--debug", action="store_true", default=False)
    p_check.add_argument("--format", type=str, choices=["plain", "jsonl"], default="jsonl")

    p_docs = sub.add_parser(
        "docs",
        help="Generate L2 README for a module",
        description=(
            "Generate Anchor (L2) README for module(s).\n\n"
            "Examples:\n"
            "  harbor docs --module harbor/core\n"
            "  harbor docs --module harbor/core --write\n"
            "  harbor docs --changed --write\n"
            "  harbor docs --all --write\n"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    p_docs.add_argument(
        "--module",
        type=str,
        help="Target module directory (e.g. harbor/core) to generate L2 view",
    )
    p_docs.add_argument(
        "--changed",
        action="store_true",
        help="Detect changed modules and generate L2 view for each",
    )
    p_docs.add_argument(
        "--all",
        dest="all_modules",
        action="store_true",
        help="Generate L2 view for all indexed modules",
    )
    p_docs.add_argument(
        "--write",
        action="store_true",
        help="Write canonical L2 README under .harbor/views/l2/<module>/README.md (and optional <module>/README.md export); default prints Markdown to console",
    )
    p_docs.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite of canonical/export README targets when used with --write",
    )
    p_stale = sub.add_parser(
        "stale",
        help="Check stale status of derived context views (L2 README + Module Capsule)",
    )
    p_stale.add_argument(
        "--module",
        type=str,
        help="Target module directory (e.g. harbor/core)",
    )
    p_stale.add_argument(
        "--changed",
        action="store_true",
        help="Detect changed modules and check stale status for each",
    )
    p_stale.add_argument(
        "--all",
        dest="all_modules",
        action="store_true",
        help="Check stale status for all indexed modules",
    )
    p_stale.add_argument(
        "--format",
        type=str,
        choices=["text", "json"],
        default="text",
        help="Output format: text (default) or json",
    )
    p_doctor = sub.add_parser(
        "doctor",
        help="Run read-only aggregated Harbor health checks",
    )
    p_doctor.add_argument(
        "--module",
        type=str,
        help="Target module directory (e.g. harbor/core)",
    )
    p_doctor.add_argument(
        "--changed",
        action="store_true",
        help="Detect changed modules and run doctor checks in changed scope",
    )
    p_doctor.add_argument(
        "--all",
        dest="all_modules",
        action="store_true",
        help="Run doctor checks for all indexed modules",
    )
    p_doctor.add_argument(
        "--format",
        type=str,
        choices=["text", "json"],
        default="text",
        help="Output format: text (default) or json",
    )
    p_workspace = sub.add_parser(
        "workspace",
        help="Workspace layout inspection commands",
    )
    p_workspace_sub = p_workspace.add_subparsers(dest="workspace_cmd", required=True)
    p_workspace_inspect = p_workspace_sub.add_parser(
        "inspect",
        help="Inspect current Harbor workspace layout (read-only advisory)",
    )
    p_workspace_inspect.add_argument(
        "--format",
        type=str,
        choices=["text", "json"],
        default="text",
        help="Output format: text (default) or json",
    )

    p_module = sub.add_parser(
        "module",
        help="Inspect or generate module capsule for one module",
    )
    p_module_sub = p_module.add_subparsers(dest="module_cmd", required=True)
    p_module_inspect = p_module_sub.add_parser(
        "inspect",
        help="Inspect indexed context for one module",
    )
    p_module_inspect.add_argument("module", type=str)
    p_module_seal = p_module_sub.add_parser(
        "seal",
        help="Preview or write module capsule for one module, changed modules, or all indexed modules",
    )
    p_module_seal.add_argument(
        "module",
        nargs="?",
        type=str,
        help="Target module directory (e.g. harbor/core)",
    )
    p_module_seal.add_argument(
        "--changed",
        action="store_true",
        help="Detect changed modules and generate module capsule for each",
    )
    p_module_seal.add_argument(
        "--all",
        dest="all_modules",
        action="store_true",
        help="Generate module capsule for all indexed modules",
    )
    p_module_seal.add_argument(
        "--write",
        action="store_true",
        help="Write capsule files under .harbor/views/modules/<module>/ (and optional docs export if enabled)",
    )
    p_module_stale = p_module_sub.add_parser(
        "stale",
        help="Check whether module capsule is stale for one module, changed modules, or all indexed modules",
    )
    p_module_stale.add_argument(
        "module",
        nargs="?",
        type=str,
        help="Target module directory (e.g. harbor/core)",
    )
    p_module_stale.add_argument(
        "--changed",
        action="store_true",
        help="Detect changed modules and check stale status for each",
    )
    p_module_stale.add_argument(
        "--all",
        dest="all_modules",
        action="store_true",
        help="Check stale status for all indexed modules",
    )
    p_module_promote = p_module_sub.add_parser(
        "promote-skill",
        help="Generate a thin optional skill entrypoint for one module",
    )
    p_module_promote.add_argument("module", type=str)

    p_project = sub.add_parser(
        "project",
        help="Project-level derived views",
    )
    p_project_sub = p_project.add_subparsers(dest="project_cmd", required=True)
    p_project_structure = p_project_sub.add_parser(
        "structure",
        help="Preview or write derived project structure view",
    )
    p_project_structure.add_argument(
        "--write",
        action="store_true",
        help="Write canonical .harbor/views/project-structure.md (and optional docs export if enabled); default prints preview",
    )

    p_log = sub.add_parser(
        "log",
        help="Context-aware diary logging",
        description=(
            "Context-aware diary logging.\n\n"
            "Write target: .harbor/diary/YYYY-MM.jsonl (canonical).\n"
            "Legacy path specs/diary/YYYY-MM.jsonl is read-compatible only.\n"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    p_log.add_argument("-m", "--message", type=str, required=False)
    p_log.add_argument("--summary", dest="message", type=str, required=False)
    p_log.add_argument("--type", type=str, default="feature")
    p_log.add_argument("--importance", type=str, default="normal")
    p_log.add_argument("--visibility", type=str, default="repo")
    p_log.add_argument("--details", type=str, default=None)
    p_log.add_argument("--ref-commit", type=str, default=None)
    p_log.add_argument("--author", type=str, default=None)
    p_log.add_argument("--ts", type=str, default=None)
    p_log.add_argument("--export", action="store_true")
    p_log.add_argument("--since", type=str, default=None)

    p_init = sub.add_parser("init", help="Initialize Harbor config")
    p_init.add_argument("--force", action="store_true")

    args = parser.parse_args(argv_mapped)

    def _load_cfg_data_safe():
        try:
            loaded = load_workspace_config(Path.cwd())
            return dict(loaded.get("config") or {})
        except Exception:
            return {}

    def _write_cfg_data(data):
        write_workspace_config(Path.cwd(), data)

    def _run_lock(*, code_roots=None, cache_dir=None, no_incremental=False, no_register_adopted=False, register_scan=False):
        builder = IndexBuilder(code_roots=code_roots, cache_dir=cache_dir)
        scanned = 0
        updated = 0
        skipped = 0
        items_total = 0
        console = Console()
        with Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task_id = progress.add_task(t("cli.lock.init"), total=0)
            total_set = False
            for ev in builder.iter_build(incremental=not no_incremental):
                if not total_set:
                    progress.update(task_id, total=ev.total)
                    total_set = True
                if ev.status == "scanning":
                    progress.update(task_id, description=t("cli.lock.scanning", path=f"{ev.path}"))
                elif ev.status == "parsed":
                    scanned += 1
                    updated += 1
                    items_total += ev.items_count
                    progress.update(task_id, advance=1, description=t("cli.lock.done", path=f"{ev.path}"))
                elif ev.status == "skipped":
                    scanned += 1
                    skipped += 1
                    progress.update(task_id, advance=1, description=t("cli.lock.skipped", path=f"{ev.path}"))
                elif ev.status == "error":
                    scanned += 1
                    progress.update(task_id, advance=1, description=t("cli.lock.error", path=f"{ev.path}"))
        print(t("cli.lock.summary", scanned=scanned, updated=updated, skipped=skipped, items=items_total, db=builder.db.db_path.as_posix()))
        try:
            db = builder.db
            files = [fp for fp, _ in db.get_all_files()]
            cfg = _load_cfg_data_safe()
            excludes = cfg.get("exclude_paths", [])
            from harbor.core.utils import derive_adopted_roots
            derived = derive_adopted_roots(files, exclude_patterns=excludes, min_count=1)
            if not no_register_adopted and derived:
                adopted = cfg.get("adopted_roots", [])
                changed = False
                for p in derived:
                    if p not in adopted:
                        adopted.append(p)
                        changed = True
                # 可选：同时注册到扫描目录
                if register_scan:
                    roots = cfg.get("code_roots", [])
                    for p in derived:
                        if p not in roots:
                            roots.append(p)
                            changed = True
                    cfg["code_roots"] = roots
                if changed:
                    cfg["adopted_roots"] = adopted
                    _write_cfg_data(cfg)
                print(t("cli.lock.register_adopted_wrote", count=len(derived)))
            else:
                if derived:
                    print(t("cli.lock.register_adopted_hint"))
        except Exception:
            pass

    def _run_status():
        console = Console()
        with console.status(f"[bold blue]{t('cli.status.scanning')}", spinner="dots"):
            eng = SyncEngine()
            rep = eng.check_status()
        total = sum(rep.counts.values())
        if total == 0:
            print(t("cli.status.nochanges"))
            return rep, True
        print(t("cli.status.title"))
        if rep.drift:
            print(f"\n{t('cli.status.drift')}")
            for e in rep.drift:
                print(f"  M {e.id} ({e.details})")
        if rep.contract_changed:
            print(f"\n{t('cli.status.contract')}")
            for e in rep.contract_changed:
                print(f"  C {e.id} ({e.details})")
        if rep.modified:
            print(f"\n{t('cli.status.modified')}")
            for e in rep.modified:
                print(f"  M {e.id} ({e.details})")
        if rep.untracked:
            print(f"\n{t('cli.status.untracked')}")
            for e in rep.untracked:
                print(f"  ? {e.id}")
        if rep.missing:
            print(f"\n{t('cli.status.missing')}")
            for e in rep.missing:
                print(f"  ! {e.id}")
        return rep, False

    def _run_check(*, fast=False, module=None, func=None, diff_only=True, debug=False, output_format="jsonl"):
        scanner = DDTScanner()
        bindings = scanner.scan_tests()
        if func:
            bindings = [b for b in bindings if b.func_id == func]
        if module:
            bindings = [b for b in bindings if b.func_id.startswith(module)]
        validator = DDTValidator()
        rep = validator.validate(bindings)
        print(t("cli.check.title"))
        print(f"\n{t('cli.check.ddt')}")
        print(t("cli.check.bindings", count=len(bindings)))
        if rep.valid:
            for b in rep.valid:
                print(f"  OK {b.func_id} v={b.l3_version} strategy={b.strategy} ({b.test_name} @ {b.file_path})")
        if rep.violations:
            for typ, b, msg in rep.violations:
                print(f"  [!] {typ.upper()} {b.func_id} v={b.l3_version} strategy={b.strategy} ({b.test_name} @ {b.file_path}) :: {msg}")
        if not rep.valid and not rep.violations:
            print(f"  {t('cli.check.nobindings')}")
        if not fast:
            eng = SyncEngine()
            status = eng.check_status()
            provider = resolve_provider()
            guard = SemanticGuard()
            model = getattr(provider, "model", "n/a")
            print(f"\n{t('cli.semantic.title')}")
            targets = []
            targets.extend(status.drift)
            targets.extend(status.modified)
            if not diff_only:
                targets.extend(status.contract_changed)
            print(f"targets={len(targets)}")
            out_lines = []
            for e in targets:
                try:
                    src = Path(e.file_path).read_text(encoding="utf-8")
                except Exception as ex:
                    if output_format == "jsonl":
                        print(json.dumps({
                            "status": "ERROR",
                            "func_id": e.id,
                            "file_path": e.file_path,
                            "reason": str(ex)
                        }, ensure_ascii=False))
                    else:
                        out_lines.append(f"ERROR {e.id} :: {str(ex)}")
                    continue
                adapter = IndexBuilder().adapter
                contracts = list(adapter.parse_file(e.file_path))
                matched = None
                for fc in contracts:
                    if fc.id == e.id:
                        matched = fc
                        break
                if matched is None:
                    if output_format == "jsonl":
                        print(json.dumps({
                            "status": "ERROR",
                            "func_id": e.id,
                            "file_path": e.file_path,
                            "reason": "contract not found"
                        }, ensure_ascii=False))
                    else:
                        out_lines.append(f"ERROR {e.id} :: contract not found")
                    continue
                res = guard.audit(matched, src, provider)
                if debug:
                    print(f"[DEBUG] Prompt >>>\n{res.prompt or ''}\n[DEBUG] Raw <<<\n{res.raw_output or ''}")
                reason = " ".join((res.reason or "").split())
                if output_format == "jsonl":
                    print(json.dumps({
                        "status": "OK" if res.status == "OK" else ("POSSIBLE_SEMANTIC_DRIFT" if res.status == "MISMATCH" else "ERROR"),
                        "func_id": e.id,
                        "file_path": e.file_path,
                        "provider": provider.name,
                        "model": model,
                        "reason": reason if res.status != "OK" else None
                    }, ensure_ascii=False))
                else:
                    if res.status == "OK":
                        out_lines.append(f"OK {e.id}")
                    elif res.status == "MISMATCH":
                        out_lines.append(f"POSSIBLE_SEMANTIC_DRIFT {e.id} :: {reason}")
                    else:
                        out_lines.append(f"ERROR {e.id} :: {reason}")
            if not out_lines:
                if output_format == "plain":
                    print(t("cli.semantic.notargets"))
            else:
                if output_format == "plain":
                    for ln in out_lines:
                        print(ln)

    def _collect_changed_paths_from_status(rep):
        changed_paths = []
        changed_paths.extend([e.file_path for e in rep.drift])
        changed_paths.extend([e.file_path for e in rep.modified])
        changed_paths.extend([e.file_path for e in rep.contract_changed])
        changed_paths.extend([e.file_path for e in rep.untracked])
        changed_paths.extend([e.file_path for e in rep.missing])
        return changed_paths

    def _collect_changed_modules_from_status(rep):
        changed_paths = _collect_changed_paths_from_status(rep)
        cwd = Path.cwd().resolve()
        workspace_paths = []
        for raw_path in changed_paths:
            p = Path(str(raw_path))
            abs_path = p if p.is_absolute() else (cwd / p)
            try:
                rel = abs_path.resolve().relative_to(cwd).as_posix()
            except Exception:
                continue
            workspace_paths.append(rel)
        return collect_modules_from_paths(workspace_paths)

    def _collect_changed_modules():
        rep = SyncEngine().check_status()
        return _collect_changed_modules_from_status(rep)

    def _collect_changed_modules_for_docs():
        rep = SyncEngine().check_status()
        changed_paths = _collect_changed_paths_from_status(rep)
        return collect_modules_from_paths(changed_paths)

    def _to_repo_relative_display(path: Path) -> str:
        try:
            return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
        except Exception:
            return path.as_posix()

    def _normalize_l2_write_paths(result) -> List[Path]:
        def _is_l2_meta(path_obj: Path) -> bool:
            return path_obj.name == "_meta.json"

        if result is None:
            return []
        if isinstance(result, Path):
            return [] if _is_l2_meta(result) else [result]
        if isinstance(result, (list, tuple)):
            out: List[Path] = []
            for item in result:
                if isinstance(item, Path):
                    if not _is_l2_meta(item):
                        out.append(item)
                else:
                    candidate = Path(str(item))
                    if not _is_l2_meta(candidate):
                        out.append(candidate)
            return out
        candidate = Path(str(result))
        return [] if _is_l2_meta(candidate) else [candidate]

    def _print_log_write_result(entry, mgr: DiaryManager) -> None:
        # Keep the first line as entry JSON for script compatibility.
        print(entry.to_json())
        target = mgr._current_file_path(entry.ts)
        print(t("cli.log.write_target", path=_to_repo_relative_display(target)))
        print(t("cli.log.path_policy"))

    def _sanitize_module_for_display(module: str, *, repo_root: Path) -> str:
        raw = str(module or "").strip()
        if not raw:
            return "<outside-repo>"
        normalized = raw.replace("\\", "/")
        candidate = Path(normalized)
        if candidate.is_absolute() or re.match(r"(?i)^[a-z]:/", normalized):
            try:
                rel = candidate.resolve().relative_to(repo_root.resolve()).as_posix()
                return rel
            except Exception:
                base = candidate.name or Path(normalized.rstrip("/")).name
                return f"<outside-repo>/{base}" if base else "<outside-repo>"
        return normalized.strip("/") or "<outside-repo>"

    def _classify_module_safety(module: str, *, repo_root: Path) -> Tuple[bool, str, str]:
        raw = str(module or "").strip()
        if not raw:
            return False, t("cli.docs.unsafe_reason.invalid"), ""

        normalized = raw.replace("\\", "/")
        while "//" in normalized:
            normalized = normalized.replace("//", "/")

        # Absolute modules are only valid when they can be mapped back into repo root.
        parts = [part for part in normalized.split("/") if part not in ("", ".")]
        head = parts[0] if parts else ""
        is_windows_abs = bool(re.match(r"(?i)^[a-z]:$", head)) or bool(re.match(r"(?i)^[a-z]:/", normalized))
        is_absolute = normalized.startswith("/") or normalized.startswith("//") or is_windows_abs
        if is_absolute:
            candidate = Path(normalized)
            try:
                rel = candidate.resolve().relative_to(repo_root.resolve()).as_posix()
            except Exception:
                return False, t("cli.docs.unsafe_reason.outside_root"), ""
            rel_parts = [part for part in rel.split("/") if part not in ("", ".")]
            if not rel_parts or any(part == ".." for part in rel_parts):
                return False, t("cli.docs.unsafe_reason.invalid"), ""
            parts = rel_parts
        else:
            if not parts:
                return False, t("cli.docs.unsafe_reason.invalid"), ""
            if any(part == ".." for part in parts):
                return False, t("cli.docs.unsafe_reason.traversal"), ""

        # Accept file-path candidates by inferring their parent module.
        if parts and (parts[-1] == "__init__.py" or "." in parts[-1]):
            parts = parts[:-1]
        if not parts:
            return False, t("cli.docs.unsafe_reason.invalid"), ""
        if any(part == ".." for part in parts):
            return False, t("cli.docs.unsafe_reason.traversal"), ""
        return True, "", "/".join(parts)

    def _select_safe_modules(modules: List[str], *, strict: bool = False) -> Tuple[List[str], List[Tuple[str, str]]]:
        repo_root = Path.cwd().resolve()
        safe_modules: List[str] = []
        skipped: List[Tuple[str, str]] = []
        seen = set()
        for module in modules:
            is_safe, reason, normalized = _classify_module_safety(module, repo_root=repo_root)
            if is_safe and normalized:
                if normalized not in seen:
                    seen.add(normalized)
                    safe_modules.append(normalized)
                continue
            display = _sanitize_module_for_display(str(module), repo_root=repo_root)
            if strict:
                raise ValueError(t("cli.docs.module_unsafe", module=display, reason=reason))
            skipped.append((display, reason))
        return safe_modules, skipped

    def _print_skipped_unsafe_modules(skipped: List[Tuple[str, str]]) -> None:
        if not skipped:
            return
        print(t("cli.docs.skipped_unsafe.title"))
        for display, reason in skipped:
            print(f"- {display} ({reason})")

    def _run_docs_changed(*, write=False, force=False, modules=None):
        gen = L2Generator()
        raw_modules = modules if modules is not None else _collect_changed_modules_for_docs()
        target_modules, skipped = _select_safe_modules(list(raw_modules), strict=False)
        _print_skipped_unsafe_modules(skipped)
        if not target_modules:
            print(t("cli.docs.changed.none"))
            return []
        print(t("cli.docs.changed.found"))
        for module in target_modules:
            print(f"- {module}")
        if not write:
            print("")
            print(t("cli.docs.preview_only"))
        updated = []
        for module in target_modules:
            md = gen.generate(module)
            if write:
                targets = _normalize_l2_write_paths(gen.write(module, md, force=force))
                updated.extend(targets)
            else:
                print("")
                print(md)
        if write:
            if not updated:
                print(t("cli.docs.nochanges"))
            else:
                print("")
                print(t("cli.docs.updated"))
                for path in updated:
                    print(f"- {_to_repo_relative_display(path)}")
        return target_modules

    def _run_module_seal_changed(*, write=False, modules=None):
        target_modules = modules if modules is not None else _collect_changed_modules()
        if not target_modules:
            print(t("cli.module.seal.changed.none"))
            return []
        print(t("cli.module.seal.changed.found"))
        for module in target_modules:
            print(f"- {module}")

        valid_contexts = []
        for module in target_modules:
            context = collect_module_context(module)
            if context.get("key_files") or context.get("contracts"):
                valid_contexts.append(context)

        if not valid_contexts:
            print(t("cli.module.seal.changed.none"))
            return target_modules

        if not write:
            print("")
            first_target = resolve_module_capsule_paths(valid_contexts[0].get("module", ""), root=Path.cwd()).get("canonical_dir")
            preview_path = _to_repo_relative_display(first_target) if first_target is not None else ".harbor/views/modules/<module>"
            print(t("cli.module.seal.batch.preview_only", path=preview_path))
            for context in valid_contexts:
                module_name = context.get("module", "")
                previews = preview_module_capsule(context)
                print("")
                print(t("cli.module.seal.title", module=module_name))
                for name in ["module-card.md", "review-checklist.md", "debug-playbook.md"]:
                    print("")
                    print(f"--- {name} ---")
                    print(previews[name])
            return target_modules

        updated = []
        for context in valid_contexts:
            result = write_module_capsule(context)
            updated.extend(result.canonical_paths)
            updated.extend(result.exported_paths)
        print(t("cli.module.seal.batch.updated"))
        for path in updated:
            print(f"- {_to_repo_relative_display(path)}")
        return target_modules

    def _run_module_stale_changed(*, modules=None):
        target_modules = modules if modules is not None else _collect_changed_modules()
        if not target_modules:
            print(t("cli.module.stale.none_changed"))
            return []
        print(t("cli.module.stale.changed.found"))
        for module in target_modules:
            context = collect_module_context(module)
            result = check_module_capsule_stale(context)
            status_text = t("cli.module.stale.up_to_date") if result.get("status") == "up_to_date" else t(
                "cli.module.stale.stale"
            )
            print(f"- {module}: {status_text}")
        return target_modules

    if args.command in ("lock", "accept"):
        code_roots = args.code_root if args.command == "lock" else None
        cache_dir = Path(args.cache_dir) if args.command == "lock" and args.cache_dir else None
        _run_lock(
            code_roots=code_roots,
            cache_dir=cache_dir,
            no_incremental=getattr(args, "no_incremental", False),
            no_register_adopted=getattr(args, "no_register_adopted", False),
            register_scan=getattr(args, "register_scan", False),
        )
        if args.command == "accept":
            print(t("cli.accept.done"))
    elif args.command == "start":
        print(t("cli.start.title"))
        _, clean = _run_status()
        if clean:
            print(t("cli.start.clean"))
        else:
            print(t("cli.start.dirty"))
    elif args.command == "checkpoint":
        print(t("cli.checkpoint.title"))
        _run_status()
        _run_check(fast=True)
    elif args.command == "finish":
        print(t("cli.finish.title"))
        _run_status()
        _run_check(fast=False)
        if not getattr(args, "sync_context", False):
            print(t("cli.finish.next_steps"))
        else:
            print("")
            print(t("cli.finish.sync_context.title"))
            changed_modules = _collect_changed_modules()
            docs_modules = _collect_changed_modules_for_docs()
            if not changed_modules and not docs_modules:
                print(t("cli.finish.sync_context.none"))
            else:
                print(t("cli.finish.sync_context.docs"))
                _run_docs_changed(write=True, modules=docs_modules)
                print("")
                print(t("cli.finish.sync_context.capsules"))
                _run_module_seal_changed(write=True, modules=changed_modules)
                print("")
                print(t("cli.finish.sync_context.stale"))
                _run_module_stale_changed(modules=changed_modules)
            print("")
            print(t("cli.finish.sync_context.next_steps"))
    elif args.command == "config" and args.cfg_cmd == "list":
        data = _load_cfg_data_safe()
        code_roots = data.get("code_roots", ["harbor/**"])
        exclude_paths = data.get("exclude_paths", [])
        profile = data.get("profile", "enforce_l3")
        language = str(data.get("language", "auto"))
        adopted_roots = data.get("adopted_roots", [])
        table = Table(title=t("cli.config.title"))
        table.add_column(t("cli.config.key"), style="bold")
        table.add_column(t("cli.config.value"))
        table.add_row("profile", profile)
        table.add_row("code_roots", ", ".join(code_roots))
        table.add_row("exclude_paths", ", ".join(exclude_paths))
        table.add_row("adopted_roots", ", ".join(adopted_roots))
        table.add_row("language", language or "auto")
        Console().print(table)
        if code_roots == ["**/*.py"]:
            print(t("cli.config.adopt_hint"))
    elif args.command == "config" and args.cfg_cmd == "add":
        data = _load_cfg_data_safe()
        roots = data.get("code_roots", [])
        p = args.path
        if p not in roots:
            roots.append(p)
        data["code_roots"] = roots
        data.setdefault("exclude_paths", [])
        data.setdefault("profile", data.get("profile", "enforce_l3"))
        data.setdefault("language", data.get("language", "auto"))
        data.setdefault("adopted_roots", [])
        _write_cfg_data(data)
        print(t("cli.config.added", path=p))
    elif args.command == "config" and args.cfg_cmd == "remove":
        data = _load_cfg_data_safe()
        roots = data.get("code_roots", [])
        p = args.path
        if p in roots:
            roots = [x for x in roots if x != p]
            data["code_roots"] = roots
            adopted = data.get("adopted_roots", [])
            if p in adopted:
                adopted = [x for x in adopted if x != p]
                data["adopted_roots"] = adopted
            _write_cfg_data(data)
            print(t("cli.config.removed", path=p))
        else:
            print(t("cli.config.nochanges"))
    elif args.command == "config" and args.cfg_cmd == "adopted":
        data = _load_cfg_data_safe()
        excludes = data.get("exclude_paths", [])
        db = IndexBuilder().db
        files = [fp for fp, _ in db.get_all_files()]
        from harbor.core.utils import derive_adopted_roots
        derived = derive_adopted_roots(files, exclude_patterns=excludes, min_count=getattr(args, "min_count", 1))
        table = Table(title=t("cli.config.title"))
        table.add_column(t("cli.config.key"), style="bold")
        table.add_column(t("cli.config.value"))
        table.add_row("derived_adopted_roots", ", ".join(derived))
        Console().print(table)
        if getattr(args, "write", False):
            adopted = data.get("adopted_roots", [])
            for p in derived:
                if p not in adopted:
                    adopted.append(p)
                if p not in data.get("code_roots", []):
                    data["code_roots"] = data.get("code_roots", []) + [p]
            data["adopted_roots"] = adopted
            _write_cfg_data(data)
            print(t("cli.config.adopted.wrote", count=len(derived)))
    elif args.command == "status":
        _run_status()
    elif args.command == "check":
        _run_check(
            fast=args.fast,
            module=args.module,
            func=args.func,
            diff_only=args.diff_only,
            debug=args.debug,
            output_format=args.format,
        )
    elif args.command == "docs":
        docs_mode_count = int(bool(args.module)) + int(bool(args.changed)) + int(bool(args.all_modules))
        if docs_mode_count != 1:
            parser.error(t("cli.docs.mode_conflict"))
        gen = L2Generator()
        if args.module:
            module_name = args.module
            if args.write:
                selected, _ = _select_safe_modules([args.module], strict=True)
                module_name = selected[0]
            md = gen.generate(module_name)
            if args.write:
                targets = _normalize_l2_write_paths(gen.write(module_name, md, force=args.force))
                if not targets:
                    print(t("cli.docs.nochanges"))
                else:
                    print(t("cli.docs.updated"))
                    for path in targets:
                        print(f"- {_to_repo_relative_display(path)}")
            else:
                print(md)
        else:
            if args.changed:
                _run_docs_changed(write=args.write, force=args.force)
                return
            else:
                raw_modules = collect_all_indexed_modules()
                modules, skipped = _select_safe_modules(raw_modules, strict=False)
                _print_skipped_unsafe_modules(skipped)
                if not modules:
                    print(t("cli.docs.all.none"))
                    return
                print(t("cli.docs.all.found"))
            for module in modules:
                print(f"- {module}")
            if not args.write:
                print("")
                print(t("cli.docs.preview_only"))
            updated = []
            for module in modules:
                md = gen.generate(module)
                if args.write:
                    targets = _normalize_l2_write_paths(gen.write(module, md, force=args.force))
                    updated.extend(targets)
                else:
                    print("")
                    print(md)
            if args.write:
                if not updated:
                    print(t("cli.docs.nochanges"))
                else:
                    print("")
                    print(t("cli.docs.updated"))
                    for path in updated:
                        print(f"- {_to_repo_relative_display(path)}")
    elif args.command == "stale":
        mode_count = int(bool(args.module)) + int(bool(args.changed)) + int(bool(args.all_modules))
        if mode_count > 1:
            parser.error(t("cli.stale.mode_conflict"))

        scope_text = t("cli.stale.scope.changed")
        scope_value = "changed"
        if args.module:
            modules = [args.module]
            scope_text = t("cli.stale.scope.module", module=args.module)
            scope_value = f"module:{args.module}"
        elif args.all_modules:
            modules = collect_all_indexed_modules()
            scope_text = t("cli.stale.scope.all")
            scope_value = "all"
            if not modules:
                if args.format == "json":
                    print(json.dumps(stale_report_to_dict([], scope=scope_value), ensure_ascii=False, sort_keys=True, indent=2))
                else:
                    print(t("cli.stale.none_all"))
                return
        else:
            modules = _collect_changed_modules()
            if not modules:
                if args.format == "json":
                    print(json.dumps(stale_report_to_dict([], scope=scope_value), ensure_ascii=False, sort_keys=True, indent=2))
                else:
                    print(t("cli.stale.none_changed"))
                return

        results = [check_module_derived_views_stale(module) for module in modules]
        if args.format == "json":
            payload = stale_report_to_dict(results, scope=scope_value)
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))
        else:
            print(format_stale_summary(results, scope_text=scope_text))
    elif args.command == "doctor":
        mode_count = int(bool(args.module)) + int(bool(args.changed)) + int(bool(args.all_modules))
        if mode_count > 1:
            parser.error(t("cli.doctor.mutually_exclusive"))

        scope_text = t("cli.doctor.scope.changed")
        scope_value = "changed"
        if args.module:
            modules = [args.module]
            scope_text = t("cli.doctor.scope.module", module=args.module)
            scope_value = f"module:{args.module}"
        elif args.all_modules:
            modules = collect_all_indexed_modules()
            scope_text = t("cli.doctor.scope.all")
            scope_value = "all"
        else:
            modules = _collect_changed_modules()

        report = build_doctor_report(
            scope=scope_text,
            modules=sorted(modules) if args.format == "json" else modules,
        )
        if args.format == "json":
            payload = report.to_dict(command="doctor")
            payload["scope"] = scope_value
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))
        else:
            print(format_doctor_report(report))
    elif args.command == "workspace" and args.workspace_cmd == "inspect":
        report = build_workspace_inspect_report(Path.cwd())
        if args.format == "json":
            payload = workspace_inspect_report_to_dict(report)
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))
        else:
            print(format_workspace_inspect_report(report))
    elif args.command == "module" and args.module_cmd == "inspect":
        context = collect_module_context(args.module)
        module_name = context.get("module", "")
        if not module_name:
            print(t("cli.module.inspect.none", module=args.module))
            return
        print(t("cli.module.inspect.title", module=module_name))
        if not context.get("key_files") and not context.get("contracts"):
            print(t("cli.module.inspect.none", module=module_name))
            return
        print(f"Module: {module_name}")
        print(f"Strictness: {context.get('strictness', 'standard')}")
        print("Key files:")
        for fp in context.get("key_files", []):
            print(f"- {fp}")
        print("")
        print("Indexed contracts:")
        contracts = context.get("contracts", [])
        if not contracts:
            print("- No indexed contracts found for this module.")
        else:
            for c in contracts:
                print(f"- {c.get('symbol')}")
        print("")
        print("Tests:")
        tests = context.get("tests", [])
        if not tests:
            print("- No test files detected by Harbor.")
        else:
            for tpath in tests:
                print(f"- {tpath}")
    elif args.command == "module" and args.module_cmd == "seal":
        mode_count = int(bool(args.module)) + int(bool(args.changed)) + int(bool(args.all_modules))
        if mode_count != 1:
            parser.error(t("cli.module.seal.mode_conflict"))

        if args.module:
            context = collect_module_context(args.module)
            module_name = context.get("module", "")
            if not module_name:
                print(t("cli.module.seal.none", module=args.module))
                return
            if not context.get("key_files") and not context.get("contracts"):
                print(t("cli.module.seal.none", module=module_name))
                return
            print(t("cli.module.seal.title", module=module_name))
            previews = preview_module_capsule(context)
            if not args.write:
                resolved = resolve_module_capsule_paths(module_name, root=Path.cwd()).get("canonical_dir")
                preview_path = _to_repo_relative_display(resolved) if resolved is not None else ".harbor/views/modules/<module>"
                print(t("cli.module.seal.preview_only", path=preview_path))
                for name in ["module-card.md", "review-checklist.md", "debug-playbook.md"]:
                    print("")
                    print(f"--- {name} ---")
                    print(previews[name])
            else:
                result = write_module_capsule(context)
                updated = list(result.canonical_paths) + list(result.exported_paths)
                print(t("cli.module.seal.updated"))
                for path in updated:
                    print(f"- {_to_repo_relative_display(path)}")
            return

        if args.changed:
            _run_module_seal_changed(write=args.write)
            return
        else:
            modules = collect_all_indexed_modules()
            if not modules:
                print(t("cli.module.seal.all.none"))
                return
            print(t("cli.module.seal.all.found"))

        for module in modules:
            print(f"- {module}")

        valid_contexts = []
        for module in modules:
            context = collect_module_context(module)
            if context.get("key_files") or context.get("contracts"):
                valid_contexts.append(context)

        if not valid_contexts:
            if args.changed:
                print(t("cli.module.seal.changed.none"))
            else:
                print(t("cli.module.seal.all.none"))
            return

        if not args.write:
            print("")
            first_target = resolve_module_capsule_paths(valid_contexts[0].get("module", ""), root=Path.cwd()).get("canonical_dir")
            preview_path = _to_repo_relative_display(first_target) if first_target is not None else ".harbor/views/modules/<module>"
            print(t("cli.module.seal.batch.preview_only", path=preview_path))
            for context in valid_contexts:
                module_name = context.get("module", "")
                previews = preview_module_capsule(context)
                print("")
                print(t("cli.module.seal.title", module=module_name))
                for name in ["module-card.md", "review-checklist.md", "debug-playbook.md"]:
                    print("")
                    print(f"--- {name} ---")
                    print(previews[name])
            return

        updated = []
        for context in valid_contexts:
            result = write_module_capsule(context)
            updated.extend(result.canonical_paths)
            updated.extend(result.exported_paths)
        print(t("cli.module.seal.batch.updated"))
        for path in updated:
            print(f"- {_to_repo_relative_display(path)}")
    elif args.command == "module" and args.module_cmd == "stale":
        mode_count = int(bool(args.module)) + int(bool(args.changed)) + int(bool(args.all_modules))
        if mode_count != 1:
            parser.error(t("cli.module.stale.mode_conflict"))

        if args.module:
            context = collect_module_context(args.module)
            module_name = context.get("module", "") or args.module
            result = check_module_capsule_stale(context)
            print(t("cli.module.stale.title", module=module_name))
            if result.get("status") == "up_to_date":
                print(f"- {t('cli.module.stale.status')}: {t('cli.module.stale.up_to_date')}")
                print(f"- {t('cli.module.stale.fingerprint')}: {result.get('current_fingerprint', '')}")
            else:
                print(f"- {t('cli.module.stale.status')}: {t('cli.module.stale.stale')}")
                print(f"- {t('cli.module.stale.reason')}: {result.get('reason', '')}")
                if result.get("reason") != "no indexed records found for module":
                    print(f"- {t('cli.module.stale.suggest')}:")
                    print(f"  harbor module seal {module_name} --write")
            return

        if args.changed:
            _run_module_stale_changed()
            return
        else:
            modules = collect_all_indexed_modules()
            if not modules:
                print(t("cli.module.stale.none_all"))
                return
            print(t("cli.module.stale.all.found"))

        for module in modules:
            context = collect_module_context(module)
            result = check_module_capsule_stale(context)
            status_text = t("cli.module.stale.up_to_date") if result.get("status") == "up_to_date" else t(
                "cli.module.stale.stale"
            )
            print(f"- {module}: {status_text}")
    elif args.command == "module" and args.module_cmd == "promote-skill":
        context = collect_module_context(args.module)
        check = check_capsule_ready_for_skill(args.module, context=context)
        module_name = check.get("module", "") or args.module
        status = check.get("status")

        if status == "unknown_module":
            print(t("cli.module.promote_skill.unknown_module", module=module_name))
            print(t("cli.module.promote_skill.unknown_module.hint", module=module_name))
            return
        if status == "missing_capsule":
            print(t("cli.module.promote_skill.missing_capsule", module=module_name))
            print(t("cli.module.promote_skill.seal_hint", module=module_name))
            return
        if status == "stale_capsule":
            print(t("cli.module.promote_skill.stale_capsule", module=module_name))
            print(t("cli.module.promote_skill.stale_hint", module=module_name))
            return

        target = write_module_skill(module_name)
        print(t("cli.module.promote_skill.generated"))
        print(f"- {target.as_posix()}")
        print("")
        print(t("cli.module.promote_skill.references", module=module_name))
        print(f"- .harbor/views/modules/{module_name}/module-card.md")
        print(f"- .harbor/views/modules/{module_name}/review-checklist.md")
        print(f"- .harbor/views/modules/{module_name}/debug-playbook.md")
    elif args.command == "project" and args.project_cmd == "structure":
        context = collect_project_structure_context(Path.cwd())
        markdown = generate_project_structure_markdown(context)
        workspace_paths = load_workspace_paths(Path.cwd(), enforce_write_safety=True)
        canonical_display = workspace_paths.project_structure_path.as_posix()
        try:
            canonical_display = workspace_paths.project_structure_path.resolve().relative_to(Path.cwd().resolve()).as_posix()
        except Exception:
            canonical_display = workspace_paths.project_structure_path.as_posix()
        if not args.write:
            print(markdown)
            print("")
            print(t("cli.project.structure.preview_only", path=canonical_display))
            if not context.has_indexed_modules:
                print(t("cli.project.structure.no_index"))
            return
        write_result = write_project_structure(context, Path.cwd())
        updated_paths = [write_result.canonical_path] + list(write_result.exported_paths)
        print(t("cli.project.structure.updated"))
        for updated in updated_paths:
            updated_display = updated.as_posix()
            try:
                updated_display = updated.resolve().relative_to(Path.cwd().resolve()).as_posix()
            except Exception:
                updated_display = updated.as_posix()
            print(f"- {updated_display}")
        if not context.has_indexed_modules:
            print(t("cli.project.structure.no_index"))
    elif args.command == "log" and args.export:
        mgr = DiaryManager()
        md = mgr.export_markdown(since=args.since, min_visibility=args.visibility or "repo")
        print(md)
    elif args.command == "log" and args.message:
        mgr = DiaryManager()
        entry = mgr.log(
            summary=args.message,
            type=args.type,
            importance=args.importance,
            visibility=args.visibility,
            details=args.details,
            ref_commit=args.ref_commit,
            author=args.author,
            ts=args.ts,
        )
        _print_log_write_result(entry, mgr)
    elif args.command == "log":
        console = Console()
        with console.status("[bold blue][Status] Analyzing code changes...", spinner="dots"):
            eng = SyncEngine()
            rep = eng.check_status()
        if (rep.counts.get("drift", 0) + rep.counts.get("modified", 0)) == 0:
            print(t("cli.log.nochanges"))
            print(f"\n{t('cli.log.tip1')}")
            print(t("cli.log.tip2"))
            print(t("cli.log.tip3"))
            return
        drafter = DiaryDrafter(sync_engine=eng)
        try:
            with console.status("[bold magenta][AI] Drafting diary entry...", spinner="line"):
                draft = drafter.generate_draft()
        except LLMNotConfiguredError as e:
            print(str(e))
            print(t("cli.log.llm_env_hint"))
            return
        except Exception as e:
            msg = str(e)
            lc = msg.lower()
            if ("context" in lc and "length" in lc) or ("token" in lc and ("too many" in lc or "exceed" in lc)) or ("maximum context" in lc) or ("prompt too long" in lc):
                print(t("cli.log.context_too_long"))
                choice = Prompt.ask(t("cli.log.ask_simplify"), choices=["Y", "N", "y", "n"], default="Y")
                if choice.upper() == "Y":
                    with console.status("[bold magenta][AI] Drafting with simplified context...", spinner="line"):
                        try:
                            draft = drafter.generate_draft(limit=6000)
                        except Exception as e2:
                            print(t("cli.log.ai_failed", msg=str(e2)))
                            if args.debug:
                                provider = resolve_provider()
                                print(f"[DEBUG] Provider: {provider.name} Model: {getattr(provider, 'model', 'n/a')}")
                                if getattr(drafter, "last_prompt", None):
                                    print(f"[DEBUG] Prompt >>>\n{drafter.last_prompt or ''}")
                                if getattr(drafter, "last_output", None):
                                    print(f"[DEBUG] Raw <<<\n{drafter.last_output or ''}")
                            return
                else:
                    return
            else:
                print(t("cli.log.ai_failed", msg=str(e)))
                if args.debug:
                    provider = resolve_provider()
                    print(f"[DEBUG] Provider: {provider.name} Model: {getattr(provider, 'model', 'n/a')}")
                    print("[DEBUG] Ensure endpoint supports JSON structured output (response_format=json_object).")
                    print("[DEBUG] For ERNIE-compatible endpoints, set HARBOR_LLM_BASE_URL and HARBOR_LLM_MODEL=ernie-4.0.")
                    if getattr(drafter, "last_prompt", None):
                        print(f"[DEBUG] Prompt >>>\n{drafter.last_prompt or ''}")
                    if getattr(drafter, "last_output", None):
                        print(f"[DEBUG] Raw <<<\n{drafter.last_output or ''}")
                return
        if not draft:
            print(t("cli.log.nochanges"))
            return
        panel_text = (
            f"[bold]{t('cli.log.panel.summary')}[/bold]: {draft.get('summary','')}\n"
            f"[bold]{t('cli.log.panel.type')}[/bold]: {draft.get('type','')}\n"
            f"[bold]{t('cli.log.panel.importance')}[/bold]: {draft.get('importance','')}\n"
            f"[bold]{t('cli.log.panel.details')}[/bold]:\n{draft.get('details','')}"
        )
        console.print(Panel(panel_text, title=t("cli.log.panel.title"), border_style="green"))
        choice = Prompt.ask(t("cli.log.ask_save"), choices=["Y", "E", "N", "y", "e", "n"], default="Y")
        ans = choice.upper()
        if ans == "N":
            print(t("cli.log.discarded"))
            return
        summary_final = draft.get("summary", "")
        if ans == "E":
            summary_final = Prompt.ask(t("cli.log.ask_new_summary"), default=summary_final)
        mgr = DiaryManager()
        entry = mgr.log(
            summary=summary_final,
            type=draft.get("type", "chore"),
            importance=draft.get("importance", "normal"),
            visibility=args.visibility or "repo",
            details=draft.get("details"),
        )
        _print_log_write_result(entry, mgr)
    elif args.command == "adopt":
        console = Console()
        eng = DecoratorEngine()
        candidates = eng.scan(args.path, strategy=args.strategy)
        table = Table(title=t("cli.adopt.table.title"))
        table.add_column(t("cli.adopt.table.action"))
        table.add_column(t("cli.adopt.table.func"))
        table.add_column(t("cli.adopt.table.file"))
        table.add_column(t("cli.adopt.table.hasdoc"))
        table.add_column(t("cli.adopt.table.hasscope"))
        doc_yes = 0
        doc_no = 0
        for c in candidates:
            if c.has_docstring:
                doc_yes += 1
            else:
                doc_no += 1
            table.add_row(c.action, c.qualified_name, c.file_path.as_posix(), "Y" if c.has_docstring else "N", "Y" if c.has_scope_tag else "N")
        console.print(table)
        missing_scope_files = {}
        for c in candidates:
            if c.action == "Keep" and c.has_docstring and not c.has_scope_tag:
                missing_scope_files[c.file_path.as_posix()] = c.file_path
        create_docs_files = {}
        if args.strategy == "aggressive":
            for c in candidates:
                if c.action == "Create" and not c.has_docstring:
                    create_docs_files[c.file_path.as_posix()] = c.file_path
        target_files = {}
        for k, v in missing_scope_files.items():
            target_files[k] = v
        for k, v in create_docs_files.items():
            target_files[k] = v
        plans = []
        singleline_skipped_total = 0
        for f in target_files.values():
            for p in eng.preview(f, strategy=args.strategy):
                plans.append(p)
                if p.will_write and p.diff_preview:
                    pass
        summary = t("cli.adopt.summary", total=len(candidates), doc_yes=doc_yes, doc_no=doc_no)
        print(summary)
        to_apply = [p for p in plans if p.will_write]
        print(t("cli.adopt.planned", count=len(to_apply)))
        if args.dry_run:
            for p in to_apply:
                if p.diff_preview:
                    print(p.diff_preview)
            return
        if not args.yes:
            choice = Prompt.ask(t("cli.adopt.apply_prompt", count=len(to_apply)), choices=["y", "n", "Y", "N"], default="N")
            if choice.upper() != "Y":
                print(t("cli.adopt.nochanges"))
                return
        rep = eng.apply(to_apply, dry_run=False, strategy=args.strategy)
        data = _load_cfg_data_safe()
        roots = data.get("code_roots", [])
        p_in = Path(args.path)
        base = p_in.parent if p_in.is_file() else p_in
        try:
            rel = base.resolve().relative_to(Path.cwd().resolve()).as_posix()
        except Exception:
            rel = base.as_posix()
        pattern = f"{rel}/**" if base.is_dir() else rel
        if pattern not in roots:
            roots.append(pattern)
        adopted_roots = data.get("adopted_roots", [])
        if pattern not in adopted_roots:
            adopted_roots.append(pattern)
        data["code_roots"] = roots
        data["adopted_roots"] = adopted_roots
        data.setdefault("exclude_paths", [])
        data.setdefault("profile", data.get("profile", "enforce_l3"))
        data.setdefault("language", data.get("language", "auto"))
        _write_cfg_data(data)
        print(t("cli.adopt.applied", files=len(rep.changed_files)))
        print(t("cli.adopt.added_config", path=pattern))
    elif args.command == "init":
        init = Initializer()
        if init.config_path.exists() and not args.force:
            print(t("cli.init.exist"))
            return
        stacks, roots, excludes = init.autodetect()
        if stacks:
            print(t("cli.init.detected", stacks=" + ".join(stacks)))
        if excludes:
            key_ex = []
            for k in ["node_modules/**", ".venv/**", "dist/**", ".next/**", "build/**"]:
                if k in excludes:
                    key_ex.append(k.split("/")[0])
            extra_cnt = max(len(excludes) - len(key_ex), 0)
            if key_ex:
                print(t("cli.init.excludes", keys=", ".join(key_ex), extra=(f" (+{extra_cnt} more)" if extra_cnt > 0 else "")))
        print(t("cli.init.roots", roots=roots))
        init.write_config(roots, force=args.force, exclude_paths=excludes)
        print(t("cli.init.done"))
        print(t("cli.init.next"))
    elif args.command == "unadopt":
        data = _load_cfg_data_safe()
        roots = data.get("code_roots", [])
        p_in = Path(args.path)
        base = p_in.parent if p_in.is_file() else p_in
        try:
            rel = base.resolve().relative_to(Path.cwd().resolve()).as_posix()
        except Exception:
            rel = base.as_posix()
        pattern = f"{rel}/**" if base.is_dir() else rel
        if pattern in roots:
            roots = [x for x in roots if x != pattern]
            data["code_roots"] = roots
            adopted = data.get("adopted_roots", [])
            if pattern in adopted:
                adopted = [x for x in adopted if x != pattern]
                data["adopted_roots"] = adopted
            _write_cfg_data(data)
            print(t("cli.config.removed", path=pattern))
        else:
            print(t("cli.config.nochanges"))

    if deprecated:
        Console().print(f"[yellow]{t('cli.deprecated', old=deprecated, new=argv_mapped[0])}[/yellow]")


if __name__ == "__main__":
    main()

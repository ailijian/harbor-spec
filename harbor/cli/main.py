import argparse
from pathlib import Path
import yaml
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, TextColumn, BarColumn, MofNCompleteColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.prompt import Prompt

from harbor.core.index import IndexBuilder
from harbor.core.sync import SyncEngine
from harbor.core.ddt import DDTScanner, DDTValidator
from harbor.core.l2 import L2Generator
from harbor.core.diary import DiaryManager
from harbor.core.audit import SemanticGuard, resolve_provider
from harbor.core.drafting import DiaryDrafter, LLMNotConfiguredError
from harbor.core.init import Initializer


def main():
    """Harbor CLI 入口。

    功能:
      - 提供 `harbor` 命令的子命令入口：`build-index/status/ddt/gen/diary/audit`。
      - 解析参数并委派到对应子系统。

    使用场景:
      - 开发者在本地与 CI 中调用 Harbor 管理上下文。

    依赖:
      - harbor.core.index.IndexBuilder
      - harbor.core.sync.SyncEngine
      - harbor.core.ddt.DDTScanner/DDTValidator
      - harbor.core.l2.L2Generator
      - harbor.core.diary.DiaryManager
      - harbor.core.audit.SemanticGuard

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
    parser = argparse.ArgumentParser(prog="harbor", description="Harbor-spec CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build-index", help="Build or update L3 index cache")
    p_build.add_argument("--no-incremental", action="store_true")
    p_build.add_argument("--code-root", action="append", default=None)
    p_build.add_argument("--cache-dir", type=str, default=None)

    p_config = sub.add_parser("config", help="Manage Harbor config")
    p_cfg_sub = p_config.add_subparsers(dest="cfg_cmd", required=True)
    p_cfg_list = p_cfg_sub.add_parser("list", help="List current config values")
    p_cfg_add = p_cfg_sub.add_parser("add", help="Add a path to code_roots")
    p_cfg_add.add_argument("path", type=str)
    p_cfg_remove = p_cfg_sub.add_parser("remove", help="Remove a path from code_roots")
    p_cfg_remove.add_argument("path", type=str)

    p_status = sub.add_parser("status", help="Show Harbor context status (no implicit index update)")
    p_ddt_validate = sub.add_parser("ddt", help="DDT commands")
    p_ddt_sub = p_ddt_validate.add_subparsers(dest="ddt_cmd", required=True)
    p_ddt_val = p_ddt_sub.add_parser("validate", help="Validate DDT bindings against index and version map")
    p_ddt_val.add_argument("--module", type=str, default=None)
    p_ddt_val.add_argument("--func", type=str, default=None)
    p_gen = sub.add_parser("gen", help="Generate views")
    p_gen_sub = p_gen.add_subparsers(dest="gen_cmd", required=True)
    p_gen_l2 = p_gen_sub.add_parser(
        "l2",
        help="Generate L2 README for a module",
        description=(
            "Generate Anchor (L2) README for the specified module directory.\n\n"
            "Examples:\n"
            "  harbor gen l2 --module harbor/core\n"
            "  harbor gen l2 --module harbor/core --write\n"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    p_gen_l2.add_argument(
        "--module",
        type=str,
        required=True,
        help="Target module directory (e.g. harbor/core) to generate L2 view",
    )
    p_gen_l2.add_argument(
        "--write",
        action="store_true",
        help="Write README.md to the module directory; default prints Markdown to console",
    )
    p_gen_l2.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing README.md when used with --write",
    )
    p_diary = sub.add_parser("diary", help="Diary commands")
    p_diary_sub = p_diary.add_subparsers(dest="diary_cmd", required=True)
    p_diary_log = p_diary_sub.add_parser("log", help="Log a diary entry")
    p_diary_log.add_argument("--summary", type=str, required=True)
    p_diary_log.add_argument("--type", type=str, default="feature")
    p_diary_log.add_argument("--importance", type=str, default="normal")
    p_diary_log.add_argument("--visibility", type=str, default="internal")
    p_diary_log.add_argument("--details", type=str, default=None)
    p_diary_log.add_argument("--ref-commit", type=str, default=None)
    p_diary_log.add_argument("--author", type=str, default=None)
    p_diary_log.add_argument("--ts", type=str, default=None)
    p_diary_export = p_diary_sub.add_parser("export", help="Export diary entries to Markdown")
    p_diary_export.add_argument("--since", type=str, default=None)
    p_diary_export.add_argument("--visibility", type=str, default="repo")
    p_diary_draft = p_diary_sub.add_parser("draft", help="Generate diary draft with AI")
    p_diary_draft.add_argument("--visibility", type=str, default="repo")
    p_diary_draft.add_argument("--debug", action="store_true", default=False)
    p_audit = sub.add_parser("audit", help="Audit commands")
    p_audit.add_argument("--semantic", action="store_true")
    p_audit.add_argument("--diff-only", action="store_true", default=True)
    p_audit.add_argument("--debug", action="store_true", default=False)
    p_init = sub.add_parser("init", help="Initialize Harbor config")
    p_init.add_argument("--force", action="store_true")

    args = parser.parse_args()
    if args.command == "build-index":
        code_roots = args.code_root
        cache_dir = Path(args.cache_dir) if args.cache_dir else None
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
            task_id = progress.add_task("[扫描中] 初始化...", total=0)
            total_set = False
            for ev in builder.iter_build(incremental=not args.no_incremental):
                if not total_set:
                    progress.update(task_id, total=ev.total)
                    total_set = True
                if ev.status == "scanning":
                    progress.update(task_id, description=f"[扫描中] {ev.path}")
                elif ev.status == "parsed":
                    scanned += 1
                    updated += 1
                    items_total += ev.items_count
                    progress.update(task_id, advance=1, description=f"[完成] {ev.path}")
                elif ev.status == "skipped":
                    scanned += 1
                    skipped += 1
                    progress.update(task_id, advance=1, description=f"[跳过] {ev.path}")
                elif ev.status == "error":
                    scanned += 1
                    progress.update(task_id, advance=1, description=f"[错误] {ev.path}")
        print(
            f"scanned={scanned} updated={updated} skipped={skipped} "
            f"items={items_total} cache={builder.cache_file.as_posix()}"
        )
    elif args.command == "config" and args.cfg_cmd == "list":
        cfg_path = Path(".harbor/config.yaml")
        data = {}
        if cfg_path.exists():
            try:
                data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
            except Exception:
                data = {}
        code_roots = data.get("code_roots", ["harbor/**"])
        exclude_paths = data.get("exclude_paths", [])
        profile = data.get("profile", "enforce_l3")
        table = Table(title="Harbor Config")
        table.add_column("Key", style="bold")
        table.add_column("Value")
        table.add_row("profile", profile)
        table.add_row("code_roots", ", ".join(code_roots))
        table.add_row("exclude_paths", ", ".join(exclude_paths))
        Console().print(table)
    elif args.command == "config" and args.cfg_cmd == "add":
        cfg_path = Path(".harbor/config.yaml")
        data = {}
        if cfg_path.exists():
            try:
                data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
            except Exception:
                data = {}
        roots = data.get("code_roots", [])
        p = args.path
        if p not in roots:
            roots.append(p)
        data["code_roots"] = roots
        data.setdefault("exclude_paths", [])
        data.setdefault("profile", data.get("profile", "enforce_l3"))
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        cfg_path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
        print(f"Added '{p}' to code_roots.")
    elif args.command == "config" and args.cfg_cmd == "remove":
        cfg_path = Path(".harbor/config.yaml")
        data = {}
        if cfg_path.exists():
            try:
                data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
            except Exception:
                data = {}
        roots = data.get("code_roots", [])
        p = args.path
        if p in roots:
            roots = [x for x in roots if x != p]
            data["code_roots"] = roots
            cfg_path.parent.mkdir(parents=True, exist_ok=True)
            cfg_path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
            print(f"Removed '{p}' from code_roots.")
        else:
            print("No changes. Path not in code_roots.")
    elif args.command == "status":
        console = Console()
        with console.status("[bold blue][Scanning] Checking file system changes...", spinner="dots"):
            eng = SyncEngine()
            rep = eng.check_status()
        total = sum(rep.counts.values())
        if total == 0:
            print("No changes detected.")
            return
        print("Harbor Context Status:")
        if rep.drift:
            print("\nChanges to implementation (Drift):")
            for e in rep.drift:
                print(f"  M {e.id} ({e.details})")
        if rep.contract_changed:
            print("\nChanges to contract:")
            for e in rep.contract_changed:
                print(f"  C {e.id} ({e.details})")
        if rep.modified:
            print("\nChanges (Body + Contract):")
            for e in rep.modified:
                print(f"  M {e.id} ({e.details})")
        if rep.untracked:
            print("\nUntracked functions:")
            for e in rep.untracked:
                print(f"  ? {e.id}")
        if rep.missing:
            print("\nMissing functions:")
            for e in rep.missing:
                print(f"  ! {e.id}")
    elif args.command == "ddt" and args.ddt_cmd == "validate":
        scanner = DDTScanner()
        bindings = scanner.scan_tests()
        if args.func:
            bindings = [b for b in bindings if b.func_id == args.func]
        if args.module:
            bindings = [b for b in bindings if b.func_id.startswith(args.module)]
        validator = DDTValidator()
        rep = validator.validate(bindings)
        print("Harbor DDT Validation:")
        print(f"Bindings scanned: {len(bindings)}")
        if rep.valid:
            print("\nValid bindings:")
            for b in rep.valid:
                print(f"  OK {b.func_id} v={b.l3_version} strategy={b.strategy} ({b.test_name} @ {b.file_path})")
        if rep.violations:
            print("\nViolations:")
            for typ, b, msg in rep.violations:
                print(f"  [!] {typ.upper()} {b.func_id} v={b.l3_version} strategy={b.strategy} ({b.test_name} @ {b.file_path}) :: {msg}")
        if not rep.valid and not rep.violations:
            print("\nNo DDT bindings found.")
    elif args.command == "gen" and args.gen_cmd == "l2":
        gen = L2Generator()
        md = gen.generate(args.module)
        if args.write:
            target = gen.write(args.module, md, force=args.force)
            if target is None:
                print("No changes needed.")
            else:
                print(f"Wrote: {target.as_posix()}")
        else:
            print(md)
    elif args.command == "diary" and args.diary_cmd == "log":
        mgr = DiaryManager()
        entry = mgr.log(
            summary=args.summary,
            type=args.type,
            importance=args.importance,
            visibility=args.visibility,
            details=args.details,
            ref_commit=args.ref_commit,
            author=args.author,
            ts=args.ts,
        )
        print(entry.to_json())
    elif args.command == "diary" and args.diary_cmd == "export":
        mgr = DiaryManager()
        md = mgr.export_markdown(since=args.since, min_visibility=args.visibility or "repo")
        print(md)
    elif args.command == "diary" and args.diary_cmd == "draft":
        console = Console()
        with console.status("[bold blue][Status] Analyzing code changes...", spinner="dots"):
            eng = SyncEngine()
            rep = eng.check_status()
        if (rep.counts.get("drift", 0) + rep.counts.get("modified", 0)) == 0:
            print("No changes detected. Nothing to draft.")
            print("\n[Tip] 'diary draft' analyzes unindexed changes (Drift/Modified).")
            print("If you just ran 'harbor build-index', the snapshot matches current code.")
            print("Modify code first, then run 'harbor diary draft' before updating the index.")
            return
        drafter = DiaryDrafter(sync_engine=eng)
        try:
            with console.status("[bold magenta][AI] Drafting diary entry...", spinner="line"):
                draft = drafter.generate_draft()
        except LLMNotConfiguredError as e:
            print(str(e))
            print("请在环境中设置 HARBOR_LLM_PROVIDER=openai 与 HARBOR_LLM_API_KEY，再重试。")
            return
        except Exception as e:
            msg = str(e)
            lc = msg.lower()
            if ("context" in lc and "length" in lc) or ("token" in lc and ("too many" in lc or "exceed" in lc)) or ("maximum context" in lc) or ("prompt too long" in lc):
                print("提示：当前上下文可能超过模型限制。")
                choice = Prompt.ask("是否使用简化上下文继续？ [Y]es / [N]o", choices=["Y", "N", "y", "n"], default="Y")
                if choice.upper() == "Y":
                    with console.status("[bold magenta][AI] Drafting with simplified context...", spinner="line"):
                        try:
                            draft = drafter.generate_draft(limit=6000)
                        except Exception as e2:
                            print(f"AI drafting failed: {str(e2)}")
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
                print(f"AI drafting failed: {str(e)}")
                if args.debug:
                    provider = resolve_provider()
                    print(f"[DEBUG] Provider: {provider.name} Model: {getattr(provider, 'model', 'n/a')}")
                    print("[DEBUG] 提示：确保端点支持 JSON 结构化输出（response_format=json_object）。")
                    print("[DEBUG] 如为 ERNIE 兼容端点，请设置 HARBOR_LLM_BASE_URL 和 HARBOR_LLM_MODEL=ernie-4.0。")
                    if getattr(drafter, "last_prompt", None):
                        print(f"[DEBUG] Prompt >>>\n{drafter.last_prompt or ''}")
                    if getattr(drafter, "last_output", None):
                        print(f"[DEBUG] Raw <<<\n{drafter.last_output or ''}")
                return
        if not draft:
            print("No changes detected. Nothing to draft.")
            return
        panel_text = (
            f"[bold]Summary[/bold]: {draft.get('summary','')}\n"
            f"[bold]Type[/bold]: {draft.get('type','')}\n"
            f"[bold]Importance[/bold]: {draft.get('importance','')}\n"
            f"[bold]Details[/bold]:\n{draft.get('details','')}"
        )
        console.print(Panel(panel_text, title="Diary Draft (AI)", border_style="green"))
        choice = Prompt.ask("Save this entry? [Y]es / [E]dit summary / [N]o", choices=["Y", "E", "N", "y", "e", "n"], default="Y")
        ans = choice.upper()
        if ans == "N":
            print("Discarded.")
            return
        summary_final = draft.get("summary", "")
        if ans == "E":
            summary_final = Prompt.ask("New summary", default=summary_final)
        mgr = DiaryManager()
        entry = mgr.log(
            summary=summary_final,
            type=draft.get("type", "chore"),
            importance=draft.get("importance", "normal"),
            visibility=args.visibility or "repo",
            details=draft.get("details"),
        )
        print(entry.to_json())
    elif args.command == "audit" and args.semantic:
        eng = SyncEngine()
        rep = eng.check_status()
        provider = resolve_provider()
        guard = SemanticGuard()
        model = getattr(provider, "model", "n/a")
        print(f"Harbor Semantic Audit (Provider: {provider.name} Model: {model}):")
        targets = []
        targets.extend(rep.drift)
        targets.extend(rep.modified)
        if not args.diff_only:
            targets.extend(rep.contract_changed)
        print(f"targets={len(targets)}")
        out_lines = []
        for e in targets:
            try:
                src = Path(e.file_path).read_text(encoding="utf-8")
            except Exception as ex:
                out_lines.append(f"ERROR {e.id} :: {str(ex)}")
                continue
            adapter = IndexBuilder().adapter  # reuse python adapter
            contracts = list(adapter.parse_file(e.file_path))
            matched = None
            for fc in contracts:
                if fc.id == e.id:
                    matched = fc
                    break
            if matched is None:
                out_lines.append(f"ERROR {e.id} :: contract not found")
                continue
            res = guard.audit(matched, src, provider)
            if args.debug:
                print(f"[DEBUG] Prompt >>>\n{res.prompt or ''}\n[DEBUG] Raw <<<\n{res.raw_output or ''}")
            if res.status == "OK":
                out_lines.append(f"OK {e.id}")
            elif res.status == "MISMATCH":
                out_lines.append(f"POSSIBLE_SEMANTIC_DRIFT {e.id} :: {res.reason or ''}")
            else:
                out_lines.append(f"ERROR {e.id} :: {res.reason or ''}")
        if not out_lines:
            print("No targets.")
        else:
            for ln in out_lines:
                print(ln)
    elif args.command == "init":
        init = Initializer()
        if init.config_path.exists() and not args.force:
            print("Config file already exists.")
            return
        roots = init.detect_code_roots()
        print(f"Auto-detected code roots: {roots}")
        init.write_config(roots, force=args.force)
        print("Initialized Harbor in current directory.")
        print("Run 'harbor build-index' to start.")


if __name__ == "__main__":
    main()

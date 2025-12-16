import argparse
from pathlib import Path

from harbor.core.index import IndexBuilder
from harbor.core.sync import SyncEngine
from harbor.core.ddt import DDTScanner, DDTValidator
from harbor.core.l2 import L2Generator
from harbor.core.diary import DiaryManager
from harbor.core.audit import SemanticGuard, resolve_provider
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

    p_status = sub.add_parser("status", help="Show Harbor context status (no implicit index update)")
    p_ddt_validate = sub.add_parser("ddt", help="DDT commands")
    p_ddt_sub = p_ddt_validate.add_subparsers(dest="ddt_cmd", required=True)
    p_ddt_val = p_ddt_sub.add_parser("validate", help="Validate DDT bindings against index and version map")
    p_ddt_val.add_argument("--module", type=str, default=None)
    p_ddt_val.add_argument("--func", type=str, default=None)
    p_gen = sub.add_parser("gen", help="Generate views")
    p_gen_sub = p_gen.add_subparsers(dest="gen_cmd", required=True)
    p_gen_l2 = p_gen_sub.add_parser("l2", help="Generate L2 README for a module")
    p_gen_l2.add_argument("--module", type=str, required=True)
    p_gen_l2.add_argument("--write", action="store_true")
    p_gen_l2.add_argument("--force", action="store_true")
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
        report = builder.build(incremental=not args.no_incremental)
        print(
            f"scanned={report.scanned_files} updated={report.updated_files} skipped={report.skipped_files} "
            f"items={report.total_items} cache={report.cache_path} elapsed_ms={report.elapsed_ms}"
        )
    elif args.command == "status":
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

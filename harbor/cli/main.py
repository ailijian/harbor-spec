import argparse
from pathlib import Path

from harbor.core.index import IndexBuilder
from harbor.core.sync import SyncEngine
from harbor.core.ddt import DDTScanner, DDTValidator
from harbor.core.l2 import L2Generator
from harbor.core.diary import DiaryManager


def main():
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

    args = parser.parse_args()
    if args.command == "build-index":
        code_roots = args.code_root
        cache_dir = Path(args.cache_dir) if args.cache_dir else None
        builder = IndexBuilder(code_roots=code_roots, cache_dir=cache_dir)
        report = builder.build(incremental=not args.no_incremental)
        print(f"scanned={report.scanned_files} updated={report.updated_files} skipped={report.skipped_files} items={report.total_items}")
        print(f"cache={report.cache_path} elapsed_ms={report.elapsed_ms}")
    elif args.command == "status":
        eng = SyncEngine()
        rep = eng.check_status()
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
        total = sum(rep.counts.values())
        if total == 0:
            print("\nNo changes detected.")
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
                print(f"  {typ.upper()} {b.func_id} v={b.l3_version} strategy={b.strategy} ({b.test_name} @ {b.file_path}) :: {msg}")
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


if __name__ == "__main__":
    main()

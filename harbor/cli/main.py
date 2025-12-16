import argparse
from pathlib import Path

from harbor.core.index import IndexBuilder
from harbor.core.sync import SyncEngine
from harbor.core.ddt import DDTScanner, DDTValidator


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


if __name__ == "__main__":
    main()

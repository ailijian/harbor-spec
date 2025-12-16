import argparse
from pathlib import Path

from harbor.core.index import IndexBuilder
from harbor.core.sync import SyncEngine


def main():
    parser = argparse.ArgumentParser(prog="harbor", description="Harbor-spec CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build-index", help="Build or update L3 index cache")
    p_build.add_argument("--no-incremental", action="store_true")
    p_build.add_argument("--code-root", action="append", default=None)
    p_build.add_argument("--cache-dir", type=str, default=None)

    p_status = sub.add_parser("status", help="Show Harbor context status (no implicit index update)")

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


if __name__ == "__main__":
    main()

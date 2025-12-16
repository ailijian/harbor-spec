import argparse
from pathlib import Path

from harbor.core.index import IndexBuilder


def main():
    parser = argparse.ArgumentParser(prog="harbor", description="Harbor-spec CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build-index", help="Build or update L3 index cache")
    p_build.add_argument("--no-incremental", action="store_true")
    p_build.add_argument("--code-root", action="append", default=None)
    p_build.add_argument("--cache-dir", type=str, default=None)

    args = parser.parse_args()
    if args.command == "build-index":
        code_roots = args.code_root
        cache_dir = Path(args.cache_dir) if args.cache_dir else None
        builder = IndexBuilder(code_roots=code_roots, cache_dir=cache_dir)
        report = builder.build(incremental=not args.no_incremental)
        print(f"scanned={report.scanned_files} updated={report.updated_files} skipped={report.skipped_files} items={report.total_items}")
        print(f"cache={report.cache_path} elapsed_ms={report.elapsed_ms}")


if __name__ == "__main__":
    main()


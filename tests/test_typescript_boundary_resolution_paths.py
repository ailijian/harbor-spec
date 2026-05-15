import json
import textwrap
from pathlib import Path

from harbor.adapters.typescript.adapter import TypeScriptAdapter


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).strip(), encoding="utf-8")


def test_boundary_resolution_supports_index_fallback_and_tsconfig_paths(tmp_path: Path):
    (tmp_path / "tsconfig.json").write_text(
        json.dumps(
            {
                "compilerOptions": {
                    "baseUrl": ".",
                    "paths": {
                        "@app/*": ["src/*"],
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    _write(
        tmp_path / "src" / "lib" / "foo.ts",
        """
        /**
         * @param value input
         * @returns output
         */
        export function foo(value: string): string {
          return value.trim();
        }
        """,
    )
    _write(
        tmp_path / "src" / "lib" / "index.ts",
        """
        export { foo } from "./foo";
        """,
    )
    _write(
        tmp_path / "src" / "public.ts",
        """
        export { foo } from "@app/lib";
        """,
    )

    foo = next(
        item
        for item in TypeScriptAdapter().parse_file(tmp_path / "src" / "lib" / "foo.ts")
        if item.qualified_name == "foo"
    )

    assert foo.metadata["public_boundary_state"] == "re_exported_surface"
    assert foo.metadata["public_boundary_confidence"] == "medium"
    assert foo.metadata["public_boundary_evidence_kinds"] == [
        "direct_export",
        "named_re_export",
    ]
    re_export_sources = {
        Path(item["source_file"]).name
        for item in foo.metadata["public_boundary_evidence_items"]
        if item["kind"] == "named_re_export"
    }
    assert re_export_sources == {"index.ts", "public.ts"}

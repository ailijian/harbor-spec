import textwrap
from pathlib import Path

from harbor.adapters.typescript.adapter import TypeScriptAdapter


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).strip(), encoding="utf-8")


def _subject(path: Path, name: str):
    return next(item for item in TypeScriptAdapter().parse_file(path) if item.qualified_name == name)


def test_re_export_resolver_adds_named_star_and_default_as_evidence(tmp_path: Path):
    _write(
        tmp_path / "src" / "foo.ts",
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
        tmp_path / "src" / "defaults.ts",
        """
        /**
         * @returns output
         */
        export default function createUser(): string {
          return "ok";
        }
        """,
    )
    _write(
        tmp_path / "src" / "barrel.ts",
        """
        export { foo as publicFoo } from "./foo";
        export * from "./foo";
        export { default as CreateUser } from "./defaults";
        """,
    )

    foo = _subject(tmp_path / "src" / "foo.ts", "foo")
    create_user = _subject(tmp_path / "src" / "defaults.ts", "createUser")

    assert foo.metadata["public_boundary_state"] == "re_exported_surface"
    assert foo.metadata["public_boundary_confidence"] == "medium"
    assert foo.metadata["public_boundary_evidence_kinds"] == [
        "direct_export",
        "named_re_export",
        "star_re_export",
    ]
    assert {item["source_ref"] for item in foo.metadata["public_boundary_evidence_items"]} >= {
        "foo as publicFoo",
        "*",
    }

    assert create_user.metadata["public_boundary_state"] == "re_exported_surface"
    assert create_user.metadata["public_boundary_confidence"] == "medium"
    assert create_user.metadata["public_boundary_evidence_kinds"] == [
        "default_export",
        "named_re_export",
    ]
    assert create_user.metadata["public_boundary_reason"] == (
        "Target default export is re-exported from 'barrel.ts' as 'CreateUser'."
    )


def test_unresolved_re_export_is_ignored_without_crashing(tmp_path: Path):
    _write(
        tmp_path / "src" / "foo.ts",
        """
        export function foo(value: string): string {
          return value.trim();
        }
        """,
    )
    _write(
        tmp_path / "src" / "barrel.ts",
        """
        export { foo } from "@missing/foo";
        export * from "@missing/foo";
        """,
    )

    foo = _subject(tmp_path / "src" / "foo.ts", "foo")

    assert foo.metadata["public_boundary_state"] == "direct_export_only"
    assert foo.metadata["public_boundary_evidence_kinds"] == ["direct_export"]

import textwrap
from pathlib import Path

from harbor.adapters.typescript.adapter import TypeScriptAdapter


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).strip(), encoding="utf-8")


def test_custom_entrypoints_preset_adds_configured_entrypoint_evidence(tmp_path: Path):
    _write(
        tmp_path / "src" / "internal" / "service.ts",
        """
        /**
         * @param value input
         * @returns output
         */
        export function api(value: string): string {
          return value.trim();
        }
        """,
    )
    _write(
        tmp_path / "src" / "public.ts",
        """
        export { api } from "./internal/service";
        """,
    )

    adapter = TypeScriptAdapter(
        config={
            "public_boundary": {
                "mode": "custom_entrypoints",
                "entrypoints": ["src/public.ts"],
            }
        }
    )
    subject = next(
        item
        for item in adapter.parse_file(tmp_path / "src" / "internal" / "service.ts")
        if item.qualified_name == "api"
    )

    assert subject.metadata["boundary_preset_mode"] == "custom_entrypoints"
    assert subject.metadata["public_boundary_state"] == "configured_entrypoint_surface"
    assert subject.metadata["public_boundary_confidence"] == "medium"
    assert set(subject.metadata["public_boundary_evidence_kinds"]) == {
        "configured_entrypoint",
        "direct_export",
        "named_re_export",
    }

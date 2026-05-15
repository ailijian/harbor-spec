import json
import textwrap
from pathlib import Path

from harbor.adapters.typescript.adapter import TypeScriptAdapter


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).strip(), encoding="utf-8")


def test_package_exports_default_dist_mapping_adds_high_confidence_evidence(tmp_path: Path):
    feature_path = tmp_path / "src" / "feature.ts"
    _write(
        feature_path,
        """
        /**
         * @param value input
         * @returns output
         */
        export function feature(value: string): string {
          return value.trim();
        }
        """,
    )
    base_adapter = TypeScriptAdapter()
    before = next(item for item in base_adapter.parse_file(feature_path) if item.qualified_name == "feature")

    _write(
        tmp_path / "src" / "index.ts",
        """
        export { feature } from "./feature";
        """,
    )
    (tmp_path / "package.json").write_text(
        json.dumps({"name": "demo", "exports": {".": "./dist/index.js", "./feature": "./dist/feature.js"}}),
        encoding="utf-8",
    )

    adapter = TypeScriptAdapter(config={"public_boundary": {"mode": "package_public"}})
    after = next(item for item in adapter.parse_file(feature_path) if item.qualified_name == "feature")

    assert before.contract_hash == after.contract_hash
    assert after.metadata["public_boundary_state"] == "package_export_surface"
    assert after.metadata["public_boundary_confidence"] == "high"
    assert after.metadata["boundary_preset_mode"] == "package_public"
    assert set(after.metadata["public_boundary_evidence_kinds"]) == {
        "direct_export",
        "named_re_export",
        "package_export",
    }
    package_items = [
        item
        for item in after.metadata["public_boundary_evidence_items"]
        if item["kind"] == "package_export"
    ]
    assert len(package_items) == 2
    assert {item["source_ref"] for item in package_items} == {".", "./feature"}


def test_package_exports_source_mapping_and_malformed_package_json_degrade_safely(tmp_path: Path):
    feature_path = tmp_path / "src" / "feature.ts"
    _write(
        feature_path,
        """
        export function feature(value: string): string {
          return value.trim();
        }
        """,
    )
    _write(
        tmp_path / "src" / "public.ts",
        """
        export { feature } from "./feature";
        """,
    )
    (tmp_path / "package.json").write_text(
        json.dumps({"name": "demo", "exports": {".": "./build/public.js"}}),
        encoding="utf-8",
    )

    adapter = TypeScriptAdapter(
        config={
            "public_boundary": {
                "mode": "package_public",
                "source_mappings": {"build/public.js": "src/public.ts"},
            }
        }
    )
    resolved = next(item for item in adapter.parse_file(feature_path) if item.qualified_name == "feature")

    assert resolved.metadata["public_boundary_state"] == "package_export_surface"
    assert "package_export" in resolved.metadata["public_boundary_evidence_kinds"]

    (tmp_path / "package.json").write_text("{not-json", encoding="utf-8")
    degraded = next(item for item in adapter.parse_file(feature_path) if item.qualified_name == "feature")

    assert degraded.metadata["public_boundary_state"] == "re_exported_surface"
    assert degraded.metadata["public_boundary_confidence"] == "medium"
    assert "package_export" not in degraded.metadata["public_boundary_evidence_kinds"]

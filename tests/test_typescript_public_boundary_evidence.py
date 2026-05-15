import textwrap
from pathlib import Path

from harbor.adapters.registry import AdapterRegistry
from harbor.adapters.typescript.adapter import TypeScriptAdapter
from harbor.adapters.typescript.public_boundary import (
    PublicBoundaryEvidence,
    PublicBoundaryEvidenceKind,
    build_public_boundary_metadata,
    normalize_public_boundary_evidence_items,
    normalize_typescript_governance_config,
)


def test_public_boundary_evidence_items_are_sorted_and_deduped_deterministically():
    items = normalize_public_boundary_evidence_items(
        [
            PublicBoundaryEvidence(
                kind=PublicBoundaryEvidenceKind.DIRECT_EXPORT,
                confidence="medium",
                source_file="src/a.ts",
                source_ref="foo",
                resolved_target="typescript:src/a.ts:function:foo",
                reason="second",
            ),
            PublicBoundaryEvidence(
                kind=PublicBoundaryEvidenceKind.DIRECT_EXPORT,
                confidence="high",
                source_file="src/a.ts",
                source_ref="foo",
                resolved_target="typescript:src/a.ts:function:foo",
                reason="first",
            ),
            PublicBoundaryEvidence(
                kind=PublicBoundaryEvidenceKind.PACKAGE_EXPORT,
                confidence="high",
                source_file="package.json",
                source_ref="exports",
                resolved_target="typescript:src/a.ts:function:foo",
                reason="package",
            ),
        ]
    )

    assert [item.kind.value for item in items] == ["direct_export", "package_export"]
    assert items[0].confidence == "high"
    assert items[0].reason == "first"


def test_public_boundary_metadata_keeps_boundary_fields_additive():
    metadata = build_public_boundary_metadata(
        evidence_items=[
            PublicBoundaryEvidence(
                kind=PublicBoundaryEvidenceKind.DIRECT_EXPORT,
                confidence="low",
                source_file="src/service.ts",
                source_ref="api",
                resolved_target="typescript:src/service.ts:function:api",
                reason="Target is exported directly from its declaring source file.",
            )
        ],
        preset_mode="legacy_exported",
        is_exported=True,
    )

    assert metadata["public_boundary_state"] == "direct_export_only"
    assert metadata["public_boundary_confidence"] == "low"
    assert metadata["public_boundary_evidence_kinds"] == ["direct_export"]
    assert metadata["public_boundary_evidence_items"][0]["kind"] == "direct_export"
    assert metadata["boundary_preset_mode"] == "legacy_exported"


def test_public_boundary_config_defaults_are_backward_compatible():
    cfg = normalize_typescript_governance_config({})

    assert cfg["public_boundary"]["mode"] == "legacy_exported"
    assert cfg["public_boundary"]["follow_re_exports"] is True
    assert cfg["public_boundary"]["read_package_exports"] is True
    assert cfg["public_boundary"]["use_tsconfig_paths"] is True
    assert cfg["public_boundary"]["declaration_surface_preview"] is False
    assert cfg["public_boundary"]["entrypoints"] == []
    assert cfg["public_boundary"]["source_mappings"] == {}
    assert cfg["contract_required_strategy"] == "legacy_exported"


def test_public_boundary_config_normalizes_invalid_values_safely():
    cfg = normalize_typescript_governance_config(
        {
            "public_boundary": {
                "mode": "unknown_mode",
                "follow_re_exports": "off",
                "read_package_exports": "yes",
                "use_tsconfig_paths": "0",
                "declaration_surface_preview": "1",
                "entrypoints": ["src/index.ts", "", "src/public.ts"],
                "source_mappings": {"dist/index.js": "src/index.ts", "": "ignored"},
            },
            "contract_required_strategy": "unexpected",
        }
    )

    assert cfg["public_boundary"]["mode"] == "legacy_exported"
    assert cfg["public_boundary"]["follow_re_exports"] is False
    assert cfg["public_boundary"]["read_package_exports"] is True
    assert cfg["public_boundary"]["use_tsconfig_paths"] is False
    assert cfg["public_boundary"]["declaration_surface_preview"] is True
    assert cfg["public_boundary"]["entrypoints"] == ["src/index.ts", "src/public.ts"]
    assert cfg["public_boundary"]["source_mappings"] == {"dist/index.js": "src/index.ts"}
    assert cfg["contract_required_strategy"] == "legacy_exported"


def test_registry_accepts_legacy_typescript_config_without_new_boundary_fields():
    registry = AdapterRegistry.from_config(
        {
            "languages": {
                "python": {"enabled": True},
                "typescript": {"enabled": True},
            }
        }
    )

    adapter = registry.get_adapter("typescript")
    assert adapter is not None
    assert registry.is_enabled("typescript") is True


def test_typescript_adapter_emits_public_boundary_metadata_without_changing_contract_hash(tmp_path: Path):
    target = tmp_path / "service.ts"
    target.write_text(
        textwrap.dedent(
            """
            /**
             * @param value input
             * @returns output
             */
            export function api(value: string): string {
              return value.trim();
            }
            """
        ).strip(),
        encoding="utf-8",
    )
    subject = next(item for item in TypeScriptAdapter().parse_file(target) if item.qualified_name == "api")

    assert subject.contract_hash is not None
    assert subject.metadata["public_boundary_state"] == "direct_export_only"
    assert subject.metadata["public_boundary_confidence"] == "low"
    assert subject.metadata["public_boundary_evidence_kinds"] == ["direct_export"]
    assert subject.metadata["public_boundary_evidence_items"] == [
        {
            "kind": "direct_export",
            "confidence": "low",
            "source_file": target.as_posix(),
            "source_ref": "api",
            "resolved_target": subject.target_id,
            "reason": "Target is exported directly from its declaring source file.",
        }
    ]
    assert subject.metadata["boundary_preset_mode"] == "legacy_exported"

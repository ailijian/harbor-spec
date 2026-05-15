from pathlib import Path

import pytest
import yaml

from harbor.core.ddt import DDTBinding
from harbor.core.verification import (
    DEFAULT_TYPESCRIPT_DDT_PREVIEW_BINDINGS_FILE,
    TYPESCRIPT_DDT_PREVIEW_SCHEMA_VERSION,
    VerificationBinding,
    TypeScriptDDTPreviewConfig,
    load_typescript_ddt_preview_sidecar,
    normalize_repo_relative_path,
    resolve_typescript_ddt_preview_config,
)


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


def test_verification_binding_maps_python_ddt_without_polluting_comparison_metadata() -> None:
    binding = DDTBinding(
        func_id="harbor.core.sync.SyncEngine.check_status",
        l3_version=3,
        strategy="strict",
        file_path="tests/test_sync_engine.py",
        test_name="test_sync_engine_drift_detection",
    )

    verification = binding.to_verification_binding()

    assert isinstance(verification, VerificationBinding)
    assert verification.language == "python"
    assert verification.func_id == "harbor.core.sync.SyncEngine.check_status"
    assert verification.target_id is None
    assert verification.target_ref.func_id == "harbor.core.sync.SyncEngine.check_status"
    assert verification.target_ref.primary_anchor() == "harbor.core.sync.SyncEngine.check_status"
    assert verification.binding_kind == "ddt"
    assert verification.version_ref == "l3:3"
    payload = verification.to_dict()
    assert "contract_source_kinds" not in payload
    assert "public_boundary_evidence_kinds" not in payload
    assert "contract_hash" not in payload
    assert "body_hash" not in payload


def test_verification_binding_uses_target_id_as_primary_anchor_for_typescript_sidecar(tmp_path: Path) -> None:
    repo_root = tmp_path
    sidecar_path = repo_root / DEFAULT_TYPESCRIPT_DDT_PREVIEW_BINDINGS_FILE
    _write_yaml(
        sidecar_path,
        {
            "schema_version": TYPESCRIPT_DDT_PREVIEW_SCHEMA_VERSION,
            "bindings": [
                {
                    "binding_id": "api-smoke",
                    "target_id": "typescript:src/api.ts:function:api",
                    "test_asset": {
                        "path": r"tests\typescript\api.test.ts",
                        "label": "api smoke",
                    },
                    "strategy": "preview_reference",
                    "contract_expectation": "tsdoc_present",
                    "note": "preview only",
                }
            ],
        },
    )

    config = resolve_typescript_ddt_preview_config(
        {
            "verification": {
                "typescript_ddt_preview": {
                    "enabled": True,
                }
            }
        }
    )
    sidecar = load_typescript_ddt_preview_sidecar(repo_root, config)

    assert sidecar is not None
    assert sidecar.schema_version == TYPESCRIPT_DDT_PREVIEW_SCHEMA_VERSION
    assert sidecar.source_path == sidecar_path.resolve()
    binding = sidecar.bindings[0]
    assert binding.language == "typescript"
    assert binding.target_id == "typescript:src/api.ts:function:api"
    assert binding.func_id is None
    assert binding.target_ref.primary_anchor() == "typescript:src/api.ts:function:api"
    assert binding.test_asset.path == "tests/typescript/api.test.ts"
    assert binding.metadata["contract_expectation"] == "tsdoc_present"
    assert binding.metadata["note"] == "preview only"

def test_typescript_ddt_preview_config_defaults_disabled_and_safe() -> None:
    config = resolve_typescript_ddt_preview_config({})
    assert config == TypeScriptDDTPreviewConfig(
        enabled=False,
        bindings_file=DEFAULT_TYPESCRIPT_DDT_PREVIEW_BINDINGS_FILE,
        require_contract_source=True,
        require_public_boundary=False,
    )


def test_typescript_ddt_preview_disabled_does_not_parse_sidecar(tmp_path: Path) -> None:
    sidecar_path = tmp_path / ".harbor" / "ddt" / "typescript-bindings.yaml"
    sidecar_path.parent.mkdir(parents=True, exist_ok=True)
    sidecar_path.write_text("schema_version: [invalid", encoding="utf-8")

    config = resolve_typescript_ddt_preview_config(
        {
            "verification": {
                "typescript_ddt_preview": {
                    "enabled": False,
                    "bindings_file": ".harbor/ddt/typescript-bindings.yaml",
                }
            }
        }
    )

    assert load_typescript_ddt_preview_sidecar(tmp_path, config) is None


def test_typescript_ddt_preview_rejects_repo_escape_in_test_asset_path(tmp_path: Path) -> None:
    sidecar_path = tmp_path / ".harbor" / "ddt" / "typescript-bindings.yaml"
    _write_yaml(
        sidecar_path,
        {
            "schema_version": TYPESCRIPT_DDT_PREVIEW_SCHEMA_VERSION,
            "bindings": [
                {
                    "binding_id": "bad-binding",
                    "target_id": "typescript:src/api.ts:function:api",
                    "test_asset": {"path": "../outside.test.ts"},
                    "strategy": "preview_strict",
                }
            ],
        },
    )
    config = resolve_typescript_ddt_preview_config(
        {
            "verification": {
                "typescript_ddt_preview": {
                    "enabled": True,
                }
            }
        }
    )

    with pytest.raises(ValueError, match="escapes repo root"):
        load_typescript_ddt_preview_sidecar(tmp_path, config)


def test_typescript_ddt_preview_rejects_unknown_strategy(tmp_path: Path) -> None:
    sidecar_path = tmp_path / ".harbor" / "ddt" / "typescript-bindings.yaml"
    _write_yaml(
        sidecar_path,
        {
            "schema_version": TYPESCRIPT_DDT_PREVIEW_SCHEMA_VERSION,
            "bindings": [
                {
                    "binding_id": "bad-strategy",
                    "target_id": "typescript:src/api.ts:function:api",
                    "test_asset": {"path": "tests/api.test.ts"},
                    "strategy": "preview_auto",
                }
            ],
        },
    )
    config = resolve_typescript_ddt_preview_config(
        {
            "verification": {
                "typescript_ddt_preview": {
                    "enabled": True,
                }
            }
        }
    )

    with pytest.raises(ValueError, match="preview_reference, preview_strict"):
        load_typescript_ddt_preview_sidecar(tmp_path, config)


def test_normalize_repo_relative_path_normalizes_windows_and_posix_forms(tmp_path: Path) -> None:
    assert (
        normalize_repo_relative_path(
            r"tests\typescript\api.test.ts",
            repo_root=tmp_path,
            field_name="test_asset.path",
        )
        == "tests/typescript/api.test.ts"
    )
    assert (
        normalize_repo_relative_path(
            "./tests/typescript/api.test.ts",
            repo_root=tmp_path,
            field_name="test_asset.path",
        )
        == "tests/typescript/api.test.ts"
    )

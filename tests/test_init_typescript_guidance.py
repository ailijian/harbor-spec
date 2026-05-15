from io import StringIO
from pathlib import Path

import yaml
from rich.console import Console

from harbor.core.init import Initializer
from harbor.core.init_wizard import InitWizard, InitWizardOptions


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_initializer_detects_typescript_hints_and_roots(tmp_path: Path):
    _write(
        tmp_path / "package.json",
        """{
  "name": "demo-pkg",
  "workspaces": ["packages/*"],
  "exports": {
    ".": "./dist/index.js"
  }
}
""",
    )
    _write(tmp_path / "tsconfig.json", "{}\n")
    _write(tmp_path / "pnpm-workspace.yaml", "packages:\n  - packages/*\n")
    _write(
        tmp_path / "src" / "index.ts",
        "export function api(): string { return 'ok'; }\n",
    )

    init = Initializer(cwd=tmp_path)
    stacks, roots, excludes = init.autodetect()
    hints = init.detect_typescript_hints()

    assert "TypeScript" in stacks
    assert "src/**" in roots
    assert "node_modules/**" in excludes
    assert hints.detected is True
    assert hints.package_json is True
    assert hints.tsconfig_json is True
    assert hints.package_exports is True
    assert hints.recommended_preset == "package_public"
    assert "src/index.ts" in hints.entrypoint_candidates
    assert "package.json#workspaces" in hints.workspace_markers
    assert "pnpm-workspace.yaml" in hints.workspace_markers


def test_init_wizard_noninteractive_keeps_typescript_guidance_advisory(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("harbor.core.init_wizard._is_tty", lambda: False)
    _write(tmp_path / "package.json", '{"name":"demo","exports":{"." :"./dist/index.js"}}\n')
    _write(tmp_path / "tsconfig.json", "{}\n")
    _write(tmp_path / "src" / "index.ts", "export const api = () => 'ok';\n")

    stream = StringIO()
    wiz = InitWizard(
        cwd=tmp_path,
        options=InitWizardOptions(
            language="zh",
            project="existing",
            governance=False,
            governance_docs=False,
            llm=False,
            update_gitignore=False,
        ),
        console=Console(file=stream, force_terminal=False, width=200),
    )
    result = wiz.run()
    config = yaml.safe_load((tmp_path / ".harbor" / "config" / "harbor.yaml").read_text(encoding="utf-8")) or {}

    assert "检测到 TypeScript 项目线索" in stream.getvalue()
    assert "推荐 preset" in stream.getvalue()
    assert config.get("languages") in (None, {})
    assert "src/**" in config.get("code_roots", [])
    assert any("未写入 languages.typescript" in note for note in result.notes)


def test_init_wizard_explicit_typescript_config_write_is_opt_in(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("harbor.core.init_wizard._is_tty", lambda: False)
    _write(tmp_path / "package.json", '{"name":"demo"}\n')
    _write(tmp_path / "tsconfig.json", "{}\n")
    _write(tmp_path / "src" / "index.ts", "export const api = () => 'ok';\n")

    InitWizard(
        cwd=tmp_path,
        options=InitWizardOptions(
            language="en",
            project="existing",
            governance=False,
            governance_docs=False,
            llm=False,
            update_gitignore=False,
            typescript_enabled=True,
            typescript_preset="custom_entrypoints",
            typescript_entrypoints=["src/index.ts"],
            typescript_contract_strategy="confirmed_boundary_advisory",
        ),
        console=Console(file=StringIO(), force_terminal=False, width=200),
    ).run()
    config = yaml.safe_load((tmp_path / ".harbor" / "config" / "harbor.yaml").read_text(encoding="utf-8")) or {}

    typescript_cfg = ((config.get("languages") or {}).get("typescript") or {})
    assert typescript_cfg.get("enabled") is True
    assert typescript_cfg.get("public_boundary", {}).get("mode") == "custom_entrypoints"
    assert typescript_cfg.get("public_boundary", {}).get("entrypoints") == ["src/index.ts"]
    assert typescript_cfg.get("contract_required_strategy") == "confirmed_boundary_advisory"

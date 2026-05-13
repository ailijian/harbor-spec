from pathlib import Path
import textwrap

from harbor.adapters.python.parser import FunctionContract
from harbor.adapters.python.parser import PythonAdapter
from harbor.adapters.registry import AdapterRegistry
from harbor.adapters.typescript.adapter import TypeScriptAdapter


def _fixture_root() -> Path:
    return Path(__file__).resolve().parent / "fixtures" / "ts_project_basic" / "src"


def _to_rel(paths: list[Path], root: Path) -> set[str]:
    return {path.resolve().relative_to(root.resolve()).as_posix() for path in paths}


def test_discover_files_default_only_ts():
    adapter = TypeScriptAdapter()
    root = _fixture_root()
    files = adapter.discover_files([root])

    assert {path.suffix for path in files} == {".ts"}
    assert _to_rel(files, root) == {
        "contract_presence.ts",
        "exports.ts",
        "malformed.ts",
        "nested/keep.ts",
        "scripts/runner.ts",
    }


def test_discover_files_default_excludes_tsx_js_jsx_dts():
    adapter = TypeScriptAdapter()
    root = _fixture_root()
    files = adapter.discover_files([root])
    rels = _to_rel(files, root)

    assert "view.tsx" not in rels
    assert "helper.js" not in rels
    assert "helper.jsx" not in rels
    assert "types.d.ts" not in rels


def test_discover_files_default_excludes_standard_build_directories():
    adapter = TypeScriptAdapter()
    root = _fixture_root()
    files = adapter.discover_files([root])
    rels = _to_rel(files, root)

    assert not any("node_modules/" in rel for rel in rels)
    assert not any("dist/" in rel for rel in rels)
    assert not any("build/" in rel for rel in rels)
    assert not any("coverage/" in rel for rel in rels)
    assert not any(".next/" in rel for rel in rels)
    assert not any(".nuxt/" in rel for rel in rels)
    assert not any("out/" in rel for rel in rels)
    assert not any(".vite/" in rel for rel in rels)
    assert not any(".turbo/" in rel for rel in rels)
    assert not any("storybook-static/" in rel for rel in rels)


def test_parse_file_detects_export_function():
    adapter = TypeScriptAdapter()
    items = adapter.parse_file(_fixture_root() / "exports.ts")

    hit = next(item for item in items if item.qualified_name == "foo")
    assert hit.symbol_kind == "function"
    assert hit.language == "typescript"
    assert hit.visibility == "public"
    assert hit.metadata["export_kind"] == "export_function"


def test_parse_file_detects_export_async_function():
    adapter = TypeScriptAdapter()
    items = adapter.parse_file(_fixture_root() / "exports.ts")

    hit = next(item for item in items if item.qualified_name == "loadFoo")
    assert hit.symbol_kind == "function"
    assert hit.visibility == "public"
    assert hit.metadata["export_kind"] == "export_function_async"


def test_parse_file_detects_export_const_arrow_function():
    adapter = TypeScriptAdapter()
    items = adapter.parse_file(_fixture_root() / "exports.ts")

    hit = next(item for item in items if item.qualified_name == "makeFoo")
    assert hit.symbol_kind == "function"
    assert hit.metadata["export_kind"] == "export_const_arrow"


def test_parse_file_detects_export_const_async_arrow_function():
    adapter = TypeScriptAdapter()
    items = adapter.parse_file(_fixture_root() / "exports.ts")

    hit = next(item for item in items if item.qualified_name == "makeFooAsync")
    assert hit.symbol_kind == "function"
    assert hit.metadata["export_kind"] == "export_const_async_arrow"


def test_parse_file_detects_exported_class_public_method():
    adapter = TypeScriptAdapter()
    items = adapter.parse_file(_fixture_root() / "exports.ts")

    hit = next(item for item in items if item.qualified_name == "UserService.getUser")
    assert hit.symbol_kind == "method"
    assert hit.visibility == "public"
    assert hit.metadata["class_name"] == "UserService"
    assert hit.metadata["export_kind"] == "export_class_public_method"
    assert hit.legacy_func_id == hit.target_id
    assert hit.contract_sources == ()
    assert hit.contract_hash is None


def test_parse_file_does_not_crash_on_unsupported_or_malformed_ts():
    adapter = TypeScriptAdapter()
    items = adapter.parse_file(_fixture_root() / "malformed.ts")

    assert isinstance(items, list)


def test_malformed_parse_does_not_poison_followup_file_parse():
    adapter = TypeScriptAdapter()
    malformed_items = adapter.parse_file(_fixture_root() / "malformed.ts")
    exports_items = adapter.parse_file(_fixture_root() / "exports.ts")

    assert isinstance(malformed_items, list)
    assert any(item.qualified_name == "foo" for item in exports_items)
    assert all(item.contract_presence != "contract_parse_error" for item in exports_items)


def test_target_id_rule_for_typescript_subject():
    adapter = TypeScriptAdapter()
    path = _fixture_root() / "exports.ts"
    items = adapter.parse_file(path)
    foo = next(item for item in items if item.qualified_name == "foo")

    expected_file_path = path.as_posix()
    assert foo.file_path == expected_file_path
    assert foo.target_id == f"typescript:{expected_file_path}:function:foo"
    assert foo.signature_hash is not None
    assert foo.body_hash is not None
    assert foo.strictness is None


def test_typescript_adapter_does_not_change_python_adapter_parse_file_behavior():
    repo_root = Path(__file__).resolve().parents[1]
    target = repo_root / "harbor" / "adapters" / "python" / "parser.py"
    adapter = PythonAdapter()
    items = adapter.parse_file(str(target))

    assert items
    assert all(isinstance(item, FunctionContract) for item in items)
    assert not any(hasattr(item, "target_id") for item in items)


def test_registry_default_python_only_and_typescript_unconfigured_disabled():
    default_registry = AdapterRegistry.default()
    cfg_registry = AdapterRegistry.from_config({"languages": {"python": {"enabled": True}}})

    assert default_registry.get_enabled_languages() == ["python"]
    assert default_registry.is_enabled("typescript") is False
    assert default_registry.get_adapter("typescript") is None
    assert cfg_registry.get_enabled_languages() == ["python"]
    assert cfg_registry.is_enabled("typescript") is False


def test_parse_file_detects_exported_interface_and_type_aliases(tmp_path: Path):
    target = tmp_path / "models.ts"
    target.write_text(
        textwrap.dedent(
            """
            export interface User {
              id: string;
              name: string;
            }

            export type UserRole = "admin" | "member";

            export type CreateUserInput = {
              email: string;
              name: string;
            };

            interface InternalOnly {
              hidden: string;
            }
            """
        ).strip(),
        encoding="utf-8",
    )
    items = TypeScriptAdapter().parse_file(target)
    names = {item.qualified_name for item in items}

    assert names == {"User", "UserRole", "CreateUserInput"}
    user = next(item for item in items if item.qualified_name == "User")
    role = next(item for item in items if item.qualified_name == "UserRole")
    create_input = next(item for item in items if item.qualified_name == "CreateUserInput")

    assert user.symbol_kind == "interface"
    assert user.contract_presence == "present"
    assert user.contract_required is False
    assert user.metadata["data_contract_kind"] == "interface"
    assert [source.kind.value for source in user.contract_sources] == ["typescript_interface"]
    assert user.contract_hash is not None

    assert role.symbol_kind == "type_alias"
    assert role.metadata["data_contract_kind"] == "type_union"
    assert [source.kind.value for source in role.contract_sources] == ["typescript_type"]

    assert create_input.symbol_kind == "type_alias"
    assert create_input.metadata["data_contract_kind"] == "type_object"
    assert create_input.body_hash is None


def test_parse_file_detects_exported_zod_object_and_enum_as_shallow_sources(tmp_path: Path):
    target = tmp_path / "schema.ts"
    target.write_text(
        textwrap.dedent(
            """
            export const UserSchema = z.object({
              id: z.string(),
              name: z.string(),
            });

            export const RoleSchema = z.enum(["admin", "member"]);
            """
        ).strip(),
        encoding="utf-8",
    )
    items = TypeScriptAdapter().parse_file(target)

    user_schema = next(item for item in items if item.qualified_name == "UserSchema")
    role_schema = next(item for item in items if item.qualified_name == "RoleSchema")

    assert user_schema.symbol_kind == "const"
    assert user_schema.contract_presence == "present"
    assert user_schema.contract_required is False
    assert user_schema.metadata["schema_source_kind"] == "z.object"
    assert [source.kind.value for source in user_schema.contract_sources] == ["zod_schema"]
    assert user_schema.contract_hash is not None

    assert role_schema.metadata["schema_source_kind"] == "z.enum"
    assert [source.kind.value for source in role_schema.contract_sources] == ["zod_schema"]


def test_parse_file_detects_export_default_targets_without_confusing_contract_source(tmp_path: Path):
    target = tmp_path / "defaults.ts"
    target.write_text(
        textwrap.dedent(
            """
            export default function createUser(name: string): string {
              return name;
            }

            export default class DefaultUserService {
              public getName(): string {
                return "ok";
              }
            }
            """
        ).strip(),
        encoding="utf-8",
    )
    items = TypeScriptAdapter().parse_file(target)

    fn = next(item for item in items if item.qualified_name == "createUser")
    cls = next(item for item in items if item.qualified_name == "DefaultUserService")

    assert fn.symbol_kind == "function"
    assert fn.metadata["export_mode"] == "default"
    assert fn.metadata["public_surface_evidence"] == "default_export"
    assert fn.contract_hash is None

    assert cls.symbol_kind == "class"
    assert cls.metadata["export_mode"] == "default"
    assert cls.metadata["public_surface_evidence"] == "default_export"
    assert cls.contract_required is False


def test_body_only_change_does_not_change_typescript_contract_hash(tmp_path: Path):
    target = tmp_path / "contract.ts"
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
    adapter = TypeScriptAdapter()
    first = next(item for item in adapter.parse_file(target) if item.qualified_name == "api")

    target.write_text(
        textwrap.dedent(
            """
            /**
             * @param value input
             * @returns output
             */
            export function api(value: string): string {
              return value.toUpperCase();
            }
            """
        ).strip(),
        encoding="utf-8",
    )
    second = next(item for item in adapter.parse_file(target) if item.qualified_name == "api")

    assert first.body_hash != second.body_hash
    assert first.contract_hash == second.contract_hash


def test_contract_source_change_updates_typescript_contract_hash(tmp_path: Path):
    target = tmp_path / "contract.ts"
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
    adapter = TypeScriptAdapter()
    first = next(item for item in adapter.parse_file(target) if item.qualified_name == "api")

    target.write_text(
        textwrap.dedent(
            """
            /**
             * @param value user input
             * @returns normalized output
             */
            export function api(value: string): string {
              return value.trim();
            }
            """
        ).strip(),
        encoding="utf-8",
    )
    second = next(item for item in adapter.parse_file(target) if item.qualified_name == "api")

    assert first.body_hash == second.body_hash
    assert first.contract_hash != second.contract_hash

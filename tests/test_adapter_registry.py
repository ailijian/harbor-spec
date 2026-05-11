from pathlib import Path

from harbor.adapters.python.parser import FunctionContract
from harbor.adapters.python.parser import PythonAdapter
from harbor.adapters.registry import AdapterRegistry


def test_default_registry_enables_python():
    registry = AdapterRegistry.default()

    assert registry.is_enabled("python") is True
    assert registry.get_enabled_languages() == ["python"]


def test_default_registry_disables_typescript():
    registry = AdapterRegistry.default()

    assert registry.is_enabled("typescript") is False
    assert registry.get_adapter("typescript") is None


def test_config_can_disable_python():
    registry = AdapterRegistry.from_config(
        {
            "languages": {
                "python": {"enabled": False},
            }
        }
    )

    assert registry.is_enabled("python") is False
    assert registry.get_enabled_languages() == []
    assert registry.get_adapters() == []


def test_typescript_enabled_in_config_but_not_implemented_does_not_crash():
    registry = AdapterRegistry.from_config(
        {
            "languages": {
                "typescript": {"enabled": True},
            }
        }
    )

    assert registry.is_enabled("typescript") is False
    assert registry.get_adapter("typescript") is None
    assert "typescript" not in registry.get_enabled_languages()


def test_get_adapter_python_returns_python_adapter_instance():
    registry = AdapterRegistry.default()
    adapter = registry.get_adapter("python")

    assert isinstance(adapter, PythonAdapter)


def test_get_enabled_languages_output_is_stable():
    registry = AdapterRegistry.from_config(
        {
            "languages": {
                "python": {"enabled": True},
                "typescript": {"enabled": False},
            }
        }
    )

    assert registry.get_enabled_languages() == ["python"]
    assert registry.get_enabled_languages() == ["python"]


def test_registry_does_not_change_python_adapter_parse_file_behavior():
    registry = AdapterRegistry.default()
    adapter = registry.get_adapter("python")
    assert isinstance(adapter, PythonAdapter)

    repo_root = Path(__file__).resolve().parents[1]
    target = repo_root / "harbor" / "adapters" / "python" / "parser.py"
    items = adapter.parse_file(str(target))

    assert items
    assert all(isinstance(item, FunctionContract) for item in items)

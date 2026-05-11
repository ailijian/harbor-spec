from pathlib import Path

from harbor.adapters.python.compat import function_contract_to_subject
from harbor.adapters.python.parser import FunctionContract
from harbor.adapters.python.parser import PythonAdapter
from harbor.adapters.base import ContractSubject


def _sample_contract(docstring: str | None = "Doc text", is_method: bool = False) -> FunctionContract:
    return FunctionContract(
        id="pkg.mod.fn",
        name="fn",
        qualified_name="pkg.mod.fn",
        signature_hash="sig-hash",
        docstring=docstring,
        docstring_raw_hash="raw-hash" if docstring is not None else None,
        contract_hash="contract-hash" if docstring is not None else None,
        lineno=12,
        col_offset=0,
        scope="public",
        strictness="strict",
        is_method=is_method,
        parent_class="MyClass" if is_method else None,
        contract_presence="present" if docstring is not None else "missing",
        contract_required=True,
    )


def test_function_contract_maps_to_contract_subject():
    contract = _sample_contract(docstring="Args:\n  a: user id")
    subject = function_contract_to_subject(contract, "src\\pkg\\mod.py")

    assert isinstance(subject, ContractSubject)
    assert subject.language == "python"
    assert subject.symbol_kind == "function"
    assert subject.qualified_name == "pkg.mod.fn"
    assert subject.file_path == "src/pkg/mod.py"
    assert subject.lineno == 12
    assert subject.metadata["name"] == "fn"
    assert subject.metadata["is_method"] is False


def test_legacy_func_id_keeps_original_function_contract_id():
    contract = _sample_contract()
    subject = function_contract_to_subject(contract, "src/mod.py")

    assert subject.legacy_func_id == contract.id


def test_target_id_uses_python_file_symbol_qualified_name_rule():
    contract = _sample_contract()
    subject = function_contract_to_subject(contract, "  src\\pkg\\mod.py  ")

    assert subject.target_id == "python:src/pkg/mod.py:function:pkg.mod.fn"


def test_docstring_maps_to_docstring_contract_source():
    contract = _sample_contract(docstring="Returns:\n  int")
    subject = function_contract_to_subject(contract, "src/pkg/mod.py")

    assert len(subject.contract_sources) == 1
    source = subject.contract_sources[0]
    assert source.kind.value == "docstring"
    assert source.text == "Returns:\n  int"
    assert source.location == "src/pkg/mod.py:12"
    assert source.metadata["docstring_raw_hash"] == contract.docstring_raw_hash


def test_no_docstring_maps_to_empty_contract_sources():
    contract = _sample_contract(docstring=None)
    subject = function_contract_to_subject(contract, "src/pkg/mod.py")

    assert subject.contract_sources == ()


def test_python_adapter_parse_file_behavior_unchanged():
    repo_root = Path(__file__).resolve().parents[1]
    target = repo_root / "harbor" / "adapters" / "python" / "parser.py"
    adapter = PythonAdapter()
    items = adapter.parse_file(str(target))

    assert items
    assert all(isinstance(item, FunctionContract) for item in items)
    assert not any(hasattr(item, "target_id") for item in items)

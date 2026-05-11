from harbor.adapters.base import ContractSource
from harbor.adapters.base import ContractSourceKind
from harbor.adapters.base import ContractSubject


def test_contract_subject_required_fields_are_present():
    source = ContractSource(kind=ContractSourceKind.DOCSTRING, text="Args:\n  x: value")
    target_id = ContractSubject.make_target_id(
        language="python",
        file_path="harbor\\adapters\\python\\parser.py",
        symbol_kind="function",
        qualified_name="harbor.adapters.python.parser.PythonAdapter.parse_file",
    )
    subject = ContractSubject(
        target_id=target_id,
        legacy_func_id="harbor.adapters.python.parser.PythonAdapter.parse_file",
        language="python",
        symbol_kind="function",
        qualified_name="harbor.adapters.python.parser.PythonAdapter.parse_file",
        file_path="harbor/adapters/python/parser.py",
        lineno=1,
        contract_sources=(source,),
    )

    assert subject.target_id == target_id
    assert subject.legacy_func_id is not None
    assert subject.language == "python"
    assert subject.symbol_kind == "function"
    assert subject.qualified_name.endswith("PythonAdapter.parse_file")
    assert subject.file_path == "harbor/adapters/python/parser.py"
    assert subject.lineno == 1
    assert subject.metadata == {}
    assert source.confidence == "medium"
    assert source.metadata == {}


def test_target_id_rule_is_stable_and_normalized():
    target_id = ContractSubject.make_target_id(
        language="typescript",
        file_path="  src\\api\\service.ts  ",
        symbol_kind="function",
        qualified_name="src.api.service.fetchUsers",
    )

    assert (
        target_id
        == "typescript:src/api/service.ts:function:src.api.service.fetchUsers"
    )


def test_contract_source_fingerprint_is_stable_for_same_text():
    text_lf = "Args:\n  a: user id\nReturns:\n  str"
    text_crlf = "  Args:\r\n  a: user id\r\nReturns:\r\n  str  "
    fp_lf = ContractSource.compute_fingerprint(text_lf)
    fp_crlf = ContractSource.compute_fingerprint(text_crlf)

    assert fp_lf == fp_crlf


def test_contract_source_fingerprint_changes_on_text_change():
    fp_1 = ContractSource.compute_fingerprint("Returns:\n  int")
    fp_2 = ContractSource.compute_fingerprint("Returns:\n  str")

    assert fp_1 != fp_2


def test_contract_subject_min_serialization_is_stable():
    source = ContractSource(
        kind=ContractSourceKind.TSDOC,
        text="/** @param id user id */",
        confidence="high",
        metadata={"channel": "ts"},
    )
    target_id = ContractSubject.make_target_id(
        language="typescript",
        file_path="src\\service.ts",
        symbol_kind="function",
        qualified_name="src.service.findById",
    )
    subject = ContractSubject(
        target_id=target_id,
        language="typescript",
        symbol_kind="function",
        qualified_name="src.service.findById",
        file_path="src/service.ts",
        lineno=10,
        contract_sources=(source,),
        metadata={"owner": "adapter-test"},
    )

    payload1 = subject.to_dict()
    payload2 = subject.to_dict()

    assert payload1 == payload2
    assert list(payload1.keys()) == [
        "target_id",
        "legacy_func_id",
        "language",
        "symbol_kind",
        "qualified_name",
        "file_path",
        "lineno",
        "end_lineno",
        "visibility",
        "strictness",
        "signature_text",
        "signature_hash",
        "body_hash",
        "contract_hash",
        "contract_presence",
        "contract_required",
        "metadata",
        "contract_sources",
    ]
    assert isinstance(payload1["contract_sources"], list)
    assert payload1["contract_sources"][0]["kind"] == "tsdoc"
    assert payload1["contract_sources"][0]["confidence"] == "high"
    assert payload1["contract_sources"][0]["metadata"] == {"channel": "ts"}

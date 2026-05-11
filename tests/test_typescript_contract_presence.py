from pathlib import Path

from harbor.adapters.typescript.adapter import TypeScriptAdapter


def _fixture_root() -> Path:
    return Path(__file__).resolve().parent / "fixtures" / "ts_project_basic" / "src"


def _subject_by_name(name: str):
    adapter = TypeScriptAdapter()
    items = adapter.parse_file(_fixture_root() / "contract_presence.ts")
    return next(item for item in items if item.qualified_name == name)


def test_high_confidence_tsdoc_marks_present_and_required():
    item = _subject_by_name("documentedHigh")

    assert item.contract_presence == "present"
    assert item.contract_required is True
    assert item.contract_sources
    assert item.contract_sources[0].confidence == "high"
    assert item.contract_sources[0].kind.value == "tsdoc"
    assert "param" in item.contract_sources[0].metadata["tags"]


def test_medium_confidence_tsdoc_marks_non_contract_doc():
    item = _subject_by_name("documentedMedium")

    assert item.contract_presence == "non_contract_doc"
    assert item.contract_sources
    assert item.contract_sources[0].confidence == "medium"


def test_line_comment_is_not_contract_source():
    item = _subject_by_name("lineCommentOnly")

    assert item.contract_presence == "missing"
    assert item.contract_required is True
    assert item.contract_sources == ()


def test_exported_function_without_tsdoc_is_missing_and_required():
    item = _subject_by_name("missingDoc")

    assert item.contract_presence == "missing"
    assert item.contract_required is True


def test_internal_helper_is_not_required():
    item = _subject_by_name("internalHelper")

    assert item.contract_presence == "missing"
    assert item.contract_required is False
    assert item.metadata["contract_required_reason"] == "internal_helper_or_non_exported"


def test_exported_class_public_method_with_tsdoc_is_present_and_required():
    item = _subject_by_name("ContractService.getUser")

    assert item.contract_presence == "present"
    assert item.contract_required is True
    assert item.contract_sources
    assert item.contract_sources[0].confidence == "high"


def test_tsdoc_with_code_gap_is_not_attached_to_symbol():
    item = _subject_by_name("separatedDoc")

    assert item.contract_presence == "missing"
    assert item.contract_sources == ()


def test_signature_only_public_function_remains_missing_required():
    item = _subject_by_name("missingDoc")

    assert item.signature_text is not None
    assert item.contract_presence == "missing"
    assert item.contract_required is True


def test_malformed_or_unsupported_ts_does_not_emit_contract_parse_error():
    adapter = TypeScriptAdapter()
    items = adapter.parse_file(_fixture_root() / "malformed.ts")

    assert isinstance(items, list)
    for item in items:
        assert item.contract_presence != "contract_parse_error"
        diagnostics = item.metadata.get("diagnostics", ())
        assert all("contract_parse_error" not in message for message in diagnostics)


def test_script_file_targets_are_not_required():
    adapter = TypeScriptAdapter()
    items = adapter.parse_file(_fixture_root() / "scripts" / "runner.ts")

    target = next(item for item in items if item.qualified_name == "runJobs")
    assert target.contract_required is False
    assert target.metadata["contract_required_reason"] == "script_file"

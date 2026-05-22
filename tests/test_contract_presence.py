from harbor.adapters.python.parser import FunctionContract
from harbor.core.contract_presence import evaluate_contract_presence


def _fc(*, name: str, qualified_name: str, docstring=None, contract_hash=None, scope=None, strictness=None):
    return FunctionContract(
        id=qualified_name,
        name=name,
        qualified_name=qualified_name,
        signature_hash="sig",
        docstring=docstring,
        docstring_raw_hash=None,
        contract_hash=contract_hash,
        lineno=1,
        col_offset=0,
        scope=scope,
        strictness=strictness,
        is_method=False,
        parent_class=None,
    )


def test_public_without_docstring_is_contract_gap_required():
    fc = _fc(name="public_api", qualified_name="harbor.core.x.public_api", scope="public", strictness="standard")
    res = evaluate_contract_presence(fc, "harbor/core/x.py")
    assert res.required is True
    assert res.presence == "missing"


def test_strict_without_docstring_is_contract_gap_required():
    fc = _fc(name="run", qualified_name="harbor.core.x.run", scope="internal", strictness="strict")
    res = evaluate_contract_presence(fc, "harbor/core/x.py")
    assert res.required is True
    assert res.presence == "missing"


def test_private_light_helper_without_docstring_is_skippable():
    fc = _fc(name="_helper", qualified_name="harbor.core.x._helper", scope="internal", strictness="light")
    res = evaluate_contract_presence(fc, "harbor/core/x.py")
    assert res.required is False
    assert res.presence == "missing"


def test_write_function_without_docstring_is_required():
    fc = _fc(name="write_report", qualified_name="harbor.core.x.write_report", scope="internal", strictness="standard")
    res = evaluate_contract_presence(fc, "harbor/core/x.py")
    assert res.required is True
    assert res.presence == "missing"


def test_to_dict_like_without_docstring_is_required():
    fc = _fc(name="report_to_dict", qualified_name="harbor.core.x.report_to_dict", scope="internal", strictness="standard")
    res = evaluate_contract_presence(fc, "harbor/core/x.py")
    assert res.required is True
    assert res.presence == "missing"


def test_behavior_only_docstring_counts_as_contract_for_required_target():
    fc = _fc(
        name="main",
        qualified_name="harbor.cli.main.main",
        docstring="Execute CLI.\n\nBehavior:\n  - Dispatches commands.",
        contract_hash="hash",
        scope=None,
        strictness=None,
    )
    res = evaluate_contract_presence(fc, "harbor/cli/main.py")
    assert res.required is True
    assert res.presence == "present"

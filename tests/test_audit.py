from harbor.core.audit import SemanticGuard, MockProvider
from harbor.adapters.python.parser import FunctionContract


def test_semantic_guard_ok():
    fc = FunctionContract(
        id="pkg.mod.func",
        name="func",
        qualified_name="pkg.mod.func",
        signature_hash="x",
        docstring="Args:\n  a (int): x\nReturns:\n  int: y\nRaises:\n  ValueError: z\n@harbor.scope: public\n@harbor.l3_strictness: strict",
        docstring_raw_hash="r",
        contract_hash="c",
        lineno=1,
        col_offset=0,
    )
    src = "def func(a: int) -> int:\n    \"\"\"Args:\n    a (int): x\n    Returns:\n    int: y\n    Raises:\n    ValueError: z\n    \"\"\"\n    return a"
    g = SemanticGuard()
    prov = MockProvider()
    res = g.audit(fc, src, prov)
    assert res.status == "OK"


def test_semantic_guard_mismatch_parsing():
    fc = FunctionContract(
        id="pkg.mod.func",
        name="func",
        qualified_name="pkg.mod.func",
        signature_hash="x",
        docstring="Args:\n  a (int): x\nReturns:\n  int: y\nRaises:\n  ValueError: z\n@harbor.scope: public\n@harbor.l3_strictness: strict",
        docstring_raw_hash="r",
        contract_hash="c",
        lineno=1,
        col_offset=0,
    )
    src = "def func(a: int) -> int:\n    return a"
    class MismatchProvider(MockProvider):
        def infer(self, prompt: str) -> str:
            return "[MISMATCH]: Raises not implemented"
    g = SemanticGuard()
    res = g.audit(fc, src, MismatchProvider())
    assert res.status == "MISMATCH"
    assert "Raises" in (res.reason or "")


def test_semantic_guard_contract_gap_without_docstring():
    fc = FunctionContract(
        id="harbor.core.sync.SyncEngine.check_status",
        name="check_status",
        qualified_name="harbor.core.sync.SyncEngine.check_status",
        signature_hash="x",
        docstring=None,
        docstring_raw_hash=None,
        contract_hash=None,
        lineno=1,
        col_offset=0,
        scope="public",
        strictness="strict",
        is_method=True,
        parent_class="SyncEngine",
    )
    g = SemanticGuard()
    res = g.audit(fc, "def check_status(self):\n    return {}", MockProvider(), file_path="harbor/core/sync.py")
    assert res.status == "CONTRACT_GAP"
    assert "semantic comparison skipped" in (res.reason or "").lower()
    assert res.prompt is None
    assert res.raw_output is None


def test_semantic_guard_skipped_no_contract_for_internal_helper():
    fc = FunctionContract(
        id="harbor.core.utils._internal_helper",
        name="_internal_helper",
        qualified_name="harbor.core.utils._internal_helper",
        signature_hash="x",
        docstring=None,
        docstring_raw_hash=None,
        contract_hash=None,
        lineno=1,
        col_offset=0,
        scope="internal",
        strictness="light",
    )
    g = SemanticGuard()
    res = g.audit(fc, "def _internal_helper():\n    return 1", MockProvider(), file_path="harbor/core/utils.py")
    assert res.status == "SKIPPED_NO_CONTRACT"
    assert "semantic comparison skipped" in (res.reason or "").lower()
    assert res.prompt is None
    assert res.raw_output is None

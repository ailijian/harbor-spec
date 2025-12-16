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

from harbor.adapters.python.parser import FunctionContract
from harbor.core.audit import MockProvider, SemanticGuard


def test_python_semantic_audit_still_calls_provider_and_returns_ok():
    class _Provider(MockProvider):
        def __init__(self) -> None:
            self.calls = 0

        def infer(self, prompt: str) -> str:
            self.calls += 1
            return '{"status":"OK"}'

    contract = FunctionContract(
        id="pkg.mod.fn",
        name="fn",
        qualified_name="pkg.mod.fn",
        signature_hash="sig",
        docstring="Args:\n  x (int): input\nReturns:\n  int: output",
        docstring_raw_hash="raw",
        contract_hash="hash",
        lineno=1,
        col_offset=0,
    )
    provider = _Provider()
    result = SemanticGuard().audit(
        contract,
        'def fn(x: int) -> int:\n    """Args:\\n  x (int): input\\nReturns:\\n  int: output"""\n    return x\n',
        provider,
        file_path="pkg/mod.py",
    )
    assert result.status == "OK"
    assert provider.calls == 1


def test_python_semantic_audit_mismatch_mapping_unchanged():
    class _Provider(MockProvider):
        def infer(self, prompt: str) -> str:
            return '{"status":"MISMATCH","reason":"raises mismatch"}'

    contract = FunctionContract(
        id="pkg.mod.fn",
        name="fn",
        qualified_name="pkg.mod.fn",
        signature_hash="sig",
        docstring="Args:\n  x (int): input\nReturns:\n  int: output",
        docstring_raw_hash="raw",
        contract_hash="hash",
        lineno=1,
        col_offset=0,
    )
    result = SemanticGuard().audit(
        contract,
        "def fn(x: int) -> int:\n    return x\n",
        _Provider(),
        file_path="pkg/mod.py",
    )
    assert result.status == "MISMATCH"

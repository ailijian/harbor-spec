from harbor.adapters.python.parser import FunctionContract
from harbor.core.audit import SemanticGuard, MockProvider


class _ShouldNotCallProvider(MockProvider):
    def infer(self, prompt: str) -> str:
        raise AssertionError("LLM should not be called when contract is missing")


def test_semantic_guard_missing_required_contract_skips_llm():
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
    res = SemanticGuard().audit(
        fc,
        "def check_status(self):\n    return {}",
        _ShouldNotCallProvider(),
        file_path="harbor/core/sync.py",
    )
    assert res.status == "CONTRACT_GAP"
    assert res.prompt is None
    assert res.raw_output is None


def test_semantic_guard_missing_non_required_contract_skips_llm():
    fc = FunctionContract(
        id="harbor.core.utils._helper",
        name="_helper",
        qualified_name="harbor.core.utils._helper",
        signature_hash="x",
        docstring=None,
        docstring_raw_hash=None,
        contract_hash=None,
        lineno=1,
        col_offset=0,
        scope="internal",
        strictness="light",
        is_method=False,
        parent_class=None,
    )
    res = SemanticGuard().audit(
        fc,
        "def _helper():\n    return 1",
        _ShouldNotCallProvider(),
        file_path="harbor/core/utils.py",
    )
    assert res.status == "SKIPPED_NO_CONTRACT"
    assert res.prompt is None
    assert res.raw_output is None

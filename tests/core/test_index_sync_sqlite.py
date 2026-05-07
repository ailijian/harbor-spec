from pathlib import Path

from harbor.core.index import IndexBuilder
from harbor.core.sync import SyncEngine


def test_index_and_sync_detects_body_drift(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fixtures = Path("fixtures_sqlite")
    fixtures.mkdir(parents=True, exist_ok=True)
    target = fixtures / "sample.py"
    target.write_text(
        '''\
def func1():
    """测试函数。

    @harbor.scope: public
    @harbor.l3_strictness: strict

    Args:
      None

    Returns:
      None
    """
    x = 1
    return x
''',
        encoding="utf-8",
    )
    cfg = Path(".harbor") / "config.yaml"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text("schema_version: '1.0.2'\ncode_roots:\n  - fixtures_sqlite/**\nexclude_paths: []\n", encoding="utf-8")
    builder = IndexBuilder(code_roots=["fixtures_sqlite/**"])
    # 构建索引（写入 DB）
    _ = list(builder.iter_build(incremental=True))
    # 修改实现体（保持契约不变）
    target.write_text(
        '''\
def func1():
    """测试函数。

    @harbor.scope: public
    @harbor.l3_strictness: strict

    Args:
      None

    Returns:
      None
    """
    x = 2
    print(x)
    return x
''',
        encoding="utf-8",
    )
    eng = SyncEngine()
    rep = eng.check_status()
    assert rep.counts.get("drift", 0) >= 1 or rep.counts.get("modified", 0) >= 1

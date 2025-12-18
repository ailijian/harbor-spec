from harbor.core.utils import derive_adopted_roots


def test_derive_adopted_roots_basic():
    files = [
        "pkg/a.py",
        "pkg/b.py",
        "pkg/c.py",
        "pkg/d.py",
        "pkg/e.py",
        "tools/x.py",
        "tools/y.py",
    ]
    res = derive_adopted_roots(files, exclude_patterns=["tools/**"], min_count=5)
    assert "pkg/**" in res
    assert "tools/**" not in res

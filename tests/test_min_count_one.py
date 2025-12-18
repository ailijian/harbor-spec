from harbor.core.utils import derive_adopted_roots


def test_min_count_one_includes_single_file_dir():
    files = ["pkg/a.py"]
    res = derive_adopted_roots(files, exclude_patterns=[], min_count=1)
    assert "pkg/**" in res

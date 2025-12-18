from harbor.core.utils import derive_adopted_roots


def test_windows_abs_path_prefix():
    files = ["C:/project/app/a.py", "C:/project/app/b.py"]
    res = derive_adopted_roots(files, exclude_patterns=[], min_count=1)
    assert "app/**" in res

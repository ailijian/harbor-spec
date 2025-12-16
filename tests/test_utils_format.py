from harbor.test_utils import harbor_ddt_target
from harbor.utils import format_size
import pytest


@harbor_ddt_target(func="harbor.utils.formatting.format_size", l3_version=1)
def test_format_size_bytes():
    assert format_size(0) == "0 B"
    assert format_size(512) == "512 B"


@harbor_ddt_target(func="harbor.utils.formatting.format_size", l3_version=1)
def test_format_size_kb():
    assert format_size(1024) == "1.00 KB"
    assert format_size(1536) == "1.50 KB"


@harbor_ddt_target(func="harbor.utils.formatting.format_size", l3_version=1)
def test_format_size_mb():
    assert format_size(1048576) == "1.00 MB"
    assert format_size(2 * 1048576) == "2.00 MB"


@harbor_ddt_target(func="harbor.utils.formatting.format_size", l3_version=1)
def test_format_size_negative_raises():
    with pytest.raises(ValueError):
        format_size(-1)


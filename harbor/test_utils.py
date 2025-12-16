from __future__ import annotations

from typing import Callable, Optional


def harbor_ddt_target(func: str, l3_version: Optional[int] = None, strategy: str = "strict") -> Callable[[Callable], Callable]:
    def decorator(test_func: Callable) -> Callable:
        setattr(test_func, "_harbor_ddt_meta", {"func": func, "l3_version": l3_version, "strategy": strategy})
        return test_func
    return decorator


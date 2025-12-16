def format_size(bytes: int) -> str:
    """将字节数转换为人类可读的 KB/MB 字符串。

    功能:
      - 接受非负整数的字节数输入。
      - 小于 1024 显示为 `B`。
      - 1024 及以上显示为 `KB` 或 `MB`，保留两位小数。

    使用场景:
      - CLI 输出或报告中展示文件/索引大小。
      - 在 L2/报告中统一规格化体积呈现。

    依赖:
      - 标准库，仅执行算术与格式化。

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: pure

    Args:
      bytes (int): 需要转换的字节数，必须为非负整数。

    Returns:
      str: 规范化的人类可读字符串，如 `1.50 KB`、`1.00 MB` 或 `0 B`。

    Raises:
      ValueError: 当 `bytes` 为负数时抛出。
    """
    if bytes < 0:
        raise ValueError("bytes must be non-negative")
    if bytes < 1024:
        return f"{bytes} B"
    if bytes < 1024 * 1024:
        return f"{bytes / 1024:.2f} KB"
    return f"{bytes / (1024 * 1024):.2f} MB"


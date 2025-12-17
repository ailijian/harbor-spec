def func1():
    """测试函数。副作用：打印输出 x。

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: once

    Args:
      None

    Returns:
      int: 返回值 x
    """
    x = 2
    print(x)
    return x

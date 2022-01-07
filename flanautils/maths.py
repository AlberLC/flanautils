def sign(number: int | float) -> int:
    """
    Return the number sign.

    >>> sign(5)
    1
    >>> sign(-5.2)
    -1
    >>> sign(0)
    0
    """

    if number > 0:
        return 1
    elif number < 0:
        return -1
    return 0

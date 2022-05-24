import inspect
import typing
from typing import Any, Callable, Iterable, Iterator, Sequence, Type, overload

from flanautils import maths, strings


def chunks(elements: Sequence, size, lazy=False) -> Iterator[Sequence] | list[Sequence]:
    """Create successive n-sized chunks from elements."""

    generator_ = (elements[i:i + size] for i in range(0, len(elements), size))
    if lazy:
        return generator_
    else:
        return list(generator_)


# noinspection PyShadowingNames,PyShadowingBuiltins
def filter(elements: Iterable, target: Any = None, condition: Callable[..., bool] = None, cast_numbers=False, lazy=False) -> Iterator | list:
    """
    Smart function that find anything in an iterable (classes, objects, ...).

    If condition is not None, return the all elements that matches it.

    >>> elements = [1, 2, '3', 4, 'hola', '6.6']

    >>> filter(elements, 2)
    [2]
    >>> filter(elements, int)
    [1, 2, 4]
    >>> filter(elements, float)
    []
    >>> filter(elements, 6.6, cast_numbers=True)
    [6.6]
    >>> import numbers # Python Standard Library
    >>> filter(elements, numbers.Real, cast_numbers=True)
    [1, 2, 3, 4, 6.6]
    >>> filter(elements, condition=lambda e: isinstance(e, int | float), cast_numbers=True)
    [1, 2, 3, 4, 6.6]
    >>> type(filter(elements, numbers.Real, cast_numbers=True, lazy=True))
    <class 'generator'>
    >>> list(filter(elements, numbers.Real, cast_numbers=True, lazy=True))
    [1, 2, 3, 4, 6.6]
    """

    if condition is None:
        if isinstance(target, type) or isinstance(typing.get_origin(target), type | type(typing.Union)):
            def condition(element: Any) -> bool:
                try:
                    return issubclass(element, target)
                except TypeError:
                    return isinstance(element, target)
        else:
            def condition(element: Any) -> bool:
                return element == target

    generator_ = (final_element for element in elements if condition(final_element := strings.cast_number(element, raise_exception=False) if cast_numbers else element))
    if lazy:
        return generator_
    else:
        return list(generator_)


def filter_exceptions(elements: Iterable) -> tuple[list, list[BaseException]]:
    """Filters the exceptions of the iterable and returns a tuple with the separated results."""

    exceptions_ = []
    no_exceptions = []

    for element in elements:
        if isinstance(element, BaseException):
            exceptions_.append(element)
        else:
            no_exceptions.append(element)

    return no_exceptions, exceptions_


# noinspection PyShadowingNames
def find(elements: Iterable, target: Any = None, condition: Callable[..., bool] = None, cast_numbers=False) -> Any:
    """
    Smart function that find anything in an iterable (classes, objects, ...).

    If condition is not None, return the first element that matches it.

    Return None if nothing matches.

    >>> elements = [1, 2, '3', 4, 'hola', '6.6']

    >>> find(elements, 2)
    2
    >>> find(elements, int)
    1
    >>> find(elements, float)

    >>> find(elements, 6.6, cast_numbers=True)
    6.6
    >>> find(elements, float, cast_numbers=True)
    6.6
    """

    return next(filter(elements, target, condition, cast_numbers, lazy=True), None)


def flatten_iterator(*args: Iterable, depth=None) -> Iterator:
    """
    Iterates and flattens iterables recursively according to the specified depth.

    If depth=None (the default) it flattens recursively until it finds no iterable.

    >>> type(flatten_iterator([1, 2, [3, 4, ['cinco']]]))
    <class 'generator'>
    >>> list(flatten_iterator([1, 2, [3, 4, ['cinco']]]))
    [1, 2, 3, 4, 'cinco']
    >>> list(flatten_iterator([1, 2, [3, 4, ['cinco']]], depth=1))
    [1, 2, [3, 4, ['cinco']]]
    >>> list(flatten_iterator([1, 2, [3, 4, ['cinco']]], depth=2))
    [1, 2, 3, 4, ['cinco']]
    """

    current_depth = -1

    def flatten_iterator_(*args_: Iterable, depth_=None) -> Iterator:
        nonlocal current_depth

        if depth_ is not None:
            current_depth += 1

        for arg_ in args_:
            if isinstance(arg_, Iterable) and not isinstance(arg_, (str, bytes)) and (depth_ is None or current_depth < depth_):
                yield from flatten_iterator_(*arg_, depth_=depth_)
                if depth_ is not None:
                    current_depth -= 1
            else:
                yield arg_

    return flatten_iterator_(*args, depth_=depth)


@overload
def frange(start: float = 0, stop: float = float('inf'), step: float = 1, include_last=False) -> Iterator[float]:
    pass


@overload
def frange(stop: float = 0, include_last=False) -> Iterator[float]:
    pass


def frange(start: float = None, stop: float = None, step: float = 1, include_last=False) -> Iterator[float]:
    """
    Return a Generator that works like range but with floats.

    Can generate infinite numerical series.

    >>> type(frange(5))
    <class 'generator'>
    >>> list(frange(5))
    [0.0, 1.0, 2.0, 3.0, 4.0]
    >>> list(frange(2, 5))
    [2.0, 3.0, 4.0]
    >>> list(frange(2, 5, 0.5))
    [2.0, 2.5, 3.0, 3.5, 4.0, 4.5]
    >>> list(frange(2, 5, 0.5, include_last=True))
    [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
    >>> list(frange(3, 5, 0.2))
    [3.0, 3.2, 3.4000000000000004, 3.6000000000000005, 3.8000000000000007, 4.000000000000001, 4.200000000000001, 4.400000000000001, 4.600000000000001, 4.800000000000002]
    """

    match start, stop:
        case [(int() | float()) as stop, None]:
            start = 0
        case [(int() | float()) as stop, bool(include_last)]:
            start = 0

    step_sign = maths.sign(step)
    start = 0 if start is None else start
    stop = step_sign * (float('inf') if stop is None else stop)

    i = start
    while step_sign * i < stop or (step_sign * i == stop and include_last):
        yield float(i)
        i += step


def iterate_n(iterable: Iterable, n: int, default: Any = ...) -> Any | None:
    """
    Iterates an iterable a number of times and returns the obtained value.

    If default is given and the iterator is exhausted, it is returned instead of raising StopIteration.
    """

    if n <= 0:
        return

    iterable = iter(iterable)
    if default is not ...:
        def iterate():
            return next(iterable, default)
    else:
        def iterate():
            return next(iterable)

    for _ in range(n - 1):
        iterate()

    return iterate()


def separate_self_from_args(args: tuple, exclude_self_types: str | Type | Iterable[str | Type], globals_: dict = None) -> tuple[Any, tuple]:
    """
    Given a function arguments iterable: if the first arg is an instance of exclude_self_types return (args[0],
    args[1:]), else (None, args[1:]).

    If exclude_self_types is a string or iterable of strings, strings.str_to_class(exclude_self_types, globals_)
    is called.
    """

    match exclude_self_types:
        case str() | [*_, str()]:
            exclude_self_types = strings.str_to_class(exclude_self_types, globals_)

    if args and isinstance(args[0], exclude_self_types):
        self, *args = args
    else:
        self = None

    return self, args


def shift_function_args(*args, func: Callable = None, first_arg_default: Any = None) -> tuple:
    """
    Shift received arguments one position to the right, taking into account the possible default value of the first
    argument.
    """

    match func, first_arg_default:
        case func, _ if isinstance(func, Callable):
            first_arg_default = next(iter(inspect.signature(func).parameters.values())).default
        case _, first_arg_default:
            pass
        case _:
            raise TypeError('bad arguments')

    return None if first_arg_default is inspect.Parameter.empty else first_arg_default, *args

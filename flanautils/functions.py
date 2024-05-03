import asyncio
import functools
import inspect
import itertools
import timeit
from typing import Any, Callable, Iterable, Type

from flanautils import strings


# --------------------------------------------------- #
# -------------------- FUNCTIONS -------------------- #
# --------------------------------------------------- #
def is_function(func: Any) -> bool:
    """Checks if the func object is considered a function."""

    if isinstance(func, functools.partial):
        func = func.func

    return inspect.isfunction(func) or inspect.ismethod(func)


def separate_self_from_args(
    args: tuple,
    exclude_self_types: str | Type | Iterable[str | Type],
    globals_: dict = None
) -> tuple[Any, tuple]:
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


def shift_function_args(*args, func: Callable = None, n_positions=1) -> tuple:
    """
    Shift the received arguments n_positions to the right, taking into account the possible default value of every
    argument.

    >>> def something(x: Any = 9, y: Any = 'hello', z: Any = None):
    ...     print(x, y, z)

    >>> shift_function_args(1, func=something)
    (9, 1)
    >>> shift_function_args(1, 2, func=something)
    (9, 1, 2)
    >>> shift_function_args(1, 2, 3, func=something)
    (9, 1, 2)

    >>> shift_function_args(1, func=something, n_positions=2)
    (9, 'hello', 1)
    >>> shift_function_args(1, 2, func=something, n_positions=2)
    (9, 'hello', 1)
    >>> shift_function_args(1, 2, 3, func=something, n_positions=2)
    (9, 'hello', 1)

    >>> shift_function_args(1, func=something, n_positions=3)
    (9, 'hello', None)
    >>> shift_function_args(1, 2, func=something, n_positions=3)
    (9, 'hello', None)
    >>> shift_function_args(1, 2, 3, func=something, n_positions=3)
    (9, 'hello', None)

    >>> shift_function_args(1, func=something, n_positions=99)
    (9, 'hello', None)
    >>> shift_function_args(1, 2, func=something, n_positions=99)
    (9, 'hello', None)
    >>> shift_function_args(1, 2, 3, func=something, n_positions=99)
    (9, 'hello', None)
    """

    if func:
        first_arg_defaults = (
            None if parameter.default is inspect.Parameter.empty else parameter.default
            for parameter in inspect.signature(func).parameters.values()
        )
    else:
        first_arg_defaults = itertools.cycle((None,))

    new_args = [default for _, default in zip(range(n_positions), first_arg_defaults)]
    n_parameters = len(inspect.signature(func).parameters)
    return tuple(new_args + list(args)[:n_parameters - len(new_args)])


# --------------------------------------------------------- #
# -------------------- META DECORATORS -------------------- #
# --------------------------------------------------------- #
def shift_args_if_called(func_: Callable = None, *, n_positions=1, exclude_self_types: str | Type | Iterable[str | Type] = (), globals_: dict = None) -> Callable:
    """Decorator for decorators that shifts the arguments depending on whether the decorator is called or not."""

    if func_ is not None and not is_function(func_):
        func_, exclude_self_types, globals_ = shift_function_args(func_, exclude_self_types, globals_, func=shift_args_if_called)

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            self, args = separate_self_from_args(args, exclude_self_types, globals_)
            if args and args[0] is not None and not is_function(args[0]):
                args = shift_function_args(*args, n_positions=n_positions, func=func)

            if self:
                return func(self, *args, **kwargs)
            else:
                return func(*args, **kwargs)

        return wrapper

    return decorator(func_) if func_ else decorator


# ---------------------------------------------------- #
# -------------------- DECORATORS -------------------- #
# ---------------------------------------------------- #
@shift_args_if_called
def repeat(func_: Callable = None, /, times=2) -> Callable:
    """
    Decorator that makes the decorated function be executed the specified number of times (by default times=2).

    Returns the last result.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            result = None
            for _ in range(int(times)):
                result = func(*args, **kwargs)
            return result

        return wrapper

    return decorator(func_) if func_ else decorator


@shift_args_if_called
def return_if_first_empty(func_: Callable = None, /, return_: Any = None, exclude_self_types: str | Type | Iterable[str | Type] = (), globals_: dict = None) -> Callable:
    """
    Decorator that aborts the execution of the function if the boolean value of the first element is False.

    In case of cancellation returns the value provided by return_ (by default return_=None).

    Ignore the first element if it is an instance of exclude_self_types.
    """

    return_ = return_() if callable(return_) else return_

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            self, args = separate_self_from_args(args, exclude_self_types, globals_)

            if not args[0] if args else not next(iter(kwargs.values()), None):
                if asyncio.iscoroutinefunction(func):
                    async def temp():
                        return return_

                    return temp()
                return return_

            if self:
                args = (self, *args)
            return func(*args, **kwargs)

        return wrapper

    return decorator(func_) if func_ else decorator


@shift_args_if_called
def time_it(func_: Callable = None, /, n_executions=1) -> Callable:
    """Decorator that prints the seconds it takes for the function to run."""

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            new_template = f"""def inner(_it, _timer{{init}}):
                                   {{setup}}
                                   _t0 = _timer()
                                   for _i in _it:
                                       result = {{stmt}}
                                   _t1 = _timer()
                                   print({repr(func.__name__)} + ': ' + str(_t1 - _t0) + ' seconds')
                                   return result"""

            timeit.template = new_template
            return timeit.timeit(lambda: func(*args, **kwargs), number=n_executions)

        return wrapper

    return decorator(func_) if func_ else decorator

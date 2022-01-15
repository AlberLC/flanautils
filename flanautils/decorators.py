import asyncio
import functools
import inspect
import timeit
from typing import Any, Callable, Iterable, Type

from flanautils import iterables


# --------------------------------------------------------- #
# -------------------- META DECORATORS -------------------- #
# --------------------------------------------------------- #
def shift_args_if_called(func_: Callable = None, *, exclude_self_types: str | Type | Iterable[str | Type] = (), globals_: dict = None) -> Callable:
    """Decorator for decorators that shifts the arguments depending on whether the decorator is called or not."""

    if func_ is not None and not inspect.isfunction(func_) and not inspect.ismethod(func_):
        func_, exclude_self_types, globals_ = iterables.shift_function_args(func_, exclude_self_types, globals_, func=shift_args_if_called)

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            self, args = iterables.separate_self_from_args(args, exclude_self_types, globals_)
            if args and args[0] is not None and not inspect.isfunction(args[0]) and not inspect.ismethod(args[0]):
                args = iterables.shift_function_args(*args, func=func)

            if self:
                return func(self, *args, **kwargs)
            else:
                return func(*args, **kwargs)

        return wrapper

    return decorator(func_) if func_ else decorator


# ---------------------------------------------------- #
# -------------------- DECORATORS -------------------- #
# ---------------------------------------------------- #
def do_after(after_function: Callable) -> Callable:
    """Decorator to execute a function or coroutine function after the decorated function."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if asyncio.iscoroutinefunction(after_function):
                async def temp():
                    result_ = await func(*args, **kwargs)
                    await after_function(*args, **kwargs)
                    return result_

                return temp()

            result = func(*args, **kwargs)
            after_function(*args, **kwargs)
            return result

        return wrapper

    return decorator


def do_before(before_function: Callable) -> Callable:
    """Decorator to execute a function or coroutine function before the decorated function."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if asyncio.iscoroutinefunction(before_function):
                async def temp():
                    await before_function(*args, **kwargs)
                    return await func(*args, **kwargs)

                return temp()

            before_function(*args, **kwargs)
            return func(*args, **kwargs)

        return wrapper

    return decorator


@shift_args_if_called
def repeat(func_: Callable = None, /, times=2) -> Callable:
    """Decorator that makes the decorated function be executed the specified number of times (by default times=2)."""

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
            self, args = iterables.separate_self_from_args(args, exclude_self_types, globals_)

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

    def decorator(func):
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

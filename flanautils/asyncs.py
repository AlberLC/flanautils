import asyncio
import datetime
import multiprocessing
import queue
from asyncio import Task
from collections.abc import Callable, Iterable
from typing import Any, Type


def _process_function(
    func: Callable,
    *args,
    queue__: multiprocessing.Queue,
    **kwargs
):
    """Utility function for multiprocessing purposes."""

    if asyncio.iscoroutinefunction(func):
        queue__.put(asyncio.run(func(*args, **kwargs)))
    else:
        queue__.put(func(*args, **kwargs))


async def do_every(
    seconds: int | float | datetime.timedelta,
    func: Callable,
    *args,
    times: int = None,
    do_first_now=True,
    exceptions_to_capture: Type[Exception] | Iterable[Type[Exception]] = (),
    **kwargs
) -> Task:
    """
    Corutine function that runs the function every time provided in seconds or datetime.timedelta.

    You can specify a number of times.

    If you want to run the function the first time before waiting set do_first_now=True (the default).

    Exceptions specified in exceptions_to_capture are returned if raised when the task is completed.
    """

    if isinstance(seconds, datetime.timedelta):
        seconds = seconds.total_seconds()
    if not isinstance(exceptions_to_capture, Iterable):
        exceptions_to_capture = (exceptions_to_capture,)

    async def do_() -> Any:
        return await result if asyncio.iscoroutine(result := func(*args, **kwargs)) else result

    async def do_every_():
        if times is None:
            if do_first_now:
                await do_()
            while True:
                await asyncio.sleep(seconds)
                try:
                    await do_()
                except (*exceptions_to_capture,):
                    pass
        else:
            results = []
            if do_first_now:
                results.append(await do_())
                if times == 1:
                    return results
            while True:
                await asyncio.sleep(seconds)
                try:
                    results.append(await do_())
                except (*exceptions_to_capture,) as e:
                    results.append(e)
                if len(results) == times:
                    return results

    return asyncio.create_task(do_every_())


async def do_later(
    seconds: int | float | datetime.timedelta,
    func: Callable,
    *args,
    exceptions_to_capture: Type[Exception] | Iterable[Type[Exception]] = (),
    **kwargs
) -> Task:
    """
    Corutine function that executes the function after a time provided in seconds or datetime.timedelta.

    Exceptions specified in exceptions_to_capture are returned if raised.
    """

    if isinstance(seconds, datetime.timedelta):
        seconds = seconds.total_seconds()
    if not isinstance(exceptions_to_capture, Iterable):
        exceptions_to_capture = (exceptions_to_capture,)

    async def do_later_():
        await asyncio.sleep(seconds)
        try:
            return await result if asyncio.iscoroutine(result := func(*args, **kwargs)) else result
        except (*exceptions_to_capture,) as e:
            return e

    return asyncio.create_task(do_later_())


async def poll_process(process_: multiprocessing.Process, sleep_seconds=1):
    """
    Starts the process and wait until the process is done.

    Check every sleep_seconds (1 by default) if the process has finished.
    """

    process_.start()
    while process_.is_alive():
        await asyncio.sleep(sleep_seconds)


async def run_process_async(func: Callable, *args, timeout: int | float = None, **kwargs) -> Any:
    """
    Executes the function with the provided arguments in another process in parallel, waits asynchronously for its
    completion, and returns the result.

    If the timeout seconds expire an asyncio.TimeoutError is raised.
    """

    queue__ = multiprocessing.Queue()
    await wait_for_process(
        multiprocessing.Process(
            target=_process_function,
            args=(func, *args),
            kwargs={'queue__': queue__, **kwargs}
        ),
        timeout
    )
    try:
        return queue__.get(block=False)
    except queue.Empty:
        pass


async def wait_for_process(process_: multiprocessing.Process, timeout: int | float = None):
    """
    Wrapper function that starts the process and wait until the process is done.

    If the timeout seconds expire the process is terminated and an asyncio.TimeoutError is raised.
    """

    try:
        await asyncio.wait_for(poll_process(process_), timeout)
    except asyncio.TimeoutError:
        process_.terminate()
        raise

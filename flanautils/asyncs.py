import asyncio
import datetime
import functools
import html
import multiprocessing
import queue
from asyncio import Task
from collections.abc import Callable, Iterable
from typing import Any, Type

import aiohttp
import aiohttp.client_exceptions
import yarl

from flanautils.exceptions import ResponseError
from flanautils.models.enums import HTTPMethod


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
    exceptions_to_capture: Type[Exception] | Iterable[Type[Exception]] = (),
    **kwargs
) -> Task:
    """
    Corutine function that runs the function every time provided in seconds or datetime.timedelta.

    You can specify a number of times.

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
            while True:
                try:
                    await do_()
                except (*exceptions_to_capture,):
                    pass
                await asyncio.sleep(seconds)
        else:
            results = []
            while True:
                try:
                    results.append(await do_())
                except (*exceptions_to_capture,) as e:
                    results.append(e)
                if len(results) == times:
                    return results
                await asyncio.sleep(seconds)

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


async def request(http_method: HTTPMethod, url: str, params: dict = None, headers: dict = None, data: dict = None, session: aiohttp.ClientSession = None, return_response=False, intents=5) -> bytes | str | list | dict | aiohttp.ClientResponse:
    """
    Function that simplifies asynchronous http requests with aiohttp.

    If return_response=True it returns the response object instead of the response data (by default return_response=False).

    Retry the request if it fails up to the number of times specified by intents (by default intents=5).

    Raise exceptions.ResponseError if response.status != 200.
    """

    session_ = session or aiohttp.ClientSession()

    if http_method is HTTPMethod.GET:
        http_method = session_.get
    elif http_method is HTTPMethod.POST:
        http_method = session_.post
    else:
        raise ValueError('Bad http method.')

    try:
        if params:
            params = {str(k): str(v) for k, v in params.items()}

        for intent in range(intents):
            try:
                async with http_method(yarl.URL(url, encoded=True), params=params, headers=headers, data=data) as response:
                    if return_response:
                        return response
                    if response.status != 200:
                        raise ResponseError(f'{response.status} - {response.reason} - {await response.read()}')

                    if response.content_type == 'application/json':
                        return await response.json()
                    elif 'text' in response.content_type:
                        return html.unescape((await response.read()).decode('unicode_escape'))
                    else:
                        return await response.read()
            except aiohttp.client_exceptions.ServerDisconnectedError:
                if intent == 4:
                    raise
                await asyncio.sleep(1)
    finally:
        if not session:
            await session_.close()


get_request = functools.partial(request, HTTPMethod.GET)
post_request = functools.partial(request, HTTPMethod.POST)


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

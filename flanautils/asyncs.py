import asyncio
import datetime
import functools
import html
from asyncio import Task
from typing import Callable, Iterable, Type

import aiohttp
import aiohttp.client_exceptions

from flanautils.exceptions import ResponseError


async def do_every(
    seconds: int | datetime.timedelta,
    func: Callable,
    *args,
    exceptions_to_ignore: Type[BaseException] | Iterable[Type[BaseException]] = (),
    times: int = None,
    while_: bool = True,
    **kwargs
) -> Task:
    """
    Corutine function that runs the function every time provided in seconds or datetime.timedelta.

    You can specify a number of times and a stop condition.

    Exceptions specified in exceptions_to_ignore are ignored if raised.
    """

    if isinstance(seconds, datetime.timedelta):
        seconds = seconds.total_seconds()
    if not isinstance(exceptions_to_ignore, Iterable):
        exceptions_to_ignore = (exceptions_to_ignore,)

    async def do_every_():
        count = 0
        while while_ and (times is None or count < times):
            try:
                await func(*args, **kwargs)
            except (*exceptions_to_ignore,):
                pass
            count += 1
            await asyncio.sleep(seconds)

    return asyncio.create_task(do_every_())


async def do_later(
    seconds: int | datetime.timedelta,
    func: Callable,
    *args,
    exceptions_to_ignore: Type[BaseException] | Iterable[Type[BaseException]] = (),
    **kwargs
) -> Task:
    """
    Corutine function that executes the function after a time provided in seconds or datetime.timedelta.

    Exceptions specified in exceptions_to_ignore are ignored if raised.
    """

    if isinstance(seconds, datetime.timedelta):
        seconds = seconds.total_seconds()
    if not isinstance(exceptions_to_ignore, Iterable):
        exceptions_to_ignore = (exceptions_to_ignore,)

    async def do_later_():
        await asyncio.sleep(seconds)
        try:
            return await func(*args, **kwargs)
        except (*exceptions_to_ignore,):
            pass

    return asyncio.create_task(do_later_())


async def request(http_method, url: str, params: dict = None, headers: dict = None, data: dict = None, session: aiohttp.ClientSession = None, return_response=False, intents=5) -> bytes | str | list | dict | aiohttp.ClientResponse:
    """
    Function that simplifies asynchronous http requests with aiohttp.

    If return_response=True it returns the response object instead of the response data (by default return_response=False).

    Retry the request if it fails up to the number of times specified by intents (by default intents=5).

    Raise exceptions.ResponseError if response.status != 200.
    """

    session_ = session or aiohttp.ClientSession()

    if http_method == 'get':
        http_method = session_.get
    elif http_method == 'post':
        http_method = session_.post
    else:
        raise ValueError('Bad http method.')

    try:
        if params:
            params = {str(k): str(v) for k, v in params.items()}

        for intent in range(intents):
            try:
                async with http_method(url, params=params, headers=headers, data=data) as response:
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


get_request = functools.partial(request, 'get')
post_request = functools.partial(request, 'post')

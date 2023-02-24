import asyncio
import functools
import html

import aiohttp
import aiohttp.client_exceptions
import yarl

from flanautils import constants
from flanautils.exceptions import ResponseError
from flanautils.models.enums import HTTPMethod


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


async def resolve_real_url(url: str, headers=None) -> str:
    if not url.startswith('http'):
        url = f'https://{url}'
    if headers is None:
        headers = {'User-Agent': constants.USER_AGENT}

    return str((await get_request(url, headers=headers, return_response=True)).url)

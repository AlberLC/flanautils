import asyncio
import functools
import html
import random

import aiohttp
import aiohttp.client_exceptions
import browser_cookie3
import yarl

from flanautils import constants
from flanautils.exceptions import ResponseError
from flanautils.models.enums import HTTPMethod


def browser_cookies(domain: str, ignore_expired=True) -> list[dict]:
    cookies = []

    for cookie in browser_cookie3.chrome(domain_name=domain):
        cookie_vars = vars(cookie)
        if ignore_expired and 'expires' in cookie_vars and not cookie_vars['expires']:
            continue

        cookie_dict = {}
        for k, v in cookie_vars.items():
            if k.startswith('_'):
                cookie_dict |= v
                continue

            if k == 'secure':
                v = bool(v)
            cookie_dict[k] = v
        cookies.append(cookie_dict)

    return cookies


async def request(
    http_method: HTTPMethod,
    url: str,
    params: dict = None,
    headers: dict = None,
    data: dict = None,
    session: aiohttp.ClientSession = None,
    clean_text=True,
    return_response=False,
    attempts=5
) -> bytes | str | list | dict | aiohttp.ClientResponse:
    """
    Function that simplifies asynchronous http requests with aiohttp.

    If return_response=True it returns the response object instead of the response data (by default return_response=False).

    Retry the request if it fails up to the number of times specified by tries (by default tries=5).

    Raise exceptions.ResponseError if response.status != 200.
    """

    if not url.startswith('http'):
        url = f'https://{url}'

    if params:
        params = {str(k): str(v) for k, v in params.items()}

    session_ = session or aiohttp.ClientSession()

    try:
        if http_method is HTTPMethod.GET:
            http_method = session_.get
        elif http_method is HTTPMethod.POST:
            http_method = session_.post
        else:
            raise ValueError('Bad http method.')

        for attempt in range(attempts - 1, -1, -1):
            try:
                async with http_method(yarl.URL(url, encoded=True), params=params, headers=headers, data=data) as response:
                    if return_response:
                        return response
                    if response.status != 200:
                        raise ResponseError(f'{response.status} - {response.reason} - {await response.read()}')

                    if response.content_type == 'application/json':
                        return await response.json()
                    elif 'text' in response.content_type:
                        if clean_text:
                            return html.unescape((await response.read()).decode('unicode_escape').encode(errors='xmlcharrefreplace').decode().replace('\\', ''))
                        else:
                            return await response.text()
                    else:
                        return await response.read()
            except aiohttp.client_exceptions.ServerDisconnectedError:
                if not attempt:
                    raise
                await asyncio.sleep(1)
    finally:
        if not session:
            await session_.close()


get_request = functools.partial(request, HTTPMethod.GET)
post_request = functools.partial(request, HTTPMethod.POST)


async def resolve_real_url(url: str, headers=None) -> str:
    if headers is None:
        headers = {'User-Agent': random.choice(constants.GOOGLE_BOT_USER_AGENTS)}
    return str((await get_request(url, headers=headers, return_response=True)).url)

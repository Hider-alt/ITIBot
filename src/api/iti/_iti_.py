import asyncio
import logging
import os
from asyncio import sleep

import aiohttp
from aiohttp import ClientSession

logger = logging.getLogger(__name__)


class ITIAPI:
    BASE_URL = "https://www.ispascalcomandini.it"
    _session: aiohttp.ClientSession | None = None
    _lock = asyncio.Lock()
    _logged_in: bool = False

    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    @classmethod
    async def get_session(cls) -> ClientSession | None:
        if cls._session is None or cls._session.closed:
            cls._session = aiohttp.ClientSession(
                cookie_jar=aiohttp.CookieJar(),
                headers={"User-Agent": cls.USER_AGENT}
            )
            cls._logged_in = False
        return cls._session

    @classmethod
    async def close(cls):
        if cls._session and not cls._session.closed:
            await cls._session.close()
            cls._session = None
            cls._logged_in = False

    @classmethod
    async def _login(cls) -> bool:
        username = os.environ.get("ITI_USERNAME")
        password = os.environ.get("ITI_PASSWORD")

        if not username or not password:
            raise RuntimeError(
                "Credentials not set"
            )

        session = await cls.get_session()

        login_url = f"{cls.BASE_URL}/auth-p7/app/default/AuthApi4.php?a=aLoginPwd"
        login_headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": cls.BASE_URL,
            "Referer": f"{cls.BASE_URL}/",
            "Accept": "*/*",
        }
        login_data = {
            "cid": "",
            "uid": username,
            "pwd": password,
            "pin": "",
            "target": ""
        }

        async with session.post(login_url, data=login_data, headers=login_headers, ssl=False) as response:
            if response.status != 200:
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                    message=f"Error during login {login_url}: {response.reason}"
                )

            try:
                res_json = await response.json(content_type=None)
            except Exception as e:
                res_text = await response.text()
                raise RuntimeError(f"Invalid response: {res_text[:200]}") from e

            auth_data = res_json.get("data", {}).get("auth", {})
            if not auth_data.get("loggedIn", False):
                errors = auth_data.get("errors", ["Invalid credentials or login failed"])
                raise RuntimeError(f"Auth error: {errors}")

        # 2. Sincronizzazione sessione nel portale scolastico (pvw2)
        auth_url = f"{cls.BASE_URL}/pvw2/app/default/auth.php"
        auth_headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": cls.BASE_URL,
            "Referer": f"{cls.BASE_URL}/pagine/variazioni-orario-istituto-tecnico-tecnologico-1",
            "Accept": "application/json, text/javascript, */*; q=0.01",
        }
        async with session.post(auth_url, data={"act": "checkUser"}, headers=auth_headers, ssl=False) as response:
            if response.status != 200:
                logger.warning(f"auth.php checkUser returned {response.status}")

        cls._logged_in = True
        return True

    @classmethod
    async def _request(cls, endpoint: str, params: dict = None, method: str = "GET", _retried: bool = False) -> str:
        """
        Makes an HTTP request to the specified endpoint and returns the response text.
        Handles authentication and transparently re-authenticates if a 403 Forbidden is returned.

        :param endpoint: The API endpoint to request.
        :param params: Optional parameters for the request.
        :param method: The HTTP method to use for the request (default is "GET").
        :param _retried: Internal flag indicating if this call is already a retry attempt.
        :return: The response text from the API.
        """
        url = f"{cls.BASE_URL}{endpoint}" if endpoint.startswith("/") else endpoint
        session = await cls.get_session()

        if not cls._logged_in:
            async with cls._lock:
                if not cls._logged_in:
                    await cls._login()

        async with session.request(method, url, params=params, ssl=False) as response:
            if response.status in (401, 403):
                if not _retried:
                    logger.info(f"Received {response.status} from {url}. Attempting re-login...")
                    async with cls._lock:
                        cls._logged_in = False
                        await cls._login()

                    # Retry
                    return await cls._request(endpoint, params=params, method=method, _retried=True)
                else:
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=f"Access denied ({response.status}) to {url} even after re-login. Stopping to avoid spam."
                    )

            if response.status < 200 or response.status >= 300:
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                    message=f"Error fetching {url}: {response.reason}"
                )

            return await response.text()

    @classmethod
    async def _download_pdf(cls, url: str) -> bytes:
        """
        Downloads a PDF file from the specified URL using the managed session.

        :param url: The API endpoint or URL to download the PDF from.
        :return: The content of the downloaded PDF file as bytes.
        """
        session = await cls.get_session()
        pdf = None
        tries = 0

        while tries < 3:
            try:
                async with session.get(url, ssl=False) as response:
                    if response.status == 200:
                        pdf = await response.read()
                        break
                    else:
                        tries += 1
                        await sleep(2)
            except aiohttp.ClientError:
                tries += 1
                await sleep(2)

        if not pdf:
            raise Exception(f"Could not download PDF from {url}")

        return pdf


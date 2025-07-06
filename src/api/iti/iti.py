from asyncio import sleep

import aiohttp


class ITIAPI:
    BASE_URL = "https://www.ispascalcomandini.it"

    @staticmethod
    async def _request(endpoint: str, params: dict = None, method: str = "GET") -> str:
        """
        Makes a GET request to the specified endpoint and returns the response text.

        :param endpoint: The API endpoint to request.
        :param params: Optional parameters for the request.
        :param method: The HTTP method to use for the request (default is "GET").
        :return: The response text from the API.
        """

        url = f"{ITIAPI.BASE_URL}{endpoint}"

        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, params=params, ssl=False) as response:
                # Check if response is class 2xx
                if response.status < 200 or response.status >= 300:
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=f"Error fetching {url}: {response.reason}"
                    )

                return await response.text()

    @staticmethod
    async def _download_pdf(url: str) -> bytes:
        """
        Downloads a PDF file from the specified endpoint.

        :param url: The API endpoint to download the PDF from.
        :return: The content of the downloaded PDF file as bytes.
        """

        pdf = None
        tries = 0

        while tries < 5:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, ssl=False) as response:
                        pdf = await response.read()
            except aiohttp.ClientError:
                tries += 1
                await sleep(3)
            else:
                break

        if not pdf:
            raise Exception("Could not download PDF")

        return pdf

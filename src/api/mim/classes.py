import io

import aiohttp
import pandas as pd


class MIMClasses:
    __BASE_URL = "https://dati.istruzione.it/opendata/ALTEMILIAROMAGNA"

    @staticmethod
    async def get_classes() -> set[str]:
        """
        It gets the classes from the school books MIM API

        :return: A set of strings, each string is a class name (year + section).
        """

        query = "PREFIX%20miur%3A%20%3Chttp%3A%2F%2Fwww.miur.it%2Fns%2Fmiur%23%3E%0A%0ASELECT%20%3FAnnoCorso%20%3FSezioneAnno%0AWHERE%20%7B%0A%20%20GRAPH%20%3Fg%20%7B%0A%20%20%20%20%3FS%20miur%3ACODICESCUOLA%20%3FCodiceScuola%20.%0A%20%20%20%20%3FS%20miur%3AANNOCORSO%20%3FAnnoCorso%20.%0A%20%20%20%20%3FS%20miur%3ASEZIONEANNO%20%3FSezioneAnno%20.%0A%20%20%20%20%0A%20%20%20%20FILTER(%3FCodiceScuola%20%3D%20%22FOTF011015%22)%0A%20%20%7D%0A%7D%0A%0ALIMIT%201500"
        df = await MIMClasses.__run_query(query)

        return set(df['AnnoCorso'].astype(str) + df['SezioneAnno'])

    @staticmethod
    async def __run_query(query: str) -> pd.DataFrame:
        """
        It runs a query on the MIM API and returns the result as a DataFrame.

        :param query: The query to run on the MIM API.
        :return: A dictionary containing the result of the query.
        """

        url = f"{MIMClasses.__BASE_URL}/query?query={query}&dataType=csv"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise ValueError(f"Failed to fetch data from {url}, status code: {response.status}")

                data = await response.read()

                return pd.read_csv(io.BytesIO(data))

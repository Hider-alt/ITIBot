from bs4 import BeautifulSoup

from src.api.iti.iti import ITIAPI


class VariationsAPI(ITIAPI):
    __VARIATIONS_PATH = "/variazioni-orario-istituto-tecnico-tecnologico/2017/09/15/"
    __DIV_ID = 'post-612'

    @staticmethod
    async def get_variations_links() -> list[str]:
        """
        It gets the links of the PDF files from the ITI page

        :return: A list of strings, each string is a link to a PDF file.
        """

        iti_page = await ITIAPI._request(VariationsAPI.__VARIATIONS_PATH)

        soup = BeautifulSoup(iti_page, 'html.parser')

        # Get <a> elements of the page
        a = soup.find(id=VariationsAPI.__DIV_ID).find_all("div", {"class": "entry-content"})[0].find_all('a')

        # Get PDF links from <a> elements
        links = [link.get('href') for link in a]

        # Filter out links that do not match the conditions
        conditions = [
            lambda link: link.startswith('https://www.ispascalcomandini.it/wp-content/uploads/'),
            lambda link: 'parte2' not in link,
            lambda link: 'aule' not in link
        ]

        return [link for link in links if all(condition(link) for condition in conditions)]

    @staticmethod
    async def download_variation_pdf(url: str, save_path: str) -> None:
        """
        Downloads a PDF file from the given link.

        :param url: The URL of the PDF file to download.
        :param save_path: The local path where the PDF file will be saved.
        :return: None, but saves the PDF file to the local filesystem.
        """

        pdf = await ITIAPI._download_pdf(url)
        if pdf is None:
            raise ValueError(f"Failed to download PDF from {url}")

        with open(save_path, 'wb') as f:
            f.write(pdf)

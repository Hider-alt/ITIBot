import datetime
import re

from bs4 import BeautifulSoup

from src.api.iti._iti_ import ITIAPI
from src.api.iti.variations_parsers.excel_ui import ExcelUIParser
from src.api.iti.variations_parsers.new_ui import NewUIParser
from src.api.iti.variations_parsers.ocr import OCRParser
from src.api.iti.variations_parsers.old_ui import OldUIParser
from src.models.variation import Variation
from src.utils.datetime_utils import parse_italian_date


class VariationsAPI(ITIAPI):
    __VARIATIONS_PATH = "/pagine/variazioni-orario-istituto-tecnico-tecnologico-1"
    __DIV_ID = 'maincontent'

    @staticmethod
    async def get_variations_links() -> list[str]:
        """
        It gets the links of the PDF files from the ITI page

        :return: A list of strings, each string is a link to a PDF file.
        """

        iti_page = await ITIAPI._request(VariationsAPI.__VARIATIONS_PATH)

        soup = BeautifulSoup(iti_page, 'html.parser')

        # Get <a> elements of the page
        a = soup.find(id=VariationsAPI.__DIV_ID).find_all('a')

        # Get PDF links from <a> elements
        links: list[str] = [link.get('href') for link in a]

        # Filter out links that do not match the conditions
        conditions = [
            lambda link: link is not None,
            lambda link: link.startswith('https://cspace.spaggiari.eu/pub/FOIP0004/'),
            lambda link: 'parte2' not in link,
            lambda link: 'aule' not in link
        ]

        return [link for link in links if all(condition(link) for condition in conditions)]

    @staticmethod
    async def get_variations(*links: str) -> list[Variation] | None:
        """
        It fetches the variations from the given links and returns a list of Variation objects.

        :param links: A list of links to the PDF files containing variations.
        :return: A list of Variation objects or None if no variations are found (e.g., if all parsing methods fail).
        """

        variations = []
        for link in links:
            date = VariationsAPI.__get_date_from_link(link)

            try:
                pdf = await ITIAPI._download_pdf(link)
                if pdf is None:
                    print(f"Failed to download PDF from {link}")
                    continue

                pdf_variations = await VariationsAPI.__parse_pdf(pdf)
                VariationsAPI.__set_variations_date(pdf_variations, date)

                variations.extend(pdf_variations)
            except Exception as e:
                print(f"Error processing link {link}: {e}")

        return variations

    @staticmethod
    def __get_date_from_link(link: str) -> datetime.datetime:
        """
        Extracts the date from the link.

        :param link: The link to extract the date from.
        :return: The date in 'dd-mm-yyyy' format.
        """
        date = link.split('/')[-1][:-4].lower()
        date = re.search(r'\d+\s+\w+', date).group(0)  # Extracts the date part

        return parse_italian_date(date)

    @staticmethod
    def __set_variations_date(variations: list[Variation], date: datetime.datetime):
        """
        Sets the date for each variation in the list.

        :param variations: A list of Variation objects.
        :param date: The date to set for each variation.
        """
        for variation in variations:
            variation.set_date(date)

    @staticmethod
    async def __parse_pdf(pdf: bytes) -> list[Variation] | None:
        """
        Parses the PDF content using different methods until one succeeds.

        :param pdf: The PDF content as bytes.
        :return: A list of Variation objects or None if parsing fails.
        """

        parsers = [ExcelUIParser(), NewUIParser(), OldUIParser(), OCRParser()]

        for parser in parsers:
            try:
                variations = await parser(pdf)
                if variations:
                    return variations
            except Exception as e:
                print(f"Error parsing with {parser.__class__.__name__}: {e}")

        print("All methods failed to parse the PDF.")
        return None

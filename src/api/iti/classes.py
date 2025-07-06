import re
from io import BytesIO

import pdfplumber
from bs4 import BeautifulSoup

from src.api.iti.iti import ITIAPI


class ClassesAPI(ITIAPI):
    __CLASSES_PATH = "/orario-e-calendario/"

    @staticmethod
    async def get_classes() -> list[str]:
        """
        It gets the classes from the ITI PDF

        :return: A list of strings, each string is a class name.
        """

        link = await ClassesAPI.__get_classes_link()

        if not link:
            raise ValueError("No class link found")

        classes_pdf = await ITIAPI._download_pdf(link)
        if classes_pdf is None:
            raise ValueError(f"Failed to download PDF from {link}")

        return ClassesAPI.__extract_classes(BytesIO(classes_pdf))

    @staticmethod
    async def __get_classes_link() -> str | None:
        """
        It gets the link of the classes PDF file from the ITI page.

        :return: A string containing the link to the classes PDF file, or None if no link is found.
        """

        iti_page = await ITIAPI._request(ClassesAPI.__CLASSES_PATH)

        soup = BeautifulSoup(iti_page, 'html.parser')

        # Find <a> element that in href contains "orario" and "classi" and "pascal" (case insensitive)
        contain = ['orario', 'classi', 'pascal']
        a = soup.find('a', href=lambda href: href and all(word in href.lower() for word in contain))

        if not a:
            raise ValueError("No class links found on the page")

        # Get the href attribute of the <a> element
        link = a.get('href')
        if not link:
            raise ValueError("No href attribute found in the class link")

        return link

    @staticmethod
    def __extract_classes(pdf_bytes: BytesIO) -> list[str]:
        with pdfplumber.open(pdf_bytes) as pdf:
            # Extract the first page of the PDF
            first_page = pdf.pages[0]

            # Extract the table from the first page
            text = first_page.extract_text()

        # Get classes (using regex \d[A-Z]+)
        classes = re.findall(r"\d[A-Z]+", text)
        if not classes:
            raise ValueError("No classes found in the PDF")

        return classes

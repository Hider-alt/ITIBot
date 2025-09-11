import re
from io import BytesIO

import pdfplumber
from bs4 import BeautifulSoup

from src.api.iti._iti_ import ITIAPI


class ClassesAPI(ITIAPI):
    __CLASSES_PATH = "/orario-e-calendario/"

    @staticmethod
    async def get_classes() -> set[str]:
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

        with open("assets/classes.pdf", "rb") as f:
            classes_pdf = f.read()

        return ClassesAPI.__extract_classes(BytesIO(classes_pdf))

    @staticmethod
    async def __get_classes_link() -> str | None:
        """
        It gets the link of the classes PDF file from the ITI page.

        :return: A string containing the link to the classes PDF file, or None if no link is found.
        """

        iti_page = await ITIAPI._request(ClassesAPI.__CLASSES_PATH)

        soup = BeautifulSoup(iti_page, 'html.parser')

        # Find <a> element that in href contains "orario" and "classi" and "pascal" (case-insensitive)
        contain = ['orario', 'classi', 'pascal']
        a = soup.find('a', href=lambda href: href and all(word in href.lower() for word in contain))

        if not a:
            return None

        # Get the href attribute of the <a> element
        link = a.get('href')
        if not link:
            return None

        return link

    @staticmethod
    def __extract_classes(pdf_bytes: BytesIO) -> set[str]:
        with pdfplumber.open(pdf_bytes) as pdf:
            # Extract the 1st and 2nd page of the PDF
            page1 = pdf.pages[0]
            page2 = pdf.pages[1]

            # Extract the table from the first page
            text = page1.extract_text() + "\n" + page2.extract_text()

        # Get classes (using regex \d[A-Z]+)
        classes = re.findall(r"\d[A-Z]+", text)
        if not classes:
            raise ValueError("No classes found in the PDF")

        return set(classes)

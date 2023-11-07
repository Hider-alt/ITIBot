import csv
import os
import re

import PyPDF2
import aiohttp
import pandas as pd
import pdfplumber

from asyncio import sleep
from bs4 import BeautifulSoup

from src.utils.utils import to_thread


async def get_variations_links() -> list[str]:
    """
    It gets the links of the pdf files from the ITI page

    :return: A list of strings, each string is a link to a pdf file.
    """
    iti_url = "https://www.ispascalcomandini.it/variazioni-orario-istituto-tecnico-tecnologico/2017/09/15/"
    async with aiohttp.ClientSession() as session:
        async with session.get(iti_url) as response:
            iti_page = await response.text()

    soup = BeautifulSoup(iti_page, 'html.parser')

    # Get links of the page
    a = soup.find(id='post-612').find_all("div", {"class": "entry-content"})[0].find_all('a')

    # Filter only pdf links
    links = [link.get('href') for link in a]
    return [link for link in links if
            link.startswith('https://www.ispascalcomandini.it/wp-content/uploads/2017/09') and 'parte2' not in link]


async def save_PDF(url: str, path: str) -> None:
    """
    It downloads a PDF file from a given URL and saves it to a given path

    :param url: the url of the PDF you want to download
    :param path: The path to the file you want to save the PDF to
    """
    pdf = None
    tries = 0
    while tries < 5:
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(url) as response:
                    pdf = await response.read()
        except aiohttp.ClientError:
            tries += 1
            await sleep(3)
            continue
        else:
            break

    if not pdf:
        raise Exception("Could not download PDF")

    with open(path, 'wb') as f:
        f.write(pdf)


def pdf_to_csv(pdf_path: str, output_path: str, delete_original=True):
    """
    It takes a PDF file, converts it to a CSV file, and saves it to a given path

    :param pdf_path: The path to the PDF file you want to convert
    :param output_path: The path to the output file
    :param delete_original: If True, it deletes the original PDF file
    :return: True if the conversion was successful, False otherwise
    """

    list_pdf = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            list_pdf.extend(table)

    firma_index = None
    for i, row in enumerate(list_pdf):
        if i == 0:
            # Headers
            # [['Ora Classe Doc.Assente Sost.1 Sost.2 Pagam. Note Firma', None, None, None, None, None, None, None] -> ['Ora', 'Classe', 'Doc.Assente', 'Sost.1', 'Sost.2', 'Pagam.', 'Note', 'Firma']
            list_pdf[i] = list_pdf[i][0].split(' ')
            if list_pdf[i][0] != 'Ora':
                return False

            # Remove 'Firma' element if it exists or "..." element if it exists
            if 'Firma' in list_pdf[i]:
                firma_index = list_pdf[i].index('Firma')
                list_pdf[i].remove('Firma')
            elif '...' in list_pdf[i]:
                list_pdf[i].remove('...')

            # Remove all None elements
            list_pdf[i] = [x for x in list_pdf[i] if x]
            list_pdf[i].insert(2, 'Aula')

            continue

        if len(row) == 0:
            continue

        # Repeating header
        if row[0] == 'Ora' or row[1] is None or row[1] == '':
            list_pdf[i] = []
            continue

        # Remove the row and the next one (if it exists)
        if 'ISS "Pascal Comandini" - Cesena' in row[0]:
            list_pdf[i] = []
            if i + 1 < len(list_pdf):
                list_pdf[i + 1] = []
            continue

        # Remove 'Firma' element
        if firma_index is not None:
            row.pop(firma_index)

        # Split second element in 2nd and 3rd element (e.g. '3A(LT)' -> '3A', 'LT'; '5I\n(PALESTRAPASCAL)' -> '5I', 'PALESTRAPASCAL')
        text = str(row[1])  # Copy the string

        list_pdf[i][1] = text.split('\n')[0].split('(')[0]

        classroom = re.findall(r'\((.*?)\)', text)
        classroom = classroom[0] if len(classroom) > 0 else ''
        list_pdf[i].insert(2, classroom)

    list_pdf = [row for row in list_pdf if len(row) != 0]

    # Write list_pdf to CSV
    with open(output_path, 'w', newline='', encoding='ISO-8859-1') as f:
        writer = csv.writer(f)
        writer.writerows(list_pdf)

    if delete_original:
        os.remove(pdf_path)

    return True


def fix_pdf(pdf_path: str, output_path: str, delete_original: bool = True, rotation_degrees=270) -> None:
    """
    It takes a PDF file, rotates each page and saves the result to a new PDF file

    :param pdf_path: The path to the PDF file you want to rotate
    :param output_path: The path to the output file
    :param delete_original: If True, the original PDF will be deleted, defaults to True (optional)
    :param rotation_degrees: The degrees to rotate the pages, defaults to 270
    """
    with open(pdf_path, 'rb') as pdf_file:
        # Rotate pages
        pdf_reader = PyPDF2.PdfFileReader(pdf_file, strict=False)
        pdf_writer = PyPDF2.PdfFileWriter()

        for page in range(pdf_reader.numPages):
            page = pdf_reader.getPage(page)
            page.rotateClockwise(rotation_degrees)
            pdf_writer.addPage(page)

        # Save the rotated pages to a new PDF file
        with open(output_path, 'wb') as new_pdf:
            pdf_writer.write(new_pdf)

    if delete_original:
        os.remove(pdf_path)


@to_thread
def read_csv_pandas(csv_path):
    """
    It reads a CSV file and returns a pandas DataFrame

    :param csv_path: The path to the CSV file
    :return: A pandas DataFrame
    """
    return pd.read_csv(csv_path, converters={i: str for i in range(0, 7)}, encoding='ISO-8859-1')

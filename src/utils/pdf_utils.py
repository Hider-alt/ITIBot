import json
import os

import PyPDF2
import camelot
import requests

from asyncio import sleep
from bs4 import BeautifulSoup
from requests import Timeout
import fitz


def get_pdf_links() -> list[str]:
    """
    It gets the links of the pdf files from the ITI page

    :return: A list of strings, each string is a link to a pdf file.
    """
    iti_url = "https://www.ispascalcomandini.it/variazioni-orario-istituto-tecnico-tecnologico/2017/09/15/"
    iti_page = requests.get(iti_url).content
    soup = BeautifulSoup(iti_page, 'html.parser')

    # Get links of the page
    a = soup.find(id='post-612').find_all("div", {"class": "entry-content"})[0].find_all('a')

    # Filter only pdf links
    links = [link.get('href') for link in a]
    print(links)
    return [link for link in links if link.startswith('https://www.ispascalcomandini.it/wp-content/uploads/2017/09')]


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
            pdf = requests.get(url, timeout=10)
        except Timeout:
            tries += 1
            await sleep(3)
            continue
        else:
            break

    if not pdf:
        raise Exception("Could not download PDF")

    with open(path, 'wb') as f:
        f.write(pdf.content)


def fix_pdf(pdf_path: str, output_path: str, remove_original: bool = True) -> None:
    """
    It takes a PDF file, rotates each page by a number of degrees that is set in data/config.json,
    and saves the result to a new PDF file

    :param pdf_path: The path to the PDF file you want to rotate
    :param output_path: The path to the output file
    :param remove_original: If True, the original PDF will be deleted, defaults to True (optional)
    """
    # Open config.json
    with open('data/config.json', 'r') as f:
        config = json.load(f)

    temp_file_path = output_path[:-4] + '_temp.pdf'

    with open(pdf_path, 'rb') as pdf_file:
        # Rotate pages
        pdf_reader = PyPDF2.PdfFileReader(pdf_file)
        pdf_writer = PyPDF2.PdfFileWriter()

        for page in range(pdf_reader.numPages):
            page = pdf_reader.getPage(page)
            page.rotateClockwise(config['rotation_angle'])
            pdf_writer.addPage(page)

        # Save the rotated pages to a new PDF file
        with open(temp_file_path, 'wb') as new_pdf:
            pdf_writer.write(new_pdf)

    # Draw separator line
    with fitz.open(temp_file_path) as pdf:
        for page in pdf:
            page.draw_line(
                (config['start_coords'][0], config['start_coords'][1]), (config['end_coords'][0], config['end_coords'][1]),
                color=(0, 0, 0),
                width=2
            )

        pdf.save(output_path)

    # Delete temporary file
    os.remove(temp_file_path)

    if remove_original:
        os.remove(pdf_path)

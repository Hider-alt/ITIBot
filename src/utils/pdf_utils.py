import json
import os
from asyncio import sleep

import PyPDF2 as PyPDF2
import camelot
import requests
from bs4 import BeautifulSoup
from requests import Timeout


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


def fix_pdf(pdf_path: str, output_folder: str, remove_original: bool = True) -> None:
    """
    It takes a PDF file, rotates each page by a number of degrees that is set in data/config.json,
    and saves the result to a new PDF file

    :param pdf_path: The path to the PDF file you want to rotate
    :param output_folder: The path to the output file
    :param remove_original: If True, the original PDF will be deleted, defaults to True (optional)
    """
    # Open config.json
    with open('data/config.json', 'r') as f:
        config = json.load(f)

    with open(pdf_path, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        # Create output folder if it doesn't exist
        if not os.path.exists(output_folder):
            os.mkdir(output_folder)

        # Split pages in different files
        for num_page in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[num_page]
            page.rotate(config['rotation_angle'])
            pdf_writer = PyPDF2.PdfWriter()
            pdf_writer.add_page(page)
            with open(output_folder + f"/{num_page}.pdf", 'wb') as f:
                pdf_writer.write(f)

    if remove_original:
        os.remove(pdf_path)


def pages_to_csv(pages_path, output_folder):
    """
    It takes a folder containing PDF files, and saves the text of each page to a CSV file

    :param pages_path: The path to the folder containing the PDF files
    :param output_folder: The path to the output folder
    """

    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    for file in os.listdir(pages_path):
        if file.endswith(".pdf"):
            tables = camelot.read_pdf(pages_path + "/" + file)

            tables[0].to_csv(output_folder + "/" + file[:-4] + ".csv")
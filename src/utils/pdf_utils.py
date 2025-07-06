import csv
import os

import pdfplumber
from PyPDF2 import PdfReader, PdfWriter


class ConversionException(Exception):
    def __init__(self, message: str):
        super().__init__(message)


def rotate_pdf(pdf_path: str, output_path: str, delete_original: bool = True, rotation_degrees=270) -> None:
    """
    It takes a PDF file, rotates (anti-clockwise) each page and saves the result to a new PDF file

    :param pdf_path: The path to the PDF file you want to rotate
    :param output_path: The path to the output file
    :param delete_original: If True, the original PDF will be deleted, defaults to True (optional)
    :param rotation_degrees: The degrees to rotate the pages, defaults to 270
    """
    with open(pdf_path, 'rb') as pdf_file:
        # Rotate pages
        pdf_reader = PdfReader(pdf_file)
        pdf_writer = PdfWriter()

        for page in pdf_reader.pages:
            page.rotate(-rotation_degrees)
            pdf_writer.add_page(page)

        # Save the rotated pages to a new PDF file
        with open(output_path, 'wb') as new_pdf:
            pdf_writer.write(new_pdf)

    if delete_original:
        os.remove(pdf_path)


def get_rows_from_pdf(pdf_path: str, table_settings: dict = None) -> list:
    """
    It takes a PDF file and returns a list of strings, each representing a line in the PDF

    :param pdf_path: The path to the PDF file
    :param table_settings: Settings for the table extraction
    :return: A list of strings, each representing a line in the PDF
    """

    if table_settings is None:
        table_settings = {}

    lines = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            table = page.extract_table(table_settings=table_settings)
            lines.extend(table)

    return lines


def write_rows_to_csv(csv_path: str, rows: list, encoding: str):
    """
    Write the rows to a CSV file

    :param csv_path: Path to the CSV file
    :param rows: List of rows to write
    :param encoding: Encoding to use
    :return: None
    """

    with open(csv_path, 'w', newline='', encoding=encoding) as f:
        writer = csv.writer(f)
        writer.writerows(rows)

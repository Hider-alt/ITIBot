from io import BytesIO

import pdfplumber
from PyPDF2 import PdfReader, PdfWriter


class ConversionException(Exception):    # maybe move
    def __init__(self, message: str):
        super().__init__(message)


def save_pdf(pdf: bytes, path: str) -> None:
    """
    Saves PDF bytes to a specified file path.

    :param pdf: PDF bytes to be saved
    :param path: Path where the PDF will be saved
    """
    with open(path, 'wb') as f:
        f.write(pdf)


def rotate_pdf(pdf: bytes, rotation_degrees: int) -> bytes:
    """
    Rotates the pages of a PDF by a specified number of degrees.

    :param pdf: PDF bytes to be rotated
    :param rotation_degrees: The degrees to rotate the PDF pages. Must be a multiple of 90.
    :return: Rotated PDF bytes
    """
    if rotation_degrees % 90 != 0:
        raise ValueError("rotation_degrees must be a multiple of 90")

    if rotation_degrees % 360 == 0:
        return pdf

    with BytesIO(pdf) as input_stream, BytesIO() as output_stream:
        reader = PdfReader(input_stream)
        writer = PdfWriter()

        for page in reader.pages:
            page.rotate(rotation_degrees)
            writer.add_page(page)

        writer.write(output_stream)
        return output_stream.getvalue()


def get_rows_from_pdf_table(pdf: bytes, table_settings: dict = None) -> list[list[str]]:
    """
    Extracts rows from a PDF table (text-based extraction).

    :param pdf: PDF bytes
    :param table_settings: Settings for the table extraction
    :return: A list of strings, each representing a row in the PDF
    """

    if table_settings is None:
        table_settings = {}

    lines = []
    with pdfplumber.open(BytesIO(pdf)) as pdf:
        for page in pdf.pages:
            table = page.extract_table(table_settings=table_settings)
            lines.extend(table)

    return lines

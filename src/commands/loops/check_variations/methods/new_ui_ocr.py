import os
import re
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
from typing import Any

import pdfplumber
from PIL import Image
from PyPDF2 import PdfReader, PdfWriter
from paddleocr import PaddleOCR

from src.utils.os_utils import clear_folder
from src.utils.pdf_utils import write_rows_to_csv
from src.utils.utils import default_nested_dict, to_thread


def process_page(pdf_path) -> defaultdict[Any, defaultdict[Any, None]]:
    table = defaultdict(default_nested_dict)

    page_nr = int(pdf_path.split('-')[-1].split('.')[0])
    ocr = PaddleOCR(lang="it", use_angle_cls=False, rec_model_dir=r"data/ocr_models/rec/", det_model_dir="data/ocr_models/det/")

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]

        table_page = page.find_table(table_settings={"snap_tolerance": 1})
        page_rows = len(table_page.rows)
        cells = deepcopy(table_page.cells)

        # Loop cells and extract text (OCR)
        for j, cell in enumerate(cells):
            # Restrict cell of 3dpi
            cell_crop = page.crop((cell[0] + 3, cell[1] + 3, cell[2] - 3, cell[3] - 3))

            img = cell_crop.to_image(resolution=300)

            # Save image to data/downloads/tmp-ocr
            img_path = f'data/tmp-ocr/tmp-{page_nr}-{j}.png'
            img.save(img_path)

            # Add 50px on each side
            img = Image.open(img_path)
            width, height = img.size

            new_width = width + 100
            new_height = height + 100

            new_img = Image.new("RGB", (new_width, new_height), "white")

            new_img.paste(img, (50, 50))
            new_img.save(img_path)

            row = j % page_rows
            col = j // page_rows

            # OCR
            ocr_res = ocr.ocr(img_path, cls=False, bin=True)
            text = ocr_res[0][0][1][0] if ocr_res[0] else '-'

            # Print if % of confidence is low
            if ocr_res[0] and ocr_res[0][0][1][1] < 0.95:
                print(f'Low confidence (OCR): {ocr_res[0][0][1][1]} - Page {page_nr} - Row {row} - Col {col}')

            # Fix wrong characters in class column
            if col == 1 and row != 0:
                if len(text) == 2 and text[1] == '1':
                    text = text[0] + 'I'

            if col in [3, 4, 5] and row != 0:
                text = text.split('-')[0].replace('_', ' ')
                text = '-' if text == '' else text

            # Print if OCR not respect pattern nXXX or nX
            if col == 1 and row != 0 and not re.match(r'\d{1,3}[A-Z]?', text):
                print(f'Not existing class (OCR): {text} - Page {page_nr} - Row {row} - Col {col}')

            table[row][col] = text

    return table


@to_thread
def pdf_to_csv(pdf_path: str, output_path: str, delete_original=True):
    """
    Convert a PDF file to a CSV file using OCR.

    :param pdf_path: Path to the PDF file
    :param output_path: Path to the output CSV file
    :param delete_original: If True, the original PDF file will be deleted
    :return: True if the conversion was successful, False otherwise
    """

    # Create many PDF files in tmp-ocr, one for each page
    reader = PdfReader(pdf_path)
    pdfs = []

    for i, page in enumerate(reader.pages):
        writer = PdfWriter()
        writer.add_page(page)

        path = f'data/tmp-ocr/tmp-{i}.pdf'
        pdfs.append(path)

        with open(path, 'wb') as f:
            writer.write(f)

    # Process each page with OCR (in parallel)
    with ProcessPoolExecutor() as executor:
        tables = list(executor.map(process_page, pdfs))

    clear_folder('data/tmp-ocr')

    if tables[0][0][0] != 'Ora' and tables[0][0][1] != 'Classe':
        return False

    final_table = []
    for table in tables:
        rows = max(table.keys()) + 1
        cols = max(max(row.keys()) for row in table.values()) + 1
        matrix = [[table[i][j] if j in table[i] else None for j in range(cols)] for i in range(rows)]
        final_table.extend(matrix)

    # Remove repeated headers keeping the first one
    final_table = [final_table[0]] + [row for row in final_table[1:] if row[0] != 'Ora']

    # Replace first row (headers)
    final_table[0] = ['Ora', 'Classe', 'Aula', 'Doc.Assente', 'Sost.1', 'Sost.2', 'Pag.', 'Note', 'Firma']

    write_rows_to_csv(output_path, final_table, 'utf-8')

    if delete_original:
        os.remove(pdf_path)

    return True

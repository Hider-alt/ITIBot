import os
import re

from src.utils.pdf_utils import get_rows_from_pdf, write_rows_to_csv
from src.utils.utils import to_thread


@to_thread
def pdf_to_csv(pdf_path: str, output_path: str, delete_original=True):
    """
    It takes a PDF file, converts it to a CSV file, and saves it to a given path

    :param pdf_path: The path to the PDF file you want to convert
    :param output_path: The path to the output file
    :param delete_original: If True, it deletes the original PDF file
    :return: True if the conversion was successful, False otherwise
    """

    rows = get_rows_from_pdf(pdf_path)

    firma_index = None
    for i, row in enumerate(rows):
        # First row handling
        if i == 0:
            # Headers
            # [['Ora Classe Doc.Assente Sost.1 Sost.2 Pagam. Note Firma', None, None, None, None, None, None, None] -> ['Ora', 'Classe', 'Doc.Assente', 'Sost.1', 'Sost.2', 'Pagam.', 'Note', 'Firma']
            rows[i] = rows[i][0].split(' ')

            # Remove 'Firma' element if it exists or "..." element if it exists
            if 'Firma' in rows[i]:
                firma_index = rows[i].index('Firma')
                rows[i].remove('Firma')
            elif '...' in rows[i]:
                rows[i].remove('...')

            # Remove all None elements
            rows[i] = [x for x in rows[i] if x]

            # Check that necessary headers are present
            if not {'Ora', 'Classe', 'Doc.Assente', 'Sost.1', 'Sost.2', 'Note'}.issubset(set(rows[i])):
                return False

            rows[i].insert(2, 'Aula')

            continue

        # Empty row
        if len(row) == 0:
            continue

        # Repeating header
        if row[0] == 'Ora' or row[1] is None or row[1] == '':
            rows[i] = []
            continue

        # Remove the row and the next one (if it exists)
        if 'ISS "Pascal Comandini" - Cesena' in row[0]:
            rows[i] = []
            if i + 1 < len(rows):
                rows[i + 1] = []
            continue

        # Remove 'Firma' element
        if firma_index is not None:
            row.pop(firma_index)

        # Split second element in 2nd and 3rd element (e.g. '3A(LT)' -> '3A', 'LT'; '5I\n(PALESTRAPASCAL)' -> '5I', 'PALESTRAPASCAL')
        text = str(row[1])  # Copy the string

        rows[i][1] = text.split('\n')[0].split('(')[0]

        classroom = re.findall(r'\((.*?)\)', text)
        classroom = classroom[0] if len(classroom) > 0 else ''
        rows[i].insert(2, classroom)

        # Fix prof's names
        rows[i][3] = rows[i][3].replace('_', ' ')

    rows = [row for row in rows if len(row) != 0]

    write_rows_to_csv(output_path, rows, 'ISO-8859-1')

    if delete_original:
        os.remove(pdf_path)

    return True

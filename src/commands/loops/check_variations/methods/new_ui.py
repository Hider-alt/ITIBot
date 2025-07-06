import os

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

    rows = get_rows_from_pdf(pdf_path, table_settings={'text_x_tolerance': 1})

    firma_index = None
    for i, row in enumerate(rows):
        # First row handling
        if i == 0:
            # Headers
            rows[i] = [x.replace('Docente assente', 'Doc.Assente')
                        .replace('Sostituto 1', 'Sost.1')
                        .replace('Sostituto 2', 'Sost.2') for x in rows[i]]

            # Remove 'Firma' element if it exists
            if 'Firma' in rows[i]:
                firma_index = rows[i].index('Firma')
                rows[i].remove('Firma')

            # Check that necessary headers are present
            if not {'Ora', 'Classe', 'Doc.Assente', 'Sost.1', 'Sost.2', 'Note'}.issubset(set(rows[i])):
                return False

            continue

        # Repeating header
        if row[0] == 'Ora' or row[1] is None or row[1] == '':
            rows[i] = []
            continue

        # Remove 'Firma' element
        if firma_index is not None:
            row.pop(firma_index)

        # Ora
        rows[i][0] = int(rows[i][0])

        # Fix nomi prof
        rows[i][3] = rows[i][3].split('-')[0].replace('_', ' ')
        rows[i][4] = rows[i][4].split('-')[0].replace('_', ' ')
        rows[i][5] = rows[i][5].split('-')[0].replace('_', ' ')

        rows[i][3] = '-' if rows[i][3] == '' else rows[i][3]
        rows[i][4] = '-' if rows[i][4] == '' else rows[i][4]
        rows[i][5] = '-' if rows[i][5] == '' else rows[i][5]

        # Fix Note
        rows[i][7] = rows[i][7].replace('\n', ' ')

    rows = [row for row in rows if len(row) != 0]

    write_rows_to_csv(output_path, rows, 'ISO-8859-1')

    if delete_original:
        os.remove(pdf_path)

    return True

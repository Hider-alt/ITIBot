from enum import Enum

from src.api.iti.variations_parsers._parser_ import PDFParser
from src.models.variation import Variation
from src.utils.pdf_utils import get_rows_from_pdf_table
from src.utils.utils import to_thread


class NewUIParser(PDFParser):
    class _Columns(Enum):
        """
        Enum-like class to represent the columns in the variations table.
        """
        HOUR = 0
        CLASS = 1
        CLASSROOM = 2
        TEACHER = 3
        SUBSTITUTE_1 = 4
        SUBSTITUTE_2 = 5
        NOTES = 7

    def __init__(self):
        super().__init__()
        self._required_headers = {'Ora', 'Classe', 'Docente assente', 'Sostituto 1', 'Sostituto 2', 'Note'}

    @to_thread
    def _parse(self, pdf: bytes) -> list[Variation] | None:
        """
        Parses the PDF content and returns a list of variations.

        :param pdf: The PDF content as bytes.
        :return: A list of Variation objects or None if parsing fails.
        """

        table_rows = get_rows_from_pdf_table(pdf, table_settings={'text_x_tolerance': 1})
        if not table_rows:
            return None

        valid = self._is_parser_valid(table_rows[0])
        if not valid:
            # Try with 2nd row as header
            valid = self._is_parser_valid(table_rows[1])
            if valid:
                table_rows = table_rows[1:]
            else:
                return None

        variations = []
        signature_idx = self._get_signature_index(table_rows[0])

        for row in table_rows[1:]:
            variation = self._parse_row(row, signature_idx)
            if variation:
                variations.append(variation)

        return variations

    def _is_parser_valid(self, header_row: list[str]) -> bool:
        """
        Checks if the parsing method is valid by verifying the presence of required headers (case-insensitive).

        :param header_row: The first row of the table, which contains headers.
        :return: True if the method is valid, False otherwise.
        """

        header_set = {header.strip().lower() for header in header_row if header}
        required_set = {req_header.strip().lower() for req_header in self._required_headers}

        return required_set.issubset(header_set)

    @staticmethod
    def _get_signature_index(header_row: list[str]) -> int | None:
        """
        Finds the index of the 'Firma' column in the header row.

        :param header_row: The first row of the table, which contains headers.
        :return: The index of the 'Firma' column or None if not found.
        """
        try:
            return header_row.index('Firma')
        except ValueError:
            return None

    def _parse_row(self, row: list[str], signature_idx: int | None = None) -> Variation | None:
        """
        Parses a single row of the table into a Variation object.

        :param row: A list representing a row in the table.
        :param signature_idx: The index of the 'Firma' column, if it exists.
        :return: A Variation object or None if the row is invalid.
        """

        def fix_teacher_name(name: str) -> str:
            fixed = name.split('-')[0].replace('_', ' ').strip()

            return fixed if fixed else '-'

        # If first element is 'Ora' or the second element is empty, skip the row (repeating header or empty row)
        if row[self._Columns.HOUR.value].lower() == 'ora' or not row[self._Columns.CLASSROOM.value]:
            return None

        # Remove the 'Firma' element if it exists
        if signature_idx is not None:
            row.pop(signature_idx)

        # Convert hour to integer
        try:
            hour = int(row[self._Columns.HOUR.value])
        except ValueError:
            return None

        # Fix teacher names
        teacher = fix_teacher_name(row[self._Columns.TEACHER.value])
        substitute_1 = fix_teacher_name(row[self._Columns.SUBSTITUTE_1.value])
        substitute_2 = fix_teacher_name(row[self._Columns.SUBSTITUTE_2.value] if getattr(self._Columns, 'SUBSTITUTE_2', None) else '-')

        # Fix notes
        notes = row[self._Columns.NOTES.value].replace('\n', ' ').strip()
        if not notes:
            notes = None

        return Variation(
            hour=hour,
            class_name=row[self._Columns.CLASS.value],
            classroom=row[self._Columns.CLASSROOM.value],
            teacher=teacher,
            substitute_1=substitute_1,
            substitute_2=substitute_2,
            notes=notes
        )

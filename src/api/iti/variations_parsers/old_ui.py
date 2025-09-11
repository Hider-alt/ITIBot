import re
from enum import Enum

from src.api.iti.variations_parsers._parser_ import PDFParser
from src.models.variation import Variation
from src.utils.pdf_utils import get_rows_from_pdf_table
from src.utils.utils import to_thread


class OldUIParser(PDFParser):
    def __init__(self):
        super().__init__()
        self._required_headers = {'Ora', 'Classe', 'Doc.Assente', 'Sost.1', 'Sost.2', 'Note'}

    class __Columns(Enum):
        """
        Enum-like class to represent the columns in the variations table.
        """
        HOUR = 0
        CLASS = 1
        TEACHER = 2
        SUBSTITUTE_1 = 3
        SUBSTITUTE_2 = 4
        NOTES = 6

    @to_thread
    def _parse(self, pdf: bytes) -> list[Variation] | None:
        """
        Parses the PDF content and returns a list of variations.

        :param pdf: The PDF content as bytes.
        :return: A list of Variation objects or None if parsing fails.
        """

        table_rows = get_rows_from_pdf_table(pdf)
        if not table_rows:
            return None

        header = table_rows[0][0].split(' ')

        valid = self._is_parser_valid(header)
        if not valid:
            return None

        variations = []
        signature_idx = self._get_signature_index(header)

        for row in table_rows[1:]:
            variation = self._parse_row(row, signature_idx)
            if variation:
                variations.append(variation)

        return variations

    def _is_parser_valid(self, header_row: list[str]) -> bool:
        """
        Checks if the parsing method is valid by verifying the presence of required headers.

        :param header_row: The first row of the table, which contains headers.
        :return: True if the method is valid, False otherwise.
        """

        return self._required_headers.issubset(set(header_row))

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
        Parses a single row of the table and returns a Variation object.

        :param row: A list representing a row in the table.
        :param signature_idx: The index of the 'Firma' column, if it exists.
        :return: A Variation object or None if the row is invalid.
        """

        def get_class_and_classroom(class_info: str) -> tuple[str, str]:
            """
            Splits the class information into class name and classroom.

            :param class_info: A string containing class name and classroom, e.g. '3A(LT)' -> '3A', 'LT'; '5I\n(PALESTRAPASCAL)' -> '5I', 'PALESTRAPASCAL'
            :return: A tuple containing class name and classroom.
            """
            pattern = r'([1-5][A-Z]+)\s*\(?([A-Z0-9]+)\)?'
            class_info = class_info.replace('\n', '')

            match = re.match(pattern, class_info)

            return match.group(1), match.group(2)

        def fix_teacher_name(name: str) -> str:
            """
            Fixes the teacher name by removing any suffix after a hyphen and replacing underscores with spaces.
            """
            fixed = name.replace('_', ' ').strip()

            return fixed if fixed else '-'

        # Check if the row is empty
        if not row:
            return None

        # Remove 'Firma' element if it exists
        if signature_idx is not None:
            row.pop(signature_idx)

        # Check repeating header
        if row[self.__Columns.HOUR.value] == 'Ora' or not row[self.__Columns.CLASS.value]:
            return None

        # Convert hour to integer
        try:
            hour = int(row[self.__Columns.HOUR.value])
        except ValueError:
            return None

        # Extract class name and classroom
        try:
            class_name, classroom = get_class_and_classroom(row[self.__Columns.CLASS.value])
        except ValueError:
            return None

        # Create a Variation object from the row assets
        return Variation(
            hour=hour,
            class_name=class_name,
            classroom=classroom,
            teacher=fix_teacher_name(row[self.__Columns.TEACHER.value]),
            substitute_1=fix_teacher_name(row[self.__Columns.SUBSTITUTE_1.value]),
            substitute_2=fix_teacher_name(row[self.__Columns.SUBSTITUTE_2.value]),
            notes=row[self.__Columns.NOTES.value]
        )

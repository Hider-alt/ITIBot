from enum import Enum

from src.api.iti.variations_parsers.new_ui import NewUIParser


class ExcelUIParser(NewUIParser):
    class _Columns(Enum):
        """
        Enum-like class to represent the columns in the variations table.
        """
        HOUR = 0
        CLASS = 1
        CLASSROOM = 2
        TEACHER = 3
        SUBSTITUTE_1 = 4
        NOTES = 5

    def __init__(self):
        super().__init__()
        self._required_headers = {'Ora', 'Classe', 'Aula', 'Docente assente', 'Docente sostituto', 'Note'}

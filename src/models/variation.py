from datetime import datetime
from typing import Literal


class Variation:
    def __init__(self, hour: int, class_name: str, classroom: str, teacher: str, substitute_1: str = None, substitute_2: str = None,
                 notes: str = None, date: datetime = None, ocr: bool = False,
                 var_type: Literal['new', 'removed', 'edited'] | None = None, edited_fields: list[str] = None):
        self.hour = hour
        self.class_name = class_name
        self.classroom = classroom
        self.teacher = teacher
        self.substitute_1 = substitute_1
        self.substitute_2 = substitute_2
        self.notes = notes
        self.date = date
        self.ocr = ocr
        self.type: Literal["new", "removed", "edited"] | None = var_type
        self.edited_fields: list[str] = edited_fields if edited_fields is not None else []

    def set_date(self, date: datetime):
        """
        Sets the date for the variation.

        :param date: The date to set.
        """
        self.date = date

    def set_var_type(self, var_type: Literal['new', 'removed', 'edited']):
        """
        Sets the type of variation.

        :param var_type: The type of variation ('new', 'removed', 'edited').
        """
        self.type = var_type

    def add_edited_fields(self, *fields: str):
        """
        Adds one or more fields to the list of edited fields.

        :param fields: The fields that were edited.
        """
        self.edited_fields.extend(fields)

    def __str__(self):
        """
        Returns a string representation of the variation.

        :return: A string containing the hour, classroom, teacher, substitutes, notes, and date.
        """

        return f"Hour: {self.hour} \n" \
               f"Class: {self.class_name} \n" \
               f"Classroom: {self.classroom} \n" \
               f"Teacher: {self.teacher} \n" \
               f"Substitute 1: {self.substitute_1} \n" \
               f"Substitute 2: {self.substitute_2} \n" \
               f"Notes: {self.notes} \n" \
               f"Date: {self.date.strftime('%d/%m/%Y') if self.date else 'N/A'} \n" \
               f"OCR: {self.ocr} \n" \
               f"Var Type: {self.type}"

    def __repr__(self):
        """
        Returns a string representation of the variation for debugging.

        :return: A string containing the class name and the hour.
        """
        return f"<Variation hour={self.hour} class={self.class_name} classroom={self.classroom} teacher={self.teacher}>"

    def to_dict(self):
        """
        Returns a dictionary representation of the variation.

        :return: A dictionary containing the hour, classroom, teacher, substitutes, and notes.
        """

        return {
            "teacher": self.teacher,
            "hour": self.hour,
            "class": self.class_name,
            "classroom": self.classroom,
            "substitute_1": self.substitute_1,
            "substitute_2": self.substitute_2,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, data: dict, date: datetime = None) -> "Variation":
        """
        Creates a Variation object from a dictionary.

        :param data: A dictionary containing the hour, classroom, teacher, substitutes, and notes.
        :param date: The date of the variation.
        :return: A Variation object.
        """

        return Variation(
            hour=data.get("hour"),
            class_name=data.get("class"),
            classroom=data.get("classroom"),
            teacher=data.get("teacher"),
            substitute_1=data.get("substitute_1"),
            substitute_2=data.get("substitute_2"),
            notes=data.get("notes"),
            date=date
        )

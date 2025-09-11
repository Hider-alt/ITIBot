from datetime import datetime, date

from src.models.variation import Variation
from src.mongo_db.variations_db import VariationsDB


async def classify_variations(bot, variations: list[Variation]) -> None:
    """
    Set field `var_type` for each variation, adds removed variations to the list and removes unchanged variations.

    :param bot: The bot instance.
    :param variations: List of variations to classify.
    :return: None, the variations are modified in place (adding the `var_type` field) and deleted variations are added
             to the list.
    """

    if not variations:
        return

    variations_dates = get_variations_dates(variations)
    variations_db = VariationsDB(bot.mongo_client, bot.school_year)

    existing_variations = await variations_db.get_variations_by_date(*variations_dates)

    # Check for new or edited variations
    for new_variation in variations:
        existing_variation = find_variation(existing_variations, new_variation.teacher, new_variation.class_name, new_variation.date, new_variation.hour)

        # If no existing variation is found, it's a new variation
        if existing_variation is None:
            new_variation.set_var_type('new')

        else:
            # Check if it's an edited variation or unchanged
            edited_fields = get_edited_fields(existing_variation, new_variation)

            if edited_fields:
                new_variation.set_var_type('edited')
                new_variation.add_edited_fields(*edited_fields)

    # Add removed variations to the list (variations that are in the database but not in the new list)
    for existing_variation in existing_variations:
        new_variation = find_variation(variations, existing_variation.teacher, existing_variation.class_name, existing_variation.date, existing_variation.hour)

        if new_variation is None:
            existing_variation.set_var_type('removed')
            variations.append(existing_variation)

    # Remove variations with no var_type (unchanged)
    variations[:] = [var for var in variations if var.type is not None]


def get_variations_dates(variations: list[Variation]) -> set[date]:
    """
    Extracts unique dates from the variations.
    :param variations: List of variations.
    :return: Set of unique dates in 'dd-mm-yyyy' format.
    """
    return {variation.date.date() for variation in variations if variation.date}


def find_variation(variations: list[Variation], teacher: str, class_name: str, date: datetime, hour: int) -> Variation | None:
    """
    Finds a variation in the list by class name, date, and hour.

    :param variations: List of variations to search.
    :param teacher: Teacher name to match.
    :param class_name: Class name to match.
    :param date: Date to match (only day, month, year are considered).
    :param hour: Hour to match.
    :return: The matching variation or None if not found.
    """

    for variation in variations:
        if variation.teacher == teacher and variation.class_name == class_name and variation.date.date() == date.date() and variation.hour == hour:
            return variation

    return None


def get_edited_fields(old_variation: Variation, new_variation: Variation) -> list[str]:
    """
    Compares two variations and returns a list of fields that have been edited.
    :param old_variation: The existing variation from the database.
    :param new_variation: The new variation to compare.
    :return: List of field names that have been edited.
    """

    fields = ['classroom', 'substitute_1', 'substitute_2', 'notes']
    edited_fields = []

    for field in fields:
        if getattr(old_variation, field) != getattr(new_variation, field):
            edited_fields.append(field)

    return edited_fields

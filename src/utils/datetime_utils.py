from datetime import datetime


months = [
    "gennaio",
    "febbraio",
    "marzo",
    "aprile",
    "maggio",
    "giugno",
    "luglio",
    "agosto",
    "settembre",
    "ottobre",
    "novembre",
    "dicembre",
]


def parse_italian_date(date: str) -> datetime:
    """
    It parses a string with a date in italian with the format `[day]-[month]`

    :param date: The string containing the date in italian
    :returns: The date in datetime format
    """

    now = datetime.now()

    # Get day, month and year
    day, month_str = date.split('-')

    # Get month
    try:
        month = months.index(month_str.lower()) + 1
    except ValueError:
        month = now.month

    # Create datetime object
    date = datetime(year=now.year, month=month, day=int(day))

    return date


def is_christmas(date: datetime) -> bool:
    """
    It checks if the date is in the Christmas period (from 24/12 to 06/01)

    :param date: The date to check
    :returns: True if the date is in the Christmas period, False otherwise
    """
    year = date.year

    christmas_start = datetime(year, 12, 24, tzinfo=date.tzinfo)
    christmas_end = datetime(year + 1, 1, 6, tzinfo=date.tzinfo)

    return christmas_start <= date <= christmas_end


def is_school_over(date: datetime) -> bool:
    """
    It checks if the date is in the summer period (from 06/06 to 15/09)

    :param date: The date to check
    :returns: True if the date is in the summer period, False otherwise
    """
    year = date.year

    summer_start = datetime(year, 6, 6, tzinfo=date.tzinfo)
    summer_end = datetime(year, 9, 15, tzinfo=date.tzinfo)

    return summer_start <= date <= summer_end

import datetime


def parse_italian_date(date: str) -> datetime:
    """
    It parses a string with a date in italian with the format `[weekday]-[day]-[month]-[year]`

    :param date: The string containing the date in italian
    :returns: The date in datetime format
    """
    # Get day, month and year
    weekday, day, month, year = date.split('-')

    # Get month
    month = {
        'gennaio': 1,
        'febbraio': 2,
        'marzo': 3,
        'aprile': 4,
        'maggio': 5,
        'giugno': 6,
        'luglio': 7,
        'agosto': 8,
        'settembre': 9,
        'ottobre': 10,
        'novembre': 11,
        'dicembre': 12,
    }[month]

    # Create datetime object
    date = datetime.datetime(int(year), month, int(day))

    return date


def is_before_tomorrow(date: datetime) -> bool:
    """
    It checks if the date is before tomorrow.

    :param date: The date to check
    :return: True if the date is before tomorrow, False otherwise
    """

    return date < datetime.datetime.now() + datetime.timedelta(days=1)
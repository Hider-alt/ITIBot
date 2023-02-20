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

    # Get year
    year = int(year)

    # Get day
    day = int(day)

    # Create datetime object
    date = datetime.datetime(year, month, day)

    return date


def is_tomorrow(date: datetime) -> bool:
    """
    It checks if the date is tomorrow

    :param date: The date to check
    :returns: True if the date is tomorrow, False otherwise
    """
    return date.day == (datetime.datetime.now().day + 1)

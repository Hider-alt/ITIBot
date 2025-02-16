import datetime


def parse_italian_date(date: str) -> datetime:
    """
    It parses a string with a date in italian with the format `[day]-[month]`

    :param date: The string containing the date in italian
    :returns: The date in datetime format
    """
    # Get day, month and year
    day, month = date.split('-')

    # Tomorrow
    tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)

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
    }.get(month, tomorrow.month)

    # Create datetime object
    date = datetime.datetime(year=datetime.datetime.now().year, month=month, day=int(day))

    return date

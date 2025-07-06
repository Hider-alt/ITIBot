import datetime


months: dict = {
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
}


def parse_italian_date(date: str) -> datetime:
    """
    It parses a string with a date in italian with the format `[day]-[month]`

    :param date: The string containing the date in italian
    :returns: The date in datetime format
    """

    # Get day, month and year
    day, month_str = date.split('-')

    # Tomorrow (to get default month if not specified)
    tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)

    # Get month
    month = months.get(month_str, tomorrow.month)

    # Create datetime object
    date = datetime.datetime(year=datetime.datetime.now().year, month=month, day=int(day))

    return date


def is_christmas(date: datetime) -> bool:
    """
    It checks if the date is in the christmas period (from 24/12 to 06/01)

    :param date: The date to check
    :returns: True if the date is in the christmas period, False otherwise
    """
    year = date.year

    christmas_start = datetime.datetime(year, 12, 24, tzinfo=date.tzinfo)
    christmas_end = datetime.datetime(year + 1, 1, 6, tzinfo=date.tzinfo)

    return christmas_start <= date <= christmas_end


def is_summer(date: datetime) -> bool:
    """
    It checks if the date is in the summer period (from 10/06 to 10/09)

    :param date: The date to check
    :returns: True if the date is in the summer period, False otherwise
    """
    year = date.year

    summer_start = datetime.datetime(year, 6, 10, tzinfo=date.tzinfo)
    summer_end = datetime.datetime(year, 9, 10, tzinfo=date.tzinfo)

    return summer_start <= date <= summer_end

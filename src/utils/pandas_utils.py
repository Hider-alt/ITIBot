import pandas as pd

from src.utils.utils import to_thread


@to_thread
def read_csv(csv_path: str):
    """
    It reads a CSV file and returns a pandas DataFrame

    :param csv_path: The path to the CSV file
    :return: A pandas DataFrame
    """
    return pd.read_csv(csv_path, converters={i: str for i in range(0, 7)}, encoding='ISO-8859-1')

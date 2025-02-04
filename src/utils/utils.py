import asyncio
import functools
import os
import shutil
import typing
from collections import defaultdict

import pandas as pd


def default_nested_dict():
    return defaultdict(str)


def to_thread(func: typing.Callable):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)
    return wrapper


def clear_folder(folder: str) -> None:
    """
    It removes all files/folders in a given folder

    :param folder: the folder to clear
    """

    for file in os.listdir(folder):
        if file == '.gitkeep':
            continue

        path = os.path.join(folder, file)
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)


@to_thread
def read_csv_pandas(csv_path):
    """
    It reads a CSV file and returns a pandas DataFrame

    :param csv_path: The path to the CSV file
    :return: A pandas DataFrame
    """
    return pd.read_csv(csv_path, converters={i: str for i in range(0, 7)}, encoding='ISO-8859-1')

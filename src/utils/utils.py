import asyncio
import functools
import os
import shutil
import typing


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

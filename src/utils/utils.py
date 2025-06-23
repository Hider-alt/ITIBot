import asyncio
import functools
import typing
from collections import defaultdict


def default_nested_dict():
    return defaultdict(str)


def to_thread(func: typing.Callable):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)
    return wrapper

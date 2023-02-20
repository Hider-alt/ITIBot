import os
import shutil


def clear_folder(folder: str) -> None:
    """
    It removes all files in a given folder

    :param folder: the folder where the images are stored
    """
    for f in os.listdir(folder):
        if os.path.isdir(folder + f):
            shutil.rmtree(folder + f)
        else:
            os.remove(folder + f)

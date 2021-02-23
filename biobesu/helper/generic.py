#!/user/bin/env python3

from time import sleep
from os import makedirs
import pkg_resources


def wait(time, elapsed=0, check_frequency=1):
    """
    Sleeps until defined time has elapsed.
    :param time: the time that should be elapsed
    :param elapsed: the currently elapsed time (default: 0)
    :param check_frequency: the time between checks whether elapsed has passed waitTime (default: 1)
    :return:
    """

    while elapsed < time:
        sleep(check_frequency)
        elapsed += check_frequency


def retrieve_entry_point(name):
    """
    Retrieve a collection of entry points.
    :param name: the entry point that should be retrieved
    :return: a dictionary containing the key-value pairs belonging to the defined entry point
    :rtype: dict
    """

    collection = {}
    for entry_point in pkg_resources.iter_entry_points(name):
        collection[entry_point.name] = entry_point.load()

    return collection


def create_dir(dir_path, exist_allowed=False):
    makedirs(dir_path, exist_ok=exist_allowed)
    return dir_path

"""
Custom time utilities
"""

import time
from datetime import datetime, timezone, timedelta
from functools import cache


def get_current_epoch_time() -> timedelta:
    """
    Calcuate the current time in seconds relative to 1 January 1970

    :return: A timedelta object
    """
    epoch_start = datetime.fromtimestamp(0, timezone.utc)
    current_time = datetime.now(tz=timezone.utc) - epoch_start
    return current_time


def get_current_epoch_time_seconds() -> float:
    """
    Calcuate the current time in seconds relative to 1 January 1970

    :return: The time in seconds
    """
    return get_current_epoch_time().total_seconds()


@cache
def get_server_start_time() -> timedelta:
    """
    Gets the server start time relative to 1 January 1970

    :return: A timedelta object
    """
    current_time = get_current_epoch_time()
    running_time = timedelta(seconds=time.process_time())

    return current_time - running_time


def get_server_start_time_seconds() -> float:
    """
    Gets the server start time relative to 1 January 1970

    :return: The time in seconds
    """
    return get_server_start_time().total_seconds()


@cache
def get_server_start_time_monotonic() -> timedelta:
    """
    Gets the monotonic server start time

    :return: A timedelta object
    """
    current_time = timedelta(seconds=time.monotonic())
    running_time = timedelta(seconds=time.process_time())

    return current_time - running_time


def get_server_start_time_monotonic_seconds() -> float:
    """
    Gets the server start time relative to 1 January 1970

    :return: The time in seconds
    """
    return get_server_start_time_monotonic().total_seconds()


@cache
def mtonic_to_epoch_millis_offset() -> float:
    """
    Get the current offest of the system time compared to
    the system's monotonic time. The returned value is in
    terms of milliseconds

    :return: The offset value
    """
    offset_sec = get_server_start_time() - get_server_start_time_monotonic()
    return offset_sec.total_seconds() * 1000


def epoch_millis_to_monotonic(milliseconds: float) -> float:
    """
    Convert number of milliseconds in epoch time to monotonic time.

    :param milliseconds: Milliseconds in epoch time
    :return: The converted time in seconds
    """
    corrected_mills = milliseconds - mtonic_to_epoch_millis_offset()
    return corrected_mills / 1000


def datetime_formatted_string(datetime_: datetime) -> str:
    """
    Converts a datetime object into a formatted string

    :param time: The datetime object to convet
    :return: A formatted string
    """
    return datetime_.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def epoch_ms_formatted_string(milliseconds: float) -> str:
    """
    Convert milliseconds since epoch time to a formatted string

    :param milliseconds: Milliseconds since epoch start time
    :return: A formatted string
    """
    return datetime_formatted_string(datetime.fromtimestamp(milliseconds / 1000.0))

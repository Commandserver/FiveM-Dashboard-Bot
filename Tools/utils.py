from enum import unique, IntEnum


@unique
class ServerState(IntEnum):
    """Server states enum"""
    UNKNOWN = 1
    ONLINE = 2
    RESTARTING = 3
    OFFLINE = 4
    NOT_REACHABLE = 5
    ERROR = 6


@unique
class Intervals(IntEnum):
    """The seconds of each day/hour/minute"""

    DAY = 86400
    """How many seconds one day has"""
    HOUR = 3600
    """How many seconds one hour has"""
    MINUTE = 60
    """How many seconds one minute has"""


def create_time_from_seconds(seconds: int) -> str:
    """Creates a formatted and translated time string from an amount of seconds

    :param seconds: The seconds
    :type seconds: int
    :return: An formatted time string
    :rtype: str
    """
    days = int(seconds / Intervals.DAY)
    hours = int((seconds - (Intervals.DAY * days)) / Intervals.HOUR)
    minutes = int((seconds - ((Intervals.DAY * days) + (Intervals.HOUR * hours))) / Intervals.MINUTE)
    time_list = []
    if days == 1:
        time_list.append(f"1 Tag")
    elif days > 1:
        time_list.append(f"{days} Tage")
    if hours == 1:
        time_list.append(f"1 Stunde")
    elif hours > 1:
        time_list.append(f"{hours} Stunden")
    if minutes == 1:
        time_list.append(f"1 Minute")
    elif minutes > 1:
        time_list.append(f"{minutes} Minuten")
    delimiter = ", "
    return delimiter.join(time_list)

from enum import Enum


class State(Enum):
    ONLINE = 1
    OFFLINE = 2
    RESTARTING = 3
    NOT_REACHABLE = 4

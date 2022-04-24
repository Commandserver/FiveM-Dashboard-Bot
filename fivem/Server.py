from enum import Enum
from time import time

import requests

from .State import State


class Server:
    """The FiveM Server which you want to handle with"""

    def __init__(self, **kwargs):
        self.players: int = 0
        """The amount of players on the FiveM server"""
        self.last_offline: int = 0
        """The Uptime. The last time when the server was offline as a timestamp"""
        self.last_online: int = 0
        """The Downtime. The last time when the server was online as a timestamp"""
        self.next_restart: int = 0
        """The timestamp when the next restart is"""
        self._is_offline_twice: bool = False
        """When this Bot has connection problems or something goes wrong on requesting the FiveM server once,
        the uptime should not be reset. It should only reset the uptime when the FiveM server seems to be offline twice.
        Therefore is this indicator to check if the server was offline twice, then reset the uptime."""
        self._state: Enum = State.OFFLINE
        """The last server state of the FiveM server"""
        self._ip: str = kwargs.get("ip")
        """The IP (with port) of the server to handle with"""

    def request_state(self):
        """Requests the Status from the FiveM server and assign it to the object attributes"""
        # noinspection PyBroadException
        try:
            r = requests.get("http://" + self._ip + "/players.json", timeout=3)
            self.players = len(r.json())
        except (requests.exceptions.Timeout, requests.exceptions.URLRequired, requests.exceptions.InvalidURL):
            self.set_state_not_reachable()
        except:
            self.set_state_offline()
        else:
            self.set_state_online()

    def get_downtime_seconds(self) -> int:
        """Get the downtime of the FiveM server in seconds"""
        if self.last_online > 0:
            return int(time()) - self.last_online
        else:
            return 0

    def get_uptime_seconds(self) -> int:
        """Get the uptime of the FiveM server in seconds"""
        if self.last_offline > 0:
            return int(time()) - self.last_offline
        else:
            return 0

    def set_state_online(self):
        """Normally the state is set by :func:`fivem.Server.request_state`"""
        if not self._is_restart_schedule():  # set only if its currently no restart schedule
            self._state = State.ONLINE
            self._is_offline_twice = False
            self.last_online = int(time())

    def set_state_restarting(self):
        self._state = State.RESTARTING
        self._is_offline_twice = False
        self.last_online = int(time())
        self.last_offline = int(time())

    def set_state_offline(self):
        if not self._is_restart_schedule():  # set only if its currently no restart schedule
            self._state = State.OFFLINE
            if self._is_offline_twice:  # do not reset uptime on the first time when the server if offline
                self.last_offline = int(time())
            self._is_offline_twice = True

    def set_state_not_reachable(self):
        if not self._is_restart_schedule():  # set only if its currently no restart schedule
            self._state = State.NOT_REACHABLE
            if self._is_offline_twice:  # do not reset uptime on the first time when the server if offline
                self.last_offline = int(time())
            self._is_offline_twice = True

    def is_online(self) -> bool:
        """Check whether the server's state is online or not"""
        return self._state == State.ONLINE

    def is_restarting(self) -> bool:
        """Check whether the server's state is restarting or not"""
        return self._state == State.RESTARTING

    def is_offline(self) -> bool:
        """Check whether the server's state is offline or not"""
        return self._state == State.OFFLINE

    def is_not_reachable(self) -> bool:
        """Check whether the server's state is not reachable or not.
        The server is unreachable when the status request to the server timed out"""
        return self._state == State.NOT_REACHABLE

    def _is_restart_schedule(self) -> bool:
        """Says whether the server is currently restarting from the next_restart-timestamp point of view.

        :return: Whether the next_restart timestamp is in the last 10 seconds and the state is set to restarting
        :rtype: bool
        """
        return self.next_restart < int(time()) < self.next_restart + 16 and self.is_restarting()

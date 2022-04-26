import asyncio
import os
from datetime import datetime, timedelta
from typing import Optional

import aiodns
import aiohttp
import mariadb

from Tools.utils import ServerState


class StatusZone:
    """The represents the status-message configuration stored in the database"""

    def __init__(self, zone_id: int, cursor: mariadb):
        """
        :param zone_id: The unique identifier of the StatusZone
        :param cursor: The database cursor object
        """
        self.__cursor: mariadb = cursor
        """The cursor of the database"""
        self.__id: int = zone_id
        """The unique Database-Identifier"""

        self.__max_players: int = 64
        """the maximum players of the FiveM server. This will be displayed in the status message"""
        self.__custom_message: Optional[str] = None
        """A custom message which shows up in the description of the status message. Can be up to 1000 chars"""

        self.__next_restart_at: Optional[datetime] = None
        """The UTC-datetime when the next restart is"""

        self.__max_players_last_updated: Optional[datetime] = None
        """The UTC-datetime when the max players of the fivem server was last updated"""
        self.__status_message_id: Optional[int] = None
        """The ID of the status message to update it"""
        self.__last_status: int = 1
        """The last status of the fivem server"""
        self.__players: int = 0
        """The amount of players on the FiveM server"""
        self.__last_offline: Optional[datetime] = None
        """The UTC-datetime when the server was last offline. For the Uptime"""
        self.__last_online: Optional[datetime] = None
        """The UTC-datetime when the server was last online. For the Downtime"""
        self.__is_offline_twice: bool = False
        """When this Bot has connection problems or something goes wrong on requesting the FiveM server once, 
        the uptime should not be reset. It should only reset the uptime when the FiveM server seems to be 
        offline twice. Therefore is this indicator to check if the server was offline twice, then reset the uptime"""
        self.__skipped_message_edit: bool = False
        """Tells that the edition of the status message was skipped"""

    def __str__(self):
        return f"<StatusZone#{self.__id}>"

    @property
    def max_players(self) -> int:
        """the maximum players of the FiveM server"""
        return self.__max_players

    @max_players.setter
    def max_players(self, max_player_count: int):
        """Push the new max player count to the database"""
        self.__cursor.execute(
            "UPDATE StatusZone SET max_players = ?, max_players_last_updated = UTC_TIMESTAMP() WHERE id = ?",
            (max_player_count, self.__id,)
        )
        self.__max_players = max_player_count

    @property
    def custom_message(self):
        """A custom message which shows up in the description of the status message"""
        return self.__custom_message

    @custom_message.setter
    def custom_message(self, text: str):
        """A custom message which shows up in the description of the status message

        :param text: The text to set. It will be truncated to a maximum length of 1000 chars
        """
        self.__custom_message = (text[:1000]) if len(text) > 1000 else text

    @property
    def next_restart_at(self):
        """The UTC-datetime when the next restart is"""
        return self.__next_restart_at

    @next_restart_at.setter
    def next_restart_at(self, next_restart: datetime):
        """Push the new next restart datetime to the database"""
        self.__cursor.execute(
            "UPDATE StatusZone SET next_restart_at = ? WHERE id = ?",
            (next_restart, self.__id,)
        )
        self.__next_restart_at = next_restart

    @property
    def max_players_last_updated(self):
        """The UTC-datetime when the max players of the fivem server was last updated"""
        return self.__max_players_last_updated

    @property
    def status_message_id(self):
        return self.__status_message_id

    @status_message_id.setter
    def status_message_id(self, message_id: int):
        self.__cursor.execute(
            "UPDATE StatusZone SET status_message_id = ? WHERE id = ?",
            (message_id, self.__id,)
        )
        self.__status_message_id = message_id

    def get_status(self) -> ServerState:
        """Gets the last server state of the fivem server

        :returns: The last requested server state
        """
        return ServerState(self.__last_status)

    @property
    def players(self):
        """The current amount of players on the FiveM server"""
        return self.__players

    @property
    def skipped_message_edit(self):
        """Tells that the edition of the status message was skipped"""
        return self.__skipped_message_edit

    @skipped_message_edit.setter
    def skipped_message_edit(self, is_skipped: bool):
        """Tells that the edition of the status message was skipped"""
        self.__cursor.execute(
            "UPDATE StatusZone SET skipped_message_edit = ? WHERE id = ?",
            (is_skipped, self.__id,)
        )
        self.__skipped_message_edit = is_skipped

    def set_state_restarting(self):
        """Set the server-state manually to restarting"""
        self.__last_status = ServerState.RESTARTING
        self.__is_offline_twice = False
        self.__last_online = datetime.utcnow()
        self.__last_offline = datetime.utcnow()
        self.__cursor.execute(
            "UPDATE StatusZone SET last_status = ?, is_offline_twice = FALSE, \
            last_online = UTC_TIMESTAMP(), last_offline = UTC_TIMESTAMP() WHERE id = ?",
            (self.__last_status, self.__id,)
        )

    def __is_restart_schedule(self) -> bool:
        """Says whether the server is currently restarting from the next_restart_at-timestamp point of view.
        :return: Whether the next_restart timestamp is in the last 10 seconds and the state is set to restarting
        """
        # if next_restart_at is in the past and next_restart_at + 16 seconds is in the future
        return self.next_restart_at and self.get_status() == ServerState.RESTARTING and \
            self.next_restart_at - timedelta(seconds=6) < datetime.utcnow() < \
            self.next_restart_at + timedelta(seconds=16)

    async def request_server_state(self, session: aiohttp.ClientSession, log):
        """Requests the Status from a FiveM server and applies it. It can take up to 4 seconds to get the response
        :param session: The async client session for the request
        :param log: A logger module
        """
        if self.__is_restart_schedule():
            return
        # noinspection PyBroadException
        try:
            url: str = f"http://{os.environ.get('FIVEM_SERVER_IP')}/players.json"
            async with session.get(url, allow_redirects=False, timeout=4.0, ssl=False) as response:
                response.raise_for_status()
                resp = await response.json(encoding="UTF-8", content_type=None)
                players: int = len(resp)  # resp could be None and throw TypeError here
        except (TimeoutError, aiohttp.InvalidURL, asyncio.TimeoutError, aiodns.error.DNSError) as e:
            self.__last_status = ServerState.NOT_REACHABLE
            if self.__is_offline_twice:  # do not reset uptime on the first time when the server if offline
                self.__last_offline = datetime.utcnow()
                self.__cursor.execute(
                    "UPDATE StatusZone SET last_status = ?, last_offline = ? WHERE id = ?",
                    (self.__last_status, self.__last_offline, self.__id,)
                )
            else:
                self.__is_offline_twice = True
                self.__cursor.execute(
                    "UPDATE StatusZone SET last_status = ?, is_offline_twice = TRUE WHERE id = ?",
                    (self.__last_status, self.__id,)
                )
                if isinstance(e, aiohttp.InvalidURL):
                    log.error("Request to the fivem server timed out. Invalid Url")
                elif isinstance(e, aiodns.error.DNSError):
                    log.error("Request to the fivem server timed out. DNSError")
                else:
                    log.error("Request to the fivem server timed out")
        except TypeError:
            self.__last_status = ServerState.ERROR
            if self.__is_offline_twice:  # do not reset uptime on the first time when the server if offline
                self.__last_offline = datetime.utcnow()
                self.__cursor.execute(
                    "UPDATE StatusZone SET last_status = ?, last_offline = ? WHERE id = ?",
                    (self.__last_status, self.__last_offline, self.__id,)
                )
            else:
                self.__is_offline_twice = True
                self.__cursor.execute(
                    "UPDATE StatusZone SET last_status = ?, is_offline_twice = TRUE WHERE id = ?",
                    (self.__last_status, self.__id,)
                )
                log.error(f"Got empty response from the fivem server "
                          f"(HTTP code {response.status}) (Content {response.content})")
        except Exception as e:
            self.__last_status = ServerState.OFFLINE
            if self.__is_offline_twice:  # do not reset uptime on the first time when the server if offline
                self.__last_offline = datetime.utcnow()
                self.__cursor.execute(
                    "UPDATE StatusZone SET last_status = ?, last_offline = ? WHERE id = ?",
                    (self.__last_status, self.__last_offline, self.__id,)
                )
            else:
                self.__is_offline_twice = True
                self.__cursor.execute(
                    "UPDATE StatusZone SET last_status = ?, is_offline_twice = TRUE WHERE id = ?",
                    (self.__last_status, self.__id,)
                )
                if isinstance(e, aiohttp.ClientResponseError):
                    log.error(f"Client response error (HTTP code {response.status})")
                elif isinstance(e, ConnectionRefusedError):
                    log.error(f"Connection refused (HTTP code {response.status})")
                else:
                    log.error(f"{type(e).__name__}. Can't connect to the fivem server (HTTP code {response.status})")
        else:
            self.__last_status = ServerState.ONLINE
            self.__players = players
            self.__last_online = datetime.utcnow()
            self.__is_offline_twice = False
            self.__cursor.execute(
                "UPDATE StatusZone SET last_status = ?, players = ?, last_online = ?, is_offline_twice = FALSE \
                WHERE id = ?",
                (self.__last_status, self.__players, self.__last_online, self.__id,)
            )

    def get_downtime_seconds(self) -> int:
        """Get the downtime of the FiveM server in seconds

        :returns: The downtime in seconds of the fivem server
        """
        if self.__last_online and int(self.__last_online.timestamp()) > 0:
            return int(datetime.utcnow().timestamp()) - int(self.__last_online.timestamp())
        else:
            return 0

    def get_uptime_seconds(self) -> int:
        """Get the uptime of the FiveM server in seconds

        :returns: The downtime in seconds of the fivem server
        """
        if self.__last_offline and int(self.__last_offline.timestamp()) > 0:
            return int(datetime.utcnow().timestamp()) - int(self.__last_offline.timestamp())
        else:
            return 0

    @classmethod
    def fetch(cls, cursor: mariadb):
        """Get the record from the database

        :param cursor: The database cursor
        """
        cursor.execute(
            "SELECT id, max_players, custom_message, next_restart_at, max_players_last_updated, status_message_id, \
            last_status, players, last_offline, last_online, is_offline_twice, skipped_message_edit FROM StatusZone"
        )

        result = cursor.fetchone()
        if not result:  # if no record was found in the database
            # create a record if needed and fetch it again
            cursor.execute("INSERT INTO StatusZone VALUES ()")
            cursor.execute(
                "SELECT id, max_players, custom_message, next_restart_at, max_players_last_updated, status_message_id, \
                last_status, players, last_offline, last_online, is_offline_twice, skipped_message_edit FROM StatusZone"
            )
            result = cursor.fetchone()
        (zone_id, max_players, custom_message, next_restart_at, max_players_last_updated, status_message_id,
         last_status, players, last_offline, last_online, is_offline_twice, skipped_message_edit,) = result
        zone = cls(zone_id, cursor)
        zone.__max_players = max_players
        zone.__custom_message = custom_message
        zone.__next_restart_at = next_restart_at
        zone.__max_players_last_updated = max_players_last_updated
        zone.__status_message_id = status_message_id
        zone.__last_status = last_status
        zone.__players = players
        zone.__last_offline = last_offline
        zone.__last_online = last_online
        zone.__is_offline_twice = is_offline_twice
        zone.__skipped_message_edit = skipped_message_edit
        return zone

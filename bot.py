#!/usr/bin/python3
import asyncio
import configparser
import logging
import math
import os
import random
import sys
import traceback
from datetime import datetime
from time import time

import discord
import requests

import fivem

logging.basicConfig(
    filename=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'latest.log'),
    filemode="w",
    level=logging.INFO,
    format="%(asctime)s:%(levelname)s:%(message)s"
)
logging.info("Started with python version " + sys.version)
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.ini'))

STATUS_UPDATE_INTERVAL = int(config.get("Settings", "status-update-interval"))
STATUS_CHANNEL_ID = int(config.get("Settings", "status-channel-id"))
FIVEM_BOT_ID = int(config.get("Restart-Detection", "fivem-status-bot-id"))
RESTART_MESSAGE = str(config.get("Restart-Detection", "restart-detection-message"))
RESTART_WARN_MSG = str(config.get("Restart-Detection", "restart-warn-message"))
RESTART_WARN_DELAY = int(config.get("Restart-Detection", "restart-warn-delay"))
FIVEM_SERVER_IP = str(config.get("Settings", "fivem-server-ip"))
SERVER_DOMAIN = str(config.get("Status-Message", "fivem-domain"))
FIVEM_MAX_PLAYERS = str(config.get("Settings", "max-players"))

fiveMServer = fivem.Server(ip=FIVEM_SERVER_IP)


def get_timestamp() -> int:
    """
    Gets the current timestamp
    """
    return int(time())


def chunk_based_on_number(lst: list, chunk_numbers: int):
    """Split a list not based on the number of chunks you want to be created.
    Some elements may be None. So make sure to check the type of each element
    """
    n = math.ceil(len(lst) / chunk_numbers)

    for x in range(0, len(lst), n):
        each_chunk = lst[x: n + x]

        if len(each_chunk) < n:
            each_chunk = each_chunk + [None for _ in range(n - len(each_chunk))]
        yield each_chunk


def create_time_from_seconds(seconds: int) -> str:
    """Creates a formatted time string from an amount of seconds

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
        time_list.append("1 Tag")
    elif days > 1:
        time_list.append(str(days) + " Tage")
    if hours == 1:
        time_list.append("1 Stunde")
    elif hours > 1:
        time_list.append(str(hours) + " Stunden")
    if minutes == 1:
        time_list.append("1 Minute")
    elif minutes > 1:
        time_list.append(str(minutes) + " Minuten")
    delimiter = ", "
    return delimiter.join(time_list)


class Intervals:
    """
    The seconds of each day/hour/minute
    """
    DAY = 86400
    """How many seconds one day has"""
    HOUR = 3600
    """How many seconds one hour has"""
    MINUTE = 60
    """How many seconds one minute has"""


class Client(discord.Client):
    skipped_status_update: bool = False

    status_message: discord.Message = None
    """The status message to be updated"""
    status_channel = None
    """The GuildChannel or TextChannel in which the status message should be send in"""
    show_uptime: bool = True
    """Whether the uptime should be displayed"""
    cfx_status: str = ""
    """The status message from the official website of fivem"""
    down_detector_status: str = ""
    """The status message from down detector website"""
    show_cfx_status: bool = True
    """Whether the official cfx server status should be displayed in the status message"""
    show_down_detector_status: bool = True
    """Whether the down detector status should be displayed in the status message"""

    def __init__(self, *, loop=None, **options):
        super().__init__(loop=loop, **options)
        self.loop.create_task(self.update_status_loop())
        self.loop.create_task(self.update_fivem_status_loop())

    async def on_error(self, *args, **kwargs):
        logging.error(traceback.format_exc())

    async def on_ready(self):
        print("Logged in as " + str(self.user.name) + " (" + str(self.user.id) + ")")
        logging.info("Logged in as " + str(self.user.name) + " (" + str(self.user.id) + ")")
        self.status_channel = self.get_channel(STATUS_CHANNEL_ID)

    async def on_message(self, message):
        lower_message = message.content.lower()
        if message.author.bot and message.author.id == FIVEM_BOT_ID:
            if RESTART_MESSAGE.lower() in lower_message:
                fiveMServer.set_state_restarting()
                # update status message
                await self.edit_status_message(self.create_status_restart())

            elif RESTART_WARN_MSG.lower() in lower_message:
                fiveMServer.next_restart = (get_timestamp() + RESTART_WARN_DELAY * Intervals.MINUTE)
        elif lower_message.startswith("!toggleuptimevisibility") and message.author.guild_permissions.administrator:
            if self.show_uptime:
                self.show_uptime = False
                await message.channel.send("Onlinezeit wird nicht mehr angezeigt :mute:")
            else:
                self.show_uptime = True
                await message.channel.send("Onlinezeit wird wieder angezeigt :sound:")
        elif lower_message.startswith("!fivem"):
            async with message.channel.typing():
                embed = discord.Embed()
                embed.set_author(
                    name="FiveM Status",
                    icon_url="https://fivem.net/favicon.png",
                    url="https://status.cfx.re/",
                )
                embed.set_footer(text="FlixRP", icon_url="https://verwaltung.flixrp.net/favicon-32x32.png")
                embed.timestamp = datetime.utcnow()
                embed.add_field(
                    name="\u200b",
                    value="**FiveM Status von [status.cfx.re](https://status.cfx.re/)**\n" +
                          self.add_dot_to_fivem_status(self.cfx_status),
                    inline=True,
                )
                embed.add_field(
                    name="\u200b",
                    value="**FiveM Status von [Allestörungen.de](https://allestörungen.de/stoerung/fivem/)**\n" +
                          self.add_dot_to_fivem_status(self.down_detector_status),
                    inline=True,
                )
                await message.channel.send(embed=embed)
        elif lower_message.startswith("!togglecfxstatus") and message.author.guild_permissions.administrator:
            if self.show_cfx_status:
                self.show_cfx_status = False
                await message.channel.send("Der FiveM Status von `status.cfx.re` wird nicht mehr angezeigt :mute:")
            else:
                self.show_cfx_status = True
                await message.channel.send("Der FiveM Status von `status.cfx.re` wird wieder angezeigt :sound:")
        elif lower_message.startswith("!toggledowndetectorstatus") and message.author.guild_permissions.administrator:
            if self.show_down_detector_status:
                self.show_down_detector_status = False
                await message.channel.send("Der FiveM Status von `AlleStörungen.de` wird nicht mehr angezeigt :mute:")
            else:
                self.show_down_detector_status = True
                await message.channel.send("Der FiveM Status von `AlleStörungen.de` wird wieder angezeigt :sound:")

    async def on_connect(self):
        fiveMServer.last_offline = 0
        fiveMServer.last_online = 0
        fiveMServer.next_restart = 0

    async def edit_status_message(self, embed):
        # noinspection PyBroadException
        try:
            await self.status_message.edit(embed=embed, content=None, suppress=False)
            self.skipped_status_update = False
        except:
            if not self.skipped_status_update:
                # skips one update interval before resending the hole status message
                logging.warning("skipped status update")
                self.skipped_status_update = True
            else:
                self.skipped_status_update = False
                # try to get a message from the channel history before resending the hole status message
                try:
                    async for message in self.get_channel(STATUS_CHANNEL_ID).history(limit=10):
                        if message.author.bot and message.author.id == self.user.id:  # check if its from the bot itself
                            await message.edit(embed=embed, content=None, suppress=False)
                            self.status_message = message
                            logging.info("reused status message from history")
                            return
                except Exception as e:
                    logging.error("failed to edit message from history", exc_info=e)
                # resend the status message
                try:
                    await self.status_channel.purge(bulk=True)
                except Exception as e:
                    logging.error("cannot clean up status channel", exc_info=e)
                    return
                try:
                    self.status_message = await self.status_channel.send(embed=embed)
                    logging.info("re sent status message")
                except Exception as e:
                    logging.error("failed to send the status message.", exc_info=e)

    async def update_status_loop(self):
        """Loop for updating the server-status"""
        logging.info("Starting status-update loop")
        while True:
            await asyncio.sleep(STATUS_UPDATE_INTERVAL)
            fiveMServer.request_state()
            if fiveMServer.is_online():
                embed = self.create_status_online()
            elif fiveMServer.is_restarting():
                embed = self.create_status_restart()
            elif fiveMServer.is_not_reachable():
                embed = self.create_status_not_reachable()
            else:
                embed = self.create_status_offline()

            await self.edit_status_message(embed)

    async def update_fivem_status_loop(self):
        """Loop for updating the official fivem-status"""
        logging.info("Starting fivem status-update loop")
        while True:
            self.update_fivem_status()
            # repeat around every half minute
            await asyncio.sleep(33 + random.randint(0, 5))

    def update_fivem_status(self):
        """Update the class attributes down_detector_status and cfx_status with helpers from the fivem package"""
        try:
            self.cfx_status = fivem.cfx_status()
        except requests.exceptions.ConnectionError:
            self.cfx_status = ":grey_question: Keine Verbindung"
        except Exception as e:
            logging.warning("failed to fetch cfx status from api", exc_info=e)
            self.cfx_status = ":grey_question: Keine Daten"
        try:
            self.down_detector_status = fivem.down_detector()
        except requests.exceptions.ConnectionError:
            self.down_detector_status = ":grey_question: Keine Verbindung"
        except Exception as e:
            logging.warning("failed to fetch down detector status", exc_info=e)
            self.down_detector_status = ":grey_question: Keine Daten"

    @staticmethod
    def create_status_template() -> discord.Embed:
        embed = discord.Embed()
        embed.set_author(
            name="FlixRP Server Status",
            icon_url="https://verwaltung.flixrp.net/favicon-32x32.png",
            url="https://www.flixrp.net"
        )
        embed.add_field(
            name="**FiveM:**",
            value="`" + SERVER_DOMAIN + "`",
            inline=False,
        )
        embed.set_footer(text="Zuletzt aktualisiert")
        embed.timestamp = datetime.utcnow()
        return embed

    def add_fivem_status_to_status_message(self, embed):
        if self.show_cfx_status:
            embed.add_field(
                name="\u200b",
                value=f"**FiveM Status von [status.cfx.re](https://status.cfx.re/)**\n"
                      f"{self.add_dot_to_fivem_status(self.cfx_status)}\n\u200b",
                inline=True,
            )
        if self.show_down_detector_status:
            embed.add_field(
                name="\u200b",
                value=f"**FiveM Status von [Allestörungen.de](https://allestörungen.de/stoerung/fivem/)**\n"
                      f"{self.add_dot_to_fivem_status(self.down_detector_status)}\n\u200b",
                inline=True,
            )

    def create_status_online(self) -> discord.Embed:
        embed = self.create_status_template()
        embed.title = "**FlixRP** ist aktuell **Online!** :white_check_mark:\n\u200b"
        embed.colour = 0x74EE15
        embed.add_field(
            name="**Spieler:**",
            value="`" + str(fiveMServer.players) + " / " + FIVEM_MAX_PLAYERS + "`",
            inline=False,
        )
        # add uptime field
        if self.show_uptime and fiveMServer.get_uptime_seconds() > 60:
            embed.add_field(
                name="**Onlinezeit:**",
                value="`" + create_time_from_seconds(fiveMServer.get_uptime_seconds()) + "`",
                inline=False,
            )
        # add restart-warn-message
        if fiveMServer.next_restart > get_timestamp():
            diff = fiveMServer.next_restart - get_timestamp()
            r_time = int(diff / 60) + 1
            if r_time <= 1:
                embed.description = ":warning: FlixRP wird gleich neu gestartet!\n\u200b"
            else:
                embed.description = ":warning: FlixRP wird in " + str(r_time) + " Minuten neu gestartet!\n\u200b"
            del r_time
            del diff
        self.add_fivem_status_to_status_message(embed)
        return embed

    def create_status_restart(self) -> discord.Embed:
        embed = self.create_status_template()
        embed.title = "**FlixRP** wird neu gestartet!\n\u200b"
        embed.colour = 0xFFAC00
        self.add_fivem_status_to_status_message(embed)
        return embed

    def create_status_offline(self) -> discord.Embed:
        embed = self.create_status_template()
        embed.title = "**FlixRP** ist aktuell **Offline!** :no_entry:\n\u200b"
        embed.colour = 0xFF0000
        # add downtime field
        if fiveMServer.get_downtime_seconds() > 60:
            embed.add_field(
                name="**Offlinezeit:**",
                value="`" + create_time_from_seconds(fiveMServer.get_downtime_seconds()) + "`",
                inline=False,
            )
        self.add_fivem_status_to_status_message(embed)
        return embed

    def create_status_not_reachable(self) -> discord.Embed:
        embed = self.create_status_template()
        embed.title = "**FlixRP** ist aktuell **Nicht erreichbar!** :no_entry:\n\u200b"
        embed.colour = 0xFF0000
        embed.description = "```ping >3000```\n\u200b"
        # add downtime field
        if fiveMServer.get_downtime_seconds() > 60:
            embed.add_field(
                name="**Offlinezeit:**",
                value="`" + create_time_from_seconds(fiveMServer.get_downtime_seconds()) + "`",
                inline=False,
            )
        self.add_fivem_status_to_status_message(embed)
        return embed

    @staticmethod
    def add_dot_to_fivem_status(status: str) -> str:
        """Adds a discord formatted colored dot depending on the status in front of the string"""
        if not status.startswith(":grey_question:"):
            lower_status = status.lower()
            if lower_status == "all systems operational":
                return ":green_circle: " + status
            elif lower_status == "partial system outage":
                return ":red_circle: " + status
            elif lower_status == "minor service outage":
                return ":orange_circle: " + status
            elif lower_status == "partially degraded service":
                return ":orange_circle: " + status
            elif lower_status == "nutzerberichte deuten auf mögliche probleme bei fivem hin":
                return ":orange_circle: " + status
            elif lower_status == "nutzerberichte zeigen keine aktuellen probleme bei fivem":
                return ":green_circle: " + status
            elif lower_status == "nutzerberichte deuten auf probleme bei fivem hin":
                return ":red_circle: " + status
            else:
                return ":black_circle: " + status
        else:
            return status


if __name__ == "__main__":
    client = Client(
        allowed_mentions=discord.AllowedMentions.none(),
        guild_subscriptions=False,
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=str(config.get("Settings", "status-message")),
        ),
        intents=discord.Intents(
            guilds=True,
            members=False,
            bans=False,
            emojis=False,
            integrations=False,
            webhooks=False,
            invites=False,
            voice_states=False,
            presences=False,
            guild_messages=True,
            dm_messages=False,
            reactions=False,
            typing=False,
        ),
    )
    client.run(str(config.get("Settings", "token")))

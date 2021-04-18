import asyncio
import configparser
import logging
import sys
import time
import traceback
from datetime import datetime

import discord
import requests

logging.basicConfig(filename="latest.log", filemode="w", level=logging.INFO, format="%(asctime)s:%(levelname)s:%("
                                                                                    "message)s")
logging.info("Started with python version " + sys.version)
config = configparser.ConfigParser()
config.read("config.ini")

STATUS_UPDATE_INTERVAL = int(config.get("Settings", "status-update-interval"))
STATUS_CHANNEL_ID = int(config.get("Settings", "status-channel-id"))
FIVEM_BOT_ID = int(config.get("Restart-Detection", "fivem-status-bot-id"))
RESTART_MESSAGE = str(config.get("Restart-Detection", "restart-detection-message"))
RESTART_WARN_MSG = str(config.get("Restart-Detection", "restart-warn-message"))
RESTART_WARN_DELAY = int(config.get("Restart-Detection", "restart-warn-delay"))
FIVEM_SERVER_IP = str(config.get("Settings", "fivem-server-ip"))
SERVER_DOMAIN = str(config.get("Status-Message", "fivem-domain"))
FIVEM_MAX_PLAYERS = str(config.get("Settings", "max-players"))


def request_fivem_player_count(addr: str) -> bool or None:
    """Sets the player count of the server on FiveMServer.players

    :param addr: The IP of the server
    :return: True on success. False when the server if offline. None of the server is unreachable.
    :rtype: bool | None
    """
    try:
        r = requests.get("http://" + addr + "/players.json", timeout=3)
        FiveMServer.players = len(r.json())
    except (requests.exceptions.Timeout, requests.exceptions.URLRequired, requests.exceptions.InvalidURL):
        return None
    except:
        return False
    return True


def get_timestamp() -> int:
    """
    Gets the current timestamp
    """
    return int(time.time())


def create_time_from_seconds(seconds: int) -> str:
    """Creates a formatted time string from an amount of seconds

    :param seconds: The seconds
    :type seconds: int
    :return: An formatted time string
    :rtype: str
    """
    days = int(seconds / Intervals.day)
    hours = int((seconds - (Intervals.day * days)) / Intervals.hour)
    minutes = int((seconds - ((Intervals.day * days) + (Intervals.hour * hours))) / Intervals.minute)
    time_list = []
    if days == 1:
        time_list.append("1 day")
    elif days > 1:
        time_list.append(str(days) + " days")
    if hours == 1:
        time_list.append("1 hour")
    elif hours > 1:
        time_list.append(str(hours) + " hours")
    if minutes == 1:
        time_list.append("1 minute")
    elif minutes > 1:
        time_list.append(str(minutes) + " minutes")
    delimiter = ", "
    return delimiter.join(time_list)


class Intervals:
    """
    The seconds of each day/hour/minute
    """
    day = 86400
    hour = 3600
    minute = 60


class FiveMServer:
    """
    Static class
    """
    players = 0  # amount of players
    is_restarting = False
    last_offline = 0  # timestamp in seconds
    last_online = 0  # timestamp in seconds
    next_restart = 0  # timestamp in seconds
    status_message = None
    status_channel = None

    @staticmethod
    def get_downtime_seconds() -> int:
        if FiveMServer.last_online > 0:
            return get_timestamp() - FiveMServer.last_online
        else:
            return 0

    @staticmethod
    def get_uptime_seconds() -> int:
        if FiveMServer.last_offline > 0:
            return get_timestamp() - FiveMServer.last_offline
        else:
            return 0


class Client(discord.Client):
    async def on_error(self, *args, **kwargs):
        logging.error(traceback.format_exc())

    async def on_ready(self):
        print("Logged in as " + str(client.user.name) + " (" + str(client.user.id) + ")")
        logging.info("Logged in as " + str(client.user.name) + " (" + str(client.user.id) + ")")
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching,
                                                               name=str(config.get("Settings", "status-message"))))
        FiveMServer.status_channel = self.get_channel(STATUS_CHANNEL_ID)
        await self.edit_status_message(discord.Embed(title="Restarted Dashboard"))

        while True:
            await self.update_status()
            await asyncio.sleep(STATUS_UPDATE_INTERVAL)

    async def on_message(self, message):
        if not message.author.bot or message.author.system:
            return
        elif message.author.id == FIVEM_BOT_ID:
            lower_message = str(message.content).lower()
            if RESTART_MESSAGE.lower() in lower_message:
                FiveMServer.is_restarting = True
                FiveMServer.last_online = get_timestamp()
                FiveMServer.last_offline = get_timestamp()
                # update status message
                embed = self.create_status_restart()
                await self.edit_status_message(embed)
                del embed

            elif RESTART_WARN_MSG.lower() in lower_message:
                FiveMServer.next_restart = (get_timestamp() + RESTART_WARN_DELAY * 60)

    async def edit_status_message(self, embed):
        try:
            await FiveMServer.status_message.edit(embed=embed)
        except:
            await self.clear_status_channel(10)
            FiveMServer.status_message = await FiveMServer.status_channel.send(embed=embed)

    @staticmethod
    async def clear_status_channel(number_of_messages):
        await FiveMServer.status_channel.purge(limit=number_of_messages)

    async def update_status(self):
        result = request_fivem_player_count(FIVEM_SERVER_IP)
        if result is True and FiveMServer.is_restarting is False:
            FiveMServer.last_online = get_timestamp()
            embed = self.create_status_online()

        elif FiveMServer.is_restarting is True:
            FiveMServer.is_restarting = False
            FiveMServer.last_offline = get_timestamp()
            embed = self.create_status_restart()

        else:
            FiveMServer.last_offline = get_timestamp()
            if result is None:
                embed = self.create_status_not_reachable()
            else:
                embed = self.create_status_offline()

        await self.edit_status_message(embed)
        del result
        del embed

    @staticmethod
    def create_status_template() -> discord.Embed:
        embed = discord.Embed()
        embed.add_field(name="**FiveM:**", value="`" + SERVER_DOMAIN + "`", inline=False)
        embed.set_footer(text="Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        return embed

    def create_status_online(self) -> discord.Embed:
        embed = self.create_status_template()
        embed.title = "**Server** is currently **online!** :white_check_mark:"
        embed.colour = 0x74EE15
        embed.add_field(name="**Players:**", value="`" + str(FiveMServer.players) + " / " + FIVEM_MAX_PLAYERS + "`",
                        inline=False)
        # add uptime field
        if FiveMServer.get_uptime_seconds() > 60:
            embed.add_field(name="**Uptime:**",
                            value="`" + create_time_from_seconds(FiveMServer.get_uptime_seconds()) + "`",
                            inline=False)
        # add restart-warn-message
        if FiveMServer.next_restart > get_timestamp():
            diff = FiveMServer.next_restart - get_timestamp()
            r_time = int(diff / 60) + 1
            if r_time <= 1:
                embed.description = ":warning: Server will be restarted in a moment!"
            else:
                embed.description = ":warning: Server restarts in " + str(
                    r_time) + " minutes!"
            del r_time
            del diff
        return embed

    def create_status_restart(self) -> discord.Embed:
        embed = self.create_status_template()
        embed.title = "**Server** is restarting!"
        embed.colour = 0xFFAC00
        return embed

    def create_status_offline(self) -> discord.Embed:
        embed = self.create_status_template()
        embed.title = "**Server** is currently **offline!** :no_entry:"
        embed.colour = 0xFF0000
        # add downtime field
        if FiveMServer.get_downtime_seconds() > 60:
            embed.add_field(name="**Downtime:**",
                            value="`" + create_time_from_seconds(FiveMServer.get_downtime_seconds()) + "`",
                            inline=False)
        return embed

    def create_status_not_reachable(self) -> discord.Embed:
        embed = self.create_status_template()
        embed.title = "**Server** is currently **not available!** :no_entry:"
        embed.colour = 0xFF0000
        embed.description = "```ping >3000```"
        # add downtime field
        if FiveMServer.get_downtime_seconds() > 60:
            embed.add_field(name="**Downtime:**",
                            value="`" + create_time_from_seconds(FiveMServer.get_downtime_seconds()) + "`",
                            inline=False)
        return embed


client = Client()
client.run(str(config.get("Settings", "token")))

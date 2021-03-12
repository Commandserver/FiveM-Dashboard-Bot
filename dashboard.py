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


def get_server(addr):
    """
    Gets a server's players.json data
    :param addr: The IPv4 of the server
    :return: Returns Server object on success, None when the server is not reachable,
    Otherwise False when the server is offline or on error
    """
    serv = Server()
    try:
        r = requests.get("http://" + addr + "/players.json", timeout=3)
        serv.players = r.json()
    except (requests.exceptions.Timeout, requests.exceptions.URLRequired, requests.exceptions.InvalidURL):
        del serv
        return None
    except:
        del serv
        return False
    else:
        return serv


def get_timestamp() -> int:
    return int(time.time())


class Server:
    players = {}


class Intervals:
    day = 86400
    hour = 3600
    minute = 60


class FiveMServer:
    is_restarting = False
    last_offline = 0  # timestamp in seconds
    last_online = 0  # timestamp in seconds
    next_restart = 0  # timestamp in seconds
    status_message = None
    status_channel = None


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
        if not message.author.bot:
            return
        elif message.author == client.user:
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

    async def clear_status_channel(self, number_of_messages):
        await FiveMServer.status_channel.purge(limit=number_of_messages)

    async def update_status(self):
        server = get_server(FIVEM_SERVER_IP)
        if server is not False and server is not None and (
                FiveMServer.last_online + (STATUS_UPDATE_INTERVAL * 2)) < get_timestamp():
            FiveMServer.is_restarting = False
            embed = self.create_status_online(server)

        elif FiveMServer.is_restarting is True:
            if FiveMServer.last_online + Intervals.minute < get_timestamp():
                FiveMServer.is_restarting = False
            FiveMServer.last_offline = get_timestamp()
            embed = self.create_status_restart()

        else:
            FiveMServer.last_offline = get_timestamp()
            if server is None:
                embed = self.create_status_not_reachable()
            else:
                embed = self.create_status_offline()

        await self.edit_status_message(embed)
        del server
        del embed

    def create_status_template(self) -> discord.Embed:
        embed = discord.Embed()
        embed.set_footer(text="Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        return embed

    def create_status_online(self, server) -> discord.Embed:
        embed = self.create_status_template()
        embed.title = "**Server** is currently **Online!** :white_check_mark:"
        embed.colour = 0x74EE15
        embed.add_field(name="**FiveM:**", value="`" + SERVER_DOMAIN + "`", inline=False)
        players = str(len(server.players))
        embed.add_field(name="**Players:**", value="`" + players + " / " + FIVEM_MAX_PLAYERS + "`", inline=False)
        # add uptime field
        if FiveMServer.last_offline > 0 and FiveMServer.last_offline + 60 < get_timestamp():
            embed.add_field(name="**Uptime:**", value="`" + self.get_calculated_online_time_str() + "`")
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
        embed.description = "**FiveM:** `" + SERVER_DOMAIN + "`"
        return embed

    def create_status_offline(self) -> discord.Embed:
        embed = self.create_status_template()
        embed.title = "**Server** is currently **Offline!** :no_entry:"
        embed.colour = 0xFF0000
        embed.description = "**FiveM:** `" + SERVER_DOMAIN + "`"
        return embed

    def create_status_not_reachable(self) -> discord.Embed:
        embed = self.create_status_template()
        embed.title = "**Server** is currently **Not available!** :no_entry:"
        embed.colour = 0xFF0000
        embed.description = "```ping >3000```\n**FiveM:** `" + SERVER_DOMAIN + "`"
        return embed

    def get_calculated_online_time_str(self) -> str:
        diff = get_timestamp() - FiveMServer.last_offline
        days = int(diff / Intervals.day)
        hours = int((diff - (Intervals.day * days)) / Intervals.hour)
        minutes = int((diff - ((Intervals.day * days) + (Intervals.hour * hours))) / Intervals.minute)
        liste = []
        if days == 1:
            liste.append("1 day")
        elif days > 1:
            liste.append(str(days) + " days")
        if hours == 1:
            liste.append("1 hour")
        elif hours > 1:
            liste.append(str(hours) + " hours")
        if minutes == 1:
            liste.append("1 minute")
        elif minutes > 1:
            liste.append(str(minutes) + " minutes")
        trennzeichen = ", "
        return trennzeichen.join(liste)


client = Client()
client.run(str(config.get("Settings", "token")))

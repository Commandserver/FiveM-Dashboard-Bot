import configparser
import logging
import sys
import traceback
import time
from datetime import datetime
import discord
import asyncio
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
SERVER_DOMAIN = str(config.get("Status-Message", "server-domain"))


class Server:
    info = {}
    players = {}


class Intervals:
    day = 86400
    hour = 3600
    minute = 60


def get_server(addr):
    serv = Server()
    try:
        r = requests.get("http://" + addr + "/info.json", timeout=8)
        serv.info = r.json()
        r = requests.get("http://" + addr + "/players.json", timeout=8)
        serv.players = r.json()
    except requests.exceptions.Timeout:
        logging.warning("Request to the FiveM-Server timed out")
        del serv
        return False
    except requests.exceptions.InvalidURL:
        logging.warning("Request failed. The IP " + FIVEM_SERVER_IP + " seems to be invalid")
        del serv
        return False
    except Exception:
        del serv
        return False
    return serv


def get_timestamp() -> int:
    return int(time.time())


class Client(discord.Client):
    server_is_restarting = False
    # timestamp in sekunden
    server_last_online_timestamp = 0
    # timestamp in sekunden
    server_next_restart_timestamp = 0
    server_last_offline = get_timestamp()
    status_message = None
    status_channel = None

    async def on_error(self, *args, **kwargs):
        logging.error(traceback.format_exc())

    async def on_ready(self):
        print("Logged in as " + str(client.user.name) + " (" + str(client.user.id) + ")")
        logging.info("Logged in as " + str(client.user.name) + " (" + str(client.user.id) + ")")
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching,
                                                               name=str(config.get("Settings", "status-message"))))
        self.status_channel = self.get_channel(STATUS_CHANNEL_ID)
        await self.edit_status_message(discord.Embed(title="Dashboard-Bot wurde neu gestartet"))

        while True:
            await self.update_status()
            await asyncio.sleep(STATUS_UPDATE_INTERVAL)

    async def on_message(self, message):
        # nichts tun wenn nicht von einem bot
        if not message.author.bot:
            return
        # nichts tun wenn vom bot selbst
        if message.author == client.user:
            return
        # wenn vom fivem bot gesendet
        if message.author.id == FIVEM_BOT_ID:
            lower_message = str(message.content).lower()
            if RESTART_MESSAGE.lower() in lower_message:
                self.server_is_restarting = True
                self.server_last_online_timestamp = get_timestamp()
                self.server_last_offline = get_timestamp()
                # status-nachricht aktualisieren
                embed = self.create_status_restart()
                await self.edit_status_message(embed)
                del embed

            elif RESTART_WARN_MSG.lower() in lower_message:
                self.server_next_restart_timestamp = (get_timestamp() + RESTART_WARN_DELAY * 60)

    async def edit_status_message(self, embed):
        try:
            await self.status_message.edit(embed=embed)
        except Exception:
            await self.clear_status_channel(10)
            self.status_message = await self.status_channel.send(embed=embed)

    async def clear_status_channel(self, number_of_messages):
        await self.status_channel.purge(limit=number_of_messages)

    async def update_status(self):
        server = get_server(FIVEM_SERVER_IP)
        if server is not False and (
                self.server_last_online_timestamp + (STATUS_UPDATE_INTERVAL * 2)) < get_timestamp():
            self.server_is_restarting = False
            embed = self.create_status_online(server)

        elif self.server_is_restarting is True:
            self.server_last_offline = get_timestamp()
            embed = self.create_status_restart()

        else:
            self.server_last_offline = get_timestamp()
            embed = self.create_status_offline()

        await self.edit_status_message(embed)
        del server
        del embed

    def create_status_template(self) -> discord.Embed:
        embed = discord.Embed()
        embed.set_footer(text="Zuletzt aktualisiert: " + datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
        return embed

    def create_status_online(self, server) -> discord.Embed:
        embed = self.create_status_template()
        embed.title = "Server ist aktuell **Online!** :white_check_mark:"
        embed.colour = 0x74EE15
        embed.add_field(name="**FiveM:**", value="`" + SERVER_DOMAIN + "`", inline=False)
        max_players = str(server.info["vars"]["sv_maxClients"])
        players = str(len(server.players))
        embed.add_field(name="**Spieler:**", value="`" + players + " / " + max_players + "`", inline=False)
        # online-zeit field hinzufügen
        if self.server_last_offline > 0 and self.server_last_offline + 60 < get_timestamp():
            embed.add_field(name="**Onlinezeit:**", value="`" + self.get_calculated_online_time_str() + "`")
        # neustart message hinzufügen
        if self.server_next_restart_timestamp > get_timestamp():
            diff = self.server_next_restart_timestamp - get_timestamp()
            r_time = int(diff / 60) + 1
            if r_time <= 1:
                embed.description = ":warning: Server wird gleich neu gestartet!"
            else:
                embed.description = ":warning: Server wird in " + str(
                    r_time) + " Minuten neu gestartet!"
            del r_time
            del diff
        return embed

    def create_status_restart(self) -> discord.Embed:
        embed = self.create_status_template()
        embed.title = "Server wird neu gestartet!"
        embed.colour = 0xFFAC00
        embed.description = "**FiveM:** `" + SERVER_DOMAIN + "`"
        return embed

    def create_status_offline(self) -> discord.Embed:
        embed = self.create_status_template()
        embed.title = "Server ist aktuell **Offline!** :no_entry:"
        embed.colour = 0xFF0000
        embed.description = "**FiveM:** `" + SERVER_DOMAIN + "`"
        return embed

    def get_calculated_online_time_str(self) -> str:
        diff = get_timestamp() - self.server_last_offline
        days = int(diff / Intervals.day)
        hours = int((diff - (Intervals.day * days)) / Intervals.hour)
        minutes = int((diff - ((Intervals.day * days) + (Intervals.hour * hours))) / Intervals.minute)
        liste = []
        if days == 1:
            liste.append("1 Tag")
        elif days > 1:
            liste.append(str(days) + " Tage")
        if hours == 1:
            liste.append("1 Stunde")
        elif hours > 1:
            liste.append(str(hours) + " Stunden")
        if minutes == 1:
            liste.append("1 Minute")
        elif minutes > 1:
            liste.append(str(minutes) + " Minuten")
        trennzeichen = ", "
        return trennzeichen.join(liste)


client = Client()
client.run(str(config.get("Settings", "token")))

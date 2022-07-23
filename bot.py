#!/usr/bin/python3

# The Fivem-Dashboard Discord-Bot (v2) with database connection

import asyncio
import configparser
import logging
import os
import sys
import traceback
from datetime import datetime, timedelta

import aiohttp
import discord
import mariadb
from discord_slash import SlashCommand, SlashContext
from dotenv import load_dotenv

import storage
from Tools.embeds import create_fivem_status_embed, create_status_restart, create_status
from Tools.useragent import Useragent
from storage import StatusZone


class Client(discord.Client):
    def __init__(self, *, loop=None, **options):
        super().__init__(loop=loop, **options)
        self.status_channel = None
        self.loop.create_task(self.update_serverstatus_loop())  # create update status loop

    async def on_error(self, event_method, *args, **kwargs):
        logging.error(f"Unknown exception occurred in {event_method}: {traceback.format_exc()}")

    async def on_ready(self):
        print(f"Logged in as {self.user.name} ({self.user.id})")
        logging.info(f"Logged in as {self.user.name} ({self.user.id})")
        self.status_channel = self.get_channel(int(os.environ.get('STATUS_CHANNEL_ID')))

    async def on_message(self, message):
        if message.author.system or message.author.id == self.user.id:
            return
        lower_message = message.content.lower()
        if message.author.bot:
            if message.author.id == int(os.environ.get("BUILD_IN_BOT_ID", 0)):
                # modify this according to your language from https://github.com/citizenfx/txAdmin/tree/master/locale
                if "wird neu gestartet".lower() in lower_message:
                    zone = StatusZone.fetch(cur)
                    zone.set_state_restarting()
                    # update status message
                    await self.edit_status_message(create_status_restart(zone, cur), zone)
                elif "wird in 5 Minuten neu gestartet".lower() in lower_message:
                    zone = StatusZone.fetch(cur)
                    zone.next_restart_at = datetime.utcnow() + timedelta(minutes=5)
        elif lower_message.startswith("!fivem"):
            await message.channel.send(embed=create_fivem_status_embed(cur))

    async def update_serverstatus_loop(self):
        """Loop for updating the server-status"""
        await self.wait_until_ready()
        logging.info("Starting status-update loop")
        while True:
            await asyncio.sleep(int(os.environ.get("STATUS_UPDATE_INTERVAL")))
            headers = {"User-Agent": Useragent.random()}
            connector = aiohttp.TCPConnector(
                ssl=False,
                ttl_dns_cache=60,
                resolver=aiohttp.AsyncResolver(),  # async version is pretty robust but might fail in very rare cases.
            )
            async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
                # noinspection PyBroadException
                try:
                    zone = StatusZone.fetch(cur)
                    await zone.request_server_state(session, logging)  # request server status e.g. offline, online...
                    embed = create_status(zone, cur)
                    await self.edit_status_message(embed, zone)
                except mariadb.Error as mariadb_error:
                    logging.log(logging.FATAL, "Database error in update status loop", exc_info=mariadb_error)
                except Exception as unknown_e:
                    logging.log(logging.FATAL, "Unknown error in update status loop", exc_info=unknown_e)

    async def edit_status_message(self, embed, zone: storage.StatusZone):
        if not self.status_channel:
            logging.error(f"No channel was found with that ID {os.environ.get('STATUS_CHANNEL_ID')}")
            return
        if not zone.status_message_id:
            # noinspection PyBroadException
            try:
                await self.status_channel.purge(limit=100, bulk=True)
            except discord.Forbidden:
                logging.error("No permissions to clear the status-channel")
            except Exception as e:
                logging.error("Failed to clear status-channel", exc_info=e)
            else:
                # noinspection PyBroadException
                try:
                    message = await self.status_channel.send(embed=embed)
                    zone.status_message_id = message.id
                except discord.Forbidden:
                    logging.error("No permissions to send the status-message")
                except Exception as e:
                    logging.error("Failed to send the status-message", exc_info=e)
                else:
                    logging.info("Sent status-message")
            return
        # noinspection PyBroadException
        try:
            message = self.status_channel.get_partial_message(zone.status_message_id)
            await message.edit(embed=embed, content=None, suppress=False)
            if zone.skipped_message_edit:
                zone.skipped_message_edit = False
        except Exception:
            if not zone.skipped_message_edit:
                # skips one update interval before resending the hole status message
                zone.skipped_message_edit = True
                logging.warning("Skipped status-message edit")
            else:
                zone.skipped_message_edit = False
                # noinspection PyBroadException
                try:
                    # try to get a message from the channel history before resending the hole status message
                    async for message in self.status_channel.history(limit=11):
                        if message.author == self.user:  # check if its from the bot itself
                            # noinspection PyBroadException
                            try:
                                await message.edit(embed=embed, content=None, suppress=False)
                                zone.status_message_id = message.id
                            except Exception as e:
                                logging.error("Failed to edit status-message from channel history", exc_info=e)
                            else:
                                logging.info("Reused status-message from channel history")
                            return
                except discord.Forbidden:
                    logging.error("No permissions to read history messages in the status-channel")
                    return
                except Exception as e:
                    logging.error("Failed to go through status-channel history", exc_info=e)
                # resend the status message...
                # noinspection PyBroadException
                try:
                    await self.status_channel.purge(limit=100, bulk=True)
                except discord.Forbidden:
                    logging.error("No permissions to clear the status-channel")
                except Exception as e:
                    logging.error("Failed to clear status-channel", exc_info=e)
                else:
                    # noinspection PyBroadException
                    try:
                        message = await self.status_channel.send(embed=embed)
                        zone.status_message_id = message.id
                    except discord.Forbidden:
                        logging.error("No permissions to send the status-message")
                    except Exception as e:
                        logging.error("Failed to send the status-message", exc_info=e)
                    else:
                        logging.info("Resent status-message")


if __name__ == "__main__":
    load_dotenv()
    logging.basicConfig(
        filename=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'latest.log'),
        level=logging.INFO,
        format="%(asctime)s:%(levelname)s:%(message)s"
    )
    logging.info("Started with python version " + sys.version)
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.ini'))

    os.environ["FIVEM_SERVER_IP"] = config.get("Settings", "fivem_server_ip")

    try:
        db = mariadb.connect(
            user=config.get("MariaDB", "user"),
            password=config.get("MariaDB", "password"),
            host=config.get("MariaDB", "host"),
            port=int(config.get("MariaDB", "port")),
            database=config.get("MariaDB", "database")
        )
    except mariadb.Error as e:
        print(f"Connection error with MariaDB Platform: {e}")
        logging.error(f"Connection error with MariaDB Platform: {e}")
        sys.exit(1)

    db.auto_reconnect = True
    db.autocommit = True

    cur = db.cursor()

    client = Client(
        allowed_mentions=discord.AllowedMentions.none(),
        guild_subscriptions=False,
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="/fivem",
        ),
        intents=discord.Intents(
            guilds=True,
            guild_messages=True,
        ),
    )

    slash = SlashCommand(client, sync_commands=True)


    @slash.slash(name="fivem", description="Show the current FiveM status")
    async def slash_command_fivem(ctx: SlashContext):
        await ctx.send(embed=create_fivem_status_embed(cur))


    try:
        client.run(config.get("Settings", "token"))
    finally:
        db.close()

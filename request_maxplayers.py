#!/usr/bin/python3

# A script to request your fivem server for the max player count
# as the max player count are not important, It's enough to call this script one time per hour or day

import asyncio
import os
import sys
import traceback

import aiohttp
import mariadb

from Tools.useragent import Useragent
from storage import StatusZone
from dotenv import load_dotenv


async def update_max_players():
    """Requests the max player count from your fivem server"""
    headers = {"User-Agent": Useragent.random()}
    async with aiohttp.ClientSession(headers=headers) as session:
        # noinspection PyBroadException
        try:
            async with session.get(f"http://{os.getenv('FIVEM_SERVER_IP')}/info.json",
                                   allow_redirects=False, compress=True, ssl=False) as response:
                data = await response.json(encoding="UTF-8", content_type=None)
                response.raise_for_status()
                zone = StatusZone.fetch(cur)
                zone.max_players = int(data["vars"]["sv_maxClients"])
        except Exception:
            print("Failed to fetch max-players")
            traceback.print_stack()
            sys.exit(1)


if __name__ == "__main__":
    load_dotenv()
    try:
        db = mariadb.connect(
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=int(os.getenv('DB_PORT')),
            database=os.getenv('DB_DATABASE'),
        )
    except mariadb.Error as e:
        print(f"Connection error with MariaDB Platform: {e}")
        sys.exit(1)

    db.auto_reconnect = True
    db.autocommit = True

    cur = db.cursor()

    asyncio.get_event_loop().run_until_complete(update_max_players())
    db.close()

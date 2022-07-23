#!/usr/bin/python3

# A program which frequency requests the official fivem status from cfx and stores it in the database

import asyncio
import configparser
import os
import random
import sys

import aiodns
import aiohttp
import mariadb

from storage import set_cfx_status


async def request_cfx_status_loop():
    """A loop which frequency requests the official fivem status from cfx and stores it in the database"""
    url: str = "https://status.cfx.re/api/v2/status.json"
    headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate',
        'User-Agent': 'python-requests/2.7.0',
    }
    while True:
        response_code: int = 0
        async with aiohttp.ClientSession(headers=headers) as session:
            # noinspection PyBroadException
            try:
                async with session.get(url, allow_redirects=False, compress=True, timeout=10.0) as response:
                    response_code = response.status
                    response.raise_for_status()

                    # parse the status out of the html code
                    json = await response.json(encoding="UTF-8", content_type=None)
                    status = str(json["status"]["description"])
                    status = (status[:100]) if len(status) > 100 else status

            except (aiohttp.ClientError, aiohttp.WebSocketError, TimeoutError, asyncio.TimeoutError,
                    aiodns.error.DNSError) as e:
                status = "no connection"
                print(f"{type(e).__name__}. Request to status.cfx failed (HTTP code {response_code}); {e}")
            except (aiohttp.ClientError, ValueError, aiodns.error.DNSError) as e:
                status = "no data"
                print(f"{type(e).__name__}. Parsing status.cfx response failed (HTTP code {response_code}); {e}")
            except Exception as e:
                status = "no data"
                print(f"{type(e).__name__}. Unknown error on status.cfx request (HTTP code {response_code}); {e}")
            set_cfx_status(cur, status)
        await asyncio.sleep(28 + random.randint(0, 6))


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.ini'))

    try:
        db = mariadb.connect(
            user=config.get("MariaDB", "user"),
            password=config.get("MariaDB", "password"),
            host=config.get("MariaDB", "host"),
            port=int(config.get("MariaDB", "port")),
            database=config.get("MariaDB", "database"),
            connect_timeout=40
        )
    except mariadb.Error as e:
        print(f"Connection error with MariaDB Platform: {e}")
        sys.exit(1)

    db.auto_reconnect = True
    db.autocommit = True

    cur = db.cursor()

    try:
        asyncio.get_event_loop().run_until_complete(request_cfx_status_loop())
    finally:
        db.close()

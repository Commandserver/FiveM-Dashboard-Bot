#!/usr/bin/python3

# A program which frequency requests the fivem status from downdetector and stores it in the database

import asyncio
import os
import random
import sys

import mariadb
import requests
from pyquery import PyQuery

from Tools.useragent import Useragent
from storage import set_downdetector_status
from dotenv import load_dotenv


async def request_downdetector_status_loop():
    """A loop which frequency requests the fivem status from downdetector and stores it in the database"""

    while True:
        response_code: int = 0
        # Note: I use requests here because it's the only package that worked for me to request downdetector
        # noinspection PyBroadException
        try:
            headers = {'User-Agent': Useragent.random()}
            # request the down-detector site
            response = requests.get(os.getenv('ALLE_STOERUNGEN_URL'), headers=headers, timeout=6)

            response_code = response.status_code
            response.raise_for_status()

            # parse the status out of the html code
            pq = PyQuery(response.text)
            tag = pq("body div#company div.h2.entry-title")
            status = tag.html()
            if not status:
                raise ValueError()
            status = status.strip()
            status = (status[:100]) if len(status) > 100 else status

        except requests.exceptions.ConnectionError as e:
            status = "no connection"
            print(f"{type(e).__name__}. Request to down detector failed (HTTP code {response_code}); {e}")
        except ValueError:
            status = "no data"
            print(f"Parsing down detector response failed (HTTP code {response_code})")
        except Exception as e:
            status = "no data"
            print(f"{type(e).__name__}. Unknown error on down detector request (HTTP code {response_code}); {e}")
        set_downdetector_status(cur, status)

        await asyncio.sleep(26 + random.randint(0, 7))


if __name__ == "__main__":
    load_dotenv()
    try:
        db = mariadb.connect(
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=int(os.getenv('DB_PORT')),
            database=os.getenv('DB_DATABASE'),
            connect_timeout=40
        )
    except mariadb.Error as e:
        print(f"Connection error with MariaDB Platform: {e}")
        sys.exit(1)

    db.auto_reconnect = True
    db.autocommit = True

    cur = db.cursor()

    try:
        asyncio.get_event_loop().run_until_complete(request_downdetector_status_loop())
    finally:
        db.close()

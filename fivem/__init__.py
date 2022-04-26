import requests
from pyquery import PyQuery

import useragent
from .Server import Server
from .State import State


def down_detector() -> str:
    """Check the FiveM Server status from `AlleStörungen.de`.
    It requests the website and will parse the html code to identify the status message.

    :return: The status message from the website. Truncated to 500 characters
    :rtype: str

    :raises Exception: When the request or parsing the data fails.
    """
    url = 'https://allestörungen.de/stoerung/fivem/'
    headers = {'User-Agent': useragent.rand()}
    response = requests.get(url, headers=headers, timeout=6)
    pq = PyQuery(response.text)
    tag = pq("body div#company div.h2.entry-title")
    status = tag.html()
    if not status:
        raise Exception("parsing the status failed")
    status = status.strip()
    tc = (status[:500] + '..') if len(status) > 500 else status
    return tc


def cfx_status() -> str:
    """Request the FiveM server status from the official cfx.re status api
    https://status.cfx.re/api/v2/status.json

    :return: The official cfx.re status message of fivem. Truncated to 500 characters
    :rtype: str

    :raises Exception: When the request or parsing the data fails.
    """
    r = requests.get("https://status.cfx.re/api/v2/status.json", timeout=5)
    status = str(r.json()["status"]["description"])
    tc = (status[:500] + '..') if len(status) > 500 else status
    return tc

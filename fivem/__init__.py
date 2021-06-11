import requests
from pyquery import PyQuery

from .Data import Data
from .Player import Player
from .Server import Server
from .State import State


def get_serverdata(ip: str) -> Data:
    """Retrieve information about a fivem server.
    It uses the info.json and the players.json from the Fivem server.

    :return: The fivem data.
    :rtype: Data

    :raises Exception: When the request or parsing the data fails.
    """
    server = Data()

    r = requests.get("http://{0}/info.json".format(ip), timeout=4)
    data = r.json()
    server.info.description = data["vars"]["sv_projectDesc"]
    server.info.max_players = int(data["vars"]["sv_maxClients"])
    server.info.name = data["vars"]["sv_projectName"]

    r = requests.get("http://{0}/players.json".format(ip), timeout=4)
    data = r.json()
    for p in data:
        player = Player()
        player.name = p["name"]
        player.ping = int(p["ping"])
        player.id = int(p["id"])
        server.players.append(player)
    return server


def down_detector() -> str:
    """Check the FiveM Server status from `AlleStörungen.de`.
    It requests the website and will parse the html code to identify the status message.

    :return: The status message from the website. Truncated to 500 characters
    :rtype: str

    :raises Exception: When the request or parsing the data fails.
    """
    url = 'https://allestörungen.de/stoerung/fivem/'
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) '
                             'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    response = requests.get(url, headers=headers, timeout=6)
    pq = PyQuery(response.text)
    tag = pq("body div#company div.h2.entry-title")
    status = tag.html().strip()
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

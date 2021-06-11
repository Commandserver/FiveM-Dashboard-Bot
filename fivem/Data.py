from typing import List

from .Player import Player


class Data:
    """The data of a fivem server"""

    def __init__(self):
        self.info = self.Info()
        """Info object about the server"""
        self.players = List[Player]
        """A List of Player"""

    class Info:
        """General information of the server"""

        def __init__(self):
            self.name: str = ""
            self.max_players: int = 0
            self.description: str = ""

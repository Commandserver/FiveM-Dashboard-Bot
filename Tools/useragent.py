import os
import random
from typing import List


class Useragent:
    """Useful stuff for User-agents"""

    __user_agents: List[str] = []
    """Cached user-agents"""

    @classmethod
    def random(cls) -> str:
        """Get a random user agent for a request with a custom header.
        When It's failed to read the user agents from the file, it will return a fallback agent which is always the same
        """
        if not cls.__user_agents:
            file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "useragents.txt")
            # noinspection PyBroadException
            try:
                with open(file) as f:
                    for line in f.read().splitlines():
                        if line:
                            cls.__user_agents.append(line)
            except Exception:
                return "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0"
        return random.choice(cls.__user_agents)

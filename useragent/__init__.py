import os
import random
from typing import List


_cache: List[str] = []


def rand() -> str:
    """Get a random user agent for a request with a custom header

    :raise OSError: When the user-agents-file failed to read
    """
    if not _cache:
        file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "useragents.txt")
        with open(file) as f:
            for line in f.read().splitlines():
                if line:
                    _cache.append(line)
    return random.choice(_cache)

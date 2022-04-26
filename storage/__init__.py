import mariadb

from .StatusZone import StatusZone


def get_down_detector_status(cursor: mariadb) -> str:
    """
    Fetches the downdetector status from the database
    :param cursor: The database connection
    """
    cursor.execute(
        "SELECT status_message FROM FivemStatus WHERE type = 2 AND updated_at > UTC_TIMESTAMP() - INTERVAL 2 MINUTE"
    )
    result = cursor.fetchone()
    if result:
        (message,) = result
        return format_fivem_status(message)
    else:
        return format_fivem_status("no data")


def get_cfx_status(cursor: mariadb):
    """Fetches the official fivem status from the database
    :param cursor: The database connection
    """
    cursor.execute(
        "SELECT status_message FROM FivemStatus WHERE type = 1 AND updated_at > UTC_TIMESTAMP() - INTERVAL 2 MINUTE"
    )
    result = cursor.fetchone()
    if result:
        (message,) = result
        return format_fivem_status(message)
    else:
        return format_fivem_status("no data")


def format_fivem_status(status: str) -> str:
    lower_status = status.lower()
    if lower_status == "no connection":
        return ":grey_question: Keine Verbindung"
    elif lower_status == "no data":
        return ":grey_question: Keine Daten"
    elif lower_status == "all systems operational":
        return f":green_circle: {status}"
    elif lower_status == "partial system outage":
        return f":red_circle: {status}"
    elif lower_status == "minor service outage":
        return f":orange_circle: {status}"
    elif lower_status == "partially degraded service":
        return f":orange_circle: {status}"
    elif lower_status == "nutzerberichte deuten auf mögliche probleme bei fivem hin":
        return f":orange_circle: {status}"
    elif lower_status == "nutzerberichte zeigen keine aktuellen probleme bei fivem":
        return f":green_circle: {status}"
    elif lower_status == "nutzerberichte deuten auf probleme bei fivem hin":
        return f":red_circle: {status}"
    else:
        return f":black_circle: {status}"


def set_cfx_status(cursor, status: str):
    """
    Update the official fivem status in the database
    :param cursor: The database connection
    :param status: The status message. It will be truncated to 100 characters
    """
    status = (status[:100]) if len(status) > 100 else status
    cursor.execute(
        "UPDATE FivemStatus SET updated_at = UTC_TIMESTAMP(), status_message = ? WHERE type = 1",
        (status,),
    )
    if cursor.rowcount < 1:
        cursor.execute(
            "INSERT INTO FivemStatus (updated_at, type, status_message) VALUES (UTC_TIMESTAMP(), 1, ?)",
            (status,),
        )


def set_downdetector_status(cursor, status: str):
    """
    Update the downdetector status in the database
    :param cursor: The database connection
    :param status: The status message. It will be truncated to 100 characters
    """
    status = (status[:100]) if len(status) > 100 else status
    cursor.execute(
        "UPDATE FivemStatus SET updated_at = UTC_TIMESTAMP(), status_message = ? WHERE type = 2",
        (status,),
    )
    if cursor.rowcount < 1:
        cursor.execute(
            "INSERT INTO FivemStatus (updated_at, type, status_message) VALUES (UTC_TIMESTAMP(), 2, ?)",
            (status,),
        )

import os
from datetime import datetime

import discord

from Tools.utils import create_time_from_seconds
from Tools.utils import ServerState
from storage import get_cfx_status, get_down_detector_status, StatusZone


def create_fivem_status_embed(cursor) -> discord.Embed:
    """Create the embed of the fivem status command
    :param cursor: The database cursor object
    """
    embed = discord.Embed()
    embed.set_author(
        name="FiveM Status",
        icon_url="https://fivem.net/favicon.png",
    )
    embed.set_footer(text=os.environ.get("PROJECT_NAME"), icon_url=os.environ.get("ICON_URL", ""))
    embed.timestamp = datetime.utcnow()
    add_fivem_status_to_embed(embed, cursor)
    return embed


def create_status(zone: StatusZone, cursor) -> discord.Embed:
    """Create the status-message
    :param cursor: The database cursor object
    """
    if zone.get_status() is ServerState.ONLINE:
        embed = create_status_online(zone, cursor)
    elif zone.get_status() is ServerState.RESTARTING:
        embed = create_status_restart(zone, cursor)
    elif zone.get_status() is ServerState.NOT_REACHABLE:
        embed = create_status_not_reachable(zone, cursor)
    elif zone.get_status() is ServerState.OFFLINE:
        embed = create_status_offline(zone, cursor)
    else:
        embed = create_status_unknown(zone, cursor)
    # add custom message
    if zone.custom_message:
        if embed.description:
            embed.description = f"{embed.description}{zone.custom_message}\n\u200b"
        else:
            embed.description = zone.custom_message + "\n\u200b"
    return embed


def add_fivem_status_to_embed(embed, cursor):
    """Adds the fivem status to an embed message
    :param embed: The embed to add the status to
    :param cursor: The database cursor object
    """
    embed.add_field(
        name="\u200b",
        value=f"**FiveM Status von [status.cfx.re](https://status.cfx.re/)**\n{get_cfx_status(cursor)}\n\u200b",
        inline=True,
    )
    embed.add_field(
        name="\u200b",
        value=f"**FiveM Status von [Allestörungen.de](https://allestörungen.de/stoerung/fivem/)**\n"
              f"{get_down_detector_status(cursor)}\n\u200b",
        inline=True,
    )


def create_status_template() -> discord.Embed:
    """Main status message template. It's used to display the status-messages"""
    embed = discord.Embed()
    embed.set_author(
        name=f"{os.environ.get('PROJECT_NAME')} Server Status",
        icon_url=os.environ.get("ICON_URL", ""),
        url=os.environ.get("WEBSITE_URL", "")
    )
    embed.add_field(
        name="**FiveM:**",
        value=f"`{os.environ.get('FIVEM_CONNECTION', '')}`",
        inline=False,
    )
    embed.set_footer(text=f"Zuletzt aktualisiert {datetime.now().strftime('%H:%M:%S')}")
    embed.timestamp = datetime.utcnow()
    return embed


def create_status_online(zone: StatusZone, cursor) -> discord.Embed:
    """
    Create the embed for online server-status
    :param cursor: The database cursor object
    """
    embed = create_status_template()
    embed.title = f"**{os.environ.get('PROJECT_NAME')}** ist aktuell **Online!** :white_check_mark:\n\u200b"
    embed.colour = 0x74EE15
    embed.add_field(
        name="**Spieler:**",
        value=f"`{zone.players} / {zone.max_players}`",
        inline=False,
    )
    # add uptime field
    if zone.get_uptime_seconds() > 60:
        embed.add_field(
            name="**Onlinezeit:**",
            value=f"`{create_time_from_seconds(zone.get_uptime_seconds())}`",
            inline=False,
        )
    # add restart-warn-message
    if zone.next_restart_at and zone.next_restart_at > datetime.utcnow():
        diff = zone.next_restart_at - datetime.utcnow()
        r_time = int(diff.total_seconds() / 60) + 1
        if r_time <= 1:
            embed.description = f":warning: {os.environ.get('PROJECT_NAME')} wird gleich neu gestartet!\n\u200b"
        else:
            embed.description = f":warning: {os.environ.get('PROJECT_NAME')} wird in {r_time} " \
                                f"Minuten neu gestartet!\n\u200b"
    add_fivem_status_to_embed(embed, cursor)
    return embed


def create_status_restart(zone: StatusZone, cursor) -> discord.Embed:
    """
    Create the embed for restarting server-status
    :param cursor: The database cursor object
    """
    embed = create_status_template()
    embed.title = f"**{os.environ.get('PROJECT_NAME')}** wird neu gestartet!\n\u200b"
    embed.colour = 0xFFAC00
    add_fivem_status_to_embed(embed, cursor)
    return embed


def create_status_offline(zone: StatusZone, cursor) -> discord.Embed:
    """
    Create the embed for offline server-status
    :param cursor: The database cursor object
    """
    embed = create_status_template()
    embed.title = f"**{os.environ.get('PROJECT_NAME')}** ist aktuell **Offline!** :no_entry:\n\u200b"
    embed.colour = 0xFF0000
    # add downtime field
    if zone.get_downtime_seconds() > 60:
        embed.add_field(
            name="**Offlinezeit:**",
            value="`" + create_time_from_seconds(zone.get_downtime_seconds()) + "`",
            inline=False,
        )
    add_fivem_status_to_embed(embed, cursor)
    return embed


def create_status_not_reachable(zone: StatusZone, cursor) -> discord.Embed:
    """
    Create the embed for not reachable server-status
    :param cursor: The database cursor object
    """
    embed = create_status_template()
    embed.title = f"**{os.environ.get('PROJECT_NAME')}** ist aktuell **Nicht erreichbar!** :no_entry:\n\u200b"
    embed.colour = 0xFF0000
    embed.description = "```ms >4000```\n\u200b"
    # add downtime field
    if zone.get_downtime_seconds() > 60:
        embed.add_field(
            name="**Offlinezeit:**",
            value="`" + create_time_from_seconds(zone.get_downtime_seconds()) + "`",
            inline=False,
        )
    add_fivem_status_to_embed(embed, cursor)
    return embed


def create_status_unknown(zone: StatusZone, cursor) -> discord.Embed:
    """
    Create the embed for unknown server-status
    :param cursor: The database cursor object
    """
    embed = create_status_template()
    embed.title = f"**{os.environ.get('PROJECT_NAME')}** ist aktuell **Unbekannt!** :black_circle:\n\u200b"
    add_fivem_status_to_embed(embed, cursor)
    return embed

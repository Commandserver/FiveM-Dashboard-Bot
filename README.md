<div align="center">
  <p>
    <h1>
      FiveM-Dashboard-Bot <small>v2</small>
    </h1>
    <h4>A Discord bot which displays the live-status of your FiveM Server.</h4>
    <img alt="GitHub release (latest by date)" src="https://img.shields.io/github/v/release/Commandserver/FiveM-Dashboard-Bot">
    <img alt="GitHub" src="https://img.shields.io/github/license/Commandserver/FiveM-Dashboard-Bot">
    <img alt="GitHub all releases" src="https://img.shields.io/github/downloads/Commandserver/FiveM-Dashboard-Bot/total">
  </p>
</div>

## About

Shows the live-status of your FiveM Server and how many players are currently playing on it.
The live [official fivem status](https://status.cfx.re/) and [AlleStörungen.de](https://allestörungen.de/stoerung/fivem/) will also be displayed.

This branch (v2) is running with a database.

[See the releases](https://github.com/Commandserver/FiveM-Dashboard-Bot/releases)

## Preview:

![](https://user-images.githubusercontent.com/44061123/165137815-6acaf05d-99ce-4701-a6a4-ed6a3ed1dc71.png)

## Commands

`!fivem` and `/fivem` to show the current fivem status from [AlleStörungen.de](https://allestörungen.de/stoerung/fivem/) and [status.cfx.re](https://status.cfx.re/)

## Dependencies:

- Python3.8 or higher
- A MySQL Database like MariaDB
- For required python packages see the `requirements.txt`

Make sure you've installed it!

## Running

If you just want to have the `/fivem` command on your server, you can also just [invite the bot to your server](https://discord.com/api/oauth2/authorize?client_id=871415662109659156&permissions=280576&scope=bot%20applications.commands) rather than running your own instance of it.

1. **Install dependencies**

Just do `pip3 install -r requirements.txt`

2. **Create the database**

Use the following statements to create a schema, and user if you want to.

```mysql
CREATE SCHEMA fivem_dashboard;

CREATE USER 'fivem_dashboard'@'localhost' IDENTIFIED BY 'your_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON fivem_dashboard.* TO 'fivem_dashboard'@'localhost';
FLUSH PRIVILEGES;
```

Use this to create the required tables in your database:

```mysql
CREATE TABLE StatusZone (
    id                       INT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT 'The Database-Identifier',
    created_at               TIMESTAMP    DEFAULT NOW() NOT NULL COMMENT 'The datetime when the object was created',
    max_players              INT UNSIGNED DEFAULT 64    NOT NULL COMMENT 'the maximum players of the FiveM server. This will be displayed in the status message',
    custom_message           VARCHAR(1000)              NULL COMMENT 'A custom message which shows up in the description of the status message',
-- restart detection system
    next_restart_at          TIMESTAMP                  NULL COMMENT 'The UTC-datetime when the next restart is',
-- fivem server state
    max_players_last_updated TIMESTAMP                  NULL COMMENT 'The UTC-datetime when the max players of the fivem server was last updated. It will be automatic updated every 10 minutes by a subprocess',
    status_message_id        BIGINT UNSIGNED            NULL COMMENT 'The ID of the status message to update it',
    last_status              TINYINT      DEFAULT 1     NOT NULL COMMENT 'The last status of the fivem server. 1=Unknown, 2=Online, 3=Restarting, 4=Offline, 5=Not reachable, 6=Error',
    players                  INT          DEFAULT 0     NOT NULL COMMENT 'The amount of players on the FiveM server',
    last_offline             TIMESTAMP                  NULL COMMENT 'The UTC-datetime when the server was last offline. For the Uptime',
    last_online              TIMESTAMP                  NULL COMMENT 'The UTC-datetime when the server was last online. For the Downtime',
    is_offline_twice         BOOLEAN      DEFAULT FALSE NOT NULL COMMENT 'When this Bot has connection problems or something goes wrong on requesting the FiveM server once, the uptime should not be reset. It should only reset the uptime when the FiveM server seems to be offline twice. Therefore is this indicator to check if the server was offline twice, then reset the uptime',
    skipped_message_edit     BOOLEAN      DEFAULT FALSE NOT NULL COMMENT 'Tells that the edition of the status message was skipped'
) COMMENT 'Used for the status message';

CREATE TABLE FivemStatus (
    updated_at     TIMESTAMP    NOT NULL COMMENT 'The datetime when the status was last updated',
    type           TINYINT      NOT NULL COMMENT 'Where the status is from. 1=official-cfx-status, 2=downdetector',
    status_message VARCHAR(255) NOT NULL COMMENT 'The latest status message to display in the StatusZones'
) COMMENT 'Status of Fivem';
```

3. **Bot Configuration**

Modify the config templates `config.ini` and `.env`.

When creating your own bot on the [discord developer portal](https://discord.com/developers/applications), the bot needs the `bot` and `applications.commands` scope along with the following permissions:

* Send messages
* View channel

Now you can launch your discord bot. Just do `python3 ./bot.py`. If you've setup all correctly, the status-message should appear in discord after some seconds.

There are three more scripts which i need to explain.

When i ran this bot on my own server, i had problems to get the downdetector status to work. Due downdetector.com is using cloudflare i was thinking that my IP Adress was blocked by them. However i always got 405 Forbidden when i requested downdetector.

So i seperated the downdetector status update to another file to have the ability to run this script elsewhere on other servers and only push the status to the database.

The `request_cfx_status.py` requests the official fivem status frequency every ~30 seconds. Just run it with `python3 ./request_cfx_status.py`.

The `request_downdetector_status.py` requests the fivem status from downdetector frequency around every 30 seconds too.

The `request_maxplayers.py` is used to request the maximum player count of your own fivem server. The max player count isn't really a thing that gets often changed tbh, so it might be enough to call this script once per day or so. Or just ignore this script if you don't need an auto updating max-player count. 

## Running with systemctl on Linux

I'd recommend running the scripts with systemctl to keep the bot always online.

You can use the following _.service_ file templates. Create them in `/etc/systemd/system` (_debian_) and adapt them according to your setup.

Use the following unit file for your discord bot. Name it `fivem-dashboard.service`

```unit file (systemd)
[Unit]
Description=Fivem Dashboard Discord bot
Wants=mariadb.service
After=mariadb.service network.target

[Service]
ExecStart=python3 /path_to_project/bot.py
Type=simple
Restart=always
RestartSec=1min

[Install]
WantedBy=multi-user.target
```

This _.service_ file is for the 3 other scripts. As you can see it refers to the unit file of the discord bot so when you stop one of it, all will be stopped.

```unit file (systemd)
[Unit]
Description=Worker for Fivem Dashboard Discord bot
Wants=mariadb.service
PartOf=fivem-dashboard.service
After=mariadb.service network.target fivem-dashboard.service

[Service]
ExecStart=python3 /path_to_project/request_maxplayers.py
Type=simple
Restart=always
RestartSec=1min

[Install]
WantedBy=multi-user.target fivem-dashboard.service
```

The following _.timer_ file template can be used to run the max-players-script once every day. Create it in the same folder as the other _.service_ files.

```unit file (systemd)
[Unit]
Description=Timer to requests the maxplayer count of your fivem server once per day
Requires=fivem-dashboard-maxplayers.service

[Timer]
Unit=fivem-dashboard-maxplayers.service
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

Replace the "fivem-dashboard-maxplayers.service" with the same name (except the extension) as your max-player-unit file.

[Read here more about systemd (Unit files)](https://www.digitalocean.com/community/tutorials/understanding-systemd-units-and-unit-files).

## Show your support

Be sure to leave a ⭐️ if you like the project and also be sure to contribute, if you're interested! Want to help? Drop me a line or send a PR.
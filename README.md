<div align="center">
  <p>
    <h1>
      FiveM-Dashboard-Bot
    </h1>
    <h4>Monitor your FiveM server on your Discord server with this bot.</h4>
    <a href="https://discord.flixrp.net"><img src="https://img.shields.io/discord/665677622604201993?color=7289da&logo=discord&logoColor=white" alt="Discord server" /></a>
    <img alt="GitHub release (latest by date)" src="https://img.shields.io/github/v/release/Commandserver/FiveM-Dashboard-Bot">
    <img alt="GitHub all releases" src="https://img.shields.io/github/downloads/Commandserver/FiveM-Dashboard-Bot/total">
<img alt="GitHub" src="https://img.shields.io/github/license/Commandserver/FiveM-Dashboard-Bot">
  </p>
</div>

## About

Show the status of Your FiveM server and how many players are currently playing on it, on your Discord Server.
It uses the players.json of the FiveM server to count the online-players.

Download only the [releases](https://gitlab.com/Commandserver/fivem-dashboard-bot/-/releases), don't download the main branch.

## Preview:

![](https://gitlab.com/Commandserver/fivem-dashboard-bot/uploads/8d6bd5e4adaae7b84d1a99034b155d51/image.png)
![](https://camo.githubusercontent.com/2d6b2194dd4e1d3563e0e7de9a0b8c81bd271da797b716d5fa8952c72ea4b58c/68747470733a2f2f692e696d6775722e636f6d2f525268697950632e706e67)

### Bot Commands

`!toggleuptimevisibility` to toggle the visibility of the uptime in the status message 

➥ You must be a server administrator to use this. Otherwise, the bot will not react.

`!fivem` show the current fivem status from [downdetector](https://allestörungen.de/stoerung/fivem/) and [cfx.re](https://status.cfx.re/)

➥ Has a cooldown of 6 seconds

`!players` to request the online players on the FiveM server

➥ You must be a server administrator to use this. Otherwise, the bot will not react. Has a cooldown of 5 seconds

`!toggledowndetectorstatus` to toggle the visibility of the FiveM Status from [AlleStörungen.de](https://allestörungen.de/stoerung/fivem/) in the status message 

➥ You must be a server administrator to use this. Otherwise, the bot will not react.

`!togglecfxstatus` to toggle the visibility of the FiveM Status from [status.cfx.re](https://status.cfx.re/api/v2/status.json) in the status message 

➥ You must be a server administrator to use this. Otherwise, the bot will not react.

## Dependencies:

- obviously Python3
- [requests](https://pypi.org/project/requests/)
- [discord](https://pypi.org/project/discord.py/) (without voice)
- [pyquery](https://pypi.org/project/pyquery/)

Make sure you have installed it!

This bot needs the build-in status bot from your fivem server for the restart detection.

## Running

Its recommended running this Bot on an external server with systemd.
The systemd (.service) file could look like this:

```ini
[Unit]
Description=Discord FiveM Dashboard Bot

[Service]
ExecStart=/home/foobar/bot.py
Type=simple
Restart=always

[Install]
WantedBy=multi-user.target
```

Optional you can run the Bot in a screen session with the `start.sh` and `stop.sh`.

When the bot is running, it will create a log file named `latest.log`.

### Configuration

The Bot can be configured in the <i>config.ini</i>.

### Needed Discord permissions

The Discord Bot needs the following permissions in the status channel where he sends the status message in:

- View Channel
- Send Messages
- Embed Links
- Manage Messages
- Read Message History

### Known issues

When starting the Bot with systemd, the config cannot be read, and the log file has not been created. In this case you have to set the absolute path to these files in the `bot.py`.
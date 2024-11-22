<div align="center">

<h1>FiveM-Dashboard-Bot v1</h1>

<h4>A Discord bot which displays the live-status of your FiveM Server.</h4>

![License](https://img.shields.io/github/license/Commandserver/FiveM-Dashboard-Bot)

</div>

## Features

- shows the live-status of your FiveM Server and how many players are currently playing on it
- live-status of the [official fivem status](https://status.cfx.re/) and [AlleStörungen.de](https://allestörungen.de/stoerung/fivem/)
- A command to get the current fivem status
- Restart detection of your fivem server with the help of your built-in TxAdmin Discord Bot

## Preview:

This is how the live-dashboard message can look like. It gets updated every 8 seconds.

![](https://user-images.githubusercontent.com/44061123/165137815-6acaf05d-99ce-4701-a6a4-ed6a3ed1dc71.png)

Note: If you just want to have a `/fivem` slash command the get the fivem status on your server, you can also just [invite my public discord bot](https://discord.com/api/oauth2/authorize?client_id=871415662109659156&permissions=280576&scope=bot%20applications.commands) to your server rather than running your own instance of it.

## Commands

Message based commands:

`!fivem` show the current fivem status from [AlleStörungen.de](https://allestörungen.de/stoerung/fivem/) and [status.cfx.re](https://status.cfx.re/)

`!toggleuptimevisibility` to toggle the visibility of the uptime in the status message 

➥ You must be a server administrator to use this. Otherwise, the bot will not react.

`!toggledowndetectorstatus` to toggle the visibility of the FiveM Status from [AlleStörungen.de](https://allestörungen.de/stoerung/fivem/) in the status message 

➥ You must be a server administrator to use this. Otherwise, the bot will not react.

`!togglecfxstatus` to toggle the visibility of the FiveM Status from [status.cfx.re](https://status.cfx.re/api/v2/status.json) in the status message 

➥ You must be a server administrator to use this. Otherwise, the bot will not react.

## Dependencies:

- Python3.8 or higher
- For required python packages see the `requirements.txt`

## Getting started

### Install python dependencies

You can install the python packages globally via `pip3 install -r requirements.txt` or by creating a virtual environment like so:

```shell
# setup virtual environment
python3 -m venv venv
# install python packages into the virtual environment
./venv/bin/pip3 install -r requirements.txt
# run the bot
./venv/bin/python3 bot.py
```

### Configuration

Rename the `config.ini.dist` to `config.ini` and configure it.

### Run the bot

Just run `./venv/bin/python3 bot.py` in your project directory.

When the bot is running, it will create a log file named `latest.log` in the project directory.

### Running with systemctl under Linux

I'd recommend running the Bot with systemctl to keep the bot always online.
The systemd (.service) file could look like this:

```ini
[Unit]
Description=Discord FiveM Dashboard Bot
After=network.target

[Service]
WorkingDirectory=/path_to_project
ExecStart=/path_to_project/venv/bin/python3 bot.py
Type=simple
Restart=always
#User=fivem-dashboard

[Install]
WantedBy=multi-user.target
```

### Required Discord permissions

The Discord Bot needs the following permissions:

- View Channel (Read messages)
- Send Messages
- Embed Links
- Manage Messages
- Read Message History

## Show your support

Be sure to leave a ⭐️ if you like the project and also be sure to contribute, if you're interested! Want to help? Drop me a line or send a PR.

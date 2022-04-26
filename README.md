<div align="center">
  <p>
    <h1>
      FiveM-Dashboard-Bot
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

[See the releases](https://github.com/Commandserver/FiveM-Dashboard-Bot/releases)

## Preview:

![](https://user-images.githubusercontent.com/44061123/165137815-6acaf05d-99ce-4701-a6a4-ed6a3ed1dc71.png)

## Commands

`!toggleuptimevisibility` to toggle the visibility of the uptime in the status message 

➥ You must be a server administrator to use this. Otherwise, the bot will not react.

`!fivem` show the current fivem status from [AlleStörungen.de](https://allestörungen.de/stoerung/fivem/) and [status.cfx.re](https://status.cfx.re/)

➥ Has a cooldown of 6 seconds

`!players` to request the online players on the FiveM server

➥ You must be a server administrator to use this. Otherwise, the bot will not react. Has a cooldown of 5 seconds

`!toggledowndetectorstatus` to toggle the visibility of the FiveM Status from [AlleStörungen.de](https://allestörungen.de/stoerung/fivem/) in the status message 

➥ You must be a server administrator to use this. Otherwise, the bot will not react.

`!togglecfxstatus` to toggle the visibility of the FiveM Status from [status.cfx.re](https://status.cfx.re/api/v2/status.json) in the status message 

➥ You must be a server administrator to use this. Otherwise, the bot will not react.

## Dependencies:

- Python3.8 or higher
- For required python packages see the `requirements.txt`

Make sure you have installed it!

## Running

I'd recommend running the Bot with systemctl to keep the bot always online.
The systemd (.service) file could look like this:

```ini
[Unit]
Description=Discord FiveM Dashboard Bot
After=network.target

[Service]
ExecStart=/path_to_the_project/bot.py
Type=simple
Restart=always

[Install]
WantedBy=multi-user.target
```

Optional you can run the Bot in a screen session with the `start.sh` and `stop.sh`.

When the bot is running, it will create a log file named `latest.log`.

### Configuration

The Bot can be configured in the `config.ini`.

### Needed Discord permissions

The Discord Bot needs the following permissions in the status channel where he sends the status message in:

- View Channel
- Send Messages
- Embed Links
- Manage Messages
- Read Message History

## Show your support

Be sure to leave a ⭐️ if you like the project and also be sure to contribute, if you're interested! Want to help? Drop me a line or send a PR.
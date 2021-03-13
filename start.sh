#!/bin/bash
#
# Starts the bot in a screen

name="fivem-dashboard"

if screen -list | grep $name; then
	echo "${name} is already online"
else
	screen -A -ln -dmS $name bash -c 'python3 dashboard.py'
	echo "Discord bot: ${name} started!"
fi

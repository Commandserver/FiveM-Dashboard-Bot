#!/bin/bash
#
# Starts the bot in a screen

# go into the project directory
cd $(dirname $0)

name="fivem-dashboard"

if screen -list | grep $name; then
	echo "${name} is already online"
else
	screen -A -ln -dmS $name bash -c 'python3 bot.py'
	echo "Discord bot: ${name} started!"
fi

#!/bin/bash
#
# Kills the bot in the screen

# go into the project directory
cd $(dirname $0)

name="fivem-dashboard"

if screen -list | grep $name; then
	screen -S $name -p 0 -X stuff "^C"
	echo "Stopped ${name}"
else
	echo "${name} screen not found. Bot seems to be Offline."
fi

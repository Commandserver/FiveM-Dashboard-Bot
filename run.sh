#!/bin/bash

# go into the project directory
cd $(dirname $0)

# activate virtual environment
source ./venv/bin/activate

# start the bot
python3 ./bot.py
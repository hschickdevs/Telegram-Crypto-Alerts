#!/bin/bash
tmux new-session -t bot

cd ~/Telegram-Crypto-Alerts

# Start the bot
python3 -m bot
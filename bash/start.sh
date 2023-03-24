#!/bin/bash
tmux new-session -d -s bot 'cd ~/Telegram-Crypto-Alerts && python3 -m bot'

echo "The bot has been started! Use 'bash stop.sh' to stop it."
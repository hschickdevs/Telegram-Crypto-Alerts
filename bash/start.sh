#!/bin/bash
tmux new-session -d -s bot 'cd ~/Telegram-Crypto-Alerts && python3 -m bot'

echo "The bot has been started! Use 'bash stop.sh' to stop it."

# After 3 seconds, attach to the tmux session:
sleep 3
tmux attach -t bot
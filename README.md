<p align="left">
<img src="img/telegram-binance.png" width="300" alt="logo">
</p>

# Telegram-Crypto-Alerts

Telegram-Crypto-Alerts is a Python script that allows you to receive alerts on cryptocurrency price movements through [Telegram](https://telegram.org/) using their open-source API.
- Prices are fetched using the Binance API
- Alerts are stored in a local JSON database.

## Installation

Clone the repository and run the following command:
```bash
pip install -r requirements.txt
```

## Setup

1. If you haven't already, create a telegram bot using [BotFather](https://core.telegram.org/bots#3-how-do-i-create-a-bot) and get the bot token.

2. In the https://t.me/BotFather telegram chat:
   - type /mybots
   - -> @yourbot
   - -> Edit Bot
   - -> Edit Commands
   - Paste and send the contents of [`bot_commands.txt`](https://github.com/hschickdevs/telegram-crypto-alerts/blob/main/bot_commands.txt) into the chat
   
3. Set your environment variables or hard code them into the src/config.py file.
    ```bash
     TELEGRAM_GROUP_IDS=-123456789,-123456789  # No-space comma separated string of Telegram group or user IDs to send alerts to
     TELEGRAM_ADMIN_IDS=123456789  # No-space comma separated string of Telegram user IDs to error alerts to
     TELEGRAM_BOT_TOKEN=123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ  # Your telegram bot token
    ```
4. Run the script using the run.py entry point script:
   ```bash
   python run.py
   ```
   You can either run this script on your local machine, or use a cloud computing service like Google Cloud Platform, Heroku, or PythonAnywhere.

## Usage

Once the bot is running, you can type `/help` in any telegram chat that the bot is in to see the available commands.

## License
[MIT](https://choosealicense.com/licenses/mit/)
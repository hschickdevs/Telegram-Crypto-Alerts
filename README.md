<!-- PROJECT HEADER -->
<div align="center">
  <img src="img/telegram-binance.png" alt="Logo" width="270">
  <h2 align="center"><strong>Telegram-Crypto-Alerts</strong></h2>
  <p align="center">
    Software written in Python that allows you to receive alerts on cryptocurrency price movements through <a href="https://telegram.org/">Telegram</a> using their open-source API, and optionally email as well.
    <br>
  </p>
  <p align="center">
    <h3><strong>Features Include:</strong></h3>
    Simple Telegram command interface<br>
    Live cryptocurrency pair prices from Binance<br>
    Dynamic HTML styled email alerts using <a href="https://github.com/kootenpv/yagmail">yagmail</a><br>
    State and configuration data stored in a local JSON database
</div>
<br>


## Installation

Clone the repository and run the following command:
```bash
pip install -r requirements.txt
```
Ensure that you have Python 3.9+ installed. If not, you can download [here](https://www.python.org/downloads/release/python-3912/). The syntax is dependent on features added in this recent version.

## Setup

1. If you haven't already, create a telegram bot using [BotFather](https://core.telegram.org/bots#3-how-do-i-create-a-bot) and get the bot token.

2. In the https://t.me/BotFather telegram chat:
   - type /mybots
   - -> @yourbot
   - -> Edit Bot
   - -> Edit Commands
   - Paste and send the contents of [`bot_commands.txt`](https://github.com/hschickdevs/telegram-crypto-alerts/blob/main/bot_commands.txt) into the chat

3. Set your environment variables or create a `.env` file in the root directory with the following:
    ```bash
     TELEGRAM_BOT_TOKEN=123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ  # Your telegram bot token
     (OPTIONAL) ALERTS_EMAIL_USER=email@email.com  # The email from which to send price alerts
     (OPTIONAL) ALERTS_EMAIL_PASS=password  # The password for the email from which to send price alerts
    ```
    If the alerts email variables are not set, only Telegram alerts will be available. The bot uses these email credentials to send email alerts using [yagmail](https://github.com/kootenpv/yagmail).

    The alert emails are dynamically built from the `src/templates/email_template.html` file.

4. **(IMPORTANT)** Run the setup script using the `setup.py` file:
   ```sh
   # Windows:
   python setup.py --id YOUR_TELEGRAM_USER_ID
   # or
   py setup.py --id YOUR_TELEGRAM_USER_ID

   # Mac/Linux:
   python3 setup.py --id YOUR_TELEGRAM_USER_ID
   ```
   This script will set up the local json data files for your user configuration and alerts.
   If you don't know how to get your telegram user id, use the command: 
   ```sh
   python setup.py --help
   ```

5. Run the main script using the `main.py` file:
   ```sh
   # Windows:
   python run.py
   # or
   py run.py

   # Mac/Linux:
   python3 run.py
   ```
   You can either run this script on your local machine, or use a cloud computing service like Google Cloud Platform, Heroku, or PythonAnywhere.

## Telegram Bot Commands

- ### Alerts

   ```sh
   /viewalerts
   # Returns all active alerts

   /indicators
   # View the list of available indicators for the /newalert command

   /newalert <base/quote> <indicator> <target>
   # Creates a new active alert (See use /indicators command to see available indicators)
   # e.g. /newalert BTC/USDT ABOVE 2000

   /cancelalert <base/quote> <index>
   # Cancels the pair alert at the given index (use /viewalerts <base/quote> to see the indexes)
   # e.g. /cancelalert BTC/USDT 1
   ```

- ### Pricing

   ```sh
   /getprice <base/quote>
   # Get the current pair price from Binance

   /priceall
   # Get the current pair price for all pairs with active alerts.
   ```

- ### Configuration

   ```sh
   /viewconfig
   # Returns the current general configuration for the bot

   /setconfig <key>=<value> <key>=<value>
   # Modify individual configuration settings
   # e.g. /setconfig send_email_alerts=True
   # You can change multiple settings by separating them with a space

   /admins VIEW/ADD/REMOVE <telegram_user_id>,<telegram_user_id>
   # VIEW - Returns the current list of admins from the registry
   # ADD - Adds each of the telegram user ids (separated by a comma) to the admin registry
   # REMOVE - Removes each of the telegram user ids (separated by a comma) from the admin registry
   # e.g. /admins ADD -123456789,-987654321

   /channels VIEW/ADD/REMOVE <telegram_channel_id>,<telegram_channel_id>
   # VIEW - Returns the current list of Telegram channels in which to send price alerts
   # ADD - Adds each of the telegram channel ids (separated by a comma) to the channel registry. The <telegram_channel_id> parameter can be either a user's telegram id or a channel's telegram id
   # REMOVE - Removes each of the telegram channel ids (separated by a comma) from the channel registry
   # e.g. /channels ADD 123456789,987654321

   /emails VIEW/ADD/REMOVE <emal@email.com>,<email@email.com>
   # VIEW - Returns the current list of emails in which to send price alerts. If the send_email_alerts config is set to False, emails will not be sent.
   # ADD - Adds each of the emails (separated by a comma) to the email registry. 
   # REMOVE - Removes each of the emails (separated by a comma) from the channel registry
   # e.g. /channels ADD 123456789,987654321
   ```

## Roadmap

1. Scale to multiple unique user configurations using MySQL & SQLAlchemy
2. Integrate technical indicators from [taapi.io](https://taapi.io/)
3. Implement concurrency if needed
4. Create twitter alerts integration
5. Create a web interface

## License

[MIT](https://choosealicense.com/licenses/mit/)

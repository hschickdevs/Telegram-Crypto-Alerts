<!-- PROJECT HEADER -->
<div align="center">
  <img src="img/telegram-binance.png" alt="Logo" width="270">
  <h2 align="center"><strong>Telegram-Crypto-Alerts</strong></h2>
  <p align="center">
    Software written in Python that allows you to receive alerts on cryptocurrency price movements and technical indicators through <a href="https://telegram.org/">Telegram</a> using their open-source API, and optionally email as well.
    <br>
  </p>
  <p align="center">
    <h3><strong>Features Include:</strong></h3>
    Simple Telegram command interface<br>
    Live cryptocurrency pair prices from Binance<br>
    Technical indicator alerts integrated using <a href="https://taapi.io/">Taapi.io</a><br>
    Dynamic HTML styled email alerts using <a href="https://www.sendgrid.com">SendGrid</a><br>
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
     TAAPIIO_APIKEY=123456789.ABCDEFGHIJKLMNOPQRSTUVWXYZ  # Your TAAPI.IO API key
     TAAPIIO_APIKEY2=123456789.ABCDEFGHIJKLMNOPQRSTUVWXYZ  # Alternate TAAPI.IO key for the telegram message handler
     
     (OPTIONAL) SENDGRID_APIKEY=your_apikey  # Your SendGrid API key for automated email alerts
     (OPTIONAL) ALERTS_EMAIL=your_email  # The email from which you would like alerts to be sent from (must be registered on SendGrid)
    ```
    If the *SENDGRID_APIKEY* and *ALERTS_EMAIL* variables are not set, only Telegram alerts will be available. The bot uses these email credentials to send email alerts using [SendGrid](https://sendgrid.com/). You can sign up [here](https://signup.sendgrid.com/) for free.

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
   # View the list of all available types of simple and technical indicators with their detailed descriptions.


   """Create new alert for simple indicators ONLY (see /indicators)"""
   /newalert <BASE/QUOTE> <INDICATOR> <COMPARISON> <TARGET> <optional_ENTRY_PRICE>
   # - BASE/QUOTE: The base currency for the alert (e.g. BTC/USDT)
   # - INDICATOR: Currently, the only available simple indicator is "PRICE"
   # - COMPARISON: The comparison operator for the alert (ABOVE, BELOW, or PCTCHG)
   # - TARGET: The target value for the alert (For PCTCHG, use % form e.g. 10.5% = 10.5)
   # - optional_ENTRY_PRICE: If using the "PCTCHG" comparison opperator, you can specify this as an alternate entry price to the current price for calculating percentage changes.
   
   # Creates a new active simple indicator alert with the given parameters.
   # E.g. /newalert BTC/USDT PRICE PCTCHG 10.0 1200


   """Create new alert for technical indicators ONLY (see /indicators)"""
   /newalert <BASE/QUOTE> <INDICATOR> <TIMEFRAME> <PARAMS> <OUTPUT_VALUE> <COMPARISON> <TARGET>
   # - BASE/QUOTE: The base currency for the alert (e.g. BTC/USDT)
   # - INDICATOR: The ID for the technical indicator (e.g. RSI)
   # - TIMEFRAME: The desired time interval for the indicator (Options: 1m, 5m, 15m, 30m, 1h, 2h, 4h, 12h, 1d, or 1w)
   # - PARAMS: No-space-comma-separated list of param=value pairs for the indicator (E.g. period=10,stddev=3) (Use "default" to skip passing params and use default values) (See /indicators for available params)
   # - OUTPUT_VALUE: The desired output value to monitor (See /indicators for available output values)
   # - COMPARISON: The comparison operator for the alert (Options: ABOVE or BELOW)
   # - TARGET: The target value of <OUTPUT_VALUE> for the alert to trigger

   # Creates a new active technical indicator alert with the given parameters.
   # E.g. /newalert ETH/USDT BBANDS 1d default valueUpperBand ABOVE 1500


   /cancelalert <base/quote> <index>
   # Cancels the pair alert at the given index (use /viewalerts <base/quote> to see the indexes)
   # e.g. /cancelalert BTC/USDT 1
   ```

- ### Pricing/Data

   ```sh
   /getprice <base/quote>
   # Get the current pair price from Binance


   /priceall
   # Get the current pair price for all pairs with active alerts.

   
   /getindicator <BASE/QUOTE> <INDICATOR> <TIMEFRAME> <PARAMS>
   # - BASE/QUOTE: The base currency for the alert (e.g. BTC/USDT)
   # - INDICATOR: The ID for the technical indicator (e.g. BBANDS)
   # - TIMEFRAME: The desired time interval for the indicator (Options: 1m, 5m, 15m, 30m, 1h, 2h, 4h, 12h, 1d, or 1w)
   # - PARAMS: No-space-comma-separated list of param=value pairs for the indicator (E.g. period=10,stddev=3) (use "default" to use the default values for the indicator)
   
   # Get the current value(s) of a technical indicator
   # E.g. /getindicator ETH/USDT BBANDS 1d default
   ```

- ### Configuration

   ```sh
   /viewconfig
   # Returns the current general configuration for the bot


   /setconfig <key>=<value> <key>=<value>
   # Modify individual configuration settings
   # e.g. /setconfig send_email_alerts=True
   # You can change multiple settings by separating them with a space


   /channels VIEW/ADD/REMOVE <telegram_channel_id>,<telegram_channel_id>
   # VIEW - Returns the current list of Telegram channels in which to send price alerts
   # ADD - Adds each of the telegram channel ids (separated by a comma) to the channel registry. The <telegram_channel_id> parameter can be either a user's telegram id or a channel's telegram id
   # REMOVE - Removes each of the telegram channel ids (separated by a comma) from the channel registry

   # Interact with your channels alert output configuration
   # e.g. /channels ADD 123456789,987654321


   /emails VIEW/ADD/REMOVE <email@email.com>,<email@email.com>
   # VIEW - Returns the current list of emails in which to send price alerts. If the send_email_alerts config is set to False, emails will not be sent.
   # ADD - Adds each of the emails (separated by a comma) to the email registry. 
   # REMOVE - Removes each of the emails (separated by a comma) from the channel registry

   # Interact with your email alert output configuration  
   # e.g. /channels ADD 123456789,987654321
   ```
- ### Administrator Only:

   ```sh
   /admins VIEW/ADD/REMOVE <telegram_user_id>,<telegram_user_id>
   # VIEW - Returns the current list of admins from the registry
   # ADD - Adds each of the telegram user ids (separated by a comma) to the admin registry
   # REMOVE - Removes each of the telegram user ids (separated by a comma) from the admin registry

   # Interact with the bot's administrator list
   # e.g. /admins ADD -123456789,-987654321


   /whitelist VIEW/ADD/REMOVE <telegram_user_id>,<telegram_user_id>
   # VIEW - Returns the current whitelist
   # ADD - Adds each of the telegram user ids (separated by a comma) to the whitelist
   # REMOVE - Removes each of the telegram user ids (separated by a comma) from the whitelist

   # Interact with the bot's whitelist
   # e.g. /whitelist ADD -123456789,-987654321


   /getlogs
   # Returns the current process logs
   ```

## Roadmap

1. ~~Scale to multiple unique user configurations~~
2. ~~Build infrastructure to integrate indicators from [taapi.io](https://taapi.io/)~~
3. Refactor to Docker container 
4. Add support for other indicators from [taapi.io](https://taapi.io/)
5. Create twitter alerts integration
6. Create alternate message handler for Discord

## License

[MIT](https://choosealicense.com/licenses/mit/)

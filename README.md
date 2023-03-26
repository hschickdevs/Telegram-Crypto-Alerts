![made-with-python](https://img.shields.io/badge/Made%20with-Python3-yellow)

<!-- PROJECT HEADER -->
<div align="center">
  <img src="docs/img/logo.png" alt="Logo" width="300">
  <hr>
  <!-- <h2 align="center"><strong>Telegram-Crypto-Alerts</strong></h2> -->
  <p align="center">
    Python software that facilitates alerts on cryptocurrency price movements and technical indicators through <a href="https://telegram.org/"><b>Telegram</b></a> using their open-source API, and optionally email as well.
    <br />
   </p>
   <p align="center">
   <a href="#about-the-project"><b>About the Project</b></a> •
   <a href="#getting-started"><b>Getting Started</b></a> •
   <a href="#telegram-bot-commands"><b>Bot Commands</b></a> •
   <a href="#how-to-add-technical-indicators"><b>Add Indicators</b></a> •
   <a href="#contributing"><b>Contribute</b></a> •
   <a href="#contact"><b>Contact</b></a>
   </p>

   <p align="center">
  
   ![screenshot](docs/img/demo.gif)
   </p>                      

  <!-- <p align="center">
    Python software that facilitates alerts on cryptocurrency price movements and technical indicators through <a href="https://telegram.org/">Telegram</a> using their open-source API, and optionally email as well.
    <br>
  </p>
  <p align="center">
    <h3><strong>Features Include:</strong></h3>
    Simple Telegram command interface<br>
    Live cryptocurrency pair prices from Binance<br>
    Technical indicator alerts integrated using <a href="https://taapi.io/">Taapi.io</a><br>
    Dynamic HTML styled email alerts using <a href="https://www.sendgrid.com">SendGrid</a><br>
    State and configuration data stored in a local JSON database  -->
</div>
<br>

> ⚠️**Disclaimer**⚠️ Due to recent changes with the Binance regulations, some IPs may be blocked from accessing the Binance API. If you are experiencing issues with the bot, please try using a VPN or proxy service (e.g. NordVPN, IPVN). 

## About the Project

The primary goal of _Telegram Crypto Alerts_ is to be a lightweight, intuitive, and modular cryptocurrency price alert bot for the Telegram messaging client.

The bot utilizes Telegram's simple chat interface to provide users the following features:
* Get live crypto pair prices from Binance, and receive alerts on price movements like **_above_**, **_below_**, **_% change_**, and **_24 hour % change_**
* Receive alerts on crypto technical indicators like **_RSI_**, **_MACD_**, **_Bollinger Bands_**, _**MA**_, **_SMA_**, and **_EMA_**.
   - The bot has the capacity to support any technical indicator that is available on [Taapi.io](https://taapi.io/), but only these are shipped from the start. See [How to Add Technical Indicators](#how-to-add-technical-indicators) for more information.
* Optionally receive dynamic HTML-styled email alerts using the SendGrid API
* Configure bot access with a full suite of administrator commands
   - _Invite your friends to use the bot!_
   - Add additional users with their own unique alerts and configuration.
* Stores all state and configuration data in a local JSON database

## Getting Started

**⚠️ RECOMMENDED ⚠️** Follow this comprehensive guide to learn how to set the bot up on a Linode VPS: [**_Linode Setup Guide_**](./docs/linode_setup_guide.md)

Alternatively, follow the steps below to set it up on your local machine.

### Local Installation

Clone the repository:

```bash
git clone https://github.com/hschickdevs/Telegram-Crypto-Alerts.git
```

CD into the repository root directory:

```bash
cd /Telegram-Crypto-Alerts
```

Install the required Python package dependencies:

```bash
pip install -r requirements.txt
```
Ensure that you have _**Python 3.9+**_ installed. If not, you can download [here](https://www.python.org/downloads/release/python-3912/). The syntax is dependent on features added in this recent version.

### Local Setup

1. If you haven't already, create a telegram bot using [BotFather](https://core.telegram.org/bots#3-how-do-i-create-a-bot) and get the bot token.

2. In the https://t.me/BotFather telegram chat:
   - type /mybots
   - -> @yourbot
   - -> Edit Bot
   - -> Edit Commands
   - Paste and send the contents of [`commands.txt`](./commands.txt) into the chat

3. Ensure that you are in the repository _root_ directory

   ```bash
   cd Telegram-Crypto-Alerts
   ```

4. Set your environment variables or create a `.env` file in the _root_ directory with the following:
    ```bash
     TELEGRAM_BOT_TOKEN=123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ  # Your telegram bot token
     TAAPIIO_APIKEY=123456789.ABCDEFGHIJKLMNOPQRSTUVWXYZ  # Your TAAPI.IO API key
     TAAPIIO_APIKEY2=123456789.ABCDEFGHIJKLMNOPQRSTUVWXYZ  # Alternate TAAPI.IO key for the telegram message handler
     
     (OPTIONAL) SENDGRID_APIKEY=your_apikey  # Your SendGrid API key for automated email alerts
     (OPTIONAL) ALERTS_EMAIL=your_email  # The email from which you would like alerts to be sent from (must be registered on SendGrid)
    ```
    If the *SENDGRID_APIKEY* and *ALERTS_EMAIL* variables are not set, only Telegram alerts will be available. The bot uses these email credentials to send email alerts using [SendGrid](https://sendgrid.com/). You can sign up [here](https://signup.sendgrid.com/) for free.

    > Email alerts are **disabled** in the configuration _by default_, but if you **did** set a Sendgrid API key and email you can enable email alerts using the `/setconfig send_email_alerts=true` command once you start the bot.

    The alert emails are dynamically built from the `src/templates/email_template.html` file.

5. **(IMPORTANT)** Run the setup script using the `setup.py` file to create your admin account:
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

   > Note: If you want to add another user as an admin on the bot, you can run the setup script again with the `--id` argument and the additional user's telegram user id.

6. Run the bot module using:
   ```bash
   # Windows:
   python -m bot
   # or
   py -m bot

   # Mac/Linux:
   python3 -m bot
   ```
   You can either run this script on your local machine, or use a cloud computing service like [Heroku](https://devcenter.heroku.com/articles/getting-started-with-python) or [PythonAnywhere](https://www.pythonanywhere.com/).

## Telegram Bot Commands

- ### Alerts

   ```bash
   /viewalerts
   # Returns all active alerts


   /indicators
   # View the list of all available types of simple and technical indicators with their detailed descriptions.


   """Create new alert for simple indicators ONLY (see /indicators)"""
   /newalert <BASE/QUOTE> <INDICATOR> <COMPARISON> <TARGET> <optional_ENTRY_PRICE>
   # - BASE/QUOTE: The base currency for the alert (e.g. BTC/USDT)
   # - INDICATOR: Currently, the only available simple indicator is "PRICE"
   # - COMPARISON: The comparison operator for the alert (ABOVE, BELOW, PCTCHG, or 24HRCHG)
   # - TARGET: The target value for the alert (For PCTCHG and 24HRCHG, use % form e.g. 10.5% = 10.5)
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

   ```bash
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

   ```bash
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

   ```bash
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

## How to Add Technical Indicators

As stated previously, the bot is designed to be easily extensible. View the currently available indicators by using the `/indicators` command on the bot. If your indicator is not listed, head over to [taapi.io/indicators](https://taapi.io/indicators/) and find the indicator you want to add. You can add any technical indicator that is supplied by taapi.io by following the steps below:

1. Shut the bot down if it is currently running using `CRTL+C` in the terminal window.

2. Open the `/util/add_indicators.ipynb` file using jupyter notebook.
   
   > If you don't have jupyter installed, see this guide: [https://jupyter.org/install](https://jupyter.org/install)

3. Make a new cell, and use the `db.add_indicator` function to add the indicator to the database:

   View the previous **examples** of how the existing indicators were added to the database using the `db.add_indicator` function (see `TADatabaseClient.add_indicator` in [`/bot/indicators.py`](/bot/indicators.py))

   The usage of the `db.add_indicator` function is as follows:

   ```python
   db.add_indicator(
      indicator_id  # Name/abbreviation of the endpoint as shown on taapi.io (e.g. BBANDS, MACD, MA)
      name  # The full name of the indicator on taapi.io (e.g. Bollinger Bands, Moving)
      endpoint  # the endpoint for the indicator in the following format: https://api.taapi.io/{indicator_id}?secret={api_key}&exchange=binance
      reference_url  # The url to the taapi.io documentation for the indicator
      params  # A list of tuples to specify additional parameters for the indicator: (param_name, param_description, default_value)
      output  # A list of output values for the indicator, as shown on taapi.io (e.g. upperBand, middleBand, lowerBand)
   )
   ```

   ### Important Restrictions:
   - **endpoint** - Must match the format shown above. The bot automatically adds the `symbol` and `interval` required parameters. Additional parameters can be added using the `params`.
   - **params** - The `param_name` must match the name of the parameter as shown on taapi.io. The `param_description` is a short description of the parameter (used in the /indicators command). The `default_value` is your custom default value for the parameter.

       Using the following screenshot below as an example:

       ![./docs/img/taapiio_ss.png](./docs/img/taapiio_ss.png)

       The params list would look like the following:
       ```python
       [
         ("optInFastPeriod", "Fast period length", 12),
         ("optInSlowPeriod", "Slow period length", 26),
         ("optInSignalPeriod", "Signal smoothing", 9),
       ]
       ```
   - **output** - The `output` list must match the output values as shown on taapi.io.

      Additionally, the output value must be directly accessible from the API response as keys in a dictionary. For example, the following response **would be** valid:
       
      ```json
      {
         "valueMACD": 737.4052287912818,
         "valueMACDSignal": 691.8373005221695,
         "valueMACDHist": 45.56792826911237
      }
      ```

      Because of this, parameters such as **`backtracks`** are restricted because they turn the response into a list of dictionaries. The bot is not designed to handle this type of response. The following response **would NOT** be valid:
      
      ```json
      [
         {
            "valueMACD": 979.518807843051,
            "valueMACDSignal": 893.54139321284,
            "valueMACDHist": 85.977414630211,
            "backtrack": 0
         },
         {
            "valueMACD": 949.7317001653792,
            "valueMACDSignal": 872.0470395552873,
            "valueMACDHist": 77.6846606100919,
            "backtrack": 1
         },
      ]
      ```

      You may need to DYOR to ensure that the parameters that you are configuring will result in a valid response.

## Contributing

Contributions are always welcome! To contribute to the project, please do one of the following:

* Create a [new issue](https://github.com/hschickdevs/Telegram-Crypto-Alerts/issues/new) and describe your idea/suggestion in detail
* Create a pull request
   1. Fork the project
   2. Create a branch for your new edits (E.g. new-indicator)
   3. Implement and test your changes (test, test, test!)
   4. [Submit your pull request](https://makeapullrequest.com/)

I am actively maintaining this project, and I will respond to any issues or pull requests as soon as possible.

> Please Star ⭐ the project if it helps you so that visibility increases to help others!

## Contact

If you have any questions, feel free to reach out to me on [**Telegram**](https://t.me/hschickdevs).

## Roadmap

- [X] Scale to multiple unique user configurations~~
- [X] Build infrastructure to integrate indicators from [taapi.io](https://taapi.io/)

## License

[MIT](https://choosealicense.com/licenses/mit/)

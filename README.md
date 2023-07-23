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

> ⚠️**Disclaimer**⚠️ Due to recent changes with the Binance regulations, some IPs may be blocked from accessing the Binance API. If you are experiencing issues with the bot, please try using a VPN or proxy service (e.g. NordVPN, IPVN, CyberGhost). 

## About the Project

<p>
   <img src="https://skillicons.dev/icons?i=python,mongodb" />
   <img src="https://cdn-icons-png.flaticon.com/512/2504/2504941.png" width=50 />
   <img src="https://cdn-icons-png.flaticon.com/512/6001/6001283.png" width=50 />
   <img src="https://taapi.io/wp-content/uploads/2019/10/social_icon.png" width=50 />
</p>

The primary goal of _Telegram Crypto Alerts_ is to be a lightweight, intuitive, and modular cryptocurrency price alert bot for the Telegram messaging client.

The bot utilizes Telegram's simple chat interface to provide users the following features:
* Get live crypto pair prices from Binance, and receive alerts on price movements like **_above_**, **_below_**, **_% change_**, and **_24 hour % change_**
* Receive alerts on crypto technical indicators like **_RSI_**, **_MACD_**, **_Bollinger Bands_**, _**MA**_, **_SMA_**, and **_EMA_**.
   - The bot has the capacity to support any technical indicator that is available on [Taapi.io](https://taapi.io/), but only these are shipped from the start. See [How to Add Technical Indicators](#how-to-add-technical-indicators) for more information.
* Optionally receive dynamic HTML-styled email alerts using the SendGrid API
* Configure bot access with a full suite of administrator commands
   - _Invite your friends to use the bot!_
   - Add additional users with their own unique alerts and configuration.
* Optional state and configuration data - Use a local JSON database or configure a MongoDB server!

## Getting Started

### Cloud Installation & Setup (Recommended)

Follow this comprehensive guide to learn how to set the bot up on a Linode cloud VPS: 

[**Linode Setup Guide**](./docs/linode_setup_guide.md) <- Click here

### Local Installation

Alternatively, follow the steps below to set it up on your local machine.

1. Clone the repository:

    ```bash
    git clone https://github.com/hschickdevs/Telegram-Crypto-Alerts.git
    ```

2. CD into the repository root directory:

    ```bash
    cd /Telegram-Crypto-Alerts
    ```

3. Install the required Python package dependencies:

    ```bash
    pip install -r requirements.txt
    ```
    
4. Ensure that you have _**Python 3.9+**_ installed. If not, you can download [here](https://www.python.org/downloads/release/python-3912/). The syntax is dependent on features added in this recent version.

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

5. **(OPTIONAL)** MongoDB Setup & Configuration

   <img src="https://cdn.icon-icons.com/icons2/2415/PNG/512/mongodb_original_wordmark_logo_icon_146425.png" width="100" style="margin-right: 20px;"/>
   <p>As of 7/16/2023, this bot now supports MongoDB as a database backend to enable data persistence. If you'd like to use a MongoDB server to store your data, instead of the local JSON database default, follow the steps below:</p>

   First, set the `USE_MONGO_DB` config variable to `True` in the static configuration file: [`/bot/config.py`](/bot/static_config.py)

   Next, you will need to create a MongoDB Atlas account. You can sign up [here](https://www.mongodb.com/cloud/atlas/register).

   Once you have created an account, you will need to create a new databse using the Altas UI: https://www.mongodb.com/basics/create-database#option-1

   You will need to locate the following:
   * Your `database connection string`
   * Your `database name`
   * Your `database collection name`

   All of the documents required for the program's backend are stored in the same collection. The documents are differentiated by the `user_id` field. The `user_id` field is the telegram user id of the user that the document belongs to.

   You will then need to set the following environment variables or add them to your `.env` file:

   ```bash
   MONGODB_CONNECTION_STRING=your_connection_string  # The URI for your MongoDB server
   MONGODB_DATABASE=your_database  # The name of the database to use
   MONGODB_COLLECTION=your_collection  # The name of the database collection to use
   ```

6. **(IMPORTANT)** Run the setup script using the `setup.py` file to create your admin account:
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

7. Run the `bot` module using:
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

- ### Alert Commands:

   #### `/viewalerts`
   
   Returns all active alerts

   ___

   #### `/indicators`

   View the list of all available types of simple and technical indicators with their detailed descriptions.

   ___

   #### `/newalert <BASE/QUOTE> <INDICATOR> <COMPARISON> <TARGET> <optional_ENTRY_PRICE>`

   > ⚠️ Create new alert for **simple indicators** ONLY (see [/indicators](https://github.com/hschickdevs/Telegram-Crypto-Alerts/blob/pancakeswap-integration/README%20copy.md#indicators))

   Creates a new active simple indicator alert with the given parameters.

   | Parameter | Description |
   |-------------------|-------------|
   | BASE/QUOTE        | The base and quote currencies for the alert (e.g. BTC/USDT) |
   | INDICATOR         | The indicator for which you want to set an alert. In the current context, the only available simple indicator is "PRICE". |
   | COMPARISON        | The comparison operator for the alert. Options are "ABOVE", "BELOW", "PCTCHG", or "24HRCHG". |
   | TARGET            | The target value for the alert. For "PCTCHG" and "24HRCHG", this should be a percentage (e.g. for 10.5%, use 10.5). |
   | optional_ENTRY_PRICE | If using the "PCTCHG" comparison operator, you can specify this as an alternate entry price to the current price for calculating percentage changes. |

   _For example, the following command sets an alert for when the price of BTC/USDT changes by 10% relative to an entry price of 1200:_

   `/newalert BTC/USDT PRICE PCTCHG 10.0 1200`

   ___

   #### `/newalert <BASE/QUOTE> <INDICATOR> <TIMEFRAME> <PARAMS> <OUTPUT_VALUE> <COMPARISON> <TARGET>`

   > ⚠️ Create new alert for **technical indicators** ONLY (see [/indicators](https://github.com/hschickdevs/Telegram-Crypto-Alerts/blob/pancakeswap-integration/README%20copy.md#indicators))

   Creates a new active technical indicator alert with the given parameters.

   | Parameter | Description |
   |-------------------|-------------|
   | BASE/QUOTE        | The base currency for the alert (e.g. BTC/USDT) |
   | INDICATOR         | The ID for the technical indicator (e.g. RSI) |
   | TIMEFRAME         | The desired time interval for the indicator. Options: 1m, 5m, 15m, 30m, 1h, 2h, 4h, 12h, 1d, or 1w |
   | PARAMS            | No-space-comma-separated list of param=value pairs for the indicator. E.g. period=10,stddev=3. Use "default" to skip passing params and use default values. See /indicators for available params |
   | OUTPUT_VALUE      | The desired output value to monitor. See /indicators for available output values |
   | COMPARISON        | The comparison operator for the alert. Options: ABOVE or BELOW |
   | TARGET            | The target value of OUTPUT_VALUE for the alert to trigger |

   _For example, the following command sets an alert for the ETH/USDT pair that triggers when the value of the upper Bollinger Band (calculated on the 1d timeframe) is above 1500:_

   `/newalert ETH/USDT BBANDS 1d default valueUpperBand ABOVE 1500`

   ___

   #### `/cancelalert <BASE/QUOTE> <INDEX>`
   
   Cancels the pair alert at the given index

   | Parameter | Description |
   |-------------------|-------------|
   | BASE/QUOTE | The base and quote currencies for the alert (e.g. BTC/USDT) |
   | INDEX | The index of the alert you want to cancel. You can see the indexes by using the `/viewalerts BASE/QUOTE` command. |

   _For example, if you want to cancel the first alert of the BTC/USDT pair, you would use:_
   
   `/cancelalert BTC/USDT 1`

- ### Pricing/Data Commands:

   #### `/getprice <BASE/QUOTE>`

   | Parameter | Description |
   |-------------------|-------------|
   | BASE/QUOTE | The base and quote currencies for the price data (e.g. BTC/USDT) |

   _For example, if you want to get the current price of the BTC/USDT pair, you would use:_

   `/getprice BTC/USDT`

   ___


   #### `/priceall`

   This command does not take any parameters. It gets the current pair price for all pairs with active alerts.

   ___

   #### `/getindicator <BASE/QUOTE> <INDICATOR> <TIMEFRAME> <PARAMS>`

   | Parameter | Description |
   |-------------------|-------------|
   | BASE/QUOTE | The base and quote currencies for the alert (e.g. BTC/USDT) |
   | INDICATOR | The ID for the technical indicator (e.g. BBANDS) |
   | TIMEFRAME | The desired time interval for the indicator. Options: 1m, 5m, 15m, 30m, 1h, 2h, 4h, 12h, 1d, or 1w |
   | PARAMS | No-space-comma-separated list of param=value pairs for the indicator. E.g. period=10,stddev=3. Use "default" to use the default values for the indicator |

   _For example, the following command gets the current value(s) of the Bollinger Bands indicator for the ETH/USDT pair on the 1d timeframe using the default parameters:_

   `/getindicator ETH/USDT BBANDS 1d default`

   ___

- ### Configuration Commands:

   #### `/viewconfig`
   
   Returns the current general configuration for the bot

   ___

   #### `/setconfig <key>=<value> <key>=<value>`

   Modify individual configuration settings. You can change multiple settings by separating them with a space.
   
   _For example, the following command sets the `send_email_alerts` config key to True:_

   `/setconfig send_email_alerts=True`

   ___

   #### `/channels <ACTION> <TG_CHANNEL_ID,<TG_CHANNEL_ID>`

   Allows you to view or modify the current list of Telegram channels set to receive alerts from the bot.

   | Parameter | Description |
   |-------------------|-------------|
   | ACTION | This can be either `VIEW`, `ADD`, or `REMOVE`. Each action has different effects and parameters: |
   | | **VIEW** - Returns the current list of Telegram channels in which to send price alerts. This action does not require any additional parameters. |
   | | **ADD** - Adds the specified Telegram channel IDs to the channel registry. The IDs should be separated by commas. For example: `/channels ADD 123456789,987654321` |
   | | **REMOVE** - Removes the specified Telegram channel IDs from the channel registry. The IDs should be separated by commas. For example: `/channels REMOVE 123456789,987654321` |
   | TG_CHANNEL_ID | This is a list of Telegram channel IDs (_separated by a comma no-spaces_). These channels will be added or removed from the channel registry based on the ACTION parameter. This parameter is not required when ACTION is `VIEW`. |

   _For example, the following command adds two Telegram channels to the alerts registry:_

   `/channels ADD 123456789,987654321`

   ___

   #### `/emails <ACTION> <EMAIL>,<EMAIL>`

   Allows you to view or modify the current list of email addresses set to receive alerts from the bot.

   > ⚠️ Registered emails will only be sent if you have configured the bot to use SendGrid for email alerts.

   | Parameter | Description |
   |-------------------|-------------|
   | ACTION | This can be either `VIEW`, `ADD`, or `REMOVE`. Each action has different effects and parameters: |
   | | **VIEW** - Returns the current list of email addresses in which to send price alerts. This action does not require any additional parameters. |
   | | **ADD** - Adds the specified email addresses to the email registry. The email addresses should be separated by commas. For example: `/emails ADD example1@email.com,example2@email.com` |
   | | **REMOVE** - Removes the specified email addresses from the email registry. The email addresses should be separated by commas. For example: `/emails REMOVE example1@email.com,example2@email.com` |
   | EMAIL | This is a list of email addresses (_separated by a comma no-spaces_). These email addresses will be added or removed from the email registry based on the ACTION parameter. This parameter is not required when ACTION is `VIEW`. |

   _For example, the following command adds two email addresses to the alerts registry:_

   `/emails ADD example1@email.com,example2@email.com`

   
- ### Administrator Only Commands:

   #### `/admins <ACTION> <TG_USER_ID,<TG_USER_ID>`

   Allows you to view or modify the current list of bot administrators.

   | Parameter | Description |
   |-------------------|-------------|
   | ACTION | This can be either `VIEW`, `ADD`, or `REMOVE`. Each action has different effects and parameters: |
   | | **VIEW** - Returns the current list of administrators. This action does not require any additional parameters. |
   | | **ADD** - Adds the specified Telegram user IDs to the administrators registry. The IDs should be separated by commas. For example: `/admins ADD 123456789,987654321` |
   | | **REMOVE** - Removes the specified Telegram user IDs from the administrators registry. The IDs should be separated by commas. For example: `/admins REMOVE 123456789,987654321` |
   | TG_USER_ID | This is a list of Telegram user IDs (_separated by a comma no-spaces_). These user IDs will be added or removed from the administrators registry based on the ACTION parameter. This parameter is not required when ACTION is `VIEW`. |

   _For example, the following command adds two administrators to the registry:_

   `/admins ADD 123456789,987654321`

   ___

   #### `/whitelist <ACTION> <TG_USER_ID,<TG_USER_ID>`

   Allows you to view or modify the bot's whitelist.

   | Parameter | Description |
   |-------------------|-------------|
   | ACTION | This can be either `VIEW`, `ADD`, or `REMOVE`. Each action has different effects and parameters: |
   | | **VIEW** - Returns the current whitelist. This action does not require any additional parameters. |
   | | **ADD** - Adds the specified Telegram user IDs to the whitelist. The IDs should be separated by commas. For example: `/whitelist ADD 123456789,987654321` |
   | | **REMOVE** - Removes the specified Telegram user IDs from the whitelist. The IDs should be separated by commas. For example: `/whitelist REMOVE 123456789,987654321` |
   | TG_USER_ID | This is a list of Telegram user IDs (_separated by a comma no-spaces_). These user IDs will be added or removed from the whitelist based on the ACTION parameter. This parameter is not required when ACTION is `VIEW`. |

   _For example, the following command adds two users to the whitelist:_

   `/whitelist ADD 123456789,987654321`

   ___

   #### `/getlogs`

   Returns the current process logs

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

- [X] Scale to multiple unique user configurations
- [X] Build infrastructure to integrate indicators from [taapi.io](https://taapi.io/)

## License

[MIT](https://choosealicense.com/licenses/mit/)

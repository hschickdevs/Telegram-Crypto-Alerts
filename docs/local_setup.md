<div>
    <center>
        <img src="https://cdn.freebiesupply.com/logos/large/2x/linode-1-logo-png-transparent.png" width="50"/>
        &nbsp;&nbsp;&nbsp;&nbsp;
        <img src="https://github.com/hschickdevs/Telegram-Crypto-Alerts/raw/main/docs/img/logo.png" width="80"/>
    </center>
    <br>
</div>

# Install and Deploy the Bot Locally

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
   - From this point on, you will be using the new bot that you created for all commands. To access the new bot, click on the link that the BotFather sends you when generating the token where it says `@<YOUR_BOT_NAME_HERE>`.

3. Open a your command terminal and ensure that you are in the repository _root_ directory

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

   First, set the `USE_MONGO_DB` config variable to `True` in the static configuration file: [`/bot/config.py`](/bot/config.py)

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
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

4. Locate and set your environment variables:

    The following environment variables are used by the bot: 

    - `TELEGRAM_USER_ID`: Your Telegram user ID (Use [Raw Data Bot](https://t.me/raw_data_bot))

        Using this ID the bot will set you up as the initial administrator.

    - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token (Use [BotFather](https://t.me/botfather))

    - `LOCATION` (_Optional_): Either `US` or `global`, determines which Binance market to use based on IP restrictions.

    - `TAAPIIO_APIKEY` (_Optional_): Your Taapi.io API key. If not provided, technical alerts will be unavailable. (Create an account on the [Taapi.io website](https://taapi.io/))

    - `TAAPIIO_TIER` (_Optional_): Your Taapi.io subscription tier. (Defaults to `free` if not provided)

        Options are `free`, `basic`, `pro`, and `expert`. Defaults to `free` if not provided. This is used to optimize rate limits.

    See [`.env.example`](../) for an example of these environment variables.

    You can either create a `.env` file in the source directory and add the environment variables there, or you can set them in your system environment variables.

5. **(OPTIONAL)** MongoDB Setup & Configuration

   <img src="https://cdn.icon-icons.com/icons2/2415/PNG/512/mongodb_original_wordmark_logo_icon_146425.png" width="100" style="margin-right: 20px;"/>
   <p>As of version 2, this bot supports MongoDB as a database backend to enable data persistence. If you'd like to use a MongoDB server to store your data, instead of the local JSON database default, follow the steps below:</p>

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
   MONGODB_CONNECTION_STRING=<YOUR_URI>  # The URI for your MongoDB server
   MONGODB_DATABASE=<YOUR_DB>  # The name of the database to use
   MONGODB_COLLECTION=<YOUR_COLLECTION>  # The name of the database collection to use
   ```

6. Run the `src` module using:
   ```bash
   # Windows:
   python -m src
   # or
   py -m src

   # Mac/Linux:
   python3 -m bot
   ```
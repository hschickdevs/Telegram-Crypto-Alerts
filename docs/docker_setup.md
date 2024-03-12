# Deploy the Telegram Crypto Alerts Software with Docker

Before continuing, ensure that you have installed Docker on your machine. If you haven't, you can follow the instructions in the [official Docker documentation](https://docs.docker.com/get-docker/).

Once you have Docker installed, you can deploy the Telegram Crypto Alerts bot using the following steps:

1. **Locate your environment variables:**

    The following environment variables are used by the bot: 

    - `TELEGRAM_USER_ID`: Your Telegram user ID (Use [Raw Data Bot](https://t.me/raw_data_bot))

        Using this ID the bot will set you up as the initial administrator.

    - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token (Use [BotFather](https://t.me/botfather))

    - `LOCATION` (_Optional_): Either `US` or `global`. Binance global is banned in the US, so `US` users use a different API endpoint (defaults to `global` if not provided).

    - `TAAPIIO_APIKEY` (_Optional_): Your Taapi.io API key. If not provided, technical alerts will be unavailable. (Create an account on the [Taapi.io website](https://taapi.io/))

    - `TAAPIIO_TIER` (_Optional_): Your Taapi.io subscription tier.

        Options are `free`, `basic`, `pro`, and `expert`. Defaults to `free` if not provided. This is used to optimize rate limits.


    See [`.env.example`](../) for an example of these environment variables.

2. **(OPTIONAL) -  MongoDB Setup & Configuration:**

   As of version 2, this bot supports MongoDB as a database backend to empower data persistence across machines. If you'd like to use a MongoDB server to store your data, instead of the local JSON database default, follow the steps below:</p>

   First, set the `USE_MONGO_DB` config variable to `True` in the static configuration file: [`src/config.py`](../src/config.py)

   Next, you will need to create a MongoDB Atlas account. You can sign up [here](https://www.mongodb.com/cloud/atlas/register).

   Once you have created an account, you will need to create a new databse using the Altas UI: https://www.mongodb.com/basics/create-database#option-1

   You will need to locate the following:
   * Your `database connection string`
   * Your `database name`
   * Your `database collection name`

   All of the documents required for the program's backend are stored in the same collection. The documents are differentiated by the `user_id` field. The `user_id` field is the telegram user id of the user that the document belongs to.

   You will then need to set the following environment variables when starting the container, in addition to the previous step:

   ```bash
   MONGODB_CONNECTION_STRING=<YOUR_URI>
   MONGODB_DATABASE=<YOUR_DB>
   MONGODB_COLLECTION=<YOUR_COLLECTION>
   ```

3. **Pull the container:**

    ```bash
    docker pull hschickdevs/telegram-crypto-alerts:latest
    ```

4. **Run the container using your environment variables:**

    > Note that you only need to provide the non-optional environment variables as shown in the previous step. However, this example includes all of the environment variables (excluding MongoDB) for clarity.

    ```bash
    docker run -d --name telegram-crypto-alerts \
      -e TELEGRAM_USER_ID=<YOUR_ID> \
      -e TELEGRAM_BOT_TOKEN=<YOUR_TOKEN> \
      -e LOCATION=<YOUR_LOCATION> \
      -e TAAPIIO_APIKEY=<YOUR_KEY> \
      -e TAAPIIO_TIER=<YOUR_TIER> \
      hschickdevs/telegram-crypto-alerts

5. **Follow the logs:**

    ```bash
    docker logs -f telegram-crypto-alerts
    ```

Your bot should now be running, head to the Telegram app and try some commands!
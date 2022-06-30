import threading
from os import getenv

from src.alert_handler import AlertHandler
from src.telegram_handler import TelegramBot
from src.io_client import handle_env, get_whitelist
from src.indicators import TaapiioProcess

if __name__ == "__main__":
    if len(get_whitelist()) == 0:
        raise Exception("Setup not complete. "
                        "Please run the setup.py script to initialize the bot using 'python setup.py --id your_tg_id'")

    # Process environment variables
    handle_env()

    # Run the Taapi.io process in a daemon thread
    threading.Thread(target=TaapiioProcess(taapiio_apikey=getenv('TAAPIIO_APIKEY')).run, daemon=True).start()

    # Run the AlertHandler() in a daemon thread
    threading.Thread(target=AlertHandler(telegram_bot_token=getenv('TELEGRAM_BOT_TOKEN'),
                                         alert_email_user=getenv('ALERTS_EMAIL_USER'),
                                         alert_email_pass=getenv('ALERTS_EMAIL_PASS')).run, daemon=True).start()

    # Run the TG bot in the main thread
    TelegramBot(bot_token=getenv('TELEGRAM_BOT_TOKEN')).run()

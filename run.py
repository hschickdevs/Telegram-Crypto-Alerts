import threading
from os import getenv

from src.alert_handler import AlertHandler
from src.telegram_handler import TelegramBot
from src.io_client import handle_env
from src.indicators import TaapiioProcess

if __name__ == "__main__":
    # Process environment variables
    handle_env()

    # Run the Taapi.io process in a daemon thread
    threading.Thread(target=AlertHandler(telegram_bot_token=getenv('TAAPIIO_APIKEY')).run, daemon=True).start()

    # Run the AlertHandler() in a daemon thread
    threading.Thread(target=AlertHandler(telegram_bot_token=getenv('TELEGRAM_BOT_TOKEN'),
                                         alert_email_user=getenv('ALERTS_EMAIL_USER'),
                                         alert_email_pass=getenv('ALERTS_EMAIL_PASS')).run, daemon=True).start()

    # Run the TG bot in the main thread
    TelegramBot(bot_token=getenv('TELEGRAM_BOT_TOKEN')).run()

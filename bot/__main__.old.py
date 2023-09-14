import threading
from os import getenv
from time import sleep

from .alert_handler import AlertHandler
from .telegram import TelegramBot
from .user import handle_env, get_whitelist
from .indicators import TaapiioProcess
from ._logger import logger

if __name__ == "__main__":
    if len(get_whitelist()) == 0:
        raise Exception("Setup not complete. "
                        "Please run the setup.py script to initialize the bot using 'python setup.py --id your_tg_id'")

    # Process environment variables
    handle_env()

    # Run the Taapi.io process in a daemon thread
    threading.Thread(target=TaapiioProcess(taapiio_apikey=getenv('TAAPIIO_APIKEY'),
                                           telegram_bot_token=getenv('TELEGRAM_BOT_TOKEN')).run, 
                     daemon=True).start()

    # Run the AlertHandler() in a daemon thread
    threading.Thread(target=AlertHandler(telegram_bot_token=getenv('TELEGRAM_BOT_TOKEN'),
                                         sendgrid_apikey=getenv(
                                             'SENDGRID_APIKEY'),
                                         alert_email=getenv('ALERTS_EMAIL')).run, 
                     daemon=True).start()

    # Run the TG bot in a daemon thread
    threading.Thread(target=TelegramBot(bot_token=getenv('TELEGRAM_BOT_TOKEN'),
                                        taapiio_apikey=getenv('TAAPIIO_APIKEY2')).run, 
                     daemon=True).start()

    # Keep the main thread alive
    logger.info("Bot started - use Ctrl+C to stop the bot.")
    while True:
        try:
            sleep(0.5)
        except KeyboardInterrupt:
            logger.info("Bot stopped")
            exit(1)
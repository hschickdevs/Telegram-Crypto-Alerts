import threading
from os import getenv
from time import sleep

from .alert_processes import CEXAlertProcess, DEXAlertProcess, TechnicalAlertProcess
from .telegram import TelegramBot
from .user_configuration import get_whitelist
from .util import handle_env
from .indicators import TaapiioProcess
from ._logger import logger

if __name__ == "__main__":
    if len(get_whitelist()) == 0:
        raise Exception("Setup not complete. "
                        "Please run the setup.py script to initialize the bot using 'python setup.py --id your_tg_id'")

    # Process environment variables
    handle_env()

    # Create global Taapi.io process for the aggregator and telegram bot to sync calls
    taapiio_process = TaapiioProcess(taapiio_apikey=getenv('TAAPIIO_APIKEY'))
    
    # Create the Telegram bot to listen to commands and send messages
    telegram_bot = TelegramBot(bot_token=getenv('TELEGRAM_BOT_TOKEN'), 
                               taapiio_process=taapiio_process)

    # Run the TG bot in a daemon thread
    # threading.Thread(target=TelegramBot(bot_token=getenv('TELEGRAM_BOT_TOKEN'),
    #                                     taapiio_process=taapiio_process).run,
    #                  daemon=True).start()
    threading.Thread(target=telegram_bot.run, daemon=True).start()

    # Run the Taapi.io process in a daemon thread
    threading.Thread(target=taapiio_process.run,
                     daemon=True).start()

    # Run the TechnicalAlertProcess in a daemon thread
    threading.Thread(target=TechnicalAlertProcess(telegram_bot_token=getenv('TELEGRAM_BOT_TOKEN')).run,
                     daemon=True).start()

    # Run the CEXAlertProcess in a daemon thread
    threading.Thread(target=CEXAlertProcess(telegram_bot_token=getenv('TELEGRAM_BOT_TOKEN')).run,
                     daemon=True).start()

    # # Run the DEXAlertProcess in a daemon thread
    # threading.Thread(target=DEXAlertProcess(telegram_bot_token=getenv('TELEGRAM_BOT_TOKEN')).run,
    #                  daemon=True).start()

    # Keep the main thread alive to listen to interrupt
    logger.info("Bot started - use Ctrl+C to stop the bot.")
    while True:
        try:
            sleep(0.5)
        except KeyboardInterrupt:
            logger.info("Bot stopped")
            exit(1)
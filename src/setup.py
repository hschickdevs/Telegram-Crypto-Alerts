from os import getenv

from .user_configuration import LocalUserConfiguration, MongoDBUserConfiguration
from .logger import logger
from .config import USE_MONGO_DB


def do_setup():
    user_id = getenv('TELEGRAM_USER_ID')

    # Set up required user files:
    try:
        logger.info(f"Creating default bot configuration for Telegram user {user_id}...")

        if not USE_MONGO_DB:
            LocalUserConfiguration(user_id).whitelist_user(is_admin=True)
        else:
            MongoDBUserConfiguration(user_id).whitelist_user(is_admin=True)

        logger.info("Setup complete! You can now run the bot module using: python3 -m bot")
    except Exception as exc:
        logger.exception("An unexpected error occurred during setup", exc_info=exc)

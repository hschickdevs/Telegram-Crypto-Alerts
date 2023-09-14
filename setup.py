import argparse

from bot.user_configuration import LocalUserConfiguration, MongoDBUserConfiguration
from bot._logger import logger
from bot.config import USE_MONGO_DB

parser = argparse.ArgumentParser()
parser.add_argument('--id', type=str, required=True,
                    help='See how to get your TG user ID here: https://www.youtube.com/watch?v=W8ifn3ATpdA')

# Parse the argument
user_id = parser.parse_args().id

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

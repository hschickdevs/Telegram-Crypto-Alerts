import argparse

from src.io_client import UserConfiguration
from src.custom_logger import logger

parser = argparse.ArgumentParser()
parser.add_argument('--id', type=str, required=True,
                    help='See how to get your TG user ID here: https://www.youtube.com/watch?v=W8ifn3ATpdA')

# Parse the argument
user_id = parser.parse_args().id

# Set up required user files:
try:
    logger.info(f"Creating default bot configuration for Telegram user {user_id}...")

    UserConfiguration(user_id).whitelist_user(is_admin=True)

    logger.info("Setup complete! You can now run the bot using the run.py script.")
except Exception as exc:
    logger.exception("An unexpected error occurred during setup", exc_info=exc)

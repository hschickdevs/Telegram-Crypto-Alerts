import argparse

from src._json_.json_struct_references import dump_config, dump_alerts_db_config
from src.custom_logger import logger

parser = argparse.ArgumentParser()
parser.add_argument('--id', type=str, required=True,
                    help='See how to get your TG user ID here: https://www.youtube.com/watch?v=W8ifn3ATpdA')

# Parse the argument
user_id = parser.parse_args().id

# Set up required json files:
try:
    logger.info('Setting up configuration database...')
    dump_config()

    logger.info('Setting up alerts database...')
    dump_alerts_db_config()

    logger.info("Setup complete! You can now run the bot using the run.py script.")
except Exception as exc:
    logger.exception("An unexpected error occurred during setup", exc_info=exc)

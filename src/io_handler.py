from os import mkdir, getcwd
from os.path import isdir, join, basename, dirname, abspath, isfile
import json

ALERTS_DB_PATH = join(dirname(__file__), '_json_/alerts_db.json')


def load_db() -> dict:
    """Loads the alerts database from _json_"""
    # Create alerts database if it does not already exist
    if not isfile(ALERTS_DB_PATH):
        with open(ALERTS_DB_PATH, 'w+') as database:
            database.write(json.dumps({}, indent=2))

    # Load the database contents and return it in JSON format
    with open(ALERTS_DB_PATH, 'r') as infile:
        return json.load(infile)


def update_db(data: dict) -> None:
    with open(ALERTS_DB_PATH, 'w') as outfile:
        outfile.write(json.dumps(data, indent=2))


# Create logs dir if it doesn't exist in the current working directory
def get_logfile() -> str:
    log_dir = join(getcwd(), 'logs')
    if not isdir(log_dir):
        mkdir(log_dir)
    return join(log_dir, 'log.txt')


# Get administrator users (these are hardcoded)
def get_administrators() -> list[str]:
    admins_file = join(dirname(abspath(__file__)), '_json_/administrators.json')
    with open(admins_file, 'r') as infile:
        return [admin for admin in json.loads(infile.read())['administrators']]

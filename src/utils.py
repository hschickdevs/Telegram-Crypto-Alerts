from os import mkdir, getcwd, getenv, listdir
from os.path import isdir, join, dirname, abspath, isfile, exists
from dotenv import find_dotenv, load_dotenv
from functools import wraps
from ratelimit import limits, sleep_and_retry
import re

from .config import *

""" -------------- UTILITIES -------------- """


def get_ratelimits() -> tuple:
    """Get the rate limits for the current tier"""
    return SUBSCRIPTION_TIERS[getenv("TAAPIIO_TIER", "free").lower()]


def get_logfile() -> str:
    """Get logfile path & create logs dir if it doesn't exist in the current working directory"""
    log_dir = join(getcwd(), "logs")
    if not isdir(log_dir):
        mkdir(log_dir)
    return join(log_dir, "log.txt")


def get_help_command() -> str:
    with open(
        join(dirname(abspath(__file__)), "resources/help_command.txt"), "r"
    ) as help_file:
        return help_file.read()


def handle_env():
    """Checks if the .env file exists in the current working dir, and imports the variables if so"""
    try:
        envpath = find_dotenv(raise_error_if_not_found=True, usecwd=True)
        load_dotenv(dotenv_path=envpath)
    except:
        pass
    finally:
        mandatory_vars = ["TELEGRAM_USER_ID", "TELEGRAM_BOT_TOKEN", "LOCATION"]
        for var in mandatory_vars:
            val = getenv(var)
            if val is None:
                raise ValueError(f"Missing environment variable: {var}")


def get_commands() -> dict:
    """Fetches the commands from the templates for the help command"""
    commands = {}

    # Define the path to the commands.txt file
    file_path = join(dirname(abspath(__file__)), "resources", "commands.txt")

    with open(file_path, "r") as f:
        for line in f.readlines():
            # Splitting at the first '-' to separate command and description
            command, description = line.strip().split(" - ", 1)
            commands[command.strip()] = description.strip()

    return commands


def get_binance_price_url() -> str:
    """Get the binance price url for the location"""
    location = getenv("LOCATION")
    assert (
        location in BINANCE_LOCATIONS
    ), f"Location must be in {BINANCE_LOCATIONS} for the Binance exchange."

    return (
        BINANCE_PRICE_URL_US
        if location.lower() == "us"
        else BINANCE_PRICE_URL_GLOBAL
    )


def parse_trigger_cooldown(cooldown_str: str = None) -> dict:
    """
    Parses a cooldown string like '30s', '5m', '1h' into seconds.
    If invalid, return None.

    :param cooldown_str: The cooldown string to parse
    :return: A dictionary with the cooldown seconds and last triggered time
    """
    if cooldown_str is None:
        return {"cooldown_seconds": None, "last_triggered": 0}

    match = re.match(r"^(\d+)([smh])$", cooldown_str.lower())
    if not match:
        raise ValueError(
            f"{cooldown_str} is an invalid cooldown format.\n"
            f'Format Options: [s, m, h], e.g. "1h"'
        )

    value, unit = match.groups()
    value = int(value)

    unit_multipliers = {"s": 1, "m": 60, "h": 3600}  # Seconds  # Minutes  # Hours

    return {
        "cooldown_seconds": max(value * unit_multipliers[unit], 5),
        "last_triggered": 0,
    }

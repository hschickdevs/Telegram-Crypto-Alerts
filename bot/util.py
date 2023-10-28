from os import mkdir, getcwd, getenv, listdir
from os.path import isdir, join, dirname, abspath, isfile, exists
import json
from dotenv import find_dotenv, load_dotenv
import yaml


""" -------------- UTILITIES -------------- """


def get_logfile() -> str:
    """Get logfile path & create logs dir if it doesn't exist in the current working directory"""
    log_dir = join(getcwd(), 'logs')
    if not isdir(log_dir):
        mkdir(log_dir)
    return join(log_dir, 'log.txt')


def get_help_command() -> str:
    with open(join(dirname(abspath(__file__)), 'resources/help_command.txt'), 'r') as help_file:
        return help_file.read()


def load_swap_networks() -> dict:
    with open(join(dirname(__file__), "blockchain", "mappings", "networks.yml"), "r") as f:
        return yaml.safe_load(f)


def load_swap_protocols() -> dict:
    with open(join(dirname(__file__), "blockchain", "mappings", "protocols.yml"), "r") as f:
        return yaml.safe_load(f)


def handle_env():
    """Checks if the .env file exists in the current working dir, and imports the variables if so"""
    try:
        envpath = find_dotenv(raise_error_if_not_found=True, usecwd=True)
        load_dotenv(dotenv_path=envpath)
    except:
        pass
    finally:
        mandatory_vars = ['TELEGRAM_BOT_TOKEN']
        for var in mandatory_vars:
            val = getenv(var)
            if val is None:
                raise ValueError(f"Missing environment variable: {var}")
from os import mkdir, getcwd, getenv, listdir
from os.path import isdir, join, dirname, abspath, isfile, exists
import json
from dotenv import find_dotenv, load_dotenv
import shutil

from .static_config import *


class UserConfiguration:
    """Simplifies interaction with the json database system"""

    def __init__(self, tg_user_id: str):
        """
        :param tg_user_id: The Telegram user ID of the bot user to locate their configuration
        """
        self.user_id = tg_user_id
        self.user_config_root = join(WHITELIST_ROOT, f'{self.user_id}')
        self.config_path = join(WHITELIST_ROOT, f'{self.user_id}', 'config.json')
        self.alerts_path = join(WHITELIST_ROOT, f'{self.user_id}', 'alerts.json')

        # Should be changed to allow user to use new alert template later
        self.email_template_path = join(RESOURCES_ROOT, 'email_template.html')

        # Utility Paths:
        self.default_alerts_path = join(RESOURCES_ROOT, 'default_alerts.json')
        self.default_config_path = join(RESOURCES_ROOT, 'default_config.json')

    def whitelist_user(self, is_admin: bool = False):
        """Add necessary files and directories to database for TG user ID"""

        # Return if user data directory already exists
        if self.user_id in get_whitelist():
            return

        # Make root dir
        mkdir(self.user_config_root)

        try:
            # Make default configuration:
            with open(self.default_config_path, 'r') as _in:
                default_config = json.load(_in)
            default_config["channels"].append(self.user_id)
            if is_admin:
                default_config["is_admin"] = True
            with open(self.config_path, 'w') as _out:
                _out.write(json.dumps(default_config, indent=2))

            # Make default alerts configuration
            shutil.copy(self.default_alerts_path, self.alerts_path)
        except Exception as exc:
            self.blacklist_user()
            raise exc

    def blacklist_user(self):
        """Remove TG user configuration from database"""

        # Removes user configuration recursively
        if exists(self.user_config_root):
            shutil.rmtree(self.user_config_root)

    def load_alerts(self) -> dict:
        """Load the database contents and return it in JSON format"""
        with open(self.alerts_path, 'r') as infile:
            return json.load(infile)

    def update_alerts(self, data: dict) -> None:
        with open(self.alerts_path, 'w') as outfile:
            outfile.write(json.dumps(data, indent=2))

    def load_config(self) -> dict:
        with open(self.config_path, 'r') as infile:
            return json.load(infile)

    def update_config(self, data: dict) -> None:
        with open(self.config_path, 'w') as outfile:
            outfile.write(json.dumps(data, indent=2))

    def admin_status(self, new_value: bool = None) -> bool:
        config = self.load_config()
        if new_value is not None:
            config['is_admin'] = new_value
            self.update_config(config)
        return config['is_admin']

    def get_emails(self) -> list[str]:
        return self.load_config()['emails']

    def add_emails(self, emails: list[str]) -> None:
        config = self.load_config()
        for email in emails:
            if email not in config['emails']:
                config['emails'].append(email)
        self.update_config(config)

    def remove_emails(self, emails: list[str]) -> list[str]:
        """Attempts to remove emails from config, and returns fails"""
        config = self.load_config()
        fail = []
        for email in emails:
            if email in config['emails']:
                config['emails'].remove(email)
            else:
                fail.append(email)
        self.update_config(config)
        return fail

    def get_channels(self) -> list[str]:
        return self.load_config()['channels']

    def add_channels(self, channels: list[str]) -> None:
        config = self.load_config()
        for channel in channels:
            if channel not in config['channels']:
                config['channels'].append(channel)
        self.update_config(config)

    def remove_channels(self, channels: list[str]) -> list[str]:
        """Attempts to remove channels from config, and returns fails"""
        config = self.load_config()
        fail = []
        for channel in channels:
            if channel in config['channels']:
                config['channels'].remove(channel)
            else:
                fail.append(channel)
        self.update_config(config)
        return fail

    def get_email_template(self) -> str:
        with open(self.email_template_path, 'r') as template:
            return template.read()


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


def get_whitelist() -> list:
    if not isdir(WHITELIST_ROOT):
        mkdir(WHITELIST_ROOT)

    return [_id for _id in listdir(WHITELIST_ROOT) if isdir(join(WHITELIST_ROOT, _id))]


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

from os import mkdir, getcwd, getenv
from os.path import isdir, join, dirname, abspath, isfile
import json
from dotenv import find_dotenv, load_dotenv


class ConfigHandler:
    """Creates functionality to simplify interaction with the json database system"""

    def __init__(self):
        self.alerts_path = join(dirname(__file__), '_json_/alerts_db.json')
        self.config_path = join(dirname(abspath(__file__)), '_json_/config.json')
        self.help_path = join(dirname(abspath(__file__)), 'templates/help_command.txt')
        self.email_template_path = join(dirname(abspath(__file__)), 'templates/email_template.html')

    def load_alerts(self) -> dict:
        """Loads the alerts database from _json_/alerts_db.json"""
        # Create alerts database if it does not already exist
        if not isfile(self.alerts_path):
            with open(self.alerts_path, 'w+') as database:
                database.write(json.dumps({}, indent=2))

        # Load the database contents and return it in JSON format
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

    def get_administrators(self) -> list[str]:
        with open(self.config_path, 'r') as infile:
            return json.loads(infile.read())['administrators']

    def add_administrators(self, ids: list[str]) -> None:
        config = self.load_config()
        for tg_id in ids:
            if tg_id not in config['administrators']:
                config['administrators'].append(tg_id)
        self.update_config(config)

    def remove_administrators(self, ids: list[str]) -> list[str]:
        """Attempts to remove administrators from config, and returns fails"""
        config = self.load_config()
        fail = []
        for tg_id in ids:
            if tg_id in config['administrators']:
                config['administrators'].remove(tg_id)
            else:
                fail.append(tg_id)
        self.update_config(config)
        return fail

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

    def get_help_command(self) -> str:
        with open(self.help_path, 'r') as help_file:
            return help_file.read()

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

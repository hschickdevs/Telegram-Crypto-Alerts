import time
from datetime import datetime
from typing import Union
from os import getenv

from .logger import logger
from .user_configuration import (
    LocalUserConfiguration,
    MongoDBUserConfiguration,
    get_whitelist,
)
from .utils import (
    get_logfile,
    get_help_command,
    get_commands,
    get_binance_price_url,
    parse_trigger_cooldown,
)
from .config import *
from .indicators import TADatabaseClient, TaapiioProcess
from .models import TechnicalAlert, CEXAlert

from telebot import TeleBot, types
import requests
from requests.exceptions import ReadTimeout

BaseConfig = LocalUserConfiguration if not USE_MONGO_DB else MongoDBUserConfiguration


class TelegramBot(TeleBot):
    def __init__(self, bot_token: str, taapiio_process: TaapiioProcess = None):
        super().__init__(token=bot_token)
        self.binance_price_endpoint = get_binance_price_url()
        self.taapiio_cli = None
        self.indicators_ref_cli = TADatabaseClient()
        self.indicators_db = self.indicators_ref_cli.fetch_ref()
        if taapiio_process is None:
            logger.warning(
                "Taapi.io APIKEY not set - Technical indicator requests will be unavailable."
            )
        else:
            self.taapiio_cli = taapiio_process

        # Set the bot commands:
        logger.info("Setting bot commands ...")
        user_commands = [
            types.BotCommand(command=command, description=description)
            for command, description in get_commands().items()
        ]
        self.set_my_commands(user_commands)

        @self.message_handler(commands=["id"])
        def on_id(message):
            """Public function to return someone's Telegram user ID"""
            self.reply_to(
                message,
                f"{message.from_user.username}'s Telegram ID:\n{message.from_user.id}",
            )

        @self.message_handler(commands=["help"])
        @self.is_whitelisted
        def on_help(message):
            self.reply_to(message, get_help_command())

        @self.message_handler(commands=["new_alert", "newalert"])
        @self.is_whitelisted
        def on_new_alert(message):
            """/new_alert PAIR/PAIR INDICATOR TARGET optional_COOLDOWN"""
            simple_indicators = ["PRICE", "24HRCHG"]
            technical_indicators = list(self.indicators_db.keys())
            try:
                msg = self.split_message(message.text)
                indicator = msg[1].upper()
                if indicator in simple_indicators:
                    # Verify accurate formatting:
                    pair, indicator, comparison, target = msg[0], msg[1], msg[2], msg[3]

                    indicator_instance = self.parse_simple_indicator_message(
                        message.text
                    )
                elif indicator in technical_indicators:
                    if self.taapiio_cli is None:
                        self.reply_to(
                            message,
                            "Technical alerts are currently unavailable. Set the environment variable `TAAPIIO_APIKEY` to enable.",
                            parse_mode="Markdown",
                        )
                        return

                    self.reply_to(
                        message,
                        "Attempting to verify parameters with taapi.io and add alert to database...",
                    )

                    # Verify accurate formatting:
                    (
                        pair,
                        indicator,
                        interval,
                        params,
                        output_value,
                        comparison,
                        target,
                    ) = msg

                    # Verify indicator:
                    indicator_instance = self.parse_technical_indicator_message(
                        message.text
                    )
                    if indicator_instance is None:
                        self.reply_to(
                            message,
                            "Could not match passed parameters to valid technical indicator in the database.\n"
                            "Please check your formatting with `/indicators`",
                            parse_mode="Markdown",
                        )
                        return

                    # Verify that no errors are returned by the indicator on taapi.io:
                    try:
                        r = self.get_technical_indicator(indicator_instance)
                        if output_value not in r.keys():
                            self.reply_to(
                                message, f"Invalid output value - Options: {r.keys()}"
                            )
                            return
                    except Exception as exc:
                        self.reply_to(
                            message,
                            f"Database match found, but an error occurred with taapi.io:\n"
                            f"{str(exc)}\n"
                            f"The parameters passed were most likely invalid.",
                        )
                        return
                else:
                    self.reply_to(
                        message,
                        f"Invalid indicator. Valid indicators: {simple_indicators + technical_indicators}",
                    )
                    return

            except AssertionError as exc:
                self.reply_to(
                    message, "<b>Assertion Error:</b>\n" f"{exc}", parse_mode="HTML"
                )
                return
            except Exception as exc:
                self.reply_to(
                    message,
                    "Invalid message formatting.\n"
                    "Please verify that your request follows the format corresponding to your desired indicator type:\n"
                    "\n<b>Simple Indicator:</b>\n"
                    "/new_alert PAIR/PAIR INDICATOR COMPARISON TARGET optional_COOLDOWN\n"
                    "\n<b>Technical Indicator:</b>\n"
                    "/new_alert BASE/QUOTE INDICATOR TIMEFRAME PARAMS OUTPUT_VALUE COMPARISON TARGET optional_COOLDOWN\n"
                    "\nUse the /help command for more information on command formatting.",
                    parse_mode="HTML",
                )
                return

            try:
                configuration = BaseConfig(str(message.from_user.id))
                alerts_db = configuration.load_alerts()

                if MAX_ALERTS_PER_USER is not None:
                    if (
                        sum(len(alerts) for alerts in alerts_db.values())
                        >= MAX_ALERTS_PER_USER
                    ):
                        raise OverflowError(
                            f"Maximum active alerts reached ({MAX_ALERTS_PER_USER})"
                        )

                if indicator_instance.type == "s":
                    # Handle simple indicator:
                    comparison = msg[2].upper()
                    target = (
                        float(msg[3].strip())
                        if comparison not in ["PCTCHG", "24HRCHG"]
                        else float(msg[3].strip()) / 100
                    )
                    try:
                        entry_price = self.get_latest_binance_price(pair)
                    except Exception as exc:
                        self.reply_to(
                            message,
                            f"{str(exc)}\n"
                            "Please verify that your pair is listed on binance and follows the "
                            "format: TOKEN1/TOKEN2",
                        )
                        return
                    trigger = parse_trigger_cooldown(msg[4] if len(msg) > 4 else None)

                    alert = {
                        "type": indicator_instance.type,
                        "indicator": indicator_instance.indicator.upper(),
                        "comparison": comparison,
                        "entry": entry_price,
                        "target": target,
                        "params": indicator_instance.params,
                        "trigger": trigger,
                    }
                else:
                    # Handle technical indicator:
                    output_value = msg[4]
                    comparison = msg[5].upper()
                    target = float(msg[6])
                    trigger = parse_trigger_cooldown(msg[7] if len(msg) > 7 else None)
                    alert = {
                        "type": indicator_instance.type,
                        "indicator": indicator_instance.indicator.upper(),
                        "comparison": comparison,
                        "interval": indicator_instance.interval,
                        "params": indicator_instance.params,
                        "output_value": output_value,
                        "target": target,
                        "trigger": trigger,
                    }

                if pair in alerts_db.keys():
                    alerts_db[pair].append(alert)
                else:
                    alerts_db[pair] = [alert]
                configuration.update_alerts(alerts_db)
                self.reply_to(message, f"Successfully activated new alert!")
            except Exception as exc:
                self.reply_to(message, f"An error occurred:\n{exc}")
                return

        @self.message_handler(commands=["cancel_alert", "cancelalert"])
        @self.is_whitelisted
        def on_cancel_alert(message):
            """/cancel_alert PAIR/PAIR alert_index"""
            try:
                pair, alert_index = self.split_message(message.text)
                pair = pair.upper()
                alert_index = int(alert_index)
            except Exception as exc:
                self.reply_to(
                    message,
                    f"Invalid message formatting. Please ensure that your message follows this format:\n"
                    f"/cancel_alert TOKEN1/TOKEN2 alert_index",
                )
                return

            try:
                configuration = BaseConfig(str(message.from_user.id))
                alerts_db = configuration.load_alerts()
                rm_alert = alerts_db[pair].pop(alert_index - 1)
                all_rm = False
                if len(alerts_db[pair]) == 0:
                    rm_pair = alerts_db.pop(pair)
                    all_rm = True
                configuration.update_alerts(alerts_db)
                self.reply_to(
                    message,
                    f"Successfully Canceled {pair} Alert:\n"
                    f'{rm_alert}{f" (All alerts canceled for {pair})" if all_rm else ""}',
                )
            except Exception as exc:
                self.reply_to(
                    message,
                    f"An error occurred when trying to cancel the alert:\n{exc}",
                )

        @self.message_handler(commands=["view_alerts", "viewalerts"])
        @self.is_whitelisted
        def on_view_alerts(message):
            """/view_alerts PAIR (<- optional)"""
            try:
                alerts_pair = self.split_message(message.text)[0].upper()
            except IndexError:
                alerts_pair = "ALL"

            configuration = BaseConfig(str(message.from_user.id))
            alerts_db = configuration.load_alerts()
            output = ""
            for ticker in alerts_db.keys():
                if ticker == alerts_pair or alerts_pair == "ALL":
                    output += f"<b>{ticker}:</b>"
                    for index, alert in enumerate(alerts_db[ticker]):
                        output += f"\n    {index + 1} - {alert['indicator']} "
                        if "output_value" in alert.keys():
                            output += f"({alert['output_value']}) "
                        if "interval" in alert.keys():
                            output += f"{alert['interval']} "
                        output += f"{alert['comparison']} "
                        output += f"{str(alert['target'] * 100) + '% FROM ' + str(alert['entry']) if alert['comparison'] in ['PCTCHG', '24HRCHG'] else alert['target']} "
                        if (
                            "params" in alert.keys()
                            and alert["params"] is not None
                            and len(alert["params"]) > 0
                        ):
                            output += f"with params: {alert['params']}"

                    output += "\n\n"
            self.reply_to(
                message,
                output if len(output) > 0 else "Found 0 matching alerts.",
                parse_mode="HTML",
            )

        @self.message_handler(commands=["get_price", "getprice"])
        @self.is_whitelisted
        def on_get_price(message):
            """/get_price PAIR/PAIR"""
            try:
                pair = self.split_message(message.text)[0]
            except:
                self.reply_to(
                    message,
                    f"Invalid message formatting. Please use the following format:\n"
                    f"/get_price TOKEN1/TOKEN2",
                )
                return
            try:
                self.reply_to(
                    message,
                    f'{pair}: {self.get_latest_binance_price(pair.replace("/", "").upper())}',
                )
            except Exception as exc:
                self.reply_to(message, str(exc))

        @self.message_handler(commands=["get_indicator", "getindicator"])
        @self.is_whitelisted
        def on_get_indicator(message):
            """/get_indicator BASE/QUOTE INTERVAL TIMEFRAME kwarg,kwarg"""
            if self.taapiio_cli is None:
                self.reply_to(
                    message,
                    "Technical indicators are currently unavailable. Set the environment variable `TAAPIIO_APIKEY` to enable.",
                    parse_mode="Markdown",
                )
                return

            indicator = self.parse_technical_indicator_message(message.text)
            if indicator is None:
                self.reply_to(
                    message,
                    "Could not match indicator and parameters to valid indicator in the reference.\n"
                    "Please check your parameters and formatting - See /indicators",
                )
                return

            self.reply_to(message, "Fetching indicator, please wait...")
            try:
                r = self.get_technical_indicator(indicator)
            except Exception as exc:
                self.reply_to(message, str(exc))
                return

            msg = ""
            for k, v in r.items():
                if type(v) is float:
                    v = round(v, OUTPUT_VALUE_PRECISION)
                msg += f"<b>{k}:</b> {v}\n"
            self.reply_to(message, msg, parse_mode="HTML")

        @self.message_handler(commands=["price_all", "priceall"])
        @self.is_whitelisted
        def on_price_all(message):
            """/price_all - Gets the price of all tokens with alerts set"""
            configuration = BaseConfig(str(message.from_user.id))
            tokens = [
                f'{key}: {self.get_latest_binance_price(key.replace("/", "").upper())}'
                for key in configuration.load_alerts().keys()
            ]
            try:
                self.reply_to(message, "\n".join(tokens))
            except Exception as exc:
                self.reply_to(message, f"Error: {str(exc)}")

        @self.message_handler(commands=["indicators"])
        @self.is_whitelisted
        def on_indicators(message):
            """/indicators"""
            # Add the simple price indicator:
            output = "<u><b>Simple Indicators:</b></u>\n"
            output += (
                "<a href='https://github.com/hschickdevs/Telegram-Crypto-Alerts/tree/main#alerts'><b>PRICE</b></a> (Token Pair Spot Price):\n"
                f"   • <u>Available Comparisons:</u>\n"
            )
            for comparison in SIMPLE_INDICATOR_COMPARISONS:
                output += f"      - <b><i>{comparison}</i></b>\n"

            # Build technical indicators reference:
            output += "\n<u><b>Technical Indicators:</b></u>\n"
            for indicator, data in self.indicators_db.items():
                output += (
                    f"<a href='{data['ref']}'><b>{indicator}</b></a> ({data['name']}):\n"
                    f"   • <u>Available Params:</u>\n"
                )
                for param, desc, default in data["params"]:
                    output += (
                        f"      - <b><i>{param}:</i></b> {desc} (Default = {default})\n"
                    )
                output += f"   • <u>Available Outputs:</u>\n"
                for output_val in data["output"]:
                    output += f"      - <b><i>{output_val}</i></b>\n"
                output += "\n"

            self.reply_to(
                message, output, parse_mode="HTML", disable_web_page_preview=True
            )

        @self.message_handler(commands=["view_config", "viewconfig"])
        @self.is_whitelisted
        def on_view_config(message):
            """Returns the current configuration of the bot (used as reference for /set_config)"""
            try:
                configuration = BaseConfig(str(message.from_user.id))
                config = configuration.load_config()["settings"]
                msg = f"{message.from_user.username} {self.get_me().first_name} Configuration:\n\n"
                for k, v in config.items():
                    # msg += f"{key.strip()} settings:\n"
                    # for k, v in variables.items():
                    msg += f"{k}={v}\n"
                    # msg += '\n'
                self.reply_to(message, msg)
            except Exception as exc:
                logger.exception("Could not call /view_config", exc_info=exc)
                self.reply_to(message, str(exc))

        @self.message_handler(commands=["set_config", "setconfig"])
        @self.is_whitelisted
        def on_set_config(message):
            """Used to change configuration variables of the bot"""
            msg = ""
            failed = []
            user_id = str(message.from_user.id)
            configuration = BaseConfig(user_id)
            full_config = configuration.load_config()
            try:
                config = full_config["settings"]
                for change in self.split_message(message.text):
                    try:
                        conf, val = change.split("=")

                        # Account for bool case:
                        if val.lower() == "true" or val.lower() == "false":
                            val = val.lower() == "true"

                        try:
                            var_type = type(config[conf])
                        except KeyError:
                            raise KeyError(
                                f"{conf} does not match any available config settings in database."
                            )

                        # Attempt to push the config update to the database:
                        config[conf] = var_type(val)

                        msg += f"{conf} set to {val}\n"
                        logger.info(f"{user_id}: {conf} set to {val} ({var_type})\n")
                    except Exception as exc:
                        failed.append((change, str(exc)))
                        continue

                full_config["settings"] = config
                configuration.update_config(full_config)

                if len(msg) > 0:
                    self.reply_to(message, "Successfully set configuration:\n\n" + msg)

                if len(failed) > 0:
                    fail_msg = "Failed to set:\n\n"
                    for fail in failed:
                        fail_msg += f"- {fail[0]} (Error: {fail[1]})\n"
                    self.reply_to(message, fail_msg)
            except Exception as exc:
                logger.exception("Could not set config", exc_info=exc)
                self.reply_to(message, str(exc))

        @self.message_handler(commands=["channels"])
        @self.is_whitelisted
        def on_channels(message):
            splt_msg = self.split_message(message.text)
            try:
                configuration = BaseConfig(str(message.from_user.id))
                if splt_msg[0].lower() == "add":
                    new_channels = splt_msg[1].split(",")
                    configuration.add_channels(new_channels)
                    self.reply_to(
                        message,
                        f"Successfully added channel(s): {', '.join(new_channels)}",
                    )
                elif splt_msg[0].lower() == "remove":
                    rm_channels = splt_msg[1].split(",")
                    fails = configuration.remove_channels(rm_channels)
                    if len(fails) > 0:
                        self.reply_to(
                            message, f"Failed to remove channel(s): {', '.join(fails)}"
                        )

                    self.reply_to(
                        message,
                        f"Successfully removed channel(s): "
                        f"{', '.join([channel for channel in rm_channels if channel not in fails])}",
                    )
                else:
                    channels = configuration.get_channels()
                    if len(channels) == 0:
                        self.reply_to(
                            message,
                            "No channels registered. Use /channels ADD ID,ID,ID",
                        )
                        return

                    msg = "Current Alert Channels:\n\n"
                    for channel in channels:
                        msg += f"{channel}\n"
                    self.reply_to(message, msg)
            except IndexError:
                self.reply_to(
                    message,
                    "Invalid formatting - Use /channels VIEW/ADD/REMOVE ID,ID,ID",
                )
            except Exception as exc:
                self.reply_to(message, f"An unexpected error occurred - {exc}")

        """------ ADMINISTRATOR COMMANDS: ------"""

        @self.message_handler(commands=["whitelist"])
        @self.is_admin
        def on_whitelist(message):
            splt_msg = self.split_message(message.text)
            try:
                if splt_msg[0].lower() == "add":
                    new_users = splt_msg[1].split(",")
                    for user in new_users:
                        BaseConfig(user).whitelist_user()
                    self.reply_to(message, f"Whitelisted Users: {', '.join(new_users)}")
                elif splt_msg[0].lower() == "remove":
                    rm_users = splt_msg[1].split(",")
                    for user in rm_users:
                        BaseConfig(user).blacklist_user()
                    self.reply_to(
                        message, f"Removed Users from Whitelist: {', '.join(rm_users)}"
                    )
                else:
                    msg = "Current Whitelist:\n\n"
                    for user_id in get_whitelist():
                        msg += f"{user_id}\n"
                    self.reply_to(message, msg)
            except IndexError:
                self.reply_to(
                    message,
                    "Invalid formatting - Use /whitelist VIEW/ADD/REMOVE TG_USER_ID,TG_USER_ID",
                )
            except Exception as exc:
                self.reply_to(message, f"An unexpected error occurred - {exc}")

        @self.message_handler(commands=["get_logs", "getlogs"])
        @self.is_admin
        def on_get_logs(message):
            """Returns the program's logs at logs/logs.txt"""
            try:
                with open(get_logfile(), "rb") as logfile:
                    if len(logfile.read()) > 0:
                        self.reply_to(message, "Fetching logs...")
                        try:
                            self.send_document(message.chat.id, logfile)
                        except Exception as exc:
                            self.reply_to(message, f"An error occurred - {exc}")
                    else:
                        self.reply_to(
                            message,
                            "Logfile exists, but no logs have been recorded yet.",
                        )
            except Exception as exc:
                self.reply_to(message, f"Could not fetch logs - {str(exc)}")

        @self.message_handler(commands=["admins"])
        @self.is_admin
        def on_admins(message):
            splt_msg = self.split_message(message.text)
            try:
                whitelist = get_whitelist()
                if splt_msg[0].lower() == "add":
                    new_admins = splt_msg[1].split(",")
                    failure_msgs = []
                    for i, new_admin in enumerate(new_admins):
                        try:
                            if new_admin in whitelist:
                                BaseConfig(new_admin).admin_status(new_value=True)
                            else:
                                failure_msgs.append(
                                    f"{new_admins.pop(i)} - User is not yet whitelisted"
                                )
                        except Exception as exc:
                            failure_msgs.append(f"{new_admins.pop(i)} - {exc}")
                    msg = (
                        f"Successfully added administrator(s): {', '.join(new_admins)}"
                    )
                    if len(failure_msgs) > 0:
                        msg += "\n\nFailed to add administrator(s):"
                        for fail_msg in failure_msgs:
                            msg += f"\n{fail_msg}"
                    self.reply_to(message, msg)
                elif splt_msg[0].lower() == "remove":
                    rm_admins = splt_msg[1].split(",")
                    failure_msgs = []
                    for i, admin in enumerate(rm_admins):
                        try:
                            if admin in whitelist:
                                BaseConfig(admin).admin_status(new_value=False)
                            else:
                                failure_msgs.append(
                                    f"{rm_admins.pop(i)} - User is not yet whitelisted"
                                )
                        except Exception as exc:
                            failure_msgs.append(f"{rm_admins.pop(i)} - {exc}")
                    msg = (
                        f"Successfully revoked administrator(s): {', '.join(rm_admins)}"
                    )
                    if len(failure_msgs) > 0:
                        msg += "\n\nFailed to revoke administrator(s):"
                        for fail_msg in failure_msgs:
                            msg += f"\n{fail_msg}"
                    self.reply_to(message, msg)
                else:
                    msg = "Current Administrators:\n\n"
                    for user_id in get_whitelist():
                        if BaseConfig(user_id).admin_status():
                            msg += f"{user_id}\n"
                    self.reply_to(message, msg)
            except IndexError:
                self.reply_to(
                    message,
                    "Invalid formatting - Use /admins VIEW/ADD/REMOVE USER_ID,USER_ID",
                )
            except Exception as exc:
                self.reply_to(message, f"An unexpected error occurred - {exc}")

    def split_message(self, message: str, convert_type=None) -> list:
        return [
            chunk.strip() if convert_type is None else convert_type(chunk.strip())
            for chunk in message.split(" ")[1:]
            if not all(char == " " for char in chunk) and len(chunk) > 0
        ]

    def is_whitelisted(self, func):
        """
        (Decorator) Checks if the user is an administrator before proceeding with the function

        :param func: PyTelegramBotAPI message handler function, with the 'message' class as the first argument
        """

        def wrapper(*args, **kw):
            message = args[0]
            if str(message.from_user.id) in get_whitelist():
                return func(*args, **kw)
            else:
                self.reply_to(
                    message,
                    f"{message.from_user.username} ({message.from_user.id}) is not whitelisted",
                )
                return False

        return wrapper

    def is_admin(self, func):
        """
        (Decorator) Checks if the user is an administrator before calling the function

        :param func: PyTelegramBotAPI message handler function, with the 'message' class as the first argument
        """

        def wrapper(*args, **kw):
            message = args[0]
            if BaseConfig(str(message.from_user.id)).admin_status():
                return func(*args, **kw)
            else:
                self.reply_to(
                    message,
                    f"{message.from_user.username} ({message.from_user.id}) is not an admin",
                )
                return False

        return wrapper

    def get_latest_binance_price(self, pair):
        try:
            response = requests.get(
                self.binance_price_endpoint.format(
                    pair.replace("/", ""), BINANCE_TIMEFRAMES[0]
                )
            )
            # response = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={pair.replace("/", "")}')
            try:
                return round(float(response.json()["lastPrice"]), 3)
            except KeyError:
                raise ValueError(
                    f"{pair} is not a valid pair.\n" f"API Response: {response.json()}"
                )
        except KeyError:
            raise ValueError(
                f"{pair} is not a valid pair.\n"
                f"Please make sure to use this formatting: TOKEN1/TOKEN2"
            )
        except Exception as exc:
            logger.exception(
                f"An unexpected error occurred when trying to fetch the binance price of {pair}",
                exc_info=exc,
            )
            raise Exception(
                f"An unexpected error has occurred when trying to fetch the price of {pair} on Binance - {exc}"
            )

    def get_technical_indicator(self, indicator: TechnicalAlert) -> dict:
        # Message should first be parsed, and have the technical indicator returned.

        # Prepare the params for the taapi.io single call GET request:
        params = indicator.params
        params["symbol"] = indicator.pair
        params["interval"] = indicator.interval

        # Call the taapi.io API to get the indicator values:
        endpoint = indicator.endpoint.format(api_key=self.taapiio_cli.apikey)
        r = self.taapiio_cli.call_api(endpoint, params, "GET")
        try:
            return {output_val: r[output_val] for output_val in indicator.output_vals}
        except Exception as exc:
            err_msg = f"Could not get technical indicator: {str(exc)}"
            if "errors" in r.keys():
                err_msg += f" - {r['errors']}"
            if "error" in r.keys():
                err_msg += f" - {r['error']}"
            raise Exception(err_msg)

    def parse_technical_indicator_message(
        self, message: str
    ) -> Union[TechnicalAlert, None]:
        """
        Message should follow the following format:
        /get_indicator BASE/QUOTE INDICATOR TIMEFRAME kwarg,kwarg
        The "kwarg" parameter guide:
            - For indicator parameters: param_name=value,param_name=value
            - For selection output values: output=output_value_name
            - Note: You can combine these: param_name=value,output=output_value_name

        :returns: A TechnicalIndicator object instance if params are valid, else None
            - pair
            - indicator
            - interval
            - params
            - output
        """
        splt_msg = self.split_message(message)
        pair = splt_msg[0]
        indicator_id = splt_msg[1].upper()
        interval = splt_msg[2].lower()
        try:
            args = splt_msg[3]
            if args.lower() == "default":
                args = None
        except IndexError:
            args = None

        # Parse args
        params = {}
        output = []
        if args is not None:
            splt_args = args.split(",")
            for arg in splt_args:
                param, val = arg.split("=")
                if param == "output":
                    output.append(val)
                else:
                    params[param] = val

        # Validate indicator with reference:
        indicator = self.indicators_ref_cli.validate_indicator(indicator_id, args)
        if indicator is None:
            return None

        # Add default/missing values to params and output:
        for param, desc, default in indicator["params"]:
            if param not in params.keys():
                params[param] = default
        if len(output) == 0:
            output = indicator["output"]

        # This should be done if a single (not bulk) request needs to be made to the API
        # params["symbol"] = pair
        # params["interval"] = interval

        return TechnicalAlert(
            pair,
            indicator_id,
            interval,
            params,
            output,
            indicator["endpoint"],
            indicator["name"],
        )

    def parse_simple_indicator_message(self, message: str) -> CEXAlert:
        msg = self.split_message(message)
        pair = msg[0].upper()
        indicator = msg[1].upper()
        comparison = msg[2].upper()
        assert comparison in SIMPLE_INDICATOR_COMPARISONS, (
            f"{comparison} is an invalid simple indicator comparison operator.\n"
            f"Options: {SIMPLE_INDICATOR_COMPARISONS}"
        )

        return CEXAlert(pair, indicator)

    def run(self):
        logger.warn(f"{self.get_me().username} started at {datetime.utcnow()} UTC+0")
        while True:
            try:
                self.polling(non_stop=True)
            except KeyboardInterrupt:
                break
            except ReadTimeout:
                logger.error(
                    "Bot has crashed due to read timeout - Restarting in 5 seconds..."
                )
                time.sleep(5)
            except Exception as exc:
                logger.critical(
                    f"Unexpected error has occurred while polling - Retrying in 30 seconds...",
                    exc_info=exc,
                )
                time.sleep(30)

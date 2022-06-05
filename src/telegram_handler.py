import time
from datetime import datetime

from .custom_logger import logger
from .io_client import UserConfiguration, get_logfile, get_help_command, get_whitelist
from .static_config import MAX_ALERTS_PER_USER

from telebot import TeleBot
import requests
from requests.exceptions import ReadTimeout


class TelegramBot(TeleBot):
    def __init__(self, bot_token: str):
        super().__init__(token=bot_token)

        @self.message_handler(commands=['id'])
        def on_id(message):
            """Public function to return someone's Telegram user ID"""
            self.reply_to(message, f"{message.from_user.username}'s Telegram ID:\n{message.from_user.id}")

        @self.message_handler(commands=['help'])
        @self.is_whitelisted
        def on_help(message):
            self.reply_to(message, get_help_command())

        @self.message_handler(commands=['newalert'])
        @self.is_whitelisted
        def on_new_alert(message):
            """/newalert PAIR/PAIR INDICATOR TARGET optional_ENTRY_PRICE"""
            acceptable_indicators = ['ABOVE', 'BELOW', 'PCTCHG']
            try:
                msg = self.split_message(message.text)
                pair = msg[0].upper()
                indicator = msg[1].upper()
                if indicator not in acceptable_indicators:
                    self.reply_to(message,
                                  f'Invalid indicator. Valid indicators: {acceptable_indicators}')
                    return
                target = float(msg[2].strip()) if indicator != "PCTCHG" else float(msg[2].strip()) / 100
            except:
                self.reply_to(message,
                              'Invalid message formatting.\nPlease verify that your request follows the format:\n'
                              '/newalert PAIR/PAIR INDICATOR TARGET optional_ENTRY_PRICE')
                return

            try:
                configuration = UserConfiguration(str(message.from_user.id))
                alerts_db = configuration.load_alerts()

                if MAX_ALERTS_PER_USER is not None:
                    if sum(len(alerts) for alerts in alerts_db.values()) >= MAX_ALERTS_PER_USER:
                        raise OverflowError(f"Maximum active alerts reached ({MAX_ALERTS_PER_USER})")

                if len(msg) > 3:
                    entry_price = msg[3]
                else:
                    try:
                        entry_price = self.get_binance_price(pair)
                    except Exception as exc:
                        self.reply_to(message, f"{str(exc)}\n"
                                               "Please verify that your pair is listed on binance and follows the "
                                               "format: TOKEN1/TOKEN2")
                        return

                if pair in alerts_db.keys():
                    alerts_db[pair].append(
                        {"indicator": indicator, "entry": entry_price, "target": target, "alerted": False})
                else:
                    alerts_db[pair] = [
                        {"indicator": indicator, "entry": entry_price, "target": target, "alerted": False}]
                configuration.update_alerts(alerts_db)
                self.reply_to(message, f'Successfully activated new alert!')
            except Exception as exc:
                self.reply_to(message,
                              f'An error occurred:\n{exc}')
                return

        @self.message_handler(commands=['cancelalert'])
        @self.is_whitelisted
        def on_cancel_alert(message):
            """/cancelalert PAIR/PAIR alert_index"""
            try:
                pair, alert_index = self.split_message(message.text)
                pair = pair.upper()
                alert_index = int(alert_index)
            except Exception as exc:
                self.reply_to(message,
                              f'Invalid message formatting. Please ensure that your message follows this format:\n'
                              f'/cancelalert TOKEN1/TOKEN2 alert_index')
                return

            try:
                configuration = UserConfiguration(str(message.from_user.id))
                alerts_db = configuration.load_alerts()
                rm_alert = alerts_db[pair].pop(alert_index - 1)
                all_rm = False
                if len(alerts_db[pair]) == 0:
                    rm_pair = alerts_db.pop(pair)
                    all_rm = True
                configuration.update_alerts(alerts_db)
                self.reply_to(message, f'Successfully Canceled {pair} Alert:\n'
                                       f'{rm_alert}{f" (All alerts canceled for {pair})" if all_rm else ""}')
            except Exception as exc:
                self.reply_to(message, f'An error occurred when trying to cancel the alert:\n{exc}')

        @self.message_handler(commands=['viewalerts'])
        @self.is_whitelisted
        def on_view_alerts(message):
            """/viewalerts PAIR (<- optional)"""
            try:
                alerts_pair = self.split_message(message.text)[0].upper()
            except IndexError:
                alerts_pair = "ALL"

            configuration = UserConfiguration(str(message.from_user.id))
            alerts_db = configuration.load_alerts()
            output = ""
            for ticker in alerts_db.keys():
                if ticker == alerts_pair or alerts_pair == "ALL":
                    output += f"{ticker}:"
                    for index, alert in enumerate(alerts_db[ticker]):
                        output += f"\n    {index + 1} - {alert['indicator']} " \
                                  f"{str(alert['target'] * 100) + '% FROM ' + str(alert['entry']) if alert['indicator'] == 'PCTCHG' else alert['target']}"
                    output += "\n\n"
            self.reply_to(message, output if len(output) > 0 else "Found 0 matching alerts.")

        @self.message_handler(commands=['getprice'])
        @self.is_whitelisted
        def on_get_price(message):
            """/getprice PAIR/PAIR"""
            try:
                pair = self.split_message(message.text)[0]
            except:
                self.reply_to(message, f'Invalid message formatting. Please use the following format:\n'
                                       f'/getprice TOKEN1/TOKEN2')
                return
            try:
                self.reply_to(message, f'{pair}: {self.get_binance_price(pair.replace("/", "").upper())}')
            except Exception as exc:
                self.reply_to(message, str(exc))

        @self.message_handler(commands=['priceall'])
        @self.is_whitelisted
        def on_price_all(message):
            """/priceall - Gets the price of all tokens with alerts set"""
            configuration = UserConfiguration(str(message.from_user.id))
            tokens = [f'{key}: {self.get_binance_price(key.replace("/", "").upper())}' for key
                      in configuration.load_alerts().keys()]
            try:
                self.reply_to(message, "\n".join(tokens))
            except Exception as exc:
                self.reply_to(message, str(exc))

        @self.message_handler(commands=['indicators'])
        @self.is_whitelisted
        def on_indicators(message):
            """/indicators"""
            self.reply_to(message, f'Available Indicators:\n\n'
                                   f'PCTCHG - Specify a percentage change target (ie. 10% = 10)\n'
                                   f'BELOW - Specify a price floor target for the pair.\n'
                                   f'ABOVE - Specify a price ceiling target for the pair.\n\n')

        @self.message_handler(commands=['viewconfig'])
        @self.is_whitelisted
        def on_viewconfig(message):
            """Returns the current configuration of the bot (used as reference for /setconfig)"""
            try:
                configuration = UserConfiguration(str(message.from_user.id))
                config = configuration.load_config()['settings']
                msg = f"{message.from_user.username} {self.get_me().first_name} Configuration:\n\n"
                for k, v in config.items():
                    # msg += f"{key.strip()} settings:\n"
                    # for k, v in variables.items():
                    msg += f'{k}={v}\n'
                    # msg += '\n'
                self.reply_to(message, msg)

            except Exception as exc:
                logger.exception('Could not call /viewconfig', exc_info=exc)
                self.reply_to(message, str(exc))

        @self.message_handler(commands=['setconfig'])
        @self.is_whitelisted
        def on_setconfig(message):
            """Used to change configuration variables of the bot"""
            msg = ""
            failed = []
            user_id = str(message.from_user.id)
            configuration = UserConfiguration(user_id)
            full_config = configuration.load_config()
            try:
                config = full_config['settings']
                for change in self.split_message(message.text):
                    try:
                        conf, val = change.split('=')

                        # Account for bool case:
                        if val.lower() == 'true' or val.lower() == 'false':
                            val = val.lower() == 'true'

                        try:
                            var_type = type(config[conf])
                        except KeyError:
                            raise KeyError(f"{conf} does not match any available config settings in database.")

                        # Attempt to push the config update to the database:
                        config[conf] = var_type(val)

                        msg += f"{conf} set to {val}\n"
                        logger.info(f"{user_id}: {conf} set to {val} ({var_type})\n")
                    except Exception as exc:
                        failed.append((change, str(exc)))
                        continue

                full_config['settings'] = config
                configuration.update_config(full_config)

                if len(msg) > 0:
                    self.reply_to(message, "Successfully set configuration:\n\n" + msg)

                if len(failed) > 0:
                    fail_msg = "Failed to set:\n\n"
                    for fail in failed:
                        fail_msg += f"- {fail[0]} (Error: {fail[1]})\n"
                    self.reply_to(message, fail_msg)
            except Exception as exc:
                logger.exception('Could not set config', exc_info=exc)
                self.reply_to(message, str(exc))

        @self.message_handler(commands=['channels'])
        @self.is_whitelisted
        def on_channels(message):
            splt_msg = self.split_message(message.text)
            try:
                configuration = UserConfiguration(str(message.from_user.id))
                if splt_msg[0].lower() == "add":
                    new_channels = splt_msg[1].split(",")
                    configuration.add_channels(new_channels)
                    self.reply_to(message, f"Successfully added channel(s): {', '.join(new_channels)}")
                elif splt_msg[0].lower() == "remove":
                    rm_channels = splt_msg[1].split(",")
                    fails = configuration.remove_channels(rm_channels)
                    if len(fails) > 0:
                        self.reply_to(message, f"Failed to remove channel(s): {', '.join(fails)}")

                    self.reply_to(message, f"Successfully removed channel(s): "
                                           f"{', '.join([email for email in rm_channels if email not in fails])}")
                else:
                    channels = configuration.get_channels()
                    if len(channels) == 0:
                        self.reply_to(message, 'No channels registered. Use /channels ADD ID,ID,ID')
                        return

                    msg = "Current Alert Channels:\n\n"
                    for channel in channels:
                        msg += f"{channel}\n"
                    self.reply_to(message, msg)
            except IndexError:
                self.reply_to(message, "Invalid formatting - Use /channels VIEW/ADD/REMOVE ID,ID,ID")
            except Exception as exc:
                self.reply_to(message, f"An unexpected error occurred - {exc}")

        @self.message_handler(commands=['emails'])
        @self.is_whitelisted
        def on_emails(message):
            splt_msg = self.split_message(message.text)
            try:
                configuration = UserConfiguration(str(message.from_user.id))
                if splt_msg[0].lower() == "add":
                    new_emails = splt_msg[1].split(",")
                    configuration.add_emails(new_emails)
                    self.reply_to(message, f"Successfully added email(s): {', '.join(new_emails)}")
                elif splt_msg[0].lower() == "remove":
                    rm_emails = splt_msg[1].split(",")
                    fails = configuration.remove_emails(rm_emails)
                    if len(fails) > 0:
                        self.reply_to(message, f"Failed to remove email(s): {', '.join(fails)}")

                    self.reply_to(message, f"Successfully removed email(s): "
                                           f"{', '.join([email for email in rm_emails if email not in fails])}")
                else:
                    emails = configuration.get_emails()
                    if len(emails) == 0:
                        self.reply_to(message, 'No emails registered. Use /emails ADD email@email.com,email@email.com')
                        return

                    msg = "Current Email Recipients:\n\n"
                    for email in emails:
                        msg += f"{email}\n"
                    self.reply_to(message, msg)
            except IndexError:
                self.reply_to(message, "Invalid formatting - Use /emails VIEW/ADD/REMOVE email@email.com")
            except Exception as exc:
                self.reply_to(message, f"An unexpected error occurred - {exc}")

        """------ ADMINISTRATOR COMMANDS: ------"""
        @self.message_handler(commands=['whitelist'])
        @self.is_admin
        def on_whitelist(message):
            splt_msg = self.split_message(message.text)
            try:
                if splt_msg[0].lower() == "add":
                    new_users = splt_msg[1].split(",")
                    for user in new_users:
                        UserConfiguration(user).whitelist_user()
                    self.reply_to(message, f"Whitelisted Users: {', '.join(new_users)}")
                elif splt_msg[0].lower() == "remove":
                    rm_users = splt_msg[1].split(",")
                    for user in rm_users:
                        UserConfiguration(user).blacklist_user()
                    self.reply_to(message, f"Removed Users from Whitelist: {', '.join(rm_users)}")
                else:
                    msg = "Current Whitelist:\n\n"
                    for user_id in get_whitelist():
                        msg += f"{user_id}\n"
                    self.reply_to(message, msg)
            except IndexError:
                self.reply_to(message, "Invalid formatting - Use /whitelist VIEW/ADD/REMOVE TG_USER_ID,TG_USER_ID")
            except Exception as exc:
                self.reply_to(message, f"An unexpected error occurred - {exc}")

        # @self.message_handler(commands=['blacklist'])
        # @self.is_admin
        # def on_blacklist(message):
        #     splt_msg = self.split_message(message.text)
        #     try:
        #         rm_users = splt_msg[0].split(",")
        #         for user in rm_users:
        #             UserConfiguration(user).blacklist_user()
        #         self.reply_to(message, f"Blacklisted Users: {', '.join(rm_users)}")
        #     except IndexError:
        #         self.reply_to(message, "Invalid formatting - Use /blacklist TG_USER_ID,TG_USER_ID")
        #     except Exception as exc:
        #         self.reply_to(message, f"An unexpected error occurred - {exc}")

        @self.message_handler(commands=['getlogs'])
        @self.is_admin
        def on_getlogs(message):
            """Returns the progam's logs at logs/logs.txt"""
            with open(get_logfile(), 'rb') as logfile:
                if len(logfile.read()) > 0:
                    self.reply_to(message, 'Fetching logs...')
                    try:
                        self.send_document(message.chat.id, logfile)
                    except Exception as exc:
                        self.reply_to(message, f'An error occurred - {exc}')
                else:
                    self.reply_to(message, 'Logfile exists, but no logs have been recorded yet.')

        @self.message_handler(commands=['admins'])
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
                                UserConfiguration(new_admin).admin_status(new_value=True)
                            else:
                                failure_msgs.append(f"{new_admins.pop(i)} - User is not yet whitelisted")
                        except Exception as exc:
                            failure_msgs.append(f"{new_admins.pop(i)} - {exc}")
                    msg = f"Successfully added administrator(s): {', '.join(new_admins)}"
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
                                UserConfiguration(admin).admin_status(new_value=False)
                            else:
                                failure_msgs.append(f"{rm_admins.pop(i)} - User is not yet whitelisted")
                        except Exception as exc:
                            failure_msgs.append(f"{rm_admins.pop(i)} - {exc}")
                    msg = f"Successfully revoked administrator(s): {', '.join(rm_admins)}"
                    if len(failure_msgs) > 0:
                        msg += "\n\nFailed to revoke administrator(s):"
                        for fail_msg in failure_msgs:
                            msg += f"\n{fail_msg}"
                    self.reply_to(message, msg)
                else:
                    msg = "Current Administrators:\n\n"
                    for user_id in get_whitelist():
                        if UserConfiguration(user_id).admin_status():
                            msg += f"{user_id}\n"
                    self.reply_to(message, msg)
            except IndexError:
                self.reply_to(message, "Invalid formatting - Use /admin VIEW/ADD/REMOVE USER_ID,USER_ID")
            except Exception as exc:
                self.reply_to(message, f"An unexpected error occurred - {exc}")

    def split_message(self, message: str, convert_type=None) -> list:
        return [chunk.strip() if convert_type is None else convert_type(chunk.strip()) for chunk in
                message.split(" ")[1:] if not all(char == " " for char in chunk) and len(chunk) > 0]

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
                self.reply_to(message,
                              f"{message.from_user.username} ({message.from_user.id}) is not whitelisted")
                return False
        return wrapper

    def is_admin(self, func):
        """
        (Decorator) Checks if the user is an administrator before calling the function

        :param func: PyTelegramBotAPI message handler function, with the 'message' class as the first argument
        """
        def wrapper(*args, **kw):
            message = args[0]
            if UserConfiguration(str(message.from_user.id)).admin_status():
                return func(*args, **kw)
            else:
                self.reply_to(message,
                              f"{message.from_user.username} ({message.from_user.id}) is not an admin")
                return False
        return wrapper

    def get_binance_price(self, pair):
        try:
            return round(float(
                requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={pair.replace("/", "")}').json()[
                    'price']), 3)
        except KeyError:
            raise ValueError(f'{pair} is not a valid pair.\n'
                             f'Please make sure to use this formatting: TOKEN1/TOKEN2')
        except Exception as exc:
            logger.exception(f"An unexpected error occurred when trying to fetch the binance price of {pair}",
                             exc_info=exc)
            raise Exception(
                f'An unexpected error has occurred when trying to fetch the price of {pair} on Binance - {exc}')

    def run(self):
        logger.warn(f'{self.get_me().username} started at {datetime.utcnow()} UTC+0')
        while True:
            try:
                self.polling()
            except KeyboardInterrupt:
                break
            except ReadTimeout:
                logger.error('Bot has crashed due to read timeout - Restarting in 5 seconds...')
                time.sleep(5)
            except Exception as exc:
                logger.critical(f'Unexpected error has occurred while polling - Retrying in 30 seconds...',
                                exc_info=exc)
                time.sleep(30)

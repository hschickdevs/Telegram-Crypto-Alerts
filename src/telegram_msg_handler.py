import json
import time
from datetime import datetime

from ._config import *
from .custom_logger import logger
from io_handler import get_administrators, load_db, update_db

from telebot import TeleBot

TESTING = False


class TelegramBot(TeleBot):
    def __init__(self):
        super().__init__(token=TELEGRAM_BOT_TOKEN)

        if not TESTING:
            for admin_id in TELEGRAM_ADMIN_IDS:
                self.send_message(chat_id=admin_id,
                                  text=f'Telegram Crypto Alerts Bot started at {datetime.utcnow()} UTC+0')

        @self.message_handler(commands=['help'])
        def on_help(message):
            self.reply_to(message, f'Available Commands for Telegram Crypto Alerts Bot:\n\n'
                                   f'/newalert PAIR/PAIR INDICATOR TARGET ENTRY_PRICE\n'
                                   f'Adds a new alert to the database for the pair (eg. ETH/USDT).\n'
                                   f'The "ENTRY_PRICE" parameter is only used for the "PCTCHG" indicator.\n'
                                   f'You can leave ENTRY_PRICE blank if you are using other indicators, or if you just want to use market price as entry price.\n\n'
                                   f'/cancelalert PAIR/PAIR alert_index\n'
                                   f'Cancels an active alert. Get the alert indexes by using the /viewalerts command.\n\n'
                                   f'/indicators\n'
                                   f'Returns the available indicators to use with alerts.\n\n'
                                   f'/viewalerts optional_PAIR/PAIR\n'
                                   f'Returns all active alerts, or all active alerts for the optional passed pair.\n\n'
                                   f'/getprice PAIR/PAIR\n'
                                   f'Simply returns the live binance price of the pair (eg. ETH/USDT).'
                          )

        @self.message_handler(commands=['newalert'])
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
                verified_pair = False
                if len(msg) > 3:
                    entry_price = msg[3]
                else:
                    try:
                        entry_price = self.get_binance_price(pair)
                        verified_pair = True
                    except Exception as exc:
                        self.reply_to(message, str(exc))
                        return

                if not verified_pair:
                    try:
                        lp = self.get_binance_price(pair)
                    except:
                        self.reply_to(message, "An error occurred when attempting to verify the pair on binance.\n"
                                               "Please verify that your pair is listed on binance and follows the "
                                               "format: TOKEN1/TOKEN2")
                        return

                alerts_db = load_db()
                if pair in alerts_db.keys():
                    alerts_db[pair].append(
                        {"indicator": indicator, "entry": entry_price, "target": target, "alerted": False})
                else:
                    alerts_db[pair] = [
                        {"indicator": indicator, "entry": entry_price, "target": target, "alerted": False}]
                update_db(alerts_db)
                self.reply_to(message, f'Successfully activated new alert!')
            except Exception as exc:
                self.reply_to(message,
                              f'An error occurred:\n{exc}')
                return

        @self.message_handler(commands=['cancelalert'])
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
                alerts_db = load_db()
                rm_alert = alerts_db[pair].pop(alert_index - 1)
                all_rm = False
                if len(alerts_db[pair]) == 0:
                    rm_pair = alerts_db.pop(pair)
                    all_rm = True
                update_db(alerts_db)
                self.reply_to(message, f'Successfully Canceled {pair} Alert:\n'
                                       f'{rm_alert}{f" (All alerts canceled for {pair})" if all_rm else ""}')
            except Exception as exc:
                self.reply_to(message, f'An error occurred when trying to cancel the alert:\n{exc}')

        @self.message_handler(commands=['viewalerts'])
        def on_view_alerts(message):
            """/viewalerts PAIR (<- optional)"""
            try:
                alerts_pair = self.split_message(message.text)[0].upper()
            except IndexError:
                alerts_pair = "ALL"
            alerts_db = load_db()
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
        def on_price_all(message):
            """/priceall - Gets the price of all tokens with alerts set"""
            tokens = [f'{key}: {self.get_binance_price(key.replace("/", "").upper())}' for key in load_db().keys()]
            try:
                self.reply_to(message, "\n".join(tokens))
            except Exception as exc:
                self.reply_to(message, str(exc))

        @self.message_handler(commands=['indicators'])
        def on_indicators(message):
            """/indicators"""
            self.reply_to(message, f'Available Indicators:\n'
                                   f'PCTCHG - Specify a percentage change target (ie. 10% = 10)\n'
                                   f'BELOW - Specify a price floor target for the pair.\n'
                                   f'ABOVE - Specify a price ceiling target for the pair.\n\n')

    def split_message(self, message, convert_type=None) -> list:
        if convert_type is None:
            return [chunk.strip() for chunk in message.split(" ")[1:] if
                    not all(char == " " for char in chunk) and len(chunk) > 0]
        else:
            return [convert_type(chunk.strip()) for chunk in message.split(" ")[1:] if
                    not all(char == " " for char in chunk) and len(chunk) > 0]

    def user_is_administrator(self, func):
        """
        (Decorator) Checks if the user is an administrator before proceeding with the function

        :param func: Expects the function to be a message handler, with the 'message' class as the first argument
        """
        def wrapper(*args, **kw):
            message = args[0]
            user_id = str(message.from_user.id)
            if user_id in get_administrators():
                return func(*args, **kw)
            else:
                self.reply_to(message, f"{message.from_user.username} ({message.from_user.id}) is not an administrator.")
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
        logger.info(f'Telegram Message Handler started.')
        while True:
            try:
                self.polling()
            except KeyboardInterrupt:
                break
            except Exception as exc:
                if not TESTING:
                    for admin_id in TELEGRAM_ADMIN_IDS:
                        requests.post(url=f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
                                      params={'chat_id': admin_id,
                                              'text': f'CRITICAL ERROR:\n{exc}\nRetrying in 30 seconds...'})
                else:
                    logger.critical(f'Unexpected error has occurred while polling - Retrying in 30 seconds...',
                                    exc_info=exc)
                time.sleep(30)

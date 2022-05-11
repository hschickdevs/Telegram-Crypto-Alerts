import json
import time
import traceback

from ._config import *
from .io_handler import load_db, update_db
from .custom_logger import logger

import requests

BINANCE_CALL_URL = 'https://api.binance.com/api/v3/ticker/price?symbol={}'  # format to token pair (ex: BTCUSDT)


class AlertHandler:
    def __init__(self):
        self.polling = False  # Temporary variable to manage alerts

    def binance_request(self, token_pair, _try: int = 1, retry_delay: int = 2, maximum_retries: int = 5) -> float:
        """
        Make a request to Binance API and return the response

        :param token_pair: token pair (e.g. BTCUSDT)
        :param _try: The current try for retry recursion
        :param retry_delay: seconds delay between retries
        :param maximum_retries: Maxiumum number of retries

        :return float: price of the token pair
        """
        try:
            response = requests.get(BINANCE_CALL_URL.format(token_pair))
            response.raise_for_status()
            return float(response.json()['price'])
        except Exception as err:
            if _try == maximum_retries:
                raise ConnectionAbortedError(f'Binance request failed after {_try} retries - Error: {err}')
            else:
                time.sleep(retry_delay)
                return self.binance_request(token_pair, _try + 1)

    def mainloop(self):
        logger.info('Alert handler started.')
        while True:
            alerts_database = load_db()

            post_queue = []
            for pair in alerts_database.keys():
                pair_price = self.binance_request(pair.replace("/", ""))

                remove_queue = []
                for alert in alerts_database[pair]:
                    # do_alert = False
                    alerted = alert['alerted']
                    target = alert['target']
                    indicator = alert['indicator']
                    if indicator == 'PCTCHG':
                        entry = alert['entry']
                        if pair_price > entry * (1 + target) and not alerted:
                            pct_chg = ((pair_price - entry) / entry) * 100
                            post_queue.append(f"{pair} UP {pct_chg:.1f}% AT {pair_price}")
                            alert['alerted'] = True
                        elif pair_price < entry * (1 - target) and not alerted:
                            pct_chg = ((entry - pair_price) / entry) * 100
                            post_queue.append(f"{pair} DOWN {pct_chg:.1f}% AT {pair_price}")
                            alert['alerted'] = True
                        elif alerted:
                            remove_queue.append(alert)
                    elif indicator == 'ABOVE':
                        if pair_price > target and not alerted:
                            post_queue.append(f"{pair} ABOVE {target} TARGET AT {pair_price}")
                            alert['alerted'] = True
                        elif pair_price < target * (1 - PERCENT_CHG_ALERT_RESET) and alerted:
                            alert['alerted'] = False
                        elif alerted and DELETE_ALL_ALERTS:
                            remove_queue.append(alert)
                    elif indicator == 'BELOW':
                        if pair_price < target and not alerted:
                            post_queue.append(f"{pair} BELOW {target} TARGET AT {pair_price}")
                            alert['alerted'] = True
                        elif pair_price > target * (1 + PERCENT_CHG_ALERT_RESET) and alerted:
                            alert['alerted'] = False
                        elif alerted and DELETE_ALL_ALERTS:
                            remove_queue.append(alert)

                for item in remove_queue:
                    alerts_database[pair].remove(item)

            update_db(alerts_database)

            if len(post_queue) > 0:
                self.polling = False
                for post in post_queue:
                    logger.info(post)
                    status = self.tg_alert(post=post)
                    if len(status[1]) > 0:
                        logger.warn(f"Failed to send alert ({post}) to the following IDs: {status[1]}")

            if not self.polling:
                self.polling = True
                logger.info(f'Bot polling for next alert...')
            time.sleep(PRICES_POLLING_PERIOD)

    def tg_alert(self, post: str) -> tuple:
        """
        Sends the post (price alert) to each registered user of the Telegram bot

        :param post: A message to send to each registered bot user
        :return: Tuple = ([successful group ids], [unsuccessful group ids])
        """
        output = ([], [])
        for group_id in TELEGRAM_GROUP_IDS:
            try:
                requests.post(url=f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
                              params={'chat_id': group_id, 'text': post})
                output[0].append(group_id)
            except:
                output[1].append(group_id)

        return output

    def email_alert(self, post: str):
        """
        Dynamically builds the email by formatting the string in email_template.txt with the post

        :param post: The post (price alert) to add to the email template and send to all registered emails
        :return:
        """

    def run(self):
        try:
            self.mainloop()
        except Exception as exc:
            post = f"An error has occurred in the mainloop\nError Code: {exc}\nTrying again in 15 seconds..."
            logger.exception("An error has occurred in the mainloop. Trying again in 15 seconds...", exc_info=exc)
            for admin_id in TELEGRAM_ADMIN_IDS:
                requests.post(url=f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
                              params={'chat_id': admin_id, 'text': post})
            time.sleep(15)

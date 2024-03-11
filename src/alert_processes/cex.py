import time
from datetime import datetime
import os

from ..user_configuration import LocalUserConfiguration, MongoDBUserConfiguration, get_whitelist
from ..logger import logger
from ..config import *
from .base import BaseAlertProcess
from ..telegram import TelegramBot
from ..models import BinancePriceResponse

import requests
from ratelimit import limits, sleep_and_retry


class CEXAlertProcess(BaseAlertProcess):
    def __init__(self, telegram_bot: TelegramBot):
        """
        :param telegram_bot: The Telegram bot instance
        """
        super().__init__(telegram_bot)
        self.polling = False  # Temporary variable to manage alerts

        self.location = os.getenv('LOCATION').lower()
        assert self.location in ['us', 'global'], "Location must be 'us' or 'global' for the Binance exchange."

        self.endpoint = BINANCE_PRICE_URL_US if self.location.lower() == 'us' else BINANCE_PRICE_URL_GLOBAL

    def poll_user_alerts(self, tg_user_id: str) -> None:
        """
        1. Load the user's configuration
        2. poll all alerts and create posts
        3. Remove alert conditions
        4. Send alerts if found

        :param tg_user_id: The Telegram user ID from the database
        """
        configuration = LocalUserConfiguration(tg_user_id) if not USE_MONGO_DB else MongoDBUserConfiguration(tg_user_id)
        alerts_database = configuration.load_alerts()
        config = configuration.load_config()

        do_update = False  # If any changes are made, update the database
        post_queue = []
        for pair in alerts_database.copy().keys():

            remove_queue = []
            for alert in alerts_database[pair]:
                if alert['alerted']:
                    remove_queue.append(alert)
                    do_update = True  # Since the alert needs to be removed from the database, signal do_update
                    continue

                if alert['type'] == "s":
                    condition, value, post_string = self.get_simple_indicator(pair, alert)

                    if condition:  # If there is a condition satisfied
                        post_queue.append((post_string, pair))
                        alert['alerted'] = True
                        do_update = True  # Since the alert needs to be updated in the database, signal do_update

            for item in remove_queue:
                alerts_database[pair].remove(item)
                if len(alerts_database[pair]) == 0:
                    alerts_database.pop(pair)

        if do_update:
            configuration.update_alerts(alerts_database)

        if len(post_queue) > 0:
            self.polling = False
            for post, pair in post_queue:
                logger.info(post)
                status = self.tg_alert(post=post, channel_ids=config['channels'], pair=pair)
                if len(status[1]) > 0:
                    logger.warn(f"Failed to send Telegram alert ({post}) to the following IDs: {status[1]}")

        if not self.polling:
            self.polling = True
            logger.info(f'Bot polling for next alert...')

    @sleep_and_retry
    @limits(calls=1, period=CEX_POLLING_PERIOD)
    def poll_all_alerts(self) -> None:
        for user in get_whitelist():
            self.poll_user_alerts(tg_user_id=user)

    def get_simple_indicator(self, pair: str, alert: dict, pair_price: float = None) -> tuple[bool, float, str]:
        """
        Accounts for the 3 following simple price movement indicators:
        PCTCHG - Percent change in the price
        ABOVE - Price above the target
        BELOW - Price below the target

        :param pair: The crypto pair
        :param pair_price: The current price of the crypto pair.
                           Get the pair price before calling the self.get_pair_price() function
        :param alert: An alert data dictionary as returned by src.io_handler.UserConfiguration.load_alerts()

        :returns: Tuple:
                  (Boolean) True if the indicator is satisfied, False if not
                  (Float) The current value of the indicator
                  (String) The formatted string to send with alerts
        """
        target = alert['target']
        # indicator = alert["indicator"]
        comparison = alert['comparison']
        if pair_price is None:
            pair_price = self.get_latest_price(token_pair=pair.replace("/", ""))

        if comparison == 'PCTCHG':
            entry = alert['entry']
            if pair_price > (entry * (1 + target)):
                pct_chg = ((pair_price - entry) / entry) * 100
                return True, pct_chg, f"{pair} UP {pct_chg:.1f}% FROM {entry} AT {pair_price}"
            elif pair_price < (entry * (1 - target)):
                pct_chg = ((entry - pair_price) / entry) * 100
                return True, pct_chg, f"{pair} DOWN {pct_chg:.1f}% FROM {entry} AT {pair_price}"
        elif comparison == '24HRCHG':
            pct_change = self.get_pct_change(pair.replace("/", ""))
            if abs(pct_change) >= alert['target']:
                return True, pct_change, f"{pair} 24HR CHANGE {pct_change:.1f}% AT {pair_price}"
        elif comparison == 'ABOVE':
            if pair_price > target:
                return True, pair_price, f"{pair} ABOVE {target} TARGET AT {pair_price}"
        elif comparison == 'BELOW':
            if pair_price < target:
                return True, pair_price, f"{pair} BELOW {target} TARGET AT {pair_price}"

        return False, pair_price, ""

    def get_latest_price(self, token_pair: str, retry_delay: int = 2, maximum_retries: int = 5, _try: int = 1) -> float:
        """
        Make a request to Binance API and return the response

        :param token_pair: token pair without the slash (e.g. BTCUSDT)
        :param _try: The current try for recursive retries
        :param retry_delay: seconds delay between retries
        :param maximum_retries: Maximum number of retries

        :return float: price of the token pair
        """
        url = self.endpoint.format(token_pair, BINANCE_TIMEFRAMES[0])
        try:

            response = requests.get(url)
            response.raise_for_status()

            return BinancePriceResponse(response.json()).lastPrice
        except Exception as err:
            if _try == maximum_retries:
                raise ConnectionAbortedError(f'Binance request ({url}) failed after {_try} retries - Error: {err}')
            else:
                time.sleep(retry_delay)
                return self.get_latest_price(token_pair, _try=_try + 1)

    def get_pct_change(self, token_pair: str, window: str, retry_delay: int = 2, maximum_retries: int = 5, _try: int = 1) -> float:
        """
        Make a request to Binance API and return the 24 hour % change for a token pair

        :param token_pair: token pair without the slash (e.g. BTCUSDT)
        :param window: The time window for the price change (e.g. 1d for 1 day)
        :param _try: The current try for recursive retries
        :param retry_delay: seconds delay between retries
        :param maximum_retries: Maxiumum number of retries

        :return float: The percent change of the token pair (expressed as a percentage, i.e. -3.8 for -3.8%)
        """
        assert window in BINANCE_TIMEFRAMES, (f'Invalid window ({window}) for Binance API. '
                                              f'Must be one of {BINANCE_TIMEFRAMES}')
        url = self.endpoint.format(token_pair, window)
        try:
            response = requests.get(url)
            response.raise_for_status()

            return BinancePriceResponse(response.json()).priceChangePercent
        except Exception as err:
            if _try == maximum_retries:
                raise ConnectionAbortedError(f'Binance request ({url}) failed after {_try} retries - Error: {err}')
            else:
                time.sleep(retry_delay)
                return self.get_pct_change(token_pair, window, _try=_try + 1)
    
    def tg_alert(self, post: str, channel_ids: list[str], pair: str = None) -> tuple:
        """
        Sends the post (price alert) to each registered user of the Telegram bot

        :param post: A message to send to each registered bot user
        :param channel_ids: All group ids to send the alert to (self.config_client.load_config()['channels'])
        :param pair: The binance pair corresponding to the alert (for showing chart)

        :return: Tuple = ([successful group ids], [unsuccessful group ids])
        """
        post = f"🔔 <b>CEX ALERT:</b> 🔔\n\n" + post
        if pair:
            pair_fmt = pair.replace('/', '_')
            post += f"\n\n<a href='https://www.binance.com/en/trade/{pair_fmt}?type=spot'><b>View {pair} Chart</b></a>"
        output = ([], [])
        for g_id in channel_ids:
            try:
                # requests.post(url=f'https://api.telegram.org/bot{self.tg_bot_token}/sendMessage',
                #               params={'chat_id': g_id, 'text': header_str + post, "parse_mode": "HTML"})
                self.telegram_bot.send_message(chat_id=g_id, text=post, parse_mode="HTML", disable_web_page_preview=True)
                output[0].append(g_id)
            except:
                output[1].append(g_id)

        return output
    
    def run(self):
        """
        Start the CEX alert process and run in an infinite loop
        """
        try:
            logger.warn(f'{type(self).__name__} started at {datetime.utcnow()} UTC+0')
            while True:
                self.poll_all_alerts()
        except NotImplementedError as exc:
            logger.critical(exc_info=exc)
            # self.alert_admins(str(exc))
        except KeyboardInterrupt:
            logger.critical("KeyboardInterrupt detected. Exiting...")
            exit(0)
        except Exception as exc:
            logger.critical("An error has occurred in the CEX alert process. Trying again in 15 seconds...", exc_info=exc)
            time.sleep(15)

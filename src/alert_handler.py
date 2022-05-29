import time
from datetime import datetime

from .io_client import UserConfiguration
from .custom_logger import logger

import requests
import yagmail
from ratelimit import limits, sleep_and_retry

POLLING_PERIOD = 10  # Delay for the alert handler to pull prices and check alert conditions (in seconds)


class AlertHandler:
    def __init__(self, telegram_bot_token: str, alert_email_user: str = None, alert_email_pass: str = None):
        self.polling = False  # Temporary variable to manage alerts
        self.tg_bot_token = telegram_bot_token
        self.alert_email_user = alert_email_user
        self.alert_email_pass = alert_email_pass

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

    def poll_user_alerts(self, tg_user_id: str) -> None:
        """
        1. Load the user's configuration
        2. poll all alerts and create posts
        3. Remove alert condtions
        4. Send alerts if found

        :param tg_user_id: The Telegram user ID from the database
        """
        alerts_database = self.config_handler.load_alerts()
        config = self.config_handler.load_config()

        # Load user configuration from the config_handler

        post_queue = []
        for pair in alerts_database.keys():
            pair_price = self.binance_request(pair.replace("/", ""))

            remove_queue = []
            for alert in alerts_database[pair]:
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
                    elif pair_price < target * (1 - config['settings']['pct_chg_alert_reset']) and alerted:
                        alert['alerted'] = False
                    elif alerted and config['settings']['delete_pushed_alerts']:
                        remove_queue.append(alert)
                elif indicator == 'BELOW':
                    if pair_price < target and not alerted:
                        post_queue.append(f"{pair} BELOW {target} TARGET AT {pair_price}")
                        alert['alerted'] = True
                    elif pair_price > target * (1 + config['settings']['pct_chg_alert_reset']) and alerted:
                        alert['alerted'] = False
                    elif alerted and config['settings']['delete_pushed_alerts']:
                        remove_queue.append(alert)

            for item in remove_queue:
                alerts_database[pair].remove(item)

        self.config_handler.update_alerts(alerts_database)

        if len(post_queue) > 0:
            self.polling = False
            for post in post_queue:
                logger.info(post)
                status = self.tg_alert(post=post, channel_ids=config['channels'])
                if len(status[1]) > 0:
                    logger.warn(f"Failed to send Telegram alert ({post}) to the following IDs: {status[1]}")

                if config['settings']['send_email_alerts']:
                    self.email_alert(post)

        if not self.polling:
            self.polling = True
            logger.info(f'Bot polling for next alert...')

    def format_post_string(self, alert: dict):
        pass

    @sleep_and_retry
    @limits(calls=1, period=POLLING_PERIOD)
    def poll_all_alerts(self) -> None:
        """
        1. Aggregate pairs across all users
        2. Fetch all pair prices
        3. Log individual user failures
        """
        pass

    def tg_alert(self, post: str, channel_ids: list[str]) -> tuple:
        """
        Sends the post (price alert) to each registered user of the Telegram bot

        :param post: A message to send to each registered bot user
        :param channel_ids: All group ids to send the alert to (self.config_client.load_config()['channels'])
        :return: Tuple = ([successful group ids], [unsuccessful group ids])
        """
        output = ([], [])
        for group_id in channel_ids:
            try:
                requests.post(url=f'https://api.telegram.org/bot{self.tg_bot_token}/sendMessage',
                              params={'chat_id': group_id, 'text': post})
                output[0].append(group_id)
            except:
                output[1].append(group_id)

        return output

    def email_alert(self, post: str):
        """
        Dynamically builds the email by formatting the string in email_template.html with the post

        :param post: The post (price alert) to add to the email template and send to all registered emails
        :return:
        """

        if self.alert_email_pass is None or self.alert_email_user is None:
            raise NotImplementedError(f"Email alerts are enabled, "
                                      f"but the required environment variables are missing for login.")

        logger.info(f"Sending email alert to registered users: {post}")

        emails = self.config_handler.load_config()['emails']
        with yagmail.SMTP(user=self.alert_email_user, password=self.alert_email_pass) as smtp:
            for recipient in emails:
                smtp.send(to=recipient, subject="Crypto Indicator Alert",
                          contents=self.config_handler.get_email_template().format(post=post))

        logger.info(f"Emails sent to: {emails}")

    def alert_admins(self, message: str):
        pass

    def run(self):
        try:
            logger.warn(f'{type(self).__name__} started at {datetime.utcnow()} UTC+0')
            while True:
                self.poll_all_alerts()
        except NotImplementedError as exc:
            logger.critical(exc_info=exc)
            self.alert_admins(str(exc))
        except Exception as exc:
            logger.exception("An error has occurred in the mainloop. Trying again in 15 seconds...", exc_info=exc)
            time.sleep(15)

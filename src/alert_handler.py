import time
from datetime import datetime

from .io_client import UserConfiguration, get_whitelist
from .custom_logger import logger
from .static_config import *
from .indicators import get_simple_indicator

import requests
import yagmail
from ratelimit import limits, sleep_and_retry


class AlertHandler:
    def __init__(self, telegram_bot_token: str, alert_email_user: str = None, alert_email_pass: str = None):
        self.polling = False  # Temporary variable to manage alerts
        self.tg_bot_token = telegram_bot_token
        self.alert_email_user = alert_email_user
        self.alert_email_pass = alert_email_pass

    def poll_user_alerts(self, tg_user_id: str) -> None:
        """
        1. Load the user's configuration
        2. poll all alerts and create posts
        3. Remove alert conditions
        4. Send alerts if found

        :param tg_user_id: The Telegram user ID from the database
        """
        configuration = UserConfiguration(tg_user_id)
        alerts_database = configuration.load_alerts()
        config = configuration.load_config()

        post_queue = []
        for pair in alerts_database.keys():

            remove_queue = []
            for alert in alerts_database[pair]:
                if alert['alerted']:
                    remove_queue.append(alert)
                    continue

                condition, value, post_string = get_simple_indicator(pair, alert)

                if condition:  # If there is a condition satisfied
                    post_queue.append(post_string)
                    alert['alerted'] = True

            for item in remove_queue:
                alerts_database[pair].remove(item)

        configuration.update_alerts(alerts_database)

        if len(post_queue) > 0:
            self.polling = False
            for post in post_queue:
                logger.info(post)
                status = self.tg_alert(post=post, channel_ids=config['channels'])
                if len(status[1]) > 0:
                    logger.warn(f"Failed to send Telegram alert ({post}) to the following IDs: {status[1]}")

                if config['settings']['send_email_alerts']:
                    self.email_alert(post, configuration)

        if not self.polling:
            self.polling = True
            logger.info(f'Bot polling for next alert...')

    # def format_post_string(self, alert: dict):
    #     pass

    @sleep_and_retry
    @limits(calls=1, period=POLLING_PERIOD)
    def poll_all_alerts(self) -> None:
        """
        1. Aggregate pairs across all users
        2. Fetch all pair prices
        3. Log individual user failures
        """
        for user in get_whitelist():
            self.poll_user_alerts(tg_user_id=user)

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

    def email_alert(self, post: str, configuration: UserConfiguration):
        """
        Dynamically builds the email by formatting the string in email_template.html with the post

        :param configuration: The io_handler.UserConfiguration object for the current user
        :param post: The post (price alert) to add to the email template and send to all registered emails
        :return:
        """

        if self.alert_email_pass is None or self.alert_email_user is None:
            raise NotImplementedError(f"Email alerts are enabled, "
                                      f"but the required environment variables are missing for login.")

        logger.info(f"Sending email alert to registered users: {post}")

        emails = configuration.load_config()['emails']
        with yagmail.SMTP(user=self.alert_email_user, password=self.alert_email_pass) as smtp:
            for recipient in emails:
                smtp.send(to=recipient, subject="Crypto Indicator Alert",
                          contents=configuration.get_email_template().format(post=post))

        logger.info(f"Emails sent to: {emails}")

    def alert_admins(self, message: str):
        for user in get_whitelist():
            if UserConfiguration(user).admin_status():
                requests.post(url=f'https://api.telegram.org/bot{self.tg_bot_token}/sendMessage',
                              params={'chat_id': user, 'text': message})

    def run(self):
        try:
            logger.warn(f'{type(self).__name__} started at {datetime.utcnow()} UTC+0')
            while True:
                self.poll_all_alerts()
        except NotImplementedError as exc:
            logger.critical(exc_info=exc)
            # self.alert_admins(str(exc))
        except Exception as exc:
            logger.exception("An error has occurred in the mainloop. Trying again in 15 seconds...", exc_info=exc)
            time.sleep(15)

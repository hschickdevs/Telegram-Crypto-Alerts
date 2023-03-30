import time
from datetime import datetime
import os

from .io_client import UserConfiguration, get_whitelist
from .custom_logger import logger
from .static_config import *
from .indicators import get_pair_price, TADatabaseClient, TAAggregateClient, get_24hr_price_change

import requests
from ratelimit import limits, sleep_and_retry
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import *


class AlertHandler:
    def __init__(self, telegram_bot_token: str, sendgrid_apikey: str = None, alert_email: str = None):
        self.polling = False  # Temporary variable to manage alerts
        self.tg_bot_token = telegram_bot_token
        self.alert_email = alert_email
        # self.alert_email_pass = alert_email_pass
        self.ta_db = TADatabaseClient().fetch_ref()
        self.ta_agg_cli = TAAggregateClient()
        self.sendgrid_cli = SendGridAPIClient(api_key=sendgrid_apikey) if sendgrid_apikey is not None else None

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
                elif alert['type'] == "t":
                    condition, value, post_string = self.get_technical_indicator(pair, alert)
                else:
                    raise Exception("Invalid alert type: s = simple, t = technical")

                if condition:  # If there is a condition satisfied
                    post_queue.append(post_string)
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
            for post in post_queue:
                logger.info(post)
                status = self.tg_alert(post=post, channel_ids=config['channels'])
                if len(status[1]) > 0:
                    logger.warn(f"Failed to send Telegram alert ({post}) to the following IDs: {status[1]}")

                if config['settings']['send_email_alerts']:
                    self.email_alert_sendgrid(post, configuration)

        if not self.polling:
            self.polling = True
            logger.info(f'Bot polling for next alert...')

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
        header_str = f"🔔 <b>ALERT:</b> 🔔\n"
        output = ([], [])
        for group_id in channel_ids:
            try:
                requests.post(url=f'https://api.telegram.org/bot{self.tg_bot_token}/sendMessage',
                              params={'chat_id': group_id, 'text': header_str + post, "parse_mode": "HTML"})
                output[0].append(group_id)
            except:
                output[1].append(group_id)

        return output

    def email_alert_sendgrid(self, post: str, configuration: UserConfiguration) -> None:
        """
        Dynamically builds the email by formatting the string in email_template.html with the post

        :param configuration: The io_handler.UserConfiguration object for the current user
        :param post: The post (price alert) to add to the email template and send to all registered emails
        :return:
        """
        if self.alert_email is None or self.sendgrid_cli is None:
            raise Exception("Email alerts are enabled, but the required environment variables are missing for login.")

        recipients = configuration.load_config()['emails']
        if len(recipients) == 0:
            return

        pair = post.split(" ")[0]
        binance_url = f"https://www.binance.com/en/trade/{pair.replace('/', '_')}?type=spot"
        formatted_html = configuration.get_email_template().format(post=post,
                                                                   binance_url=binance_url,
                                                                   pair=pair)

        formatted_mail = Mail(from_email=Email(self.alert_email),
                              to_emails=recipients,
                              subject=f"{pair} Crypto Indicator Alert",
                              html_content=formatted_html)
        try:
            self.sendgrid_cli.client.mail.send.post(request_body=formatted_mail.get())
            logger.info(f"Emails sent to {recipients} with post {post}")
        except Exception as exc:
            logger.warn(f"Could not send alert email to recipients: {recipients}", exc_info=exc)

    # --> Deprecated in favor of SendGrid integration and Outdated <--
    # def email_alert_smtp(self, post: str, configuration: UserConfiguration):
    #     """
    #     Dynamically builds the email by formatting the string in email_template.html with the post
    #
    #     :param configuration: The io_handler.UserConfiguration object for the current user
    #     :param post: The post (price alert) to add to the email template and send to all registered emails
    #     :return:
    #     """
    #
    #     if self.alert_email_pass is None or self.alert_email_user is None:
    #         raise NotImplementedError(f"Email alerts are enabled, "
    #                                   f"but the required environment variables are missing for login.")
    #
    #     logger.info(f"Sending email alert to registered users: {post}")
    #
    #     emails = configuration.load_config()['emails']
    #     with yagmail.SMTP(user=self.alert_email_user, password=self.alert_email_pass) as smtp:
    #         for recipient in emails:
    #             smtp.send(to=recipient, subject="Crypto Indicator Alert",
    #                       contents=configuration.get_email_template().format(post=post))
    #
    #     logger.info(f"Emails sent to: {emails}")

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
            pair_price = get_pair_price(token_pair=pair.replace("/", ""))

        if comparison == 'PCTCHG':
            entry = alert['entry']
            if pair_price > (entry * (1 + target)):
                pct_chg = ((pair_price - entry) / entry) * 100
                return True, pct_chg, f"{pair} UP {pct_chg:.1f}% FROM {entry} AT {pair_price}"
            elif pair_price < (entry * (1 - target)):
                pct_chg = ((entry - pair_price) / entry) * 100
                return True, pct_chg, f"{pair} DOWN {pct_chg:.1f}% FROM {entry} AT {pair_price}"
        elif comparison == '24HRCHG':
            pct_change = get_24hr_price_change(pair.replace("/", ""))
            if abs(pct_change) >= alert['target']:
                return True, pct_change, f"{pair} 24HR CHANGE {pct_change:.1f}% AT {pair_price}"
        elif comparison == 'ABOVE':
            if pair_price > target:
                return True, pair_price, f"{pair} ABOVE {target} TARGET AT {pair_price}"
        elif comparison == 'BELOW':
            if pair_price < target:
                return True, pair_price, f"{pair} BELOW {target} TARGET AT {pair_price}"

        return False, pair_price, ""

    def get_technical_indicator(self, pair: str, alert: dict) -> tuple[bool, float, str]:
        """
        Accounts for all of the implemented taapi.io indicators.
        Get the available indicators using the telegram command.
        References the alert against the temp/ta_aggregate.json file to check for satisfaction.

        :param pair: The crypto pair
        :param alert: An alert data dictionary as returned by src.io_handler.UserConfiguration.load_alerts()

        :returns: Tuple:
                  (Boolean) True if the indicator is satisfied, False if not
                  (Float) The current value of the indicator
                  (String) The formatted string to send with alerts
        """
        null_output = False, 0, ""

        aggregate = self.ta_agg_cli.load_agg()
        if aggregate == {}:
            logger.warn("Attempted to load the aggregate in get_technical_indicator() but it was empty")
            return null_output

        # Match the alert to its corresponding reference in the aggregate and check the value:
        matched_indicator = None
        formatted_alert = self.ta_agg_cli.format_alert_for_match(alert)

        # Attempt to find an existing indicator match for the alert
        for indicator in aggregate[pair][alert['interval']]:
            try:
                if all(indicator[k] == v for k, v in formatted_alert.items()):
                    matched_indicator = indicator
                    break
            except KeyError:
                continue

        if matched_indicator is None:
            raise ValueError(f"Could not match alert to indicator in the TA aggregate - Alert: {alert}")

        # If these tests pass, this is the correct indicator because the symbol, interval, and params pass
        value = matched_indicator['values'][alert['output_value']]
        if value is None:
            return null_output

        satisfied = False
        if alert['comparison'] == "ABOVE":
            if value > alert['target']:
                satisfied = True
        elif alert['comparison'] == "BELOW":
            if value < alert['target']:
                satisfied = True
        else:
            raise ValueError(f"'{alert['comparison']}' IS AN INVALID COMPARISON TYPE (ABOVE OR BELOW)")

        # Return
        if satisfied:
            indicator_str = f"{self.ta_db[alert['indicator'].upper()]['name']} ({alert['indicator'].upper()})"
            params_str = ', '.join([f'{param.upper()}={v}' for param, v in alert['params'].items()])
            post_str = f"{pair} {indicator_str} {alert['interval']} {params_str} {alert['comparison']} {alert['target']}" \
                       f" AT {value:.{OUTPUT_VALUE_PRECISION}f}\n"
            return True, value, post_str
        else:
            return null_output

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
            logger.critical("An error has occurred in the mainloop. Trying again in 15 seconds...", exc_info=exc)
            time.sleep(15)

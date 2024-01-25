import time
from datetime import datetime
import os

from .._logger import logger
from .base import BaseAlertProcess
from ..config import *
from ..user_configuration import get_whitelist
from ..blockchain.swap import SwapClient

import requests
from ratelimit import limits, sleep_and_retry


class DEXAlertProcess(BaseAlertProcess):
    def __init__(self):
        self.polling = False  # Temporary variable to manage alerts
        self.tg_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        super().__init__()
        
    def create_network_connections(self):
        # WILL NEED TO INSTANTIATE CONNECTIONS FOR ALL NETWORKS REGISTERED IN THE CONFIG
        pass

    # TODO: FIX THIS <--------------------------------
    def poll_user_alerts(self, tg_user_id: str) -> None:
        """
        1. Load the user's configuration
        2. poll all alerts and create posts
        3. Remove alert conditions
        4. Send alerts if found

        :param tg_user_id: The Telegram user ID from the database
        """
        # SEE THE CEX IMPLEMENTATION
        raise NotImplementedError

    @sleep_and_retry
    @limits(calls=1, period=DEX_POLLING_PERIOD)
    def poll_all_alerts(self) -> None:
        for user in get_whitelist():
            self.poll_user_alerts(tg_user_id=user)

    def tg_alert(self, post: str, channel_ids: list[str]) -> tuple:
        """
        Sends the post (price alert) to each registered user of the Telegram bot

        :param post: A message to send to each registered bot user
        :param channel_ids: All group ids to send the alert to (self.config_client.load_config()['channels'])
        :return: Tuple = ([successful group ids], [unsuccessful group ids])
        """
        header_str = f"🔔 <b>DEX ALERT:</b> 🔔\n"
        output = ([], [])
        for g_id in channel_ids:
            try:
                requests.post(url=f'https://api.telegram.org/bot{self.tg_bot_token}/sendMessage',
                              params={'chat_id': g_id, 'text': header_str + post, "parse_mode": "HTML"})
                output[0].append(g_id)
            except:
                output[1].append(g_id)

        return output

    def run(self):
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
            logger.critical("An error has occurred in the CEX alert process. Trying again in 15 seconds...",
                            exc_info=exc)
            time.sleep(15)
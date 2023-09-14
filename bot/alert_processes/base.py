from abc import ABC, abstractmethod


class BaseAlertProcess(ABC):
    """
    This base class is to be served as a template for creating alert handlers.
    
    Each of these alert handlers is run in its own thread on the bot, and should represent its own asset/alert type.
    
    This functionality allows standardized creation of new alert types/assets when needed by facilitating polymorphism.
    """

    @abstractmethod
    def poll_user_alerts(self, tg_user_id: str) -> None:
        """
        Polls the alerts for a single user of the bot.

        1. Load the user's configuration
        2. poll all alerts and create posts
        3. Remove alert conditions
        4. Send alerts if found
        """
        pass

    @abstractmethod
    def poll_all_alerts(self):
        """
        Polls the alerts for ALL users of the bot.
        
        1. Aggregate assets across all users
        2. Fetch all asset prices/metrics
        3. Log individual user failures
        """
        pass

    @abstractmethod
    def tg_alert(self, post: str, channel_ids: list[str]):
        """
        Sends a Telegram alert to the user.
        
        Each alert handler needs its own implementation of this method because the output
        will be different based on the asset/alert type.
        """
        pass

    @abstractmethod
    def run(self):
        """
        Runs the alert handler in a loop.
        
        Should be started in a new daemon thread.
        """
        pass

from .base import BaseAlertProcess

class DEXAlertProcess(BaseAlertProcess):
    def __init__(self, bot, alert):
        self.bot = bot
        self.alert = alert
    
    def poll_user_alerts(self, alert):
        pass
    
    def run(self):
        pass
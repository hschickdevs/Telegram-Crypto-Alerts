import json
import subprocess
import os
import threading

from src.alert_handler import AlertHandler
from src.telegram_msg_handler import TelegramBot

"""IF THE SCRIPT WITH RUN BOTH HANDLERS IN PARALLEL USING THREADING"""
if __name__ == "__main__":
    threading.Thread(target=AlertHandler().run).start()
    threading.Thread(target=TelegramBot().run).start()


"""IF THIS SCRIPT WILL RUN BOTH HANDLER SCRIPTS IN PARALLEL IN THE SAME SHELL"""
# if __name__ == "__main__":
#     subprocess.run("python3 src/alert_handler.py & python3 src/telegram_msg_handler.py", shell=True)

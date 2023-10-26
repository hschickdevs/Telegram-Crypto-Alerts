# Import for consolidated use in .alert_processes import
from .base import BaseAlertProcess
from .cex import CEXAlertProcess
from .dex import DEXAlertProcess
from .technical import TechnicalAlertProcess


"""
EACH OF THE PROCESSES IN THIS MODULE CONTROLS A DIFFERENT TYPE OF ALERT.

We keep these processes separate because they're addressing mostly different endpoints and can benefit from
separation for concurrency.
"""
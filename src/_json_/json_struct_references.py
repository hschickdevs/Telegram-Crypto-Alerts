import json
import time
from os.path import join, dirname


def dump_alerts_db_config():
    """Dumps the default alerts database with 3 sample alerts included"""
    # indicators = ['PCTCHG', 'ABOVE', 'BELOW']

    above_alert_struct = {'indicator': 'ABOVE',
                          'target': 999999,
                          'alerted': False}

    below_alert_struct = {'indicator': 'BELOW',
                          'target': 1,
                          'alerted': False}

    pctchg_alert_struct = {"indicator": "PCTCHG",
                           "entry": 2000,
                           "target": 10.0,  # Targetting a 1000% change from 2500
                           "alerted": False}

    default_alerts_db = {'ETH/USDT': [above_alert_struct, below_alert_struct, pctchg_alert_struct]}

    with open(join(dirname(__file__), 'alerts_db.json'), 'w') as outfile:
        outfile.write(json.dumps(default_alerts_db, indent=2))


def dump_config(default_id: str = None):
    """Used if the user does not have a config yet created"""
    default_config = {
        "settings": {
            "delete_pushed_alerts": True,  # Delete alerts from the database after they have been fulfilled
            "price_polling_period": 10,  # Polling period in seconds to check the pair prices
            "pct_chg_alert_reset": 5,  # (AS A % ie 5% = 5) Percent change of the ticker to reset the PCTCHG alert
            "send_email_alerts": False,  # Send email alerts alongside of TG alerts
        },
        "emails": [],  # List of emails to receive indicator alerts (if send_email_alerts is True)
        "channels": [],  # List of Telegram channel IDs (e.g. [-123456789, -123456789]) to receive indicator alerts (can be a group or user ID)
        "administrators": [] if default_id is None else [default_id]
    }
    with open(join(dirname(__file__), 'config.json'), 'w') as outfile:
        outfile.write(json.dumps(default_config, indent=2))

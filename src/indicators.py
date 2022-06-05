"""
Features Needed:
* PathX taapi.io api key
* Aggregate each symbol and indicator, then pull all available indicators using the taapi.io client
* Allow the user to save indicator templates so that they don't have to enter long ones again
* Message to telegram should be a list of indicators with their documentation hyperlinked:
    - https://stackoverflow.com/questions/45268368/how-to-send-a-hyperlink-in-bot-sendmessage
    - Example:
      ABOVE
      BELOW
      PCTCHG
      MAXINDEX (Index of highest value over a specified period)
      MEDPRICE (Median Price)
      SAR (Parabolic Sar)
      SIN (Vector Trigonometric Sin)
* Need a combination of indicators (AND/OR)
"""
import json
from time import time, sleep
from os import getcwd, mkdir
from os.path import join, isdir, dirname, abspath
from typing import Optional

import requests

BINANCE_CALL_URL = 'https://api.binance.com/api/v3/ticker/price?symbol={}'  # format to token pair (ex: BTCUSDT)
TA_DB_PATH = join(dirname(abspath(__file__)), 'resources/ta_db.json')


def get_simple_indicator(pair: str, alert: dict) -> tuple[bool, float, str]:
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
    indicator = alert["indicator"]
    pair_price = get_pair_price(token_pair=pair.replace("/", ""))

    if indicator == 'PCTCHG':
        entry = alert['entry']
        if pair_price > entry * (1 + target):
            pct_chg = ((pair_price - entry) / entry) * 100
            return True, pct_chg, f"{pair} UP {pct_chg:.1f}% AT {pair_price}"
        elif pair_price < entry * (1 - target):
            pct_chg = ((entry - pair_price) / entry) * 100
            return True, pct_chg, f"{pair} DOWN {pct_chg:.1f}% AT {pair_price}"
    elif indicator == 'ABOVE':
        if pair_price > target:
            return True, pair_price, f"{pair} ABOVE {target} TARGET AT {pair_price}"
    elif indicator == 'BELOW':
        if pair_price < target:
            return True, pair_price, f"{pair} BELOW {target} TARGET AT {pair_price}"

    return False, 0, ""


def get_pair_price(token_pair, retry_delay: int = 2, maximum_retries: int = 5, _try: int = 1) -> float:
    """
    Make a request to Binance API and return the response

    :param token_pair: token pair without the slash (e.g. BTCUSDT)
    :param _try: The current try for recursive retries
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
            sleep(retry_delay)
            return get_pair_price(token_pair, _try=_try + 1)


class TADatabaseClient:
    def build_ta_db(self):
        pass

    def dump_ta_db(self, data: dict) -> None:
        """Update the technical analysis indicators database"""
        with open(TA_DB_PATH, 'w') as out:
            out.write(json.dumps(data, indent=2))

    def fetch_ta_db(self) -> dict:
        """Get the location of and return the technical analysis indicators database in JSON format"""
        return json.loads(open(TA_DB_PATH).read())


class TAAPIClient(TADatabaseClient):
    def __init__(self, taapi_io_apikey: str):
        self.taapi_key = taapi_io_apikey

    def get_technical_indicators(self, pair: str, interval: str, indicators_data: dict[dict]):
        """
        Should build a bundled API call for the given pair to fetch the status of each technical indicator in the DB

        :param pair: The crypto pair (e.g. ETH/USDT)
        :param interval: The common timeframe for the query (e.g. 15m, 1h, 1d)
        :param indicators_data: { "2CROWS": {"user_params": ["interval=15m", "backtrack=20"] } }
        """
        pass

    def get_technical_indicators_aggregate(self):
        """Aggregates all technical indicators across all whitelisted users and prepares the bulk queries"""
        pass

# Might need a daily utility to update the technical analysis database using webscraping

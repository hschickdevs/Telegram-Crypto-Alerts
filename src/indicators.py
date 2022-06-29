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

from .io_client import get_whitelist, UserConfiguration
from .static_config import INTERVALS

import requests
from ratelimit import limits, sleep_and_retry

BINANCE_CALL_URL = 'https://api.binance.com/api/v3/ticker/price?symbol={}'  # format to token pair (ex: BTCUSDT)
TA_DB_PATH = join(dirname(abspath(__file__)), 'resources/ta_db.json')
AGG_DATA_LOCATION = join(dirname(abspath(__file__)), 'temp/ta_aggregate.json')


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
    """This client should handle the cross-process operations of the technical analysis indicators database"""
    def dump_ta_db(self, data: dict) -> None:
        """Update the technical analysis indicators database"""
        with open(TA_DB_PATH, 'w') as out:
            out.write(json.dumps(data, indent=2))

    def fetch_ta_db(self) -> dict:
        """Get the location of and return the technical analysis indicators database in JSON format"""
        return json.loads(open(TA_DB_PATH).read())

    def add_indicator(self, indicator_id: str, name: str, endpoint: str, reference_url: str,
                      params: list[tuple[str, str, bool]], output: list[str]) -> None:
        """
        Add an indicator to the TA database

        :param indicator_id: The uppercase indicator ID a shown on taapi.io (e.g. 2CROWS)
        :param name: The indicator name as shown on taapi.io (e.g. Two Crows)
        :param endpoint: The endpoint URL following this format:
                         https://api.taapi.io/2crows?secret={api_key}&exchange=binance
        :param reference_url: The link to the indicator's documentation on taapi.io
        :param params: List of tuples containing parameter data
            - param_id: The ID for the parameter as shown on the API parameters documentation (e.g. "symbol")
            - param_description: A docstring that lets the user know what data the parameter expects
            - param_required: A bool indicating whether the parameter is required
        :param output: List of output variables that are returned by the API so that the user can choose which
                       to use, and so that the bot can know how to process the response.
                       NOTE: All return types for the output_values are considered as FLOAT
        """
        db = self.fetch_ta_db()
        db[indicator_id.upper()] = {"name": name, "endpoint": endpoint, "ref": reference_url,
                                    "params": params, "output": output}
        self.dump_ta_db(db)
        print(f"{name} ({indicator_id}) indicator added to TA database.")

    def get_indicator(self, _id: str):
        """Returns the indicator data from the database"""
        try:
            return self.fetch_ta_db()[_id.upper()]
        except KeyError:
            raise ValueError(f"'{_id}' is an invalid indicator ID")


class TAAggregateClient:
    def __int__(self):
        self.db = TADatabaseClient()

    def build_ta_aggregate(self):
        """
        Build the TA aggregate of all users' alert databases to update the technical analysis reference

        Structure Reference:

        {
            symbol: {
                interval: {
                    [bulk_query_formatted_alert]
                }
            }
        }
        """
        # indicators = self.db.fetch_ta_db().keys()
        agg = {}
        for user in get_whitelist():
            alerts_data = UserConfiguration(user).load_alerts()
            for symbol, alerts in alerts_data.items():
                if symbol not in agg.keys():
                    agg[symbol] = {}
                    for alert in alerts:
                        if alert['type'] == 's':
                            continue
                        if alert['interval'] not in agg[symbol].keys():
                            agg[symbol][alert['interval']] = []

                        formatted_alert = {"indicator": alert['indicator'].lower()}
                        for param, value in alert['params'].items():
                            formatted_alert[param] = value

                        if formatted_alert not in agg[symbol][alert['interval']]:
                            agg[symbol][alert['interval']].append(formatted_alert)

        self.dump_agg(agg)

    def dump_agg(self, data: dict) -> None:
        with open(AGG_DATA_LOCATION, 'w') as outfile:
            outfile.write(json.dumps(data, indent=2))

    def load_agg(self) -> dict:
        with open(AGG_DATA_LOCATION, 'r') as infile:
            return json.load(infile)


class TaapiioProcess:
    """Taapi.io process should be run in a separate thread to allow for sleeping between API calls"""
    def __init__(self, taapiio_apikey: str):
        self.apikey = taapiio_apikey
        self.last_call = 0
        self.db = TADatabaseClient()

    @sleep_and_retry
    @limits(calls=1, period=15)
    def call_api(self, endpoint: str, params: dict, r_type: str = "POST"):
        """Free API key limit is 1 call every 15 seconds"""
        if r_type == "GET":
            return requests.get(endpoint.format(api_key=self.apikey), params=params).json()
        elif r_type == "POST":
            return requests.post(endpoint, json=params).json()




    def run(self):
        pass
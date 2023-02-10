from os import mkdir, getcwd, getenv, listdir
from os.path import isdir, join, dirname, abspath, isfile, exists


"""Alert Handler Configuration"""
POLLING_PERIOD = 10  # Delay for the alert handler to pull prices and check alert conditions (in seconds)
BINANCE_PRICE_URL = 'https://api.binance.com/api/v3/ticker/price?symbol={}'  # format to token pair (ex: BTCUSDT)
BINANCE_24HR_URL = 'https://api.binance.com/api/v3/ticker/24hr'  # must be parsed to locate pair
SIMPLE_INDICATORS = ['PRICE']
SIMPLE_INDICATOR_COMPARISONS = ['ABOVE', 'BELOW', 'PCTCHG', '24HRCHG']
OUTPUT_VALUE_PRECISION = 3

"""Telegram Handler Configuration"""
MAX_ALERTS_PER_USER = 10  # Integer or None (Should be set in a static configuration file)

"""Paths"""
WHITELIST_ROOT = join(dirname(abspath(__file__)), 'whitelist')
RESOURCES_ROOT = join(dirname(abspath(__file__)), 'resources')
TA_DB_PATH = join(dirname(abspath(__file__)), 'resources/indicator_format_reference.json')
AGG_DATA_LOCATION = join(dirname(abspath(__file__)), 'temp/ta_aggregate.json')

"""TAAPI.IO"""
INTERVALS = ["1m", "5m", "15m", "30m", "1h", "2h", "4h", "12h", "1d", '1w']
DEFAULT_EXCHANGE = "binance"
BULK_ENDPOINT = "https://api.taapi.io/bulk"
RATE_LIMITS = (1, 15, 0.05)  # (requests per period in seconds, period in seconds, buffer percentage)
# TA_AGGREGATE_PPERIOD = 30  # TA Aggregate polling period, to poll technical indicators
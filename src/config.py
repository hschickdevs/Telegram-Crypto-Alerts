from os import mkdir, getcwd, getenv, listdir
from os.path import isdir, join, dirname, abspath, isfile, exists


"""Alert Handler Configuration"""
CEX_POLLING_PERIOD = 10  # Delay for the CEX alert handler to pull prices and check alert conditions (in seconds)
TECHNICAL_POLLING_PERIOD = 5  # Delay for the technical alert handler check technical alert conditions (in seconds)
OUTPUT_VALUE_PRECISION = 3
SIMPLE_INDICATORS = ["PRICE"]
SIMPLE_INDICATOR_COMPARISONS = ["ABOVE", "BELOW", "PCTCHG", "24HRCHG"]

"""Telegram Handler Configuration"""
MAX_ALERTS_PER_USER = (
    10  # Integer or None (Should be set in a static configuration file)
)

"""BINANCE DATA CONFIG"""
BINANCE_LOCATIONS = ["us", "global"]
BINANCE_PRICE_URL_GLOBAL = "https://api.binance.com/api/v3/ticker?symbol={}&windowSize={}"  # (e.x. BTCUSDT, 1d)
BINANCE_PRICE_URL_US = (
    "https://api.binance.us/api/v3/ticker?symbol={}&windowSize={}"  # (e.x. BTCUSDT, 1d
)
BINANCE_TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h", "2h", "4h", "12h", "1d", "7d"]

"""SWAP DATA CONFIG"""
SWAP_POLLING_DELAY = 30  # Swap polling delay (in seconds) to handle rate limits.

"""DATABASE PREFERENCES & PATHS"""
USE_MONGO_DB = False
WHITELIST_ROOT = join(dirname(abspath(__file__)), "whitelist")
RESOURCES_ROOT = join(dirname(abspath(__file__)), "resources")
TA_DB_PATH = join(
    dirname(abspath(__file__)), "resources/indicator_format_reference.json"
)
AGG_DATA_LOCATION = join(dirname(abspath(__file__)), "temp/ta_aggregate.json")

"""TAAPI.IO"""
INTERVALS = ["1m", "5m", "15m", "30m", "1h", "2h", "4h", "12h", "1d", "1w"]
DEFAULT_EXCHANGE = "binance"
BULK_ENDPOINT = "https://api.taapi.io/bulk"
SUBSCRIPTION_TIERS = {
    "free": (1, 20),
    "basic": (5, 15),
    "pro": (30, 15),
    "expert": (75, 15),
}  # (requests, per period in seconds)
REQUEST_BUFFER = 0.05  # buffer percentage for preventing rate limit errors (e.x. 0.05 = 5% of request period, so period * 1.05)

# TA_AGGREGATE_PPERIOD = 30  # TA Aggregate polling period, to poll technical indicators

"""Alert Handler Configuration"""
POLLING_PERIOD = 10  # Delay for the alert handler to pull prices and check alert conditions (in seconds)
BINANCE_CALL_URL = 'https://api.binance.com/api/v3/ticker/price?symbol={}'

"""Telegram Handler Configuration"""
MAX_ALERTS_PER_USER = 10  # Integer or None (Should be set in a static configuration file)

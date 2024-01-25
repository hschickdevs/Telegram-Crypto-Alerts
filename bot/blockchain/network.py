from ratelimit import limits, RateLimitException, sleep_and_retry
from web3 import Web3
from typing import Callable, Any
from functools import wraps
from threading import Lock

from ..util import load_swap_networks

class Network:
    """
    This class is responsible for managing the network Web3 RPC connections for the bot.
    It will be used to manage the rate limits and protocols on the network.
    """
    def __init__(self, network: str):
        self.id = network
        self.meta = load_swap_networks()[network]
        self.w3 = Web3
        self._connect()
        self.max_calls, self.period = self.meta['ratelimit']['requests'], self.meta['ratelimit']['period']
        self.lock = Lock()
        self.rate_limited_call = self._create_rate_limited_call()

    def _connect(self):
        self.w3 = Web3(Web3.HTTPProvider(self.meta['rpc']))
        assert self.w3.is_connected(), "Web3 cannot connect to the RPC URL."

    def _create_rate_limited_call(self):
        @sleep_and_retry
        @limits(calls=self.max_calls, period=self.period)
        def rate_limited_func(func, *args, **kwargs):
            print(f"Calling rate limited function {getattr(func, '__name__', 'Unknown')} with {self.max_calls} "
                  f"max_calls and {self.period} period.")
            return func(*args, **kwargs)
        return rate_limited_func

    def call(self, contract_function: Callable[..., Any], *args, **kwargs) -> Any:
        with self.lock:  # Ensuring thread safety
            return self.rate_limited_call(contract_function, *args, **kwargs).call()

    def call_raw(self, token_address: str, function_signature: bytes) -> bytes:
        with self.lock:  # Ensuring thread safety
            return self.rate_limited_call(self.w3.eth.call, {'to': token_address, 'data': function_signature.hex()})


from ratelimiter import RateLimiter
from web3 import Web3

from ..util import load_swap_networks


class Network:
    """
    This class is responsible for managing the network Web3 RPC connections for the bot. 
    It will be used to manage the ratelimits and protocols on the network.
    """
    def __init__(self, network: str):
        self.network = network
        
        # Load the network details from the networks.yml file
        self.meta = load_swap_networks()[network]
        
        # Attempt to connect to the network
        self.w3 = Web3
        self._connect(network)
        
        # Create rate limiter
        self.ratelimiter = self._get_ratelimiter()
        
        
        
    def _get_ratelimiter(self) -> RateLimiter:
        """Returns a RateLimiter object for the specified network"""
        
        network = load_swap_networks()[network]
        
        return RateLimiter(
            max_calls=self.meta['ratelimit']['requests'],
            period=self.meta['ratelimit']['period'],
        )
        
    def _connect(self):
        """
        Connect to the network RPC and return the Web3 object
        """
        self.w3 = Web3(Web3.HTTPProvider(self.meta['rpc']))
        assert self.w3.is_connected(), "Web3 cannot connect to the RPC URL."
        
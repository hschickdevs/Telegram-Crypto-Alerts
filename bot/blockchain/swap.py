import json
import os
from typing import Any, Callable
from web3 import Web3

from .network import Network
from .abi import *
from ..util import load_swap_protocols, load_swap_networks


class SwapClient:
    """
    Provides the functionality to track the price of any pair in a Uniswap V2 fork
    - Fork's Pair contract must implement the getReserves() method
    """

    def __init__(self, protocol: str, network: Network):
        """
        Args:
            protocol (str): The protocol you are interested in (e.g. "uniswap-v2"), see ./blockchain/protocol-data.json
            network (str): The network abbreviation you are interested in (e.g. "bnb"), see ./blockchain/networks.json
            rate_limiter (RateLimiter): Should be the RateLimiter instance declared for the given network
        """
        self.network = network

        try:
            protocol = load_swap_protocols()[protocol]
        except KeyError:
            raise KeyError(f"Protocol {protocol} not found in protocols.yml. Add it or check the spelling.")

        try:
            chain = protocol['chains'][network.id]
        except KeyError:
            raise KeyError(f"Network {network} not found in networks.json. Add it or check the spelling.")

        self.factory_address = Web3.to_checksum_address(chain['factory'])
        assert self.network.w3.eth.get_code(
            self.factory_address) != "0x", "Factory address is not a valid contract address."

        self.usd_stablecoin_address = Web3.to_checksum_address(chain['stablecoin'])
        assert self.network.w3.eth.get_code(
            self.usd_stablecoin_address) != "0x", "Stablecoin address is not a valid contract address."

    def get_pair_price(self, base_token_address: str, quote_token_address: str,
                       pair_contract_metadata: dict = None) -> float:
        """Gets the price of the pair in the quote token

        Args:
            base_token_address (str, optional): Token address for the base token when fetching pair price
            quote_token_address (str, optional): Token address for the quote token when fetching pair price
            pair_contract_metadata (dict, optional): Include the pair contract metadata if it already exists for efficiency

        Returns:
            float: The computed pair price in the quote token or USD, in the direction of base_token_address -> quote_token_address
        """
        if not pair_contract_metadata:
            # This function call adds 7 web3 calls, so this data should be stored or cached and provided to the func
            pair_contract_metadata = self.get_pair(base_token_address, quote_token_address)

        # Construct the pair string:
        # pair_string = f"{pair_contract_metadata['token0']['symbol']}-{pair_contract_metadata['token1']['symbol']}"
        # print("Fetching price for pair:", pair_string)

        reserves = self.get_pair_reserves(pair_contract_metadata['address'])

        # Get the decimals for each token
        base_decimals = pair_contract_metadata["token0"]["decimals"]
        quote_decimals = pair_contract_metadata["token1"]["decimals"]

        # Determine the order of reserves based on the tokens
        if pair_contract_metadata["token0"]["address"] == Web3.to_checksum_address(base_token_address):
            reserve_base = reserves[0]
            reserve_quote = reserves[1]
        else:
            reserve_base = reserves[1]
            reserve_quote = reserves[0]

        if reserve_base == 0:
            return 0
            # raise ValueError("Reserve for base token is zero, cannot calculate pair price.")
        if reserve_quote == 0:
            return 0
            # raise ValueError("Reserve for quote token is zero, cannot calculate pair price.")

        # Calculate the price based on the reserves
        # print("reserve_quote:", reserve_quote)
        # print("reserve_base:", reserve_base)
        price = reserve_quote / reserve_base

        # Adjust the price for the different decimals between the base and quote tokens
        # price *= 10 ** (quote_decimals - base_decimals)
        price = price * 10 ** (base_decimals - quote_decimals)  # ATTEMPTED FIX

        return price

    def get_pair_reserves(self, pair_address: str) -> dict:
        contract = self.network.w3.eth.contract(address=Web3.to_checksum_address(pair_address), abi=UNISWAPV2_PAIR_ABI)

        return self.network.call(contract.functions.getReserves)

    def get_pair(self, base_token_address: str, quote_token_address: str) -> dict:
        """
        Gets the pair metadata for the given base and quote tokens
        > Should be called before get_pair_price() if needed to avoid redundant calls to the blockchain
        REF: https://github.com/Uniswap/v2-core/blob/master/contracts/UniswapV2Pair.sol

        Args:
            base_token_address (str): Base token address
            quote_token_address (str): Quote token address

        Returns:
            dict: The pair metadata {
                "pair_address": str, 
                "token0": {"address": str, "symbol": str}, 
                "token1": {"address": str, "symbol": str}
                }
            Where token0 is the base token in the pair contract,
            and token1 is the quote token in the pair contract
        """
        contract = self.network.w3.eth.contract(address=Web3.to_checksum_address(self.factory_address),
                                                abi=GET_PAIR_ABI)

        # Check if the pair exists:
        pair_address = self.network.call(contract.functions.getPair,
                                         Web3.to_checksum_address(base_token_address),
                                         Web3.to_checksum_address(quote_token_address))
        # pair_address = contract.functions.getPair(Web3.to_checksum_address(base_token_address),
        #                                           Web3.to_checksum_address(quote_token_address)).call()

        pair_contract = self.network.w3.eth.contract(address=Web3.to_checksum_address(pair_address),
                                                     abi=UNISWAPV2_PAIR_ABI)

        # Get the token pair metadata
        # token0_address = pair_contract.functions.token0().call()
        token0_address = self.network.call(pair_contract.functions.token0)
        token0_symbol = self.get_token_symbol(token0_address)
        # token1_address = pair_contract.functions.token1().call()
        token1_address = self.network.call(pair_contract.functions.token1)
        token1_symbol = self.get_token_symbol(token1_address)

        return {
            "address": Web3.to_checksum_address(pair_address),
            "token0": {"address": Web3.to_checksum_address(token0_address), "symbol": token0_symbol,
                       "decimals": self.get_token_decimals(token0_address)},
            "token1": {"address": Web3.to_checksum_address(token1_address), "symbol": token1_symbol,
                       "decimals": self.get_token_decimals(token1_address)}
        }

    def get_token_symbol(self, token_address: str) -> str:
        """Returns the ERC20 token symbol.

        Args:
            token_address (str): Token address

        Returns:
            str: Token symbol
        """
        contract = self.network.w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=ERC20_ABI)

        try:
            # First, try the regular call
            symbol_value = self.network.call(contract.functions.symbol)

            # Check if the result is bytes (indicating bytes32 return type)
            if isinstance(symbol_value, bytes):
                return symbol_value.decode('utf-8').rstrip('\x00')
            else:
                return symbol_value

        # Handle the rare case that a token will use bytes32 instead of string for symbol() output value
        except Exception as e:
            # If the regular call fails, try the raw call
            print(f"Regular symbol call failed with error: {e}. Retrying with raw call...")

            # Generate the function signature for the `symbol` function
            symbol_function_signature = self.network.w3.keccak(text="symbol()")[:10]

            # Make a raw call to the contract
            result = self.network.call_raw(token_address, symbol_function_signature)

            # Decode the result. If it's bytes32, it will have trailing null bytes which we remove.
            symbol = result.decode('utf-8').rstrip('\x00')

            return symbol

    def get_token_decimals(self, token_address: str) -> int:
        """Returns the ERC20 token decimals.

        Args:
            token_address (str): Token address

        Returns:
            int: Token decimals
        """
        contract = self.network.w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=ERC20_ABI)

        # return contract.functions.decimals().call()
        return self.network.call(contract.functions.decimals)

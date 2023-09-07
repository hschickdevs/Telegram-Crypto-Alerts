import json
import os
from web3 import Web3

from .blockchain.abi import *
from .io_clients import load_swap_protocols


class SwapClient:
    """
    Provides the functionality to track the price of any pair in a Uniswap V2 fork
    - Fork's Pair contract must implement the getReserves() method
    """

    def __init__(self, protocol: str, network: str):
        """
        Args:
            protocol (str): The protocol you are interested in (e.g. "uniswap-v2"), see ./blockchain/protocol-data.json
            network (str): The network abbreviation you are interested in (e.g. "bnb"), see ./blockchain/networks.json
        """
        try:
            protocol = load_swap_protocols()[protocol]
        except KeyError:
            raise KeyError(f"Protocol {protocol} not found in protocol-data.json. Add it or check the spelling.")

        try:
            chain = protocol['chains'][network]
        except KeyError:
            raise KeyError(f"Network {network} not found in networks.json. Add it or check the spelling.")

        self.w3 = Web3(Web3.HTTPProvider(chain['rpc_url']))
        assert self.w3.is_connected(), "Web3 cannot connect to the RPC URL."

        self.factory_address = Web3.to_checksum_address(chain['factory'])
        assert self.w3.eth.get_code(self.factory_address) != "0x", "Factory address is not a valid contract address."

        self.usd_stablecoin_address = Web3.to_checksum_address(chain['stablecoin'])
        assert self.w3.eth.get_code(
            self.usd_stablecoin_address) != "0x", "Stablecoin address is not a valid contract address."

    def get_pair_price(self, base_token_address: str, quote_token_address: str, in_usd: bool = False,
                       pair_contract_metadata: dict = None) -> float:
        """Gets the price of the pair in the quote token

        Args:
            base_token_address (str, optional): Token address for the base token when fetching pair price
            quote_token_address (str, optional): Token address for the quote token when fetching pair price
            in_usd (bool, optional): Whether to return the pair price converted to USD (uses the quote-usd_stablecoin pair). Defaults to False.
            pair_contract_metadata (dict, optional): Include the pair contract metadata if it already exists for efficiency

        Returns:
            float: The computed pair price in the quote token or USD, in the direction of base_token_address -> quote_token_address
        """
        # TODO: The metadata of pairs should be stored when alerts are created to make this process more efficient
        if not pair_contract_metadata:
            pair_contract_metadata = self.get_pair(base_token_address, quote_token_address)

        contract = self.w3.eth.contract(address=pair_contract_metadata['address'], abi=UNISWAPV2_PAIR_ABI)
        reserves = contract.functions.getReserves().call()

        # Determine the order of reserves based on the tokens
        if pair_contract_metadata["token0"]["address"] == Web3.to_checksum_address(base_token_address):
            reserve_base = reserves[0]
            reserve_quote = reserves[1]
        else:
            reserve_base = reserves[1]
            reserve_quote = reserves[0]

        if reserve_base == 0:
            raise ValueError("Reserve for base token is zero, cannot calculate pair price.")
        if reserve_quote == 0:
            raise ValueError("Reserve for quote token is zero, cannot calculate pair price.")

        # Calculate the price based on the reserves
        price = reserve_quote / reserve_base
        if in_usd:
            usd_price = self.get_pair_price(base_token_address=self.usd_stablecoin_address,
                                            quote_token_address=quote_token_address)
            price *= usd_price

        return price

    def get_pair(self, base_token_address: str, quote_token_address: str) -> dict:
        """Gets the pair metadata for the given base and quote tokens
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
        contract = self.w3.eth.contract(address=Web3.to_checksum_address(self.factory_address), abi=GET_PAIR_ABI)

        # Check if the pair exists:
        pair_address = contract.functions.getPair(Web3.to_checksum_address(base_token_address),
                                                  Web3.to_checksum_address(quote_token_address)).call()
        pair_contract = self.w3.eth.contract(address=Web3.to_checksum_address(pair_address), abi=UNISWAPV2_PAIR_ABI)

        # Get the token pair metadata
        token0_address = pair_contract.functions.token0().call()
        token0_symbol = self.get_token_symbol(token0_address)
        token1_address = pair_contract.functions.token1().call()
        token1_symbol = self.get_token_symbol(token1_address)

        return {
            "address": Web3.to_checksum_address(pair_address),
            "token0": {"address": Web3.to_checksum_address(token0_address), "symbol": token0_symbol},
            "token1": {"address": Web3.to_checksum_address(token1_address), "symbol": token1_symbol}
        }

    def get_token_symbol(self, token_address: str) -> str:
        """Returns the ERC20 token symbol.

        Args:
            token_address (str): Token address

        Returns:
            str: Token symbol
        """

        contract = self.w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=GET_SYMBOL_ABI)

        return contract.functions.symbol().call()

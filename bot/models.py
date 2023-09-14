from dataclasses import dataclass


@dataclass
class TechnicalAlert:
    """
    Models technical indicator alerts - fetched from Taapi.io.
    """
    pair: str
    indicator: str
    interval: str
    params: dict
    output_vals: list
    endpoint: str
    name: str
    type: str = 't'


@dataclass
class CEXAlert:
    """
    Models centralized exchange alerts - currently only Binance pairs.
    """
    pair: str
    indicator: str
    params: dict = None
    type: str = 's'


@dataclass
class DEXAlert:
    pair: str
    metadata: dict
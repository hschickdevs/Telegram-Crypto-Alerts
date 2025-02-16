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
    type: str = "t"


@dataclass
class CEXAlert:
    """
    Models centralized exchange alerts - currently only Binance pairs.
    """

    pair: str
    indicator: str
    params: dict = None
    type: str = "s"


class BinancePriceResponse:
    def __init__(self, response_data: dict):
        # Extract the variables from the response data and initialize them
        self.symbol = str(response_data.get("symbol", ""))
        self.priceChange = float(response_data.get("priceChange", 0.0))
        self.priceChangePercent = float(response_data.get("priceChangePercent", 0.0))
        self.weightedAvgPrice = float(response_data.get("weightedAvgPrice", 0.0))
        self.openPrice = float(response_data.get("openPrice", 0.0))
        self.highPrice = float(response_data.get("highPrice", 0.0))
        self.lowPrice = float(response_data.get("lowPrice", 0.0))
        self.lastPrice = float(response_data.get("lastPrice", 0.0))
        self.volume = float(response_data.get("volume", 0.0))
        self.quoteVolume = float(response_data.get("quoteVolume", 0.0))
        self.openTime = int(response_data.get("openTime", 0))
        self.closeTime = int(response_data.get("closeTime", 0))
        self.firstId = int(response_data.get("firstId", 0))
        self.lastId = int(response_data.get("lastId", 0))
        self.count = int(response_data.get("count", 0))
        self.window = (
            str(response_data.get("window", "")) if "window" in response_data else None
        )
        self.location = (
            str(response_data.get("location", ""))
            if "location" in response_data
            else None
        )

    def to_dict(self):
        return {
            "symbol": self.symbol,
            "priceChange": self.priceChange,
            "priceChangePercent": self.priceChangePercent,
            "weightedAvgPrice": self.weightedAvgPrice,
            "openPrice": self.openPrice,
            "highPrice": self.highPrice,
            "lowPrice": self.lowPrice,
            "lastPrice": self.lastPrice,
            "volume": self.volume,
            "quoteVolume": self.quoteVolume,
            "openTime": self.openTime,
            "closeTime": self.closeTime,
            "firstId": self.firstId,
            "lastId": self.lastId,
            "count": self.count,
            "window": self.window,
            "location": self.location,
        }

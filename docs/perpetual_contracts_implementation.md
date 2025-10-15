# Perpetual Contracts Support - Implementation Guide

This document outlines a proposed approach for adding support for perpetual (futures) contracts to the Telegram Crypto Alerts bot.

## Overview

Currently, the bot only supports spot trading pairs from Binance. Adding perpetual contracts would allow users to:
- Set alerts on futures prices and technical indicators
- Monitor funding rates
- Track open interest changes
- Receive alerts on liquidation levels

## Implementation Approach

### 1. API Endpoint Updates

**Current:** 
- Spot API: `https://api.binance.com/api/v3/ticker`

**New - Futures:**
- Futures USD-M API: `https://fapi.binance.com/fapi/v1/ticker/24hr`
- Futures COIN-M API: `https://dapi.binance.com/dapi/v1/ticker/24hr`

### 2. Configuration Changes

Add to `src/config.py`:

```python
"""BINANCE FUTURES CONFIG"""
BINANCE_FUTURES_URL_GLOBAL = "https://fapi.binance.com/fapi/v1/ticker/24hr?symbol={}"
BINANCE_FUTURES_URL_US = "https://fapi.binance.us/fapi/v1/ticker/24hr?symbol={}"
BINANCE_FUTURES_FUNDING_RATE_URL = "https://fapi.binance.com/fapi/v1/fundingRate?symbol={}"
```

### 3. Alert Model Extensions

Update `src/models.py` to support futures contracts:

```python
@dataclass
class CEXAlert:
    """
    Models centralized exchange alerts - currently only Binance pairs.
    """
    pair: str
    indicator: str
    market_type: str = "spot"  # Add: "spot", "futures-usd", "futures-coin"
    params: dict = None
    type: str = "s"
```

### 4. Command Syntax Updates

#### New Alert Command Format:

```
/new_alert <BASE/QUOTE> <MARKET_TYPE> <INDICATOR> <COMPARISON> <TARGET> <optional_COOLDOWN>
```

Where `MARKET_TYPE` can be:
- `SPOT` (default, maintains backward compatibility)
- `FUTURES` or `PERP` (for USD-M perpetual contracts)
- `COIN-PERP` (for COIN-M perpetual contracts)

#### Examples:

```
# Set alert for BTC perpetual future price
/new_alert BTC/USDT FUTURES PRICE ABOVE 50000

# Set alert for ETH spot price (backward compatible)
/new_alert ETH/USDT PRICE ABOVE 2000

# Or explicitly specify SPOT
/new_alert ETH/USDT SPOT PRICE ABOVE 2000
```

### 5. New Futures-Specific Indicators

Add support for futures-specific indicators:

#### Funding Rate Alert
```
/new_alert BTC/USDT FUTURES FUNDING_RATE ABOVE 0.05
```

#### Open Interest Alert
```
/new_alert ETH/USDT FUTURES OPEN_INTEREST PCTCHG 10.0
```

#### Mark Price vs Index Price
```
/new_alert BTC/USDT FUTURES MARK_INDEX_SPREAD ABOVE 50
```

### 6. Implementation Steps

1. **Add Futures Price Fetching Method** in `src/telegram.py`:
   ```python
   def get_futures_price(self, symbol: str, market_type: str = "usd-m") -> dict:
       """Fetch futures contract price from Binance Futures API"""
       # Implementation here
   ```

2. **Update CEX Alert Process** in `src/alert_processes/cex.py`:
   - Modify price checking logic to handle futures contracts
   - Add support for futures-specific indicators

3. **Update Command Parsers**:
   - Modify `parse_simple_indicator_message()` to handle market type
   - Add validation for futures-specific parameters

4. **Add Market Type Indicator** in alerts display:
   - Show `[SPOT]`, `[FUTURES]`, or `[COIN-PERP]` next to pair names

5. **Update Documentation**:
   - Add examples for futures alerts
   - Document new indicators and their parameters

### 7. Technical Considerations

#### Backward Compatibility
- Make `market_type` optional with default value of "spot"
- Existing alerts continue to work without modification
- Old command syntax remains valid

#### Rate Limiting
- Futures API has different rate limits than spot
- May need separate rate limiter for futures endpoints

#### Symbol Formatting
- Spot: `BTCUSDT`
- Futures: `BTCUSDT` (same format, different endpoint)
- Coin-M: `BTCUSD_PERP` (different format)

#### Data Persistence
- Update JSON schema to include `market_type` field
- Provide migration script for existing alerts

### 8. Testing Strategy

1. **Unit Tests**:
   - Test futures price fetching
   - Test command parsing with new market type parameter
   - Test backward compatibility

2. **Integration Tests**:
   - Test alert creation for futures contracts
   - Test alert triggering for futures prices
   - Test mixed spot and futures alerts

3. **Manual Testing**:
   - Create alerts for different market types
   - Verify prices are fetched correctly
   - Test with rate limiting scenarios

### 9. Example Implementation Snippets

#### Update Alert Creation:

```python
def parse_simple_indicator_message(self, message: str) -> CEXAlert:
    """Parse simple indicator message with optional market type"""
    splt_msg = self.split_message(message)
    pair = splt_msg[0]
    
    # Check if market type is specified
    if len(splt_msg) >= 2 and splt_msg[1].upper() in ["SPOT", "FUTURES", "PERP", "COIN-PERP"]:
        market_type = "futures" if splt_msg[1].upper() in ["FUTURES", "PERP"] else splt_msg[1].lower()
        indicator = splt_msg[2]
        comparison = splt_msg[3]
        target = float(splt_msg[4])
        # ... rest of parsing
    else:
        # Backward compatible: no market type specified
        market_type = "spot"
        indicator = splt_msg[1]
        comparison = splt_msg[2]
        target = float(splt_msg[3])
        # ... rest of parsing
    
    return CEXAlert(
        pair=pair,
        indicator=indicator,
        market_type=market_type,
        # ... other params
    )
```

### 10. Future Enhancements

- Support for funding rate history alerts
- Liquidation cascade alerts
- Open interest divergence alerts
- Basis spread alerts (spot vs futures)
- Support for other exchanges (FTX, Bybit, etc.)

### 11. Resources

- [Binance Futures API Documentation](https://binance-docs.github.io/apidocs/futures/en/)
- [Binance USD-M Futures](https://fapi.binance.com/)
- [Binance COIN-M Futures](https://dapi.binance.com/)

## Migration Path for Users

1. Existing spot alerts continue to work unchanged
2. Users can gradually add futures alerts using new syntax
3. Bot displays market type in alert listings
4. Users can filter alerts by market type in future versions

## Security Considerations

- Validate market type input to prevent API injection
- Ensure proper error handling for different API responses
- Rate limit futures requests separately from spot

## Conclusion

This implementation provides a clear path to add perpetual contracts support while maintaining backward compatibility and setting the foundation for additional futures-specific features.

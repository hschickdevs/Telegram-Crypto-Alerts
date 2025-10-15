# Webhook Feature Implementation Guide

This document outlines the implementation approach for adding webhook support to the Telegram Crypto Alerts bot, allowing alerts to trigger HTTP requests to external services.

## Overview

The webhook feature will enable users to integrate the bot with their existing trading systems, automation platforms, or custom applications by sending HTTP requests when alerts are triggered.

## Use Cases

- **Trading Automation**: Trigger automated trades through external trading bots
- **Notification Systems**: Send alerts to Discord, Slack, or other platforms
- **Data Logging**: Record alert events to external databases
- **Dashboard Updates**: Trigger UI updates in custom dashboards
- **Integration Platforms**: Connect to Zapier, IFTTT, n8n, or similar services
- **Portfolio Management**: Update positions in portfolio tracking systems

## Implementation Approach

### 1. Alert Model Extension

Update `src/models.py` to support webhook configuration:

```python
@dataclass
class WebhookConfig:
    """Configuration for webhook notifications"""
    url: str
    method: str = "POST"  # POST, GET, PUT
    headers: dict = None
    payload_template: dict = None
    retry_count: int = 3
    timeout: int = 10

@dataclass
class CEXAlert:
    """
    Models centralized exchange alerts - currently only Binance pairs.
    """
    pair: str
    indicator: str
    params: dict = None
    webhook: WebhookConfig = None  # Add webhook support
    type: str = "s"

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
    webhook: WebhookConfig = None  # Add webhook support
    type: str = "t"
```

### 2. Command Syntax

#### Basic Webhook Alert:
```
/new_alert <...standard params...> webhook_url=https://example.com/webhook
```

#### Advanced Webhook Alert with Custom Payload:
```
/new_alert <...standard params...> webhook_url=https://example.com/webhook webhook_method=POST webhook_payload={"alert":"triggered","pair":"BTC/USDT"}
```

#### Examples:

**Simple Price Alert with Webhook:**
```
/new_alert BTC/USDT PRICE ABOVE 50000 1h webhook_url=https://my-server.com/alert
```

**Technical Indicator Alert with Custom Webhook:**
```
/new_alert ETH/USDT RSI 1h default value ABOVE 70 webhook_url=https://api.example.com/webhook webhook_method=POST webhook_payload={"type":"rsi_overbought"}
```

**Integration with n8n:**
```
/new_alert BTC/USDT PRICE BELOW 30000 webhook_url=https://n8n.example.com/webhook/crypto-alert
```

### 3. Configuration Updates

Add to `src/config.py`:

```python
"""WEBHOOK CONFIGURATION"""
WEBHOOK_ENABLED = True
WEBHOOK_TIMEOUT = 10  # seconds
WEBHOOK_MAX_RETRIES = 3
WEBHOOK_RETRY_DELAY = 2  # seconds between retries
WEBHOOK_MAX_URL_LENGTH = 500
WEBHOOK_ALLOWED_METHODS = ["GET", "POST", "PUT", "PATCH"]
WEBHOOK_USER_AGENT = "Telegram-Crypto-Alerts-Bot/3.2.0"
```

### 4. Webhook Handler Implementation

Create new file `src/webhook_handler.py`:

```python
import requests
import json
import time
from typing import Optional, Dict
from .logger import logger
from .config import (
    WEBHOOK_TIMEOUT,
    WEBHOOK_MAX_RETRIES,
    WEBHOOK_RETRY_DELAY,
    WEBHOOK_USER_AGENT,
)


class WebhookHandler:
    """Handles webhook notifications for triggered alerts"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": WEBHOOK_USER_AGENT})

    def send_webhook(
        self,
        url: str,
        method: str = "POST",
        payload: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        alert_data: Optional[Dict] = None,
    ) -> bool:
        """
        Send webhook notification with retry logic
        
        :param url: Webhook URL
        :param method: HTTP method (GET, POST, PUT, PATCH)
        :param payload: Custom payload (if None, uses default alert_data)
        :param headers: Custom headers
        :param alert_data: Alert information to send
        :return: True if successful, False otherwise
        """
        if payload is None and alert_data is not None:
            payload = self._build_default_payload(alert_data)

        request_headers = headers or {}
        if method in ["POST", "PUT", "PATCH"] and "Content-Type" not in request_headers:
            request_headers["Content-Type"] = "application/json"

        for attempt in range(1, WEBHOOK_MAX_RETRIES + 1):
            try:
                logger.info(f"Sending webhook to {url} (attempt {attempt}/{WEBHOOK_MAX_RETRIES})")
                
                if method == "GET":
                    response = self.session.get(
                        url, params=payload, headers=request_headers, timeout=WEBHOOK_TIMEOUT
                    )
                elif method in ["POST", "PUT", "PATCH"]:
                    response = self.session.request(
                        method,
                        url,
                        json=payload,
                        headers=request_headers,
                        timeout=WEBHOOK_TIMEOUT,
                    )
                else:
                    logger.error(f"Unsupported HTTP method: {method}")
                    return False

                response.raise_for_status()
                logger.info(f"Webhook sent successfully to {url}")
                return True

            except requests.exceptions.Timeout:
                logger.warning(f"Webhook timeout for {url} (attempt {attempt})")
            except requests.exceptions.RequestException as e:
                logger.error(f"Webhook error for {url}: {str(e)}")
            
            if attempt < WEBHOOK_MAX_RETRIES:
                time.sleep(WEBHOOK_RETRY_DELAY)

        logger.error(f"Failed to send webhook to {url} after {WEBHOOK_MAX_RETRIES} attempts")
        return False

    def _build_default_payload(self, alert_data: Dict) -> Dict:
        """Build default webhook payload from alert data"""
        return {
            "timestamp": alert_data.get("timestamp"),
            "alert_type": alert_data.get("type"),
            "pair": alert_data.get("pair"),
            "indicator": alert_data.get("indicator"),
            "comparison": alert_data.get("comparison"),
            "target": alert_data.get("target"),
            "current_value": alert_data.get("current_value"),
            "message": alert_data.get("message"),
        }

    def validate_webhook_url(self, url: str) -> bool:
        """Validate webhook URL"""
        from urllib.parse import urlparse
        
        try:
            result = urlparse(url)
            return all([result.scheme in ["http", "https"], result.netloc])
        except:
            return False
```

### 5. Integration with Alert Processes

Update `src/alert_processes/cex.py` and `src/alert_processes/technical.py`:

```python
from ..webhook_handler import WebhookHandler

class CEXAlertProcess:
    def __init__(self, telegram_bot: TelegramBot):
        self.telegram_bot = telegram_bot
        self.webhook_handler = WebhookHandler()  # Add webhook handler
        # ... existing code

    def check_alert(self, alert_data, current_price):
        # ... existing alert checking logic
        
        if alert_triggered:
            # Send Telegram message (existing functionality)
            self.telegram_bot.send_message(...)
            
            # Send webhook if configured
            if alert_data.get("webhook"):
                webhook_config = alert_data["webhook"]
                alert_info = {
                    "timestamp": datetime.now().isoformat(),
                    "type": "simple",
                    "pair": alert_data["pair"],
                    "indicator": alert_data["indicator"],
                    "comparison": alert_data["comparison"],
                    "target": alert_data["target"],
                    "current_value": current_price,
                    "message": f"{alert_data['pair']} {alert_data['indicator']} alert triggered",
                }
                
                self.webhook_handler.send_webhook(
                    url=webhook_config["url"],
                    method=webhook_config.get("method", "POST"),
                    payload=webhook_config.get("payload_template"),
                    headers=webhook_config.get("headers"),
                    alert_data=alert_info,
                )
```

### 6. Command Parser Updates

Update `src/telegram.py` to parse webhook parameters:

```python
def parse_webhook_params(self, message_text: str) -> Optional[WebhookConfig]:
    """
    Parse webhook parameters from command message
    
    Looks for:
    - webhook_url=<url>
    - webhook_method=<GET|POST|PUT|PATCH>
    - webhook_payload=<json>
    - webhook_headers=<json>
    """
    import re
    
    webhook_url_match = re.search(r'webhook_url=(\S+)', message_text)
    if not webhook_url_match:
        return None
    
    url = webhook_url_match.group(1)
    
    # Validate URL
    webhook_handler = WebhookHandler()
    if not webhook_handler.validate_webhook_url(url):
        raise ValueError(f"Invalid webhook URL: {url}")
    
    # Parse optional method
    method_match = re.search(r'webhook_method=(\w+)', message_text)
    method = method_match.group(1).upper() if method_match else "POST"
    
    # Parse optional payload
    payload_match = re.search(r'webhook_payload=(\{.+?\})', message_text)
    payload = None
    if payload_match:
        try:
            payload = json.loads(payload_match.group(1))
        except json.JSONDecodeError:
            raise ValueError("Invalid webhook payload JSON")
    
    # Parse optional headers
    headers_match = re.search(r'webhook_headers=(\{.+?\})', message_text)
    headers = None
    if headers_match:
        try:
            headers = json.loads(headers_match.group(1))
        except json.JSONDecodeError:
            raise ValueError("Invalid webhook headers JSON")
    
    return WebhookConfig(
        url=url,
        method=method,
        payload_template=payload,
        headers=headers,
    )
```

### 7. Security Considerations

#### URL Validation
- Whitelist allowed protocols (http, https only)
- Block internal IP addresses (127.0.0.1, 10.x.x.x, 192.168.x.x, etc.)
- Validate URL length
- Sanitize user input

#### Rate Limiting
- Limit webhook calls per user per hour
- Implement backoff for failed webhooks
- Queue webhook requests to prevent blocking

#### Data Privacy
- Don't log sensitive webhook URLs
- Mask webhook URLs in error messages
- Allow users to use environment variables for webhook URLs

Example security implementation:

```python
def is_safe_webhook_url(url: str) -> bool:
    """Check if webhook URL is safe to call"""
    from urllib.parse import urlparse
    import ipaddress
    
    parsed = urlparse(url)
    
    # Only allow http/https
    if parsed.scheme not in ["http", "https"]:
        return False
    
    # Try to resolve hostname
    try:
        import socket
        hostname = parsed.hostname
        if not hostname:
            return False
        
        # Get IP address
        ip = socket.gethostbyname(hostname)
        ip_obj = ipaddress.ip_address(ip)
        
        # Block private/internal IPs
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local:
            logger.warning(f"Blocked webhook to private IP: {ip}")
            return False
            
    except (socket.gaierror, ValueError) as e:
        logger.error(f"Could not resolve webhook hostname: {e}")
        return False
    
    return True
```

### 8. Testing Strategy

#### Unit Tests:
```python
def test_webhook_handler():
    handler = WebhookHandler()
    
    # Test successful webhook
    result = handler.send_webhook(
        url="https://webhook.site/unique-id",
        payload={"test": "data"}
    )
    assert result is True

def test_webhook_validation():
    handler = WebhookHandler()
    
    # Valid URLs
    assert handler.validate_webhook_url("https://example.com/webhook")
    
    # Invalid URLs
    assert not handler.validate_webhook_url("ftp://example.com")
    assert not handler.validate_webhook_url("not-a-url")
```

#### Integration Tests:
- Test with webhook.site for debugging
- Test retry logic with timeout scenarios
- Test with different HTTP methods
- Test with various payload formats

### 9. Documentation Updates

Add to README.md:

```markdown
### Webhook Alerts

You can configure alerts to send webhooks to external services when triggered:

```
/new_alert BTC/USDT PRICE ABOVE 50000 webhook_url=https://example.com/webhook
```

**Webhook Parameters:**
- `webhook_url` (required): The URL to send the webhook to
- `webhook_method` (optional): HTTP method (default: POST)
- `webhook_payload` (optional): Custom JSON payload

**Default Webhook Payload:**
```json
{
  "timestamp": "2024-10-15T10:30:00Z",
  "alert_type": "simple",
  "pair": "BTC/USDT",
  "indicator": "PRICE",
  "comparison": "ABOVE",
  "target": 50000,
  "current_value": 50100,
  "message": "BTC/USDT PRICE alert triggered"
}
```
```

### 10. Future Enhancements

- **Webhook Templates**: Pre-defined templates for popular services (Discord, Slack, etc.)
- **Webhook Testing**: `/test_webhook <url>` command to verify webhook configuration
- **Webhook History**: Log webhook delivery status and responses
- **Authentication**: Support for Bearer tokens, API keys in headers
- **Webhook Groups**: Send to multiple webhooks for a single alert
- **Conditional Webhooks**: Only fire webhook on specific conditions
- **Webhook Filtering**: Filter which alert types trigger webhooks

### 11. Example Integrations

#### Discord Webhook:
```
/new_alert BTC/USDT PRICE ABOVE 50000 webhook_url=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN webhook_payload={"content":"BTC price alert triggered!"}
```

#### n8n Workflow:
```
/new_alert ETH/USDT RSI 1h default value ABOVE 70 webhook_url=https://your-n8n.com/webhook/crypto-rsi-alert
```

#### Zapier Webhook:
```
/new_alert BTC/USDT PRICE BELOW 30000 webhook_url=https://hooks.zapier.com/hooks/catch/YOUR_HOOK_ID/
```

## Migration Path

1. Webhook parameters are optional - existing alerts work unchanged
2. Users can add webhooks to new alerts
3. Future version could allow adding webhooks to existing alerts via `/edit_alert` command

## Conclusion

This webhook feature provides powerful integration capabilities while maintaining the bot's simplicity and security. The implementation is backward-compatible and extensible for future enhancements.

# Linked Alerts Implementation Guide

This document outlines the implementation approach for adding linked (conditional) alerts to the Telegram Crypto Alerts bot, allowing alerts to trigger only when multiple conditions are satisfied.

## Overview

Linked alerts enable users to create sophisticated alert conditions by requiring multiple indicators to meet specific criteria simultaneously. This is useful for technical trading strategies that rely on multiple confluent signals.

## Use Cases

- **Technical Confluence**: Alert when both RSI > 70 AND price crosses MA200
- **Divergence Detection**: Alert when price makes new high BUT RSI doesn't
- **Multi-Timeframe Analysis**: Alert when 1h RSI > 70 AND 4h RSI > 65
- **Complex Conditions**: Alert when (RSI > 70 OR MACD crosses) AND price > resistance level
- **Risk Management**: Alert only if stop-loss level is hit AND volume is high
- **Sequential Triggers**: Alert for condition B only if condition A triggered first

## Alert Dependency Types

### 1. AND Logic (All Conditions Must Be Met)
```
Alert triggers only when ALL linked conditions are true simultaneously
```

### 2. OR Logic (Any Condition Can Trigger)
```
Alert triggers when ANY of the linked conditions is true
```

### 3. Sequential (Conditions Must Occur in Order)
```
Alert triggers only after conditions A, then B, then C occur in sequence
```

### 4. NOT Logic (Inverse Condition)
```
Alert triggers when condition A is true AND condition B is NOT true
```

## Implementation Approach

### 1. Alert Model Extension

Update `src/models.py` to support alert dependencies:

```python
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class LinkType(Enum):
    """Types of alert linking"""
    AND = "and"
    OR = "or"
    SEQUENTIAL = "sequential"
    NOT = "not"


@dataclass
class AlertLink:
    """Defines a link to another alert"""
    alert_id: str  # Unique identifier of the linked alert
    link_type: LinkType
    required: bool = True  # Whether this link must be satisfied


@dataclass
class CEXAlert:
    """
    Models centralized exchange alerts - currently only Binance pairs.
    """
    pair: str
    indicator: str
    params: dict = None
    links: List[AlertLink] = field(default_factory=list)  # Alert dependencies
    alert_id: str = None  # Unique identifier for this alert
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
    links: List[AlertLink] = field(default_factory=list)  # Alert dependencies
    alert_id: str = None  # Unique identifier for this alert
    type: str = "t"
```

### 2. Alert Storage Format

Update JSON storage to include alert IDs and links:

```json
{
  "BTC/USDT": [
    {
      "alert_id": "alert_1",
      "type": "s",
      "indicator": "PRICE",
      "comparison": "ABOVE",
      "target": 45000,
      "params": {},
      "trigger": {
        "cooldown_seconds": null,
        "last_triggered": 0
      }
    },
    {
      "alert_id": "alert_2",
      "type": "t",
      "indicator": "RSI",
      "comparison": "ABOVE",
      "interval": "1h",
      "params": {"period": 14},
      "output_value": "value",
      "target": 70,
      "links": [
        {
          "alert_id": "alert_1",
          "link_type": "and",
          "required": true
        }
      ],
      "trigger": {
        "cooldown_seconds": 3600,
        "last_triggered": 0
      }
    }
  ]
}
```

### 3. Command Syntax

#### Create Linked Alert (AND Logic):
```
/new_alert_linked AND <alert_id_1,alert_id_2> <PAIR> <INDICATOR> <...params...>
```

#### Create Linked Alert (OR Logic):
```
/new_alert_linked OR <alert_id_1,alert_id_2> <PAIR> <INDICATOR> <...params...>
```

#### Create Sequential Alert:
```
/new_alert_linked SEQUENTIAL <alert_id_1,alert_id_2> <PAIR> <INDICATOR> <...params...>
```

#### Examples:

**RSI + Price Confluence:**
```
# First, create the individual alerts and note their IDs
/new_alert BTC/USDT PRICE ABOVE 45000
# Returns: Alert created with ID: alert_1

/new_alert BTC/USDT RSI 1h default value ABOVE 70
# Returns: Alert created with ID: alert_2

# Then create a linked alert that requires both
/new_alert_linked AND alert_1,alert_2 BTC/USDT PRICE ABOVE 45000 1h
```

**Alternative Simplified Syntax:**
```
# Create linked alert directly with inline conditions
/new_alert BTC/USDT PRICE ABOVE 45000 linkto=BTC/USDT:RSI:ABOVE:70
```

### 4. Alert Dependency Manager

Create new file `src/alert_dependencies.py`:

```python
from typing import Dict, List, Optional, Set
from .models import CEXAlert, TechnicalAlert, AlertLink, LinkType
from .logger import logger
import uuid


class AlertDependencyManager:
    """Manages alert dependencies and evaluates linked conditions"""

    def __init__(self):
        self.alert_states = {}  # Track current state of all alerts
        self.trigger_history = {}  # Track when alerts were last triggered

    def generate_alert_id(self) -> str:
        """Generate unique alert ID"""
        return f"alert_{uuid.uuid4().hex[:8]}"

    def check_dependencies(
        self, alert: Dict, all_alerts: Dict[str, List[Dict]]
    ) -> bool:
        """
        Check if all dependencies for an alert are satisfied
        
        :param alert: The alert to check
        :param all_alerts: All alerts organized by pair
        :return: True if all dependencies are satisfied
        """
        if "links" not in alert or not alert["links"]:
            return True  # No dependencies, always satisfied

        links = alert["links"]
        
        # Determine link type (default to AND if mixed)
        link_types = set(link.get("link_type", "and") for link in links)
        
        if len(link_types) > 1:
            logger.warning(f"Mixed link types in alert {alert.get('alert_id')}, using AND logic")
            link_type = "and"
        else:
            link_type = link_types.pop()

        # Collect linked alert states
        linked_alert_states = []
        for link in links:
            linked_alert = self._find_alert_by_id(link["alert_id"], all_alerts)
            if linked_alert is None:
                logger.error(f"Linked alert {link['alert_id']} not found")
                return False
            
            # Check if linked alert condition is currently satisfied
            is_satisfied = self._is_alert_condition_satisfied(linked_alert)
            linked_alert_states.append(is_satisfied)

        # Evaluate based on link type
        if link_type == "and":
            return all(linked_alert_states)
        elif link_type == "or":
            return any(linked_alert_states)
        elif link_type == "sequential":
            return self._check_sequential_triggers(links, all_alerts)
        elif link_type == "not":
            # First condition must be true, rest must be false
            return linked_alert_states[0] and not any(linked_alert_states[1:])
        
        return False

    def _find_alert_by_id(
        self, alert_id: str, all_alerts: Dict[str, List[Dict]]
    ) -> Optional[Dict]:
        """Find an alert by its ID across all pairs"""
        for pair, alerts in all_alerts.items():
            for alert in alerts:
                if alert.get("alert_id") == alert_id:
                    return alert
        return None

    def _is_alert_condition_satisfied(self, alert: Dict) -> bool:
        """
        Check if an alert's condition is currently satisfied
        
        This is checked independently of whether the alert should trigger
        (cooldown, etc.)
        """
        alert_id = alert.get("alert_id")
        return self.alert_states.get(alert_id, False)

    def update_alert_state(self, alert_id: str, is_satisfied: bool):
        """Update the current state of an alert condition"""
        self.alert_states[alert_id] = is_satisfied

    def record_trigger(self, alert_id: str, timestamp: float):
        """Record when an alert was triggered"""
        if alert_id not in self.trigger_history:
            self.trigger_history[alert_id] = []
        self.trigger_history[alert_id].append(timestamp)

    def _check_sequential_triggers(
        self, links: List[Dict], all_alerts: Dict[str, List[Dict]]
    ) -> bool:
        """
        Check if linked alerts were triggered in sequence
        
        Returns True only if all linked alerts triggered in the specified order
        """
        required_sequence = [link["alert_id"] for link in links]
        
        # Get trigger timestamps for all required alerts
        trigger_times = {}
        for alert_id in required_sequence:
            history = self.trigger_history.get(alert_id, [])
            if not history:
                return False  # Alert hasn't triggered yet
            trigger_times[alert_id] = history[-1]  # Use most recent trigger

        # Check if triggers occurred in correct order
        for i in range(len(required_sequence) - 1):
            curr_id = required_sequence[i]
            next_id = required_sequence[i + 1]
            if trigger_times[curr_id] >= trigger_times[next_id]:
                return False  # Out of order

        return True

    def get_linked_alert_summary(
        self, alert: Dict, all_alerts: Dict[str, List[Dict]]
    ) -> str:
        """Generate human-readable summary of linked alerts"""
        if "links" not in alert or not alert["links"]:
            return ""

        links = alert["links"]
        link_type = links[0].get("link_type", "and").upper()
        
        summary = f"\n🔗 Linked ({link_type}):\n"
        for link in links:
            linked_alert = self._find_alert_by_id(link["alert_id"], all_alerts)
            if linked_alert:
                pair = self._find_pair_for_alert(link["alert_id"], all_alerts)
                summary += f"   • {pair} {linked_alert['indicator']} {linked_alert['comparison']} {linked_alert['target']}\n"
        
        return summary

    def _find_pair_for_alert(
        self, alert_id: str, all_alerts: Dict[str, List[Dict]]
    ) -> Optional[str]:
        """Find the pair that contains this alert"""
        for pair, alerts in all_alerts.items():
            for alert in alerts:
                if alert.get("alert_id") == alert_id:
                    return pair
        return None

    def cleanup_orphaned_links(self, all_alerts: Dict[str, List[Dict]]) -> int:
        """
        Remove links to deleted alerts
        
        :return: Number of links removed
        """
        # Collect all valid alert IDs
        valid_ids = set()
        for pair, alerts in all_alerts.items():
            for alert in alerts:
                if "alert_id" in alert:
                    valid_ids.add(alert["alert_id"])

        # Remove invalid links
        removed_count = 0
        for pair, alerts in all_alerts.items():
            for alert in alerts:
                if "links" in alert:
                    original_count = len(alert["links"])
                    alert["links"] = [
                        link for link in alert["links"]
                        if link["alert_id"] in valid_ids
                    ]
                    removed_count += original_count - len(alert["links"])

        return removed_count
```

### 5. Integration with Alert Processes

Update `src/alert_processes/cex.py`:

```python
from ..alert_dependencies import AlertDependencyManager

class CEXAlertProcess:
    def __init__(self, telegram_bot: TelegramBot):
        self.telegram_bot = telegram_bot
        self.dependency_manager = AlertDependencyManager()  # Add dependency manager
        # ... existing code

    def check_alert(self, pair: str, alert: Dict, current_price: float):
        """Check if alert should trigger, considering dependencies"""
        alert_id = alert.get("alert_id")
        
        # Update alert state
        is_condition_met = self._check_alert_condition(alert, current_price)
        if alert_id:
            self.dependency_manager.update_alert_state(alert_id, is_condition_met)
        
        # Check if condition is met
        if not is_condition_met:
            return False
        
        # Check dependencies
        configuration = BaseConfig(str(user_id))
        all_alerts = configuration.load_alerts()
        
        if not self.dependency_manager.check_dependencies(alert, all_alerts):
            logger.debug(f"Alert {alert_id} condition met but dependencies not satisfied")
            return False
        
        # Check cooldown
        if not self._check_cooldown(alert):
            return False
        
        # Trigger alert
        self.trigger_alert(alert, current_price)
        
        # Record trigger
        if alert_id:
            import time
            self.dependency_manager.record_trigger(alert_id, time.time())
        
        return True

    def _check_alert_condition(self, alert: Dict, current_price: float) -> bool:
        """Check if alert condition is met (without dependencies)"""
        # ... existing alert checking logic
        pass
```

### 6. Telegram Bot Integration

Update `src/telegram.py`:

```python
from .alert_dependencies import AlertDependencyManager

class TelegramBot(TeleBot):
    def __init__(self, bot_token: str, taapiio_process: TaapiioProcess = None):
        # ... existing init
        self.dependency_manager = AlertDependencyManager()

        @self.message_handler(commands=["new_alert_linked", "newalertlinked"])
        @self.is_whitelisted
        def on_new_alert_linked(message):
            """/new_alert_linked <LINK_TYPE> <alert_ids> <...alert params...>"""
            try:
                parts = self.split_message(message.text)
                
                # Parse link type and alert IDs
                link_type = parts[0].upper()
                if link_type not in ["AND", "OR", "SEQUENTIAL", "NOT"]:
                    self.reply_to(
                        message,
                        "Invalid link type. Use: AND, OR, SEQUENTIAL, or NOT"
                    )
                    return
                
                # Parse linked alert IDs
                linked_ids = parts[1].split(",")
                
                # Parse rest as normal alert
                # Remove the first two parts and reconstruct message
                remaining_parts = parts[2:]
                # ... parse alert as usual
                
                # Create alert with links
                alert_data = self.parse_alert_message(remaining_parts)
                alert_data["alert_id"] = self.dependency_manager.generate_alert_id()
                alert_data["links"] = [
                    {
                        "alert_id": alert_id.strip(),
                        "link_type": link_type.lower(),
                        "required": True
                    }
                    for alert_id in linked_ids
                ]
                
                # Save alert
                configuration = BaseConfig(str(message.from_user.id))
                alerts_db = configuration.load_alerts()
                pair = alert_data["pair"]
                
                if pair not in alerts_db:
                    alerts_db[pair] = []
                alerts_db[pair].append(alert_data)
                configuration.update_alerts(alerts_db)
                
                # Generate summary
                summary = self.dependency_manager.get_linked_alert_summary(
                    alert_data, alerts_db
                )
                
                self.reply_to(
                    message,
                    f"✅ Linked alert created with ID: {alert_data['alert_id']}{summary}"
                )
                
            except Exception as exc:
                self.reply_to(message, f"Error creating linked alert: {str(exc)}")

        @self.message_handler(commands=["view_alert_links", "viewalertlinks"])
        @self.is_whitelisted
        def on_view_alert_links(message):
            """/view_alert_links <alert_id> - View dependencies for an alert"""
            try:
                parts = self.split_message(message.text)
                if len(parts) == 0:
                    self.reply_to(message, "Usage: /view_alert_links <alert_id>")
                    return
                
                alert_id = parts[0]
                configuration = BaseConfig(str(message.from_user.id))
                all_alerts = configuration.load_alerts()
                
                # Find alert
                alert = self.dependency_manager._find_alert_by_id(alert_id, all_alerts)
                if not alert:
                    self.reply_to(message, f"Alert {alert_id} not found")
                    return
                
                # Generate summary
                summary = self.dependency_manager.get_linked_alert_summary(
                    alert, all_alerts
                )
                
                if not summary:
                    self.reply_to(message, f"Alert {alert_id} has no links")
                else:
                    self.reply_to(message, f"Alert {alert_id}:{summary}", parse_mode="HTML")
                    
            except Exception as exc:
                self.reply_to(message, f"Error: {str(exc)}")
```

### 7. Update View Alerts Command

Modify the `/view_alerts` command to show alert IDs and links:

```python
@self.message_handler(commands=["view_alerts", "viewalerts"])
@self.is_whitelisted
def on_view_alerts(message):
    # ... existing code
    
    for idx, alert in enumerate(alerts):
        # ... existing alert display
        
        # Add alert ID
        if "alert_id" in alert:
            output += f"   <code>ID: {alert['alert_id']}</code>\n"
        
        # Add links if present
        if "links" in alert and alert["links"]:
            link_summary = self.dependency_manager.get_linked_alert_summary(
                alert, all_alerts
            )
            output += link_summary
```

### 8. Documentation Updates

Add to README.md:

```markdown
#### `/new_alert_linked <LINK_TYPE> <alert_ids> <...alert params...>`

Create an alert that only triggers when linked conditions are satisfied.

| Parameter  | Description                                                          |
|------------|----------------------------------------------------------------------|
| LINK_TYPE  | Type of linking: AND, OR, SEQUENTIAL, or NOT                         |
| alert_ids  | Comma-separated list of alert IDs to link (e.g., alert_1,alert_2)   |
| ...        | Normal alert parameters (same as /new_alert)                         |

**Examples:**

Create alerts that trigger only when both RSI > 70 AND price > 45000:
```
/new_alert BTC/USDT PRICE ABOVE 45000
# Note the alert_id returned: alert_1

/new_alert BTC/USDT RSI 1h default value ABOVE 70
# Note the alert_id returned: alert_2

/new_alert_linked AND alert_1,alert_2 BTC/USDT COMBINED ABOVE 0
```

___

#### `/view_alert_links <alert_id>`

View the dependencies for a specific alert.

```
/view_alert_links alert_1
```
```

### 9. Testing Strategy

#### Unit Tests:
```python
def test_and_dependencies():
    manager = AlertDependencyManager()
    manager.update_alert_state("alert_1", True)
    manager.update_alert_state("alert_2", True)
    
    alert = {
        "links": [
            {"alert_id": "alert_1", "link_type": "and"},
            {"alert_id": "alert_2", "link_type": "and"}
        ]
    }
    
    all_alerts = {
        "BTC/USDT": [
            {"alert_id": "alert_1", ...},
            {"alert_id": "alert_2", ...}
        ]
    }
    
    assert manager.check_dependencies(alert, all_alerts) is True

def test_sequential_dependencies():
    manager = AlertDependencyManager()
    manager.record_trigger("alert_1", 1000)
    manager.record_trigger("alert_2", 2000)
    
    # Test in-order triggers
    assert manager._check_sequential_triggers([...]) is True
    
    # Test out-of-order triggers
    manager.record_trigger("alert_3", 500)
    assert manager._check_sequential_triggers([...]) is False
```

### 10. UI/UX Considerations

- **Alert ID Display**: Show alert IDs in a clear, copyable format
- **Link Visualization**: Use emojis or symbols to indicate linked alerts
- **Dependency Status**: Show real-time status of linked conditions
- **Error Messages**: Clear feedback when linked alerts are not found
- **Cleanup**: Automatic cleanup of orphaned links when alerts are deleted

### 11. Future Enhancements

- **Visual Dependency Graph**: Generate a diagram showing alert relationships
- **Complex Logic**: Support for nested conditions: (A AND B) OR (C AND D)
- **Time Windows**: Require conditions to be met within a time window
- **Weighted Conditions**: Some conditions are more important than others
- **Alert Groups**: Link all alerts in a group with single command
- **Condition Monitoring**: Dashboard showing which conditions are currently met

## Conclusion

Linked alerts provide advanced users with powerful conditional triggering capabilities while maintaining the bot's ease of use. The implementation is extensible and provides a foundation for more complex alert logic in the future.

# Bulk Alert Import System Implementation Guide

This document outlines the implementation approach for adding bulk alert import functionality to the Telegram Crypto Alerts bot, allowing users to create multiple alerts at once.

## Overview

The bulk alert import system will enable users to:
- Import multiple alerts from a single command
- Import alerts from JSON or CSV files
- Export existing alerts for backup or sharing
- Quickly set up alerts for a portfolio of tokens

## Use Cases

- **Portfolio Monitoring**: Set up alerts for multiple tokens at once
- **Alert Templates**: Share alert configurations with other users
- **Backup & Restore**: Export alerts before updates, restore after
- **Migration**: Move alerts between different bot instances
- **Batch Configuration**: Set similar alerts across multiple pairs

## Implementation Approach

### 1. Import/Export Format

#### JSON Format (Recommended):

```json
{
  "format_version": "1.0",
  "exported_at": "2024-10-15T10:30:00Z",
  "alerts": [
    {
      "pair": "BTC/USDT",
      "type": "simple",
      "indicator": "PRICE",
      "comparison": "ABOVE",
      "target": 50000,
      "cooldown": "1h"
    },
    {
      "pair": "ETH/USDT",
      "type": "simple",
      "indicator": "PRICE",
      "comparison": "BELOW",
      "target": 2000,
      "cooldown": "30m"
    },
    {
      "pair": "BTC/USDT",
      "type": "technical",
      "indicator": "RSI",
      "interval": "1h",
      "params": {
        "period": 14
      },
      "output_value": "value",
      "comparison": "ABOVE",
      "target": 70,
      "cooldown": "1h"
    }
  ]
}
```

#### CSV Format (Simple alerts only):

```csv
pair,indicator,comparison,target,cooldown
BTC/USDT,PRICE,ABOVE,50000,1h
ETH/USDT,PRICE,BELOW,2000,30m
BNB/USDT,PRICE,ABOVE,300,
SOL/USDT,PRICE,PCTCHG,10.0,5m
```

### 2. Command Syntax

#### Import from File:
```
/import_alerts
```
Then upload a JSON or CSV file

#### Import from Inline JSON:
```
/import_alerts_json {"alerts": [{"pair": "BTC/USDT", "indicator": "PRICE", ...}]}
```

#### Import from Quick Format:
```
/bulk_alert PRICE ABOVE [BTC/USDT:50000, ETH/USDT:2000, BNB/USDT:300] 1h
```

#### Export Alerts:
```
/export_alerts
```
Returns a JSON file with all alerts

```
/export_alerts BTC/USDT
```
Returns a JSON file with alerts for a specific pair

### 3. Implementation Files

Create new file `src/bulk_import.py`:

```python
import json
import csv
from typing import List, Dict, Union, Tuple
from io import StringIO
from .models import CEXAlert, TechnicalAlert
from .logger import logger


class BulkAlertImporter:
    """Handles bulk import of alerts from various formats"""

    def __init__(self, indicators_db: dict):
        self.indicators_db = indicators_db

    def import_from_json(self, json_data: Union[str, dict]) -> Tuple[List[Dict], List[str]]:
        """
        Import alerts from JSON format
        
        :param json_data: JSON string or dict
        :return: Tuple of (successful_alerts, error_messages)
        """
        if isinstance(json_data, str):
            try:
                data = json.loads(json_data)
            except json.JSONDecodeError as e:
                return [], [f"Invalid JSON format: {str(e)}"]
        else:
            data = json_data

        if "alerts" not in data:
            return [], ["Missing 'alerts' key in JSON"]

        successful = []
        errors = []

        for i, alert_data in enumerate(data["alerts"]):
            try:
                validated_alert = self._validate_alert(alert_data)
                successful.append(validated_alert)
            except Exception as e:
                errors.append(f"Alert {i+1}: {str(e)}")

        return successful, errors

    def import_from_csv(self, csv_data: str) -> Tuple[List[Dict], List[str]]:
        """
        Import simple alerts from CSV format
        
        :param csv_data: CSV string
        :return: Tuple of (successful_alerts, error_messages)
        """
        successful = []
        errors = []

        try:
            reader = csv.DictReader(StringIO(csv_data))
            for i, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
                try:
                    alert_data = {
                        "pair": row["pair"],
                        "type": "simple",
                        "indicator": row["indicator"],
                        "comparison": row["comparison"],
                        "target": float(row["target"]),
                        "cooldown": row.get("cooldown", ""),
                    }
                    validated_alert = self._validate_alert(alert_data)
                    successful.append(validated_alert)
                except Exception as e:
                    errors.append(f"Row {i}: {str(e)}")
        except Exception as e:
            return [], [f"CSV parsing error: {str(e)}"]

        return successful, errors

    def import_from_quick_format(
        self, indicator: str, comparison: str, pairs_targets: List[Tuple[str, float]], cooldown: str = ""
    ) -> Tuple[List[Dict], List[str]]:
        """
        Import alerts from quick format
        
        :param indicator: Indicator name (e.g., PRICE)
        :param comparison: Comparison operator (e.g., ABOVE)
        :param pairs_targets: List of (pair, target) tuples
        :param cooldown: Optional cooldown string
        :return: Tuple of (successful_alerts, error_messages)
        """
        successful = []
        errors = []

        for pair, target in pairs_targets:
            try:
                alert_data = {
                    "pair": pair,
                    "type": "simple",
                    "indicator": indicator,
                    "comparison": comparison,
                    "target": target,
                    "cooldown": cooldown,
                }
                validated_alert = self._validate_alert(alert_data)
                successful.append(validated_alert)
            except Exception as e:
                errors.append(f"{pair}: {str(e)}")

        return successful, errors

    def _validate_alert(self, alert_data: Dict) -> Dict:
        """
        Validate alert data and return standardized format
        
        :param alert_data: Raw alert data
        :return: Validated alert dict
        """
        required_fields = ["pair", "indicator", "comparison", "target"]
        for field in required_fields:
            if field not in alert_data:
                raise ValueError(f"Missing required field: {field}")

        # Validate pair format
        if "/" not in alert_data["pair"]:
            raise ValueError(f"Invalid pair format: {alert_data['pair']} (should be BASE/QUOTE)")

        # Validate indicator
        indicator = alert_data["indicator"].upper()
        alert_type = alert_data.get("type", "simple")

        if alert_type == "simple":
            if indicator not in ["PRICE", "24HRCHG"]:
                raise ValueError(f"Invalid simple indicator: {indicator}")
        elif alert_type == "technical":
            if indicator not in self.indicators_db:
                raise ValueError(f"Unknown technical indicator: {indicator}")

        # Validate comparison
        comparison = alert_data["comparison"].upper()
        valid_comparisons = ["ABOVE", "BELOW", "PCTCHG", "24HRCHG"]
        if comparison not in valid_comparisons:
            raise ValueError(f"Invalid comparison: {comparison}")

        # Validate target
        try:
            target = float(alert_data["target"])
        except (ValueError, TypeError):
            raise ValueError(f"Invalid target value: {alert_data['target']}")

        # Build validated alert
        validated = {
            "pair": alert_data["pair"],
            "type": "s" if alert_type == "simple" else "t",
            "indicator": indicator,
            "comparison": comparison,
            "target": target,
            "params": alert_data.get("params", {}),
            "trigger": {
                "cooldown_seconds": self._parse_cooldown(alert_data.get("cooldown", "")),
                "last_triggered": 0,
            },
        }

        # Add technical-specific fields
        if alert_type == "technical":
            validated["interval"] = alert_data.get("interval", "1h")
            validated["output_value"] = alert_data.get("output_value", "value")

        # Add entry price for PCTCHG
        if comparison == "PCTCHG":
            validated["entry"] = alert_data.get("entry", target)

        return validated

    def _parse_cooldown(self, cooldown_str: str) -> Union[int, None]:
        """Parse cooldown string to seconds"""
        if not cooldown_str:
            return None

        import re
        match = re.match(r"(\d+)([smhd])", cooldown_str.lower())
        if not match:
            raise ValueError(f"Invalid cooldown format: {cooldown_str}")

        value, unit = int(match.group(1)), match.group(2)
        multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        return value * multipliers[unit]


class BulkAlertExporter:
    """Handles bulk export of alerts to various formats"""

    def export_to_json(self, alerts_data: Dict, pair_filter: str = None) -> str:
        """
        Export alerts to JSON format
        
        :param alerts_data: Dict of alerts by pair
        :param pair_filter: Optional pair to filter by
        :return: JSON string
        """
        from datetime import datetime

        filtered_alerts = []

        for pair, alerts in alerts_data.items():
            if pair_filter and pair != pair_filter:
                continue

            for alert in alerts:
                export_alert = {
                    "pair": pair,
                    "type": "simple" if alert["type"] == "s" else "technical",
                    "indicator": alert["indicator"],
                    "comparison": alert["comparison"],
                    "target": alert["target"],
                }

                # Add cooldown if present
                cooldown_sec = alert.get("trigger", {}).get("cooldown_seconds")
                if cooldown_sec:
                    export_alert["cooldown"] = self._seconds_to_string(cooldown_sec)

                # Add technical-specific fields
                if alert["type"] == "t":
                    export_alert["interval"] = alert["interval"]
                    export_alert["params"] = alert["params"]
                    export_alert["output_value"] = alert["output_value"]

                # Add entry price for PCTCHG
                if alert["comparison"] == "PCTCHG" and "entry" in alert:
                    export_alert["entry"] = alert["entry"]

                filtered_alerts.append(export_alert)

        export_data = {
            "format_version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "alerts": filtered_alerts,
        }

        return json.dumps(export_data, indent=2)

    def export_to_csv(self, alerts_data: Dict, pair_filter: str = None) -> str:
        """
        Export simple alerts to CSV format
        
        :param alerts_data: Dict of alerts by pair
        :param pair_filter: Optional pair to filter by
        :return: CSV string
        """
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["pair", "indicator", "comparison", "target", "cooldown"])

        for pair, alerts in alerts_data.items():
            if pair_filter and pair != pair_filter:
                continue

            for alert in alerts:
                # Only export simple alerts to CSV
                if alert["type"] != "s":
                    continue

                cooldown_sec = alert.get("trigger", {}).get("cooldown_seconds")
                cooldown_str = self._seconds_to_string(cooldown_sec) if cooldown_sec else ""

                writer.writerow([
                    pair,
                    alert["indicator"],
                    alert["comparison"],
                    alert["target"],
                    cooldown_str,
                ])

        return output.getvalue()

    def _seconds_to_string(self, seconds: int) -> str:
        """Convert seconds to cooldown string"""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m"
        elif seconds < 86400:
            return f"{seconds // 3600}h"
        else:
            return f"{seconds // 86400}d"
```

### 4. Telegram Bot Integration

Update `src/telegram.py` to add import/export commands:

```python
from .bulk_import import BulkAlertImporter, BulkAlertExporter

class TelegramBot(TeleBot):
    def __init__(self, bot_token: str, taapiio_process: TaapiioProcess = None):
        # ... existing init code
        self.bulk_importer = BulkAlertImporter(self.indicators_db)
        self.bulk_exporter = BulkAlertExporter()

        @self.message_handler(commands=["import_alerts", "importalerts"])
        @self.is_whitelisted
        def on_import_alerts(message):
            """/import_alerts - Upload a JSON or CSV file to import alerts"""
            self.reply_to(
                message,
                "Please upload a JSON or CSV file containing your alerts.\n\n"
                "JSON format:\n"
                '{"alerts": [{"pair": "BTC/USDT", "indicator": "PRICE", ...}]}\n\n'
                "CSV format:\n"
                "pair,indicator,comparison,target,cooldown\n"
                "BTC/USDT,PRICE,ABOVE,50000,1h",
            )

        @self.message_handler(content_types=["document"])
        @self.is_whitelisted
        def on_document(message):
            """Handle file uploads for alert import"""
            try:
                file_info = self.get_file(message.document.file_id)
                downloaded_file = self.download_file(file_info.file_path)
                file_content = downloaded_file.decode("utf-8")

                # Determine file type
                if message.document.file_name.endswith(".json"):
                    successful, errors = self.bulk_importer.import_from_json(file_content)
                elif message.document.file_name.endswith(".csv"):
                    successful, errors = self.bulk_importer.import_from_csv(file_content)
                else:
                    self.reply_to(message, "Unsupported file type. Please upload JSON or CSV.")
                    return

                # Add alerts to database
                configuration = BaseConfig(str(message.from_user.id))
                alerts_db = configuration.load_alerts()

                added_count = 0
                for alert_data in successful:
                    pair = alert_data["pair"]
                    if pair not in alerts_db:
                        alerts_db[pair] = []
                    alerts_db[pair].append(alert_data)
                    added_count += 1

                configuration.update_alerts(alerts_db)

                # Build response message
                response = f"✅ Successfully imported {added_count} alert(s).\n"
                if errors:
                    response += f"\n⚠️ {len(errors)} error(s) occurred:\n"
                    for error in errors[:5]:  # Limit to first 5 errors
                        response += f"• {error}\n"
                    if len(errors) > 5:
                        response += f"... and {len(errors) - 5} more errors\n"

                self.reply_to(message, response)

            except Exception as exc:
                self.reply_to(message, f"Error importing alerts: {str(exc)}")

        @self.message_handler(commands=["export_alerts", "exportalerts"])
        @self.is_whitelisted
        def on_export_alerts(message):
            """/export_alerts [PAIR] - Export alerts to JSON file"""
            try:
                msg_parts = self.split_message(message.text)
                pair_filter = msg_parts[0] if len(msg_parts) > 0 else None

                configuration = BaseConfig(str(message.from_user.id))
                alerts_db = configuration.load_alerts()

                # Export to JSON
                json_content = self.bulk_exporter.export_to_json(alerts_db, pair_filter)

                # Send as file
                from io import BytesIO
                file = BytesIO(json_content.encode("utf-8"))
                file.name = f"alerts_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

                self.send_document(message.chat.id, file)

            except Exception as exc:
                self.reply_to(message, f"Error exporting alerts: {str(exc)}")

        @self.message_handler(commands=["bulk_alert", "bulkalert"])
        @self.is_whitelisted
        def on_bulk_alert(message):
            """/bulk_alert INDICATOR COMPARISON [PAIR:TARGET, PAIR:TARGET] optional_COOLDOWN"""
            try:
                import re
                msg = message.text

                # Parse command: /bulk_alert PRICE ABOVE [BTC/USDT:50000, ETH/USDT:2000] 1h
                parts = self.split_message(msg)
                indicator = parts[0].upper()
                comparison = parts[1].upper()

                # Extract pairs and targets from bracket notation
                bracket_match = re.search(r'\[(.*?)\]', msg)
                if not bracket_match:
                    self.reply_to(
                        message,
                        "Invalid format. Use: /bulk_alert INDICATOR COMPARISON [PAIR:TARGET, PAIR:TARGET] optional_COOLDOWN"
                    )
                    return

                pairs_str = bracket_match.group(1)
                pairs_targets = []
                for pair_target in pairs_str.split(','):
                    pair_target = pair_target.strip()
                    if ':' not in pair_target:
                        continue
                    pair, target = pair_target.split(':', 1)
                    pairs_targets.append((pair.strip(), float(target.strip())))

                # Get optional cooldown
                cooldown = parts[2] if len(parts) > 2 else ""

                # Import alerts
                successful, errors = self.bulk_importer.import_from_quick_format(
                    indicator, comparison, pairs_targets, cooldown
                )

                # Add to database
                configuration = BaseConfig(str(message.from_user.id))
                alerts_db = configuration.load_alerts()

                for alert_data in successful:
                    pair = alert_data["pair"]
                    if pair not in alerts_db:
                        alerts_db[pair] = []
                    alerts_db[pair].append(alert_data)

                configuration.update_alerts(alerts_db)

                # Build response
                response = f"✅ Successfully created {len(successful)} alert(s).\n"
                if errors:
                    response += f"\n⚠️ {len(errors)} error(s):\n"
                    for error in errors:
                        response += f"• {error}\n"

                self.reply_to(message, response)

            except Exception as exc:
                self.reply_to(message, f"Error creating bulk alerts: {str(exc)}")
```

### 5. Update Commands List

Add to `src/resources/commands.txt`:

```
import_alerts - Usage: /import_alerts (then upload JSON/CSV file)
export_alerts - Usage: /export_alerts [PAIR]
bulk_alert - Usage: /bulk_alert INDICATOR COMPARISON [PAIR:TARGET, ...] optional_COOLDOWN
```

### 6. Documentation Updates

Add to README.md:

```markdown
#### `/import_alerts`

Import multiple alerts from a JSON or CSV file. This is useful for quickly setting up alerts for a portfolio of tokens.

1. Send the `/import_alerts` command
2. Upload a JSON or CSV file with your alerts

**JSON Format Example:**
```json
{
  "alerts": [
    {
      "pair": "BTC/USDT",
      "indicator": "PRICE",
      "comparison": "ABOVE",
      "target": 50000,
      "cooldown": "1h"
    },
    {
      "pair": "ETH/USDT",
      "indicator": "PRICE",
      "comparison": "BELOW",
      "target": 2000
    }
  ]
}
```

**CSV Format Example:**
```csv
pair,indicator,comparison,target,cooldown
BTC/USDT,PRICE,ABOVE,50000,1h
ETH/USDT,PRICE,BELOW,2000,
```

___

#### `/export_alerts [PAIR]`

Export your alerts to a JSON file for backup or sharing.

```
/export_alerts           # Export all alerts
/export_alerts BTC/USDT  # Export alerts for specific pair
```

___

#### `/bulk_alert <INDICATOR> <COMPARISON> [PAIR:TARGET, ...] <optional_COOLDOWN>`

Create multiple alerts with the same indicator and comparison.

_For example, to set price alerts for multiple tokens:_

```
/bulk_alert PRICE ABOVE [BTC/USDT:50000, ETH/USDT:2000, BNB/USDT:300] 1h
```
```

### 7. Testing Strategy

#### Unit Tests:
```python
def test_json_import():
    importer = BulkAlertImporter({})
    json_data = '{"alerts": [{"pair": "BTC/USDT", "indicator": "PRICE", ...}]}'
    successful, errors = importer.import_from_json(json_data)
    assert len(successful) > 0
    assert len(errors) == 0

def test_csv_import():
    importer = BulkAlertImporter({})
    csv_data = "pair,indicator,comparison,target\nBTC/USDT,PRICE,ABOVE,50000"
    successful, errors = importer.import_from_csv(csv_data)
    assert len(successful) == 1

def test_quick_format():
    importer = BulkAlertImporter({})
    pairs_targets = [("BTC/USDT", 50000), ("ETH/USDT", 2000)]
    successful, errors = importer.import_from_quick_format("PRICE", "ABOVE", pairs_targets)
    assert len(successful) == 2
```

### 8. Security Considerations

- **File Size Limits**: Limit uploaded file size (e.g., 1MB max)
- **Alert Limits**: Respect MAX_ALERTS_PER_USER when importing
- **Validation**: Validate all alert parameters before importing
- **Rate Limiting**: Limit number of bulk imports per user per day

### 9. Future Enhancements

- **Alert Templates**: Pre-made templates for common strategies
- **Sharing**: Generate shareable alert configuration links
- **Scheduled Imports**: Import alerts at specific times
- **Alert Groups**: Organize alerts into named groups
- **Conditional Import**: Import only if conditions are met
- **Alert Versioning**: Track changes to imported alerts

## Conclusion

The bulk alert import system provides a powerful way to manage multiple alerts efficiently while maintaining simplicity and security. The implementation supports multiple formats and provides a smooth user experience for both importing and exporting alerts.

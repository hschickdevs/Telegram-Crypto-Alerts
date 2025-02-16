# 📘 Change Log

All significant modifications to the project are recorded here.

## Table of Contents

- [v3.2.0 - Released 2024-02-16](#320)
- [v3.1.0 - Released 2024-08-14](#310)
- [v3.0.0 - Released 2024-03-11](#300)

## v3.2.0 - Released 2024-02-16 <a name="320"></a>

### 💎 Release Summary

This release primarily addresses the following issue: https://github.com/hschickdevs/Telegram-Crypto-Alerts/issues/30

But also introduces alert cooldowns and several quality-of-life improvements to the bot's command system.

### 🛠️ Modifications/Enhancements

- Added cooldown functionality to alerts using the new `optional_COOLDOWN` parameter (e.g., 30s, 5m, 1h)
    - See: https://github.com/hschickdevs/Telegram-Crypto-Alerts/issues/30
    - Passed as an optional parameter to the end of the `/newalert` command (see the [README](../README.md) for more information)
    - Allows users to optionally set a cooldown to make alerts fire until they are manually disabled
- Added all command aliases without the underscore (e.g., `newalert` for `new_alert`, `viewalerts` for `view_alerts`)
- Updated `LOCATION` environment variable to be case-insensitive
- Added code formatting requirements using `black`

### 📖 Documentation

- Updated command documentation to reflect new cooldown parameter
- Removed `optional_ENTRY_PRICE` parameter from documentation as it's now handled automatically
- Updated example commands to demonstrate cooldown usage

## v3.1.0 - Released 2024-08-14 <a name="310"></a>

### 💎 Release Summary

Release includes minor bugfixes and improvements

### 🛠️ Bugfixes/Improvements

- `LOCATION` environment variable is now documented as mandatory, as to handle Binance's IP restrictions for US-based users.

- Fixed a bug with the new `24HRCHG` indicator that was causing the bot to crash when an alert was present using this indicator.

- Fixed inconsistencies with the binance API endpoints that were causing the bot to crash when fetching data.

## v3.0.0 - Released 2024-03-11 <a name="300"></a>

### 💎 Release Summary

This release is a major, non-backwards compatible update to the software. It includes a number of much needed new features, removed features, and quality of life improvements which can be summarized as follows.

### 🛠️ Modifications/Enhancements

- Commands are now automatically set, removing the need to run the `setup.py` script before starting the bot.
- Containerized the software using Docker to increase portability and ease of deployment.
- Added a `View Spot Chart` link to alerts that brings users to their pair's chart on Binance.
- Added the Binance US API and the `LOCATION` environment variable, removing the need for VPNs for US users.
- Make technical alerts optional, allowing users to just use simple price alerts if desired.
- Added a `TAAPIIO_TIER` env var to determine rate limits and increase calls if able.
- Renamed commands to be more intuitive (see [`commands.txt`](../src/resources/commands.txt)).
- Renamed source code directory from `bot` -> `src` for readability.

### 🚫 Deletions 

- Removed email alert functionality since it was not being used frequently and added complexity.
- Removed requirement for additional taapi.io API key.
- Removed bash scripts as they were redundant and replaced by Docker.
- Disabled web page preview for messages with links for readability.

### 📖 Docs

- Added new README header and project logo
- Generally cleaned up the README
- Updated deployment guides and added guide for Docker

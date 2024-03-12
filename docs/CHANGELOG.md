# 📘 Change Log

All significant modifications to the project are recorded here.

## Table of Contents

- [v3.0.0 - Released 2024-03-11](#300)

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

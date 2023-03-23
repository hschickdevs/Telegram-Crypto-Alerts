#!/bin/bash
# Install script for the "Telegram Alerts Bot"

# Prompt that the user should be using Debain 11
echo "This script assumes that you are following the steps in the setup guide."
echo "If you are not, it will not work properly."
echo "If you are, press ENTER to continue - if not, press CTRL+C to cancel."
read

# Get started
cd ~

# Install dependencies
sudo apt-get install git python3-pip -y

# Clone the repository
git clone https://github.com/hschickdevs/Telegram-Crypto-Alerts.git
cd /Telegram-Crypto-Alerts

# Install Python dependencies
pip install -r requirements.txt

# Create the .env file by prompting for environment variables
echo "Creating .env file..."

echo "Enter your Telegram Bot Token..."
echo "The bot that owns this token will be the crypto alerts bot:"
read TELEGRAM_BOT_TOKEN

echo ""

echo "Now enter your TAAPI.IO API Key..."
echo "This will be used for technical indicator alerts:"
read TAAPI_API_KEY

echo ""

echo "Now enter a second TAAPI.IO API Key..."
echo "This will be used for separate requests in the Telegram bot:"
read TAAPI_API_KEY_2

echo ""

# Now dump the env files to the .env file in the current directory
printf "TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN\nTAAPI_API_KEY=$TAAPI_API_KEY\nTAAPI_API_KEY_2=$TAAPI_API_KEY_2" > .env

echo "Your .env file has been created!"
cat .env
#!/bin/bash
echo "Welcome to the Telegram Crypto Alerts setup script!"
echo ""
echo "This script assumes that you are following the steps in the setup guide."
echo "If you are not, it will not work properly."
echo "If you are, press ENTER to continue - if not, press CTRL+C to cancel."
read


# Create the .env file by prompting for environment variables
cd ~/Telegram-Crypto-Alerts

echo "Creating .env file..."
echo ""

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
printf "TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN\nTAAPIIO_APIKEY=$TAAPI_API_KEY\nTAAPIIO_APIKEY2=$TAAPI_API_KEY_2" > .env

echo "Your .env file has been created!"
cat .env

echo ""
echo ""
echo "Now, you need to add your Telegram user ID to the database."
echo "If you don't know your user ID, you can use https://t.me/raw_data_bot to get it."
echo "Please enter your user ID now:"
read TELEGRAM_USER_ID

echo ""
python3 setup.py --id $TELEGRAM_USER_ID
echo ""
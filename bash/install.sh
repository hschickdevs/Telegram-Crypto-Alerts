#!/bin/bash
# Install script for the "Telegram Alerts Bot"

# Prompt that the user should be using Debain 11
echo ""
echo "Welcome to the Telegram Alerts Bot installation script!"
echo ""
echo "This script assumes that you are following the steps in the setup guide."
echo "If you are not, it will not work properly."
echo "If you are, press ENTER to continue - if not, press CTRL+C to cancel."
read

# Get started
cd ~

# Install dependencies
sudo apt-get install git tmux python3-pip -y

# Clone the repository
git clone https://github.com/hschickdevs/Telegram-Crypto-Alerts.git
cd Telegram-Crypto-Alerts

# Install Python dependencies
pip install -r requirements.txt

# Move bash scripts to root
mv bash/* ~

echo ""
echo "The dependencies have been successfully installed!"
echo "Please continue to follow the setup steps in the guide."
echo ""
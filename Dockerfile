# Docker image location:
# https://hub.docker.com/repository/docker/hschickdevs/ai-software-architect/general

# How to install docker engine on Ubuntu:
# https://docs.docker.com/engine/install/ubuntu/

# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app
# Ensure that readme is included for docker hub
COPY README.md /app/README.md

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Run the bot when the container launches
CMD ["python3", "-m", "src"]

# ------- Docker Deployment Commands: -------
# docker build -t telegram-crypto-alerts .
# docker tag telegram-crypto-alerts hschickdevs/telegram-crypto-alerts:latest
# docker push hschickdevs/telegram-crypto-alerts:latest
# docker rmi -f $(docker images -aq)

# FOR TESTING:
# docker run --env-file .env telegram-crypto-alerts

# ------- Docker Pull & Run Commands: -------
# docker pull hschickdevs/telegram-crypto-alerts:latest

# docker run -d --name telegram-crypto-alerts \
#   -e TELEGRAM_USER_ID=<YOUR_ID> \
#   -e TELEGRAM_BOT_TOKEN=<YOUR_TOKEN> \
#   -e TAAPIIO_APIKEY=<YOUR_KEY> \
#   hschickdevs/telegram-crypto-alerts

# docker attach telegram-crypto-alerts
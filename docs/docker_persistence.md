# Docker Persistence Guide

This guide explains how to add data persistence to your Docker deployment of Telegram Crypto Alerts, ensuring your alerts and configuration survive container restarts.

## Understanding Data Storage

The bot stores data in two ways:

1. **Local JSON Files** (Default): Data is stored in the `/app/src/whitelist/` directory inside the container
2. **MongoDB** (Optional): Data is stored in a MongoDB database

## Option 1: Using Docker Volumes (Recommended for Local JSON)

When using the default local JSON storage, you can persist data across container restarts using Docker volumes.

### Create a Named Volume

```bash
docker volume create telegram-crypto-alerts-data
```

### Run Container with Volume Mounted

```bash
docker run -d --name telegram-crypto-alerts \
  -e TELEGRAM_USER_ID=<YOUR_ID> \
  -e TELEGRAM_BOT_TOKEN=<YOUR_TOKEN> \
  -e LOCATION=<YOUR_LOCATION> \
  -e TAAPIIO_APIKEY=<YOUR_KEY> \
  -e TAAPIIO_TIER=<YOUR_TIER> \
  -v telegram-crypto-alerts-data:/app/src/whitelist \
  hschickdevs/telegram-crypto-alerts:latest
```

### Using Bind Mounts (Alternative)

Instead of named volumes, you can use bind mounts to map a directory on your host machine:

```bash
# Create a directory on your host
mkdir -p ~/telegram-bot-data

# Run container with bind mount
docker run -d --name telegram-crypto-alerts \
  -e TELEGRAM_USER_ID=<YOUR_ID> \
  -e TELEGRAM_BOT_TOKEN=<YOUR_TOKEN> \
  -e LOCATION=<YOUR_LOCATION> \
  -e TAAPIIO_APIKEY=<YOUR_KEY> \
  -e TAAPIIO_TIER=<YOUR_TIER> \
  -v ~/telegram-bot-data:/app/src/whitelist \
  hschickdevs/telegram-crypto-alerts:latest
```

## Option 2: Using MongoDB (Recommended for Production)

For robust persistence across multiple deployments and machines, use MongoDB as described in the [Docker Setup Guide](./docker_setup.md#optional---mongodb-setup--configuration).

### Quick MongoDB Setup

1. Set `USE_MONGO_DB = True` in `src/config.py`

2. Create a MongoDB Atlas account at https://www.mongodb.com/cloud/atlas/register

3. Create a database and collection

4. Run the container with MongoDB environment variables:

```bash
docker run -d --name telegram-crypto-alerts \
  -e TELEGRAM_USER_ID=<YOUR_ID> \
  -e TELEGRAM_BOT_TOKEN=<YOUR_TOKEN> \
  -e LOCATION=<YOUR_LOCATION> \
  -e TAAPIIO_APIKEY=<YOUR_KEY> \
  -e TAAPIIO_TIER=<YOUR_TIER> \
  -e MONGODB_CONNECTION_STRING=<YOUR_URI> \
  -e MONGODB_DATABASE=<YOUR_DB> \
  -e MONGODB_COLLECTION=<YOUR_COLLECTION> \
  hschickdevs/telegram-crypto-alerts:latest
```

## Option 3: Using Docker Compose (Easiest for Local Development)

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  telegram-crypto-alerts:
    image: hschickdevs/telegram-crypto-alerts:latest
    container_name: telegram-crypto-alerts
    environment:
      - TELEGRAM_USER_ID=${TELEGRAM_USER_ID}
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - LOCATION=${LOCATION}
      - TAAPIIO_APIKEY=${TAAPIIO_APIKEY}
      - TAAPIIO_TIER=${TAAPIIO_TIER}
    volumes:
      - telegram-alerts-data:/app/src/whitelist
    restart: unless-stopped

volumes:
  telegram-alerts-data:
```

Then create a `.env` file with your credentials:

```bash
TELEGRAM_USER_ID=your_id
TELEGRAM_BOT_TOKEN=your_token
LOCATION=us
TAAPIIO_APIKEY=your_key
TAAPIIO_TIER=free
```

Start the container:

```bash
docker-compose up -d
```

## Verifying Persistence

1. Create some alerts in your bot
2. Stop the container: `docker stop telegram-crypto-alerts`
3. Start the container again: `docker start telegram-crypto-alerts`
4. Use `/view_alerts` to verify your alerts are still there

## Backup and Restore

### Backing Up Volume Data

```bash
# Create a backup
docker run --rm \
  -v telegram-crypto-alerts-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/telegram-bot-backup.tar.gz -C /data .
```

### Restoring Volume Data

```bash
# Restore from backup
docker run --rm \
  -v telegram-crypto-alerts-data:/data \
  -v $(pwd):/backup \
  alpine sh -c "cd /data && tar xzf /backup/telegram-bot-backup.tar.gz"
```

## Troubleshooting

### Container Keeps Restarting

Check logs to see if there are permission issues:
```bash
docker logs telegram-crypto-alerts
```

### Data Not Persisting

1. Verify the volume is mounted correctly:
   ```bash
   docker inspect telegram-crypto-alerts | grep Mounts -A 20
   ```

2. Check that data is being written to the correct directory inside the container:
   ```bash
   docker exec telegram-crypto-alerts ls -la /app/src/whitelist
   ```

### Migration from Non-Persistent to Persistent

If you've been running without persistence and want to preserve existing data:

1. Copy data from running container:
   ```bash
   docker cp telegram-crypto-alerts:/app/src/whitelist ./backup-data
   ```

2. Stop and remove the old container:
   ```bash
   docker stop telegram-crypto-alerts
   docker rm telegram-crypto-alerts
   ```

3. Start new container with volume and restore data:
   ```bash
   docker run -d --name telegram-crypto-alerts \
     -e TELEGRAM_USER_ID=<YOUR_ID> \
     -e TELEGRAM_BOT_TOKEN=<YOUR_TOKEN> \
     -v telegram-crypto-alerts-data:/app/src/whitelist \
     hschickdevs/telegram-crypto-alerts:latest
   
   docker cp ./backup-data/. telegram-crypto-alerts:/app/src/whitelist/
   docker restart telegram-crypto-alerts
   ```

## Additional Resources

- [Docker Volumes Documentation](https://docs.docker.com/storage/volumes/)
- [MongoDB Atlas Documentation](https://docs.atlas.mongodb.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

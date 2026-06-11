#!/bin/bash
set -e

echo "Starting Telegram Bot..."

# Create necessary directories
mkdir -p /app/data /app/temp /app/logs

# Initialize database
python -c "from bot.database.models import init_db; init_db()"
echo "Database initialized"

# Run database migrations if any
# python scripts/migrate.py

# Start the bot
exec "$@"

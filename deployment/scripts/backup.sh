#!/usr/bin/env bash
set -euo pipefail

# Backup script for Survey Finder

BACKUP_DIR="${BACKUP_DIR:-/backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

echo "📦 Creating backup..."

# Backup PostgreSQL
echo "📁 Backing up PostgreSQL..."
docker exec -t survey-finder-postgres-1 pg_dump -U postgres survey > "$BACKUP_DIR/postgres_$TIMESTAMP.sql"
gzip -f "$BACKUP_DIR/postgres_$TIMESTAMP.sql"

# Backup Redis (if needed)
echo "📁 Backing up Redis..."
docker exec -t survey-finder-redis-1 redis-cli SAVE
docker cp survey-finder-redis-1:/data/dump.rdb "$BACKUP_DIR/redis_$TIMESTAMP.rdb"

# Backup .env
if [ -f .env ]; then
    cp .env "$BACKUP_DIR/env_$TIMESTAMP.bak"
fi

# Cleanup old backups (keep last 7 days)
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.rdb" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.bak" -mtime +7 -delete

echo "✅ Backup complete: $BACKUP_DIR"
echo "📋 Files:"
ls -la "$BACKUP_DIR" | tail -5

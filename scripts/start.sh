#!/bin/bash
set -e

DB_PATH="/tmp/auto-studio-data/studio.db"
REPLICA_URL="${REPLICA_URL:-s3://swing-trade-backup/auto-studio/studio.db}"

mkdir -p "$(dirname "$DB_PATH")"

echo "=== Litestream: restoring DB from R2 ==="
litestream restore -if-replica-exists -o "$DB_PATH" "$REPLICA_URL"

echo "=== Litestream: starting app + replication ==="
exec litestream replicate -config /app/litestream.yml -exec "uvicorn app.main:app --host 0.0.0.0 --port $PORT"

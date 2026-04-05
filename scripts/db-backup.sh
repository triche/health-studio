#!/usr/bin/env bash
# -------------------------------------------------------------------
# Database Backup & Restore
#
# Copies the SQLite database out of (or into) the Docker volume so
# you can keep offline backups or recover from data loss.
#
# Usage:
#   ./scripts/db-backup.sh backup              # → backups/health_studio_<timestamp>.db
#   ./scripts/db-backup.sh backup myfile.db    # → myfile.db
#   ./scripts/db-backup.sh restore myfile.db   # restore from myfile.db
#   ./scripts/db-backup.sh list                # show available backups
# -------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_DIR="$ROOT_DIR/backups"
VOLUME_NAME="health-studio_health-data"
DB_PATH_IN_VOLUME="health_studio.db"

usage() {
  echo "Usage: $0 {backup [FILE]|restore FILE|list}"
  echo
  echo "Commands:"
  echo "  backup  [FILE]  Copy the database from Docker to a local file."
  echo "                  Defaults to backups/health_studio_<timestamp>.db"
  echo "  restore FILE    Copy a local file into the Docker volume."
  echo "                  ⚠️  This overwrites the current database."
  echo "  list            List available backups in the backups/ directory."
  exit 1
}

ensure_volume_exists() {
  if ! docker volume inspect "$VOLUME_NAME" > /dev/null 2>&1; then
    echo "❌ Docker volume '$VOLUME_NAME' does not exist."
    echo "   Start the app first: docker compose up -d"
    exit 1
  fi
}

do_backup() {
  ensure_volume_exists

  local dest="${1:-}"
  if [ -z "$dest" ]; then
    mkdir -p "$BACKUP_DIR"
    local timestamp
    timestamp="$(date +%Y%m%d_%H%M%S)"
    dest="$BACKUP_DIR/health_studio_${timestamp}.db"
  fi

  echo "📦 Backing up database to: $dest"
  docker run --rm \
    -v "$VOLUME_NAME":/data:ro \
    -v "$(cd "$(dirname "$dest")" && pwd)":/backup \
    alpine:3.20 \
    cp "/data/$DB_PATH_IN_VOLUME" "/backup/$(basename "$dest")"

  local size
  size="$(du -h "$dest" | cut -f1)"
  echo "✅ Backup complete ($size): $dest"
}

do_restore() {
  local src="${1:-}"
  if [ -z "$src" ]; then
    echo "❌ Please specify a backup file to restore."
    echo "   Usage: $0 restore FILE"
    exit 1
  fi

  if [ ! -f "$src" ]; then
    echo "❌ File not found: $src"
    exit 1
  fi

  ensure_volume_exists

  echo "⚠️  WARNING: This will overwrite the current database with: $src"
  echo "   Any data in the running app will be replaced."
  echo
  read -rp "Are you sure? (y/N) " confirm
  if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
  fi

  # Stop the backend so the DB isn't in use during restore
  echo "⏸️  Stopping backend..."
  docker compose -f "$ROOT_DIR/docker-compose.yml" stop backend 2>/dev/null || true

  echo "📥 Restoring database from: $src"
  docker run --rm \
    -v "$VOLUME_NAME":/data \
    -v "$(cd "$(dirname "$src")" && pwd)":/backup:ro \
    alpine:3.20 \
    cp "/backup/$(basename "$src")" "/data/$DB_PATH_IN_VOLUME"

  echo "▶️  Restarting backend..."
  docker compose -f "$ROOT_DIR/docker-compose.yml" start backend 2>/dev/null || true

  echo "✅ Restore complete. Database replaced with: $src"
}

do_list() {
  if [ ! -d "$BACKUP_DIR" ]; then
    echo "No backups directory found. Run '$0 backup' first."
    exit 0
  fi

  local count
  count="$(find "$BACKUP_DIR" -name '*.db' 2>/dev/null | wc -l | tr -d ' ')"
  if [ "$count" -eq 0 ]; then
    echo "No backups found in $BACKUP_DIR"
    exit 0
  fi

  echo "Available backups in backups/:"
  echo
  ls -lh "$BACKUP_DIR"/*.db 2>/dev/null | awk '{print "  " $NF " (" $5 ", " $6 " " $7 " " $8 ")"}'
}

case "${1:-}" in
  backup)  do_backup "${2:-}" ;;
  restore) do_restore "${2:-}" ;;
  list)    do_list ;;
  *)       usage ;;
esac

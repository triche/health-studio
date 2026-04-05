#!/usr/bin/env bash
# -------------------------------------------------------------------
# E2E Test Runner
# Spins up the full Docker Compose stack, runs Playwright tests,
# and tears everything down.
# -------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cleanup() {
  echo "🧹 Tearing down Docker Compose stack..."
  docker compose -f "$ROOT_DIR/docker-compose.yml" -f "$ROOT_DIR/docker-compose.test.yml" down -v --remove-orphans 2>/dev/null || true
}
trap cleanup EXIT

echo "🔨 Building Docker images..."
docker compose -f "$ROOT_DIR/docker-compose.yml" build

echo "🚀 Starting Docker Compose stack with TESTING=true..."
docker compose -f "$ROOT_DIR/docker-compose.yml" -f "$ROOT_DIR/docker-compose.test.yml" up -d

echo "⏳ Waiting for backend health check..."
for i in $(seq 1 60); do
  if curl -sf http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
    break
  fi
  if [ "$i" -eq 60 ]; then
    echo "❌ Backend failed to start within 60s"
    docker compose -f "$ROOT_DIR/docker-compose.yml" logs backend
    exit 1
  fi
  sleep 1
done

echo "⏳ Waiting for frontend..."
for i in $(seq 1 30); do
  if curl -sf http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is ready"
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "❌ Frontend failed to start within 30s"
    docker compose -f "$ROOT_DIR/docker-compose.yml" logs frontend
    exit 1
  fi
  sleep 1
done

echo "🎭 Running Playwright E2E tests..."
cd "$ROOT_DIR/e2e"
npx playwright test "$@"

echo "✅ E2E tests complete"

#!/usr/bin/env bash
# -------------------------------------------------------------------
# E2E Test Runner
# Spins up the full Docker Compose stack, runs Playwright tests,
# and tears everything down.
# -------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Use a separate project name so the test stack is fully isolated from dev.
# This ensures test teardown can never destroy dev data.
PROJECT="health-studio-test"
DC="docker compose -p $PROJECT -f $ROOT_DIR/docker-compose.yml -f $ROOT_DIR/docker-compose.test.yml"

# Check if the dev stack is running (would cause port conflicts)
if docker compose -f "$ROOT_DIR/docker-compose.yml" ps --status running 2>/dev/null | grep -q 'health-studio'; then
  echo "⚠️  Dev stack is running on the same ports. Stopping it first..."
  docker compose -f "$ROOT_DIR/docker-compose.yml" stop
fi

cleanup() {
  echo "🧹 Tearing down test stack (project: $PROJECT)..."
  $DC down -v --remove-orphans 2>/dev/null || true
}
trap cleanup EXIT

echo "🔨 Building Docker images..."
$DC build

echo "🚀 Starting test stack..."
$DC up -d

echo "⏳ Waiting for backend health check..."
for i in $(seq 1 60); do
  if curl -sf "http://localhost:8000/api/health" > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
    break
  fi
  if [ "$i" -eq 60 ]; then
    echo "❌ Backend failed to start within 60s"
    $DC logs backend
    exit 1
  fi
  sleep 1
done

echo "⏳ Waiting for frontend..."
for i in $(seq 1 30); do
  if curl -sf "http://localhost:3000" > /dev/null 2>&1; then
    echo "✅ Frontend is ready"
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "❌ Frontend failed to start within 30s"
    $DC logs frontend
    exit 1
  fi
  sleep 1
done

echo "🎭 Running Playwright E2E tests..."
cd "$ROOT_DIR/e2e"
npx playwright test "$@"

echo "✅ E2E tests complete"

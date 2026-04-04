#!/bin/sh
set -e

# Run database migrations then seed default data (both idempotent — safe on every start).
alembic upgrade head
python -m app.seed

# Start the application server
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

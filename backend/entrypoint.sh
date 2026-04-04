#!/bin/sh
set -e

# Run database migrations and seed default data (idempotent — safe on every start,
# but only inserts rows that don't already exist).
python -m app.seed

# Start the application server
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

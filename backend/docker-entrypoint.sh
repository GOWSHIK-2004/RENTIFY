#!/bin/sh
# Container start-up: apply migrations, optionally load demo data, then run the server.
set -e

echo "Applying database migrations..."
alembic upgrade head

if [ "$SEED_DEMO_DATA" = "true" ]; then
  echo "Loading demo data (idempotent)..."
  python seed.py
fi

exec "$@"

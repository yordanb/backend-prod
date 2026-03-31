#!/bin/bash
# Helper script to run Alembic migrations
# Usage: ./scripts/migrate.sh [up|down|revision]

set -e

COMMAND=${1:-"upgrade"}
TARGET=${2:-"head"}

echo "Running Alembic: $COMMAND $TARGET"
docker-compose exec api alembic $COMMAND $TARGET

echo "Migration completed"

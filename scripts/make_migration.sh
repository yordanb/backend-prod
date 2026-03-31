#!/bin/bash
# Helper script to generate Alembic migrations
# Usage: ./scripts/make_migration.sh "descriptive message"

set -e

MESSAGE=${1:-"auto migration"}

echo "Generating Alembic migration: $MESSAGE"
docker-compose exec api alembic revision --autogenerate -m "$MESSAGE"

echo "Migration created in alembic/versions/"

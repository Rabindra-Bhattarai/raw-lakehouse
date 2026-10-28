#!/bin/sh
# Prepare Superset's own database, create the admin user, build the dashboard, then serve.
set -e

superset db upgrade
superset fab create-admin \
    --username "${ADMIN_USER:-admin}" --password "${ADMIN_PASSWORD:-admin}" \
    --firstname Admin --lastname User --email admin@example.com || true
superset init

# Creates the Trino connection, datasets, charts and dashboard once the web server is up.
python /app/setup/setup_dashboard.py &

exec /usr/bin/run-server.sh

#!/bin/bash
# Extract PostgreSQL credentials from HIVE_DATABASE_URL

if [ -z "$HIVE_DATABASE_URL" ]; then
    echo "Error: HIVE_DATABASE_URL not set" >&2
    exit 1
fi

# Parse the database URL
# Format: postgresql+psycopg://user:password@host:port/database
URL_WITHOUT_SCHEME="${HIVE_DATABASE_URL#*://}"
USER_PASS="${URL_WITHOUT_SCHEME%%@*}"
export POSTGRES_USER="${USER_PASS%%:*}"
export POSTGRES_PASSWORD="${USER_PASS#*:}"

HOST_PORT_DB="${URL_WITHOUT_SCHEME#*@}"
HOST_PORT="${HOST_PORT_DB%%/*}"
export POSTGRES_DB="${HOST_PORT_DB#*/}"

echo "Extracted credentials from HIVE_DATABASE_URL"
echo "POSTGRES_USER=$POSTGRES_USER"
echo "POSTGRES_DB=$POSTGRES_DB"
# Don't echo password for security

# Execute the original command
exec "$@"
#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

# Set default PostgreSQL user if not provided
if [ -z "${POSTGRES_USER:-}" ]; then
    base_postgres_image_default_user='postgres'
    export POSTGRES_USER="${base_postgres_image_default_user}"
fi

# First, wait for the PostgreSQL port to be available
echo "Waiting for PostgreSQL to be available at ${POSTGRES_HOST}:${POSTGRES_PORT}..."
wait-for-it "${POSTGRES_HOST}:${POSTGRES_PORT}" -t 30

echo "PostgreSQL port is open, verifying database is ready..."

# Now verify the database is actually ready by attempting to connect
# Using Python since we have Django and psycopg2 available
python << END
import sys
import time
import psycopg

max_attempts = 30
attempt = 0

while attempt < max_attempts:
    try:
        conn = psycopg.connect(
            dbname="${POSTGRES_DB}",
            user="${POSTGRES_USER}",
            password="${POSTGRES_PASSWORD}",
            host="${POSTGRES_HOST}",
            port="${POSTGRES_PORT}",
            connect_timeout=5
        )
        conn.close()
        print("PostgreSQL is ready and accepting connections!", file=sys.stderr)
        sys.exit(0)
    except psycopg.OperationalError as e:
        attempt += 1
        print(f"PostgreSQL not ready yet (attempt {attempt}/{max_attempts}): {e}", file=sys.stderr)
        if attempt < max_attempts:
            time.sleep(1)
        else:
            print("Failed to connect to PostgreSQL after maximum attempts", file=sys.stderr)
            sys.exit(1)
END

# Execute the main command
exec "$@"

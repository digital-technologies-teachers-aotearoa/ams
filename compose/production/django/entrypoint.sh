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
# Using Python since we have Django and psycopg available
python << 'END'
import sys
import time
import os

max_attempts = 30
attempt = 0

# Get connection parameters from environment
db_params = {
    "dbname": os.environ.get("POSTGRES_DB"),
    "user": os.environ.get("POSTGRES_USER"),
    "password": os.environ.get("POSTGRES_PASSWORD"),
    "host": os.environ.get("POSTGRES_HOST"),
    "port": os.environ.get("POSTGRES_PORT"),
    "connect_timeout": 5
}

while attempt < max_attempts:
    try:
        import psycopg
        conn = psycopg.connect(**db_params)
        conn.close()
        print("PostgreSQL is ready and accepting connections!", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        attempt += 1
        # Log error without exposing sensitive details
        error_type = type(e).__name__
        print(f"PostgreSQL not ready yet (attempt {attempt}/{max_attempts}): {error_type}", file=sys.stderr)
        if attempt < max_attempts:
            time.sleep(1)
        else:
            print(f"Failed to connect to PostgreSQL after maximum attempts: {error_type}", file=sys.stderr)
            sys.exit(1)
END

# Execute the main command
exec "$@"

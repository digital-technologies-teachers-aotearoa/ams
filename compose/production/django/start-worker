#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

echo "[START-WORKER] Starting Django-Q cluster..."
exec /usr/local/bin/python /app/manage.py qcluster

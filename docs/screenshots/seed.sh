#!/usr/bin/env bash
# Flushes the database, rebuilds a clean skeleton site (no sample_data fake
# content -- a real new client's site is empty, not full of demo events and
# articles), and starts the Django dev server. The demo organisation name is
# set later, by the screenshot suite itself (docs/screenshots/run.mjs), as
# part of capturing Tutorial 2's own "enter your association's name" step --
# not by this script. Everything else the suite needs, short of an
# already-rebuilt `node` image (see docs-conventions.md).
#
# Run from the repo root: ./docs/screenshots/seed.sh (or `just docs-seed`).

set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../.."

echo "Applying migrations..."
docker compose run --rm django python manage.py migrate

echo "Flushing the database..."
docker compose run --rm django python manage.py flush --noinput

# manage.py flush truncates data without replaying migrations, which deletes
# Wagtail's root Page/Collection/default Locale (created by data migrations
# inside the wagtail package itself) without restoring them. Without this,
# setup_cms fails silently ("Root page not found. Run migrations first.").
echo "Restoring Wagtail's root page and collection..."
docker compose run --rm django python manage.py ensure_wagtail_root

echo "Setting up CMS sites and home pages..."
docker compose run --rm django python manage.py setup_cms

echo "Creating the admin account..."
docker compose run --rm django python manage.py create_sample_admin

echo "Starting the Django dev server..."
docker compose exec -d django python manage.py runserver 0.0.0.0:8000

echo "Waiting for it to respond..."
for _ in $(seq 1 30); do
  if docker compose exec -T django python -c "
import sys, urllib.request
try:
    urllib.request.urlopen('http://localhost:8000/', timeout=2)
except Exception:
    sys.exit(1)
" > /dev/null 2>&1; then
    echo "Ready."
    exit 0
  fi
  sleep 1
done

echo "Server did not respond within 30s." >&2
exit 1

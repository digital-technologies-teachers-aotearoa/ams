#!/usr/bin/env bash
# Flushes the database, rebuilds a clean skeleton site (no sample_data fake
# content -- a real new client's site is empty, not full of demo events and
# articles), sets the demo organisation name, and starts the Django dev
# server. Everything the screenshot suite (docs/screenshots/run.mjs) needs,
# short of an already-rebuilt `node` image (see docs-conventions.md).
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

echo "Setting the demo organisation name..."
docker compose run --rm django python manage.py shell -c "
from wagtail.models import Site
from ams.cms.models import AssociationSettings
for site in Site.objects.all():
    s = AssociationSettings.for_site(site)
    s.association_short_name = 'Mathematics Teachers Association'
    s.association_long_name = 'Mathematics Teachers Association'
    s.save()
"

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

#!/usr/bin/env bash
# Seeds a database for the marketing screenshots on features.md -- a
# DIFFERENT seed from seed.sh, which deliberately builds an empty skeleton
# site. Marketing screenshots are the opposite: they need `sample_data`-style
# fixture content (dozens of events/resources, a fully-blocked homepage, a
# multi-period billing history) so the page looks like a mature, active
# association rather than a fresh install. See docs-conventions.md's
# marketing screenshots section for the full rationale.
#
# Run from the repo root: ./docs/screenshots/seed-marketing.sh
# Then: docker-compose exec node npm run docs:screenshots -- marketing
#
# Do not run this before regenerating the *rest* of the suite -- reseed with
# seed.sh again first, since this leaves the database in a populated state
# the tutorial screenshots' plain-skeleton assumptions don't expect.

set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../.."

echo "Applying migrations..."
docker compose run --rm django python manage.py migrate

echo "Flushing the database..."
docker compose run --rm django python manage.py flush --noinput

echo "Restoring Wagtail's root page and collection..."
docker compose run --rm django python manage.py ensure_wagtail_root

echo "Setting up CMS sites and home pages..."
docker compose run --rm django python manage.py setup_cms

echo "Creating the admin account..."
docker compose run --rm django python manage.py create_sample_admin

echo "Creating sample events (spread across several NZ regions, for map pins)..."
docker compose run --rm django python manage.py create_sample_events

echo "Creating sample resources (well over ten)..."
docker compose run --rm django python manage.py create_sample_resources

echo "Creating sample CMS content (every StreamField block type, on the home page)..."
docker compose run --rm django python manage.py create_sample_cms_content

echo "Creating the billing renewal-history fixture (past/current/future memberships)..."
docker compose exec -T django python manage.py shell < docs/screenshots/fixtures/marketing_billing_history.py

echo "Creating mock forum activity in Discourse (permanent -- see the fixture's own comment)..."
docker compose cp docs/screenshots/fixtures/marketing_forum_content.rb discourse:/tmp/marketing_forum_content.rb
docker compose exec discourse bash -lc 'cd /var/www/discourse && bin/rails runner /tmp/marketing_forum_content.rb'

echo "Starting the Django dev server..."
docker compose exec -d django python manage.py runserver 0.0.0.0:8000 || true

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

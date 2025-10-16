#!/usr/bin/env bash
set -eo pipefail

# run-init.sh - wait for app, ensure safe git dir, run pending migrations once, then run rails runner init script.
# Mounted into the container and executed by the discourse_init service.

echo "run-init.sh starting..."

# Make Git accept the repo ownership (fixes 'detected dubious ownership' error)
git config --global --add safe.directory /var/www/discourse || true
echo "Added /var/www/discourse to git safe.directory"

# Wait until Rails app can talk to DB (retry loop)
tries=0
until bundle exec rails runner -e production 'puts "db ok"' > /dev/null 2>&1 || [ $tries -gt 120 ]; do
  tries=$((tries+1))
  echo "waiting for discourse to be ready... ($tries)"
  sleep 2
done

if [ $tries -gt 120 ]; then
  echo "Timeout waiting for DB/app readiness"
  exit 1
fi

# Run migrations if any pending. This is idempotent.
echo "Running database migrations (idempotent)..."
bundle exec rake db:migrate RAILS_ENV=production >/dev/null 2>&1 || {
  echo "Warning: rake db:migrate returned non-zero; printing last 80 lines"
  bundle exec rake db:migrate RAILS_ENV=production || true
}

echo "Running discourse-init.rb via rails runner..."
bundle exec rails runner -e production /usr/local/bin/discourse-init.rb

echo "run-init.sh finished."

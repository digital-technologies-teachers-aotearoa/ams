#!/bin/bash
# Configure discourse

set -o errexit -o nounset

docker_compose() {
    COMPOSEFILES="-f ../docker-compose.yml -f ../docker-compose.test.yml"
    command docker-compose $COMPOSEFILES "$@"
}

discourse_psql() {
    docker_compose exec -T --user postgres discourse-data psql "$@"
}

discourse_setting() {
    docker_compose exec -T --workdir '/var/www/discourse' discourse bundle exec rails runner "$@"
}

docker_compose up -d discourse

discourse_psql -c "ALTER USER discourse WITH PASSWORD '${DISCOURSE_DB_PASSWORD}'"
discourse_psql -d discourse -c "GRANT ALL PRIVILEGES ON DATABASE discourse TO discourse"

docker_compose exec -T discourse git config --global --add safe.directory /var/www/discourse
docker_compose exec -T discourse chown -R discourse:www-data /shared/uploads
docker_compose exec -T --workdir '/var/www/discourse' discourse bundle exec rake db:migrate

discourse_setting "SiteSetting.set('content_security_policy_script_src', '${DISCOURSE_HOSTNAME}')"
discourse_setting "SiteSetting.set('discourse_connect_allowed_redirect_domains', '${APPLICATION_WEB_HOST}')"
discourse_setting "SiteSetting.set('discourse_connect_url', 'http://${APPLICATION_WEB_HOST}/forum/sso')"
discourse_setting "SiteSetting.set('discourse_connect_secret', '${DISCOURSE_CONNECT_SECRET}')"
discourse_setting "SiteSetting.set('enable_discourse_connect', true)"
discourse_setting "SiteSetting.set('auth_overrides_name', true)"
discourse_setting "SiteSetting.set('auth_overrides_username', true)"
discourse_setting "SiteSetting.set('logout_redirect', 'http://${APPLICATION_WEB_HOST}/users/logout')"

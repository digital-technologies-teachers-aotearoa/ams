MAKEFLAGS := --warn-undefined-variables
.SHELLFLAGS := -o nounset -c

# Add .env to environment
include .env
export $(shell sed 's/=.*//' .env)

.PHONY: developer
developer:
	git config --local core.hooksPath 'git-hooks'
	./docker_compose down
	./docker_compose build backend
	./docker_compose build db
	./docker_compose build nginx
	./docker_compose up -d db
	./wait-for-db.bash
	./docker_compose exec -T db dropdb --if-exists --username=postgres "$(APPLICATION_DB_NAME)"
	./docker_compose exec -T db createdb --username=postgres "$(APPLICATION_DB_NAME)"
	./docker_compose run -T --rm --entrypoint="poetry install" backend
	./docker_compose run -T --rm --entrypoint="poetry run ./manage.py migrate" backend
	./docker_compose run -T --rm --entrypoint="poetry run ./manage.py loaddata membership_options organisation_types" backend
	./docker_compose run -T --rm --entrypoint="poetry run ./manage.py createsuperuser --noinput" backend

.PHONY: db-shell
db-shell:
	./docker_compose run --rm --entrypoint="psql -h db -d $(APPLICATION_DB_NAME) --username=postgres" backend

.PHONY: backend-shell
backend-shell:
	./docker_compose exec -e SHELL=bash backend poetry shell

.PHONY: backend-migrate
backend-migrate:
	./docker_compose run -T --rm --entrypoint="poetry run ./manage.py migrate" backend

.PHONY: backend-make-migrations
backend-make-migrations:
	./docker_compose run -T --rm --entrypoint="poetry run ./manage.py makemigrations" backend

.PHONY: backend-check-migrations
backend-check-migrations:
	./docker_compose run -T --rm --entrypoint="poetry run ./manage.py makemigrations --dry-run" backend
	./docker_compose run -T --rm --entrypoint="poetry run ./manage.py makemigrations --check" backend

.PHONY: backend-reload-server
backend-reload-server:
	./docker_compose exec -T backend pkill -HUP gunicorn

.PHONY: translations
translations:
	./docker_compose run -T --rm --entrypoint="mkdir locale && poetry run ./manage.py makemessages --locale=mi" backend

.PHONY: compile-translations
compile-translations:
	./docker_compose run -T --rm --entrypoint="poetry run ./manage.py compilemessages --locale=mi" backend

.PHONY: test-backend
test-backend:
	./docker_compose run -T --rm --entrypoint="poetry run pytest $(TESTS)" backend

.PHONY: test-backend-reuse-db
test-backend-reuse-db:
	./docker_compose run -T --rm --entrypoint="poetry run pytest --reuse-db $(TESTS)" backend

.PHONY: lint-python
lint-python:
	./docker_compose run --rm --no-deps --entrypoint="poetry run ./lint-python.bash" backend

.PHONY: format-python
format-python:
	./docker_compose run --rm --no-deps --entrypoint="poetry run ./format-python.bash" backend

.PHONY: start
start:
	./docker_compose up -d

.PHONY: stop
stop:
	./docker_compose down

.PHONY: update-theme
update-theme:
	./update-theme.bash

# Discourse related targets
.PHONY: discourse-install
discourse-install: discourse-set-db-permisions discourse-build-app

.PHONY: discourse-set-db-permision
discourse-set-db-permisions: discourse-start-only-data
	./docker_compose exec -T --user postgres discourse-data psql -c "alter user discourse with password '${DISCOURSE_DB_PASSWORD}'"
	./docker_compose exec -T --user postgres discourse-data psql -d discourse -c "grant all privileges on database discourse to discourse"

.PHONY: discourse-build-app
discourse-build-app: discourse-start
	./docker_compose exec -T discourse git config --global --add safe.directory /var/www/discourse
	./docker_compose exec -T discourse chown -R discourse:www-data /shared/uploads
	./docker_compose exec -T --workdir '/var/www/discourse' discourse bundle exec rake db:migrate
	./docker_compose exec -T --workdir '/var/www/discourse' discourse bundle exec rails runner "SiteSetting.set('content_security_policy_script_src', '${DISCOURSE_HOSTNAME}')"
	./docker_compose exec -T --workdir '/var/www/discourse' discourse bundle exec rails runner "SiteSetting.set('discourse_connect_allowed_redirect_domains', '${APPLICATION_WEB_HOST}')"
	./docker_compose exec -T --workdir '/var/www/discourse' discourse bundle exec rails runner "SiteSetting.set('discourse_connect_url', 'http://${APPLICATION_WEB_HOST}/users/discourse/sso')"
	./docker_compose exec -T --workdir '/var/www/discourse' discourse bundle exec rails runner "SiteSetting.set('discourse_connect_secret', '${DISCOURSE_CONNECT_SECRET}')"
	./docker_compose exec -T --workdir '/var/www/discourse' discourse bundle exec rails runner "SiteSetting.set('enable_discourse_connect', true)"

.PHONY: discourse-migrate
discourse-migrate:
	./docker_compose up -d discourse --no-recreate
	./docker_compose exec -T --workdir '/var/www/discourse' discourse bundle exec rake db:migrate

.PHONY: discourse-recreate-db
discourse-recreate-db: discourse-start-only-data
	./docker_compose exec -T --user postgres discourse-data dropdb --if-exists --username=postgres "discourse"
	./docker_compose exec -T --user postgres discourse-data createdb --username=postgres "discourse"

.PHONY: discourse-create-admin
discourse-create-admin: discourse-start
	./docker_compose exec -e SHELL=bash discourse rake admin:create
	
.PHONY: discourse-start
discourse-start:
	./docker_compose up -d discourse

.PHONY: discourse-start-only-data
discourse-start-only-data:
	./docker_compose stop discourse
	./docker_compose up -d discourse-data --no-recreate

.PHONY: discourse-stop
discourse-stop:
	./docker_compose stop discourse discourse-data

.PHONY: discourse-rails-shell
discourse-rails-shell:
	./docker_compose up -d discourse
	./docker_compose exec -e SHELL=bash --workdir '/var/www/discourse' discourse bundle exec rails c

.PHONY: discourse-db-shell
discourse-db-shell:
	./docker_compose up -d discourse-data
	./docker_compose exec -e SHELL=bash --user postgres discourse-data psql -d discourse --username=postgres

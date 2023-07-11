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
	./docker_compose run -T --rm --entrypoint="poetry run ./manage.py loaddata membership_options" backend
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


.PHONY: backend-reload-server
backend-reload-server:
	./docker_compose exec -T backend pkill -HUP gunicorn

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
	./docker_compose up -d nginx

.PHONY: stop
stop:
	./docker_compose down
MAKEFLAGS := --warn-undefined-variables
.SHELLFLAGS := -o nounset -c

# Add .env to environment
include .env
export $(shell sed 's/=.*//' .env)

.PHONY: developer
developer:
	git config --local core.hooksPath 'git-hooks'
	./docker_compose build backend
	./docker_compose build db
	./docker_compose build nginx
	./docker_compose up -d db
	./wait-for-db.bash
	./docker_compose exec -T db dropdb --if-exists --username=postgres "$(APPLICATION_DB_NAME)"
	./docker_compose exec -T db createdb --username=postgres "$(APPLICATION_DB_NAME)"
	./docker_compose run -T --rm --entrypoint="poetry install" backend
	./docker_compose run -T --rm --entrypoint="poetry run ./manage.py migrate" backend

.PHONY: db-shell
db-shell:
	./docker_compose run --rm --entrypoint="psql -h db -d $(APPLICATION_DB_NAME) --username=postgres" backend

.PHONY: backend-shell
backend-shell:
	./docker_compose exec -e SHELL=bash backend poetry shell

.PHONY: backend-reload-server
backend-reload-server:
	./docker_compose exec -T backend pkill -HUP gunicorn

.PHONY: start
start:
	./docker_compose up -d nginx

.PHONY: stop
stop:
	./docker_compose down
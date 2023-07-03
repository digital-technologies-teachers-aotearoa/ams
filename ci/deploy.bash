#!/bin/bash

# Configure compose files for the environment.
COMPOSEFILES="-f ../docker-compose.yml -f ../docker-compose.test.yml"

# Import Environment vars
ENVFILE="../.env"
if [ -f $ENVFILE ]
then
  export $(cat $ENVFILE | xargs)
fi

# Bring up the DB
docker-compose $COMPOSEFILES up -d db
until docker-compose exec -T db pg_isready -U postgres; do
    echo "waiting for database to be ready"
    sleep 1
done

# Set up the Database
docker-compose exec -T db dropdb --if-exists --username=postgres $APPLICATION_DB_NAME
docker-compose exec -T db createdb --username=postgres $APPLICATION_DB_NAME
docker-compose exec -T db psql -U postgres -c "CREATE ROLE ${APPLICATION_DB_USER} WITH LOGIN ENCRYPTED PASSWORD '${APPLICATION_DB_PASSWORD}';"
docker-compose exec -T db psql -U postgres -c "ALTER DATABASE ${APPLICATION_DB_NAME} OWNER TO ${APPLICATION_DB_USER};"

# Bring up the rest of the stack and configure the backend.
docker-compose $COMPOSEFILES up -d

docker-compose $COMPOSEFILES run -T --rm --entrypoint="poetry run ./manage.py migrate" backend
docker-compose $COMPOSEFILES run -T --rm --entrypoint="poetry run ./manage.py createsuperuser --noinput" backend
docker-compose $COMPOSEFILES run -T --rm --entrypoint="poetry run ./manage.py collectstatic --noinput" backend

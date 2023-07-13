#!/bin/bash

# Configure compose files for the environment.
COMPOSEFILES="-f ../docker-compose.yml -f ../docker-compose.test.yml"

# Import Environment vars
ENVFILE="../.env"
if [ -f $ENVFILE ]
then
  export $(cat $ENVFILE | xargs)
fi

RECREATE_DB="${RECREATE_DB:-0}"

if [ "$RECREATE_DB" -eq "1" ]
then
  # Remove named volumes including database volume
  docker-compose down -v
fi

# Bring up the DB
docker-compose $COMPOSEFILES up -d db
until docker-compose exec -T db pg_isready -U postgres; do
    echo "Waiting for database to be ready"
    sleep 1
done

if [ "$RECREATE_DB" -eq "1" ]
then
  # Recreate the database
  echo "Recreating database"
  docker-compose exec -T db dropdb --if-exists --username=postgres $APPLICATION_DB_NAME
  docker-compose exec -T db createdb --username=postgres $APPLICATION_DB_NAME
  docker-compose exec -T db psql -U postgres -c "CREATE ROLE ${APPLICATION_DB_USER} WITH LOGIN ENCRYPTED PASSWORD '${APPLICATION_DB_PASSWORD}';"
  docker-compose exec -T db psql -U postgres -c "ALTER DATABASE ${APPLICATION_DB_NAME} OWNER TO ${APPLICATION_DB_USER};"
fi

docker-compose $COMPOSEFILES run -T --rm --entrypoint="poetry run ./manage.py migrate" backend
docker-compose $COMPOSEFILES run -T --rm --entrypoint="poetry run ./manage.py collectstatic --noinput" backend

if [ "$RECREATE_DB" -eq "1" ]
then
  # Load fixtures
  docker-compose $COMPOSEFILES run -T --rm --entrypoint="poetry run ./manage.py loaddata membership_options" backend

  # Create superuser
  docker-compose $COMPOSEFILES run -T --rm --entrypoint="poetry run ./manage.py createsuperuser --noinput" backend
fi

# Bring up the rest of the stack
docker-compose $COMPOSEFILES up -d

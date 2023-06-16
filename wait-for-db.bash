#!/bin/bash

until ./docker_compose exec -T db pg_isready -U postgres; do
    echo "waiting for database to be ready"
    sleep 1
done

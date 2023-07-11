# AMS

## Development environment setup

### Dependencies

To run the developer environment you need to install [Docker with the docker compose plugin](https://docs.docker.com/engine/install/ubuntu/).

### Getting started

1. Copy `.env.example` to `.env` and customize it to your liking.

1. Create the development environment by running `make developer`.

After this is finished you can run `make start` to bring up application. If successful you should be able to go to http://localhost:1800.

### Makefile commands

Run the backend tests:

    make test-backend

Run the backend tests, reusing an existing test database (faster):

    make test-backend-reuse-db

Python lint check:

    make lint-python

Format python code:

    make format-python

Open psql shell on the database:

    make db-shell

Open a poetry shell on the backend:

    make backend-shell

Run django migrations:

    make backend-migrate

Reload the backend server without restarting it:

    make backend-reload-server

Bring down the application:

    make stop

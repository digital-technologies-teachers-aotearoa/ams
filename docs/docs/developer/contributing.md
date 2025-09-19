# Contributing

The repository has been setup for use with Dev Containers with Visual Studio Code.
It is possible to develop the project locally, but we recommend using Dev Containers for a simplified and consistent development experience.

## Using Dev Containers

### Requirements

- Docker & Docker Compose
    - The Docker Desktop application includes both of these.

### Setup

After cloning the repository to your machine:

1. Start the Docker containers using Docker Compose: `docker compose up -d`.
    - The first time this runs, it may take some time to build the required images.
    - A [justfile](https://github.com/casey/just) is provided to shortcut commands, use `just up`.
2. Open the repository in Visual Studio Code and a prompt will appear stating a Dev Container configuration is available. Click 'Reopen in Container'.
    - If this prompt does not appear, you can also trigger the command from the Command Palette: 'Dev Containers: Reopen in Container'.

Visual Studio should then reopen within the `django` container.
All required dependencies for Python will be already installed.

### Usage

To run the Django web server, run `python manage.py runserver 0.0.0.0:8000` or use the preset alias `runserver`.
Creating an additional terminal window can be useful for running other commands such as `makemigrations` or `migrate`.

The following URLs should then be available:

- [Django website - `localhost:3000`](http://localhost:3000) (includes BrowserSync for hot reloading)
- [BrowserSync UI - `localhost:3001`](http://localhost:3001)
- [Documentation - `localhost:8001`](http://localhost:8001)
- [Local email server - `localhost:8025`](http://localhost:8025)

Additionally, the database will be available on `localhost:5432`.

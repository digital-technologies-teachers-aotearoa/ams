# Contributing

The repository has been setup for use with Dev Containers with Visual Studio Code.
It is possible to develop the project locally, but we recommend using Dev Containers for a simplified and consistent development experience.

## Using Dev Containers

### Requirements

- Docker & Docker Compose
    - The Docker Desktop application includes both of these.

### Setup

After cloning the repository to your machine:

1.
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

## Local Development Guide

### Common Commands

- Start the server:

    ```bash
    python manage.py runserver 0.0.0.0:8000
    ```

    - If you are using Dev Containers, an alias is preset for you:

        ```bash
        runserver
        ```

- Load sample data for development:

    ```bash
    python manage.py sample_data
    ```

- Run tests and coverage:

    ```bash
    pytest
    coverage run -m pytest && coverage html
    ```

- Type checks:

    ```bash
    mypy ams
    ```

### Justfile Shortcuts

The repository includes a `justfile` with common tasks.
This is useful for starting or stopping the containers from the host machine.

### Database & Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Environment Settings

- Environment values are loaded from `.envs/.local/` files.
- Django settings files live in `config/settings/` (`local.py`, `production.py`, `test.py`).

#### Optional Private Settings

For optional features like billing integrations, you can create a `django-private.ini` file in `.envs/.local/`:

1. Copy the example file:

    ```bash
    cp .envs/.local/django-private-example.ini .envs/.local/django-private.ini
    ```

2. Update the values in `django-private.ini` with your actual credentials.

The `django-private.ini` file supports the following optional settings:

- **Billing Service Configuration:**
    - `AMS_BILLING_SERVICE_CLASS` - The billing service provider class (e.g., `"ams.billing.providers.xero.XeroBillingService"`)

- **Xero Integration** (if using Xero as billing provider):
    - `XERO_CLIENT_ID` - Your Xero OAuth2 client ID
    - `XERO_CLIENT_SECRET` - Your Xero OAuth2 client secret
    - `XERO_TENANT_ID` - Your Xero tenant/organization ID
    - `XERO_WEBHOOK_KEY` - Webhook signing key for Xero webhooks
    - `XERO_ACCOUNT_CODE` - Default account code for invoices (e.g., `"200"`)
    - `XERO_AMOUNT_TYPE` - Tax amount type: `"INCLUSIVE"` or `"EXCLUSIVE"`
    - `XERO_CURRENCY_CODE` - Currency code for invoices (e.g., `"NZD"`)

- **Local Development:**
    - `NGROK_HOST` - Your ngrok tunnel URL for webhook testing (e.g., `"your-subdomain.ngrok-free.dev"`)

**Note:** The `django-private.ini` file is gitignored and should never be committed to version control as it contains sensitive credentials.

### Coding Conventions

- Keep changes focused; update docs for new features.
- Write tests for new functionality and ensure coverage.
- Follow Django app structure (`models.py`, `views.py`, `urls.py`, `tests/`).

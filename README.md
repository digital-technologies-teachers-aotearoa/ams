# AMS

## Development environment setup

### Dependencies

To run the developer environment you need to install [Docker with the docker compose plugin](https://docs.docker.com/engine/install/ubuntu/).

### Getting started

1. Copy `.env.example` to `.env` and customize it to your liking.

1. Edit your /etc/hosts file and add additional aliases `ams.local` and `discourse.local` for 127.0.0.1. E.g:

```
127.0.0.1       localhost ams.local discourse.local
```

1. Create the development environment by running `make developer`.

After this is finished you can run `make start` to bring up application. If successful you should be able to go to http://ams.local.

Additional setup instructions:

1. [Discourse setup](#discourse-setup) instructions.
1. [Billing service setup](#billing-service-setup) instructions.

### Stylesheet editing

For instructions on editing the main stylesheet see [frontend/README.md](frontend/README.md).

### Makefile commands

Run the backend tests:

    make test-backend

Run the backend tests with dtta settings:

    make test-dtta-backend

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

Update the main theme and styles from the frontend/ folder:

    make update-theme

Make translations:

    make translations

Compile translations:

    make compile-translations

Bring down the application:

    make stop

## Discourse setup

### Overview

Discourse images are built outside the AMS project using the Discourse Docker launcher build process.  See: https://github.com/discourse/discourse_docker

In short, the launcher build process takes the upstream base image and "bootstraps" a bunch of additional, before commiting the final result in the final distributable image - which we use in AMS.

TODO: add link to our Discourse local build repo when it is ready.

There are 2 containers:

1. `discourse` : The Discourse Ruby on Rails app itself, and assorted dependencies.
2. `discourse-data` : A separate container providing both Postgres and Redis data stores for the Discourse application.  

_Note: We will probably replace the discourse-data container in due time with one of our own - certainly for production.  The Discourse launcher built one is convenient for now in initial development however._

### Getting started

To run Discourse locall you must pull the docker image from Harbor

1. Get added to the dtta project docker repo at https://harbor.catalyst.net.nz/

1. Log into docker.catalyst.net.nz with your harbor username and CLI secret: `docker login docker.catalyst.net.nz`

### API

To complete the setup you need to configure DISCOURSE_API_KEY and DISCOURSE_API_USERNAME to enable syncing user changes such as name, email, profile image to Discourse.
You can create an API key interface using an account with admin access at http://discourse.local/admin/api/keys

Get Discourse running:

    make discourse-install

Create admin user:

    make discourse-create-admin

### Makefile commands

Start Discourse containers only:

    make discourse-start

Run migrations

    make discourse-migrate

Open psql shell on the Discourse database:

    make discourse-db-shell

Open a rails shell on the discourse app:

    make discourse-rails-shell

Recreate/Empty the Discourse database:

    make discourse-recreate-db

## Billing service setup

To use Xero as your billing service set `BILLING_SERVICE_CLASS` to `ams.xero.service.XeroBillingService`
in your `.env` file as well as the XERO prefixed variables.

To receive updates to your invoices you need to setup [Xero webhooks](https://developer.xero.com/documentation/guides/webhooks/creating-webhooks).

Configure Xero to call '/xero/webhooks/' on your website and set `XERO_WEBHOOK_KEY` to the key provided.

For testing purposes you can use a proxy service like [Ngrok](https://ngrok.com/) to pass Xero webhook events to your local development server.

Here is a tutorial on [how to setup Xero webhooks with Ngrok](https://ngrok.com/docs/integrations/xero/webhooks/). Command line:

    ngrok http --host-header ams.local http://ams.local

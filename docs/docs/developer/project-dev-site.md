# AMS project development site

This page is about the AMS project's own development site, hosted by DigitalOcean and used by contributors to preview `main`.
It is not about deploying your own AMS instance — see [Deployment](../hosting/deployment.md) for that, or the [worked example](../hosting/provisioning-runbook.md) if you're the provider standing up a client instance on the project's DigitalOcean stack.

## What it is

When the [GitHub Container Registry](https://github.com/digital-technologies-teachers-aotearoa/ams/pkgs/container/ams-django) image is built (on every push to `main`), it's automatically deployed to this development environment.
It's available at [django-rnnrj.ondigitalocean.app](https://django-rnnrj.ondigitalocean.app/).

## How it's managed

This site is managed by the [`.do/app.yaml`](https://github.com/digital-technologies-teachers-aotearoa/ams/blob/main/.do/app.yaml) configuration file in the repository root.
Deploying this file overrides any configuration made directly on the DigitalOcean website, so changes belong in the file, not made by hand in the DigitalOcean console.

All [secrets are stored within GitHub](https://github.com/digital-technologies-teachers-aotearoa/ams/settings/environments/9546005305/edit) and are available to the GitHub Actions workflow.
These secrets are passed through to the DigitalOcean deployment step, and rendered into the `.do/app.yaml` configuration file at deploy time.

`.do/app.yaml` runs AMS as a single `django` component (gunicorn only — see [Deployment: Container architecture](../hosting/deployment.md#container-architecture)) plus two jobs: a `job-deploy` **PRE_DEPLOY** job that runs `deploy_steps`, and a `fetch-invoice-updates` **SCHEDULED** job that runs `fetch_invoice_updates` for Xero every 15 minutes (see [Deployment: Scheduled tasks](../hosting/deployment.md#scheduled-tasks)).
It's a useful syntax reference for the DigitalOcean App Platform spec format, but it describes only this one site, not the environment-split (UAT/production) structure a client deployment uses — see the [worked example](../hosting/provisioning-runbook.md#2-server-setup-digitalocean-app-platform) for that.

# Deployment

Upon a push to the `main` branch, a Docker image is built and stored on [GitHub Container Registry](https://github.com/digital-technologies-teachers-aotearoa/ams/pkgs/container/ams-django).
By running this image, AMS can be deployed on any platform that supports Docker containers — for example [DigitalOcean](https://www.digitalocean.com/) App Platform, or a self-managed system such as [Kubernetes](https://kubernetes.io/).
This page describes what any deployment needs, independent of platform.

If you're the provider standing up a new client instance on the project's recommended stack (DigitalOcean, Postmark, Cloudflare), see the [Provisioning runbook](../hosting/provisioning-runbook.md) instead — it's deliberately opinionated about that stack and cross-links back here for the generic parts rather than repeating them.
For the AMS project's own development site (used by contributors, not client instances), see [AMS project development site](project-dev-site.md).

## Container architecture

AMS runs as a single container, running gunicorn only to serve HTTP requests — see `compose/production/django/start-web.sh` for the exact startup command.
There is no separate background worker process or task queue: scheduled/background work (currently just syncing Xero invoice updates) runs as a one-off invocation of a management command on whatever schedule your platform provides (e.g. a cron job or a scheduled-job feature), not a long-running worker.
See [Deployment steps](#deployment-steps) below for the management commands involved.

## Requirements

- PostgreSQL database.
- Media storage (storage buckets):
    - Requires Amazon S3, DigitalOcean Spaces, or [any other S3-compatible provider](https://django-storages.readthedocs.io/en/latest/backends/s3_compatible/index.html).
    - Additional details regarding media related environment variables can be found on [this settings page](https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings), matching settings by suffix (for example: `AWS_S3_ENDPOINT_URL` and `DJANGO_MEDIA_PUBLIC_ENDPOINT_URL` are equivalent).
    - Files uploaded have ACLs applied to them, so buckets currently don't require policies applied to them.
- Observability: an error-tracking sink and a log-ingestion sink — both required today (see [Hard requirements](#hard-requirements-today) below); currently configured for [Better Stack](https://betterstack.com/), which covers both.

## Container resources

**Memory requirements:**

Memory requirements depend on your deployment configuration:

- **Minimum:** 512MB RAM, suitable for low-traffic sites or development environments (limited request throughput).
- **Recommended (production):** 1GB RAM, with more gunicorn workers for better performance under load and headroom for traffic spikes.

**Worker configuration:**

The number of gunicorn workers is set with the `--workers` flag in `compose/production/django/start-web.sh`.
The current default is 2 workers.

To increase throughput on a container with more memory, edit that flag.

### Scaling options

For high-traffic deployments, consider:

1. Increasing container memory to 1GB+ and adding more gunicorn workers.
2. Horizontal scaling with multiple web containers behind a load balancer.

## Environment variables

The following environment variables are available, with some required for running AMS.

The client-decidable `AMS_*` settings — `AMS_ENABLED_LANGUAGES`, `AMS_EVENTS_ENABLED`, `AMS_RESOURCES_ENABLED`, `AMS_NOTIFY_STAFF_ORGANISATION_EVENTS`, `AMS_NOTIFY_STAFF_MEMBERSHIP_EVENTS`, and `AMS_REQUIRE_FREE_MEMBERSHIP_APPROVAL` — are documented once, in plain language, in the [settings glossary](../getting-started/settings-glossary.md), rather than repeated here.
An automated check (see [Documentation conventions](docs-conventions.md#settings-glossary-anti-drift-check)) fails the build if any of them end up duplicated in this table, so the two pages can't drift apart.

| Variable | Requirement | Example Value | Description |
|---|---|---|---|
| `SITE_DOMAIN` | ⚪ Optional | `ams.com` | The domain the website is hosted on. Defaults to `ams.com` — set this explicitly for any real deployment. |
| `SITE_PORT` | ⚪ Optional | `80` | The port number the website is accessible at |
| `POSTGRES_HOST` | 🔴 Required | `postgres` | The hostname of the PostgreSQL database server |
| `POSTGRES_PORT` | ⚪ Optional | `5432` | The port of the PostgreSQL database server |
| `POSTGRES_DB` | 🔴 Required | `ams` | The database name of the PostgreSQL database server |
| `POSTGRES_USER` | 🔴 Required | `username` | The name of the user to access the PostgreSQL server |
| `POSTGRES_PASSWORD` | 🔴 Required | `password` | The password of the user to access the PostgreSQL server |
| `DJANGO_SECRET_KEY` | 🔴 Required | `secret-key` | The Django secret key |
| `DJANGO_ADMIN_URL` | 🔴 Required | `admin/` | The URL for the Django admin |
| `DJANGO_ALLOWED_HOSTS` | ⚪ Optional | `*` | The allowed hosts for Django. Defaults to a value scoped to the AMS project's own site — set this explicitly for any real deployment, or Django will reject requests for your domain. |
| `DJANGO_EMAIL_ESP` | ⚪ Optional | `mailgun` | The email service provider to send transactional email through. One of `mailgun` (default), `postmark`, `mailtrap` |
| `MAILGUN_API_KEY` | 🔴 Required if `DJANGO_EMAIL_ESP=mailgun` | `redacted-api-key` | The API key for Mailgun |
| `MAILGUN_DOMAIN` | 🔴 Required if `DJANGO_EMAIL_ESP=mailgun` | `sandbox.mailgun.org` | The domain for Mailgun |
| `MAILGUN_API_URL` | ⚪ Optional | `https://api.mailgun.net/v3` | The API URL for Mailgun (EU accounts use the EU URL) |
| `POSTMARK_SERVER_TOKEN` | 🔴 Required if `DJANGO_EMAIL_ESP=postmark` | `redacted-server-token` | The server token for Postmark |
| `MAILTRAP_API_TOKEN` | 🔴 Required if `DJANGO_EMAIL_ESP=mailtrap` | `redacted-api-token` | The API token for Mailtrap |
| `MAILTRAP_SANDBOX_ID` | ⚪ Optional | `123456` | The Mailtrap sandbox/test inbox ID (live sending is used if unset) |
| `AMS_BILLING_SERVICE_CLASS` | ⚪ Optional | `ams.billing.providers.xero.XeroBillingService` | The provider to use for billing. Defaults to Xero — see [Hard requirements](#hard-requirements-today) below for why this makes Xero a de facto requirement today. |
| `AMS_BILLING_EMAIL_WHITELIST_REGEX` | ⚪ Optional | `@domain.com` | Allowed emails to send billing emails to (sends all emails when unset) |
| `XERO_CLIENT_ID` | 🔴 Required (see note below) | `redacted-client-id` | OAuth2 client ID from your Xero Custom Connection — see [Billing integration](billing.md) |
| `XERO_CLIENT_SECRET` | 🔴 Required (see note below) | `redacted-client-secret` | OAuth2 client secret from your Xero Custom Connection |
| `XERO_TENANT_ID` | 🔴 Required (see note below) | `redacted-tenant-id` | Xero organisation/tenant ID |
| `XERO_WEBHOOK_KEY` | 🔴 Required (see note below) | `redacted-webhook-key` | Webhook signing key for validating Xero webhook requests |
| `XERO_ACCOUNT_CODE` | 🔴 Required (see note below) | `200` | Default account code for invoice line items |
| `XERO_AMOUNT_TYPE` | 🔴 Required (see note below) | `INCLUSIVE` | Tax calculation type: `INCLUSIVE` or `EXCLUSIVE` |
| `XERO_CURRENCY_CODE` | 🔴 Required (see note below) | `NZD` | Currency code for invoices |
| `DISCOURSE_REDIRECT_DOMAIN` | ⚪ Optional | `https://forum.ams.com` | The domain of the forum to send users to. Only needed if the forum is enabled — leave unset otherwise. |
| `DISCOURSE_CONNECT_SECRET` | ⚪ Optional | `redacted-secret` | The secret used in SSO Discourse communication. Only needed if the forum is enabled — leave unset otherwise. |
| `DJANGO_MEDIA_PUBLIC_BUCKET_NAME` | 🔴 Required | `public-media` | The name of the bucket used for public media storage |
| `DJANGO_MEDIA_PUBLIC_ENDPOINT_URL` | 🔴 Required | `https://s3.example-provider.com` | Custom URL to use when connecting to public media storage, including scheme |
| `DJANGO_MEDIA_PUBLIC_ACCESS_KEY` | 🔴 Required | `G789DFGH349VH` | Access key used for updating the public media storage |
| `DJANGO_MEDIA_PUBLIC_SECRET_KEY` | 🔴 Required | `DSGF987DGF9D8` | Secret key used for updating the public media storage |
| `DJANGO_MEDIA_PUBLIC_REGION_NAME` | ⚪ Optional | `us-east-1` | Name of the region to use for public media storage |
| `DJANGO_MEDIA_PUBLIC_CUSTOM_DOMAIN` | ⚪ Optional | `https://s3.example-provider.com` | Custom URL to use when connecting to public media storage, including scheme |
| `DJANGO_MEDIA_PRIVATE_BUCKET_NAME` | 🔴 Required | `private-media` | The name of the bucket used for private media storage |
| `DJANGO_MEDIA_PRIVATE_ENDPOINT_URL` | 🔴 Required | `https://private-media.ams.com` | Custom URL to use when connecting to private media storage, including scheme |
| `DJANGO_MEDIA_PRIVATE_ACCESS_KEY` | 🔴 Required | `G789DFGH349VH` | Access key used for updating the private media storage |
| `DJANGO_MEDIA_PRIVATE_SECRET_KEY` | 🔴 Required | `DSGF987DGF9D8` | Secret key used for updating the private media storage |
| `DJANGO_MEDIA_PRIVATE_REGION_NAME` | ⚪ Optional | `us-east-1` | Name of the region to use for private media storage |
| `DJANGO_MEDIA_PRIVATE_CUSTOM_DOMAIN` | ⚪ Optional | `https://private-media.ams.com` | Custom URL to use when connecting to private media storage, including scheme |
| `DJANGO_WAGTAIL_AMS_ADMIN_HELPERS` | ⚪ Optional | `True` | Shows helper text within the Wagtail CMS admin |
| `DJANGO_LOG_LEVEL` | ⚪ Optional | `INFO` | Python logging level for production (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`). Defaults to `INFO` (or `DEBUG` if `DJANGO_DEBUG=True`). Also sets the default for `SENTRY_LOG_LEVEL` when that variable is not explicitly set. |
| `SENTRY_DSN` | 🔴 Required | `https://123@456.ingest.de.sentry.io/789` | The DSN value for Sentry observability |
| `SENTRY_LOG_LEVEL` | ⚪ Optional | `40` | The level to log at (default `20`) |
| `SENTRY_ENVIRONMENT` | ⚪ Optional | `dev` | The environment value for observability (default `production`) |
| `SENTRY_TRACES_SAMPLE_RATE` | ⚪ Optional | `1.0` | A float of the rate to sample at (default `0.0`) |
| `LOGTAIL_SOURCE_TOKEN` | 🔴 Required | `123456789abcdef` | The application token for Better Stack (Logtail) logging observability |
| `LOGTAIL_INGESTING_HOST` | 🔴 Required | `s123456.eu-nbg-2.betterstackdata.com` | The host for ingesting logs with Better Stack (Logtail) |

### Available values

#### `SENTRY_LOG_LEVEL`

- `50`: Critical
- `40`: Error
- `30`: Warning
- `20`: Info
- `10`: Debug
- `0`: Not set

### Hard requirements today

AMS is designed so opinionated stack choices belong in the provider's own runbook, not here — but a few things are, today, genuinely required by the code itself regardless of platform, so they're stated plainly rather than implied as free choices:

- **PostgreSQL** and an **S3-compatible object store** — the application won't start without database and media storage credentials.
- **Observability** — `config/settings/production.py` reads these with no default, so a deployment can't opt out of either piece today:
    - Error tracking (`SENTRY_DSN` and related settings) uses the [Sentry SDK](https://github.com/getsentry/sentry-python) protocol, not necessarily Sentry.io itself — any Sentry-DSN-compatible provider works (self-hosted Sentry, or a third party that implements the same protocol).
      `config/settings/production.py` currently points this at [Better Stack](https://betterstack.com/)'s own Sentry-compatible error tracking, per its own comment (`# Better Stack (uses Sentry SDK)`).
    - Log ingestion (`LOGTAIL_SOURCE_TOKEN`, `LOGTAIL_INGESTING_HOST`) uses Better Stack's own Logtail SDK (the `logtail-python` package) directly, so this one is specific to Better Stack rather than a portable protocol.
    - In practice, one Better Stack account covers both today — but the two settings are separate integration points, not inherently tied to the same vendor.
- **Xero** (`XERO_CLIENT_ID`, `XERO_CLIENT_SECRET`, `XERO_TENANT_ID`, `XERO_WEBHOOK_KEY`, `XERO_ACCOUNT_CODE`, `XERO_AMOUNT_TYPE`, `XERO_CURRENCY_CODE`) — this one is a known gap, not an intentional design choice: `AMS_BILLING_SERVICE_CLASS` (which selects the billing provider) has a default, but the seven `XERO_*` variables above it are read unconditionally in `config/settings/production.py`, with no default and no check of which billing service class is actually configured.
  This mirrors how `DJANGO_EMAIL_ESP` used to make Mailgun a hard requirement, before it became a pluggable choice — the same fix (gating `XERO_*` behind `AMS_BILLING_SERVICE_CLASS`, the way `DJANGO_EMAIL_ESP` gates `MAILGUN_*`/`POSTMARK_*`/`MAILTRAP_*`) hasn't landed yet for billing.
  Transactional email is no longer an example of a hard requirement: as of commit `0438752`, `DJANGO_EMAIL_ESP` makes it a pluggable choice of `mailgun`/`postmark`/`mailtrap` instead.

## Deployment steps

During the deployment, there is a Django management command `deploy_steps` that will perform the following steps:

1. Migrate the database.
2. Check required CMS pages are present.

## Scheduled tasks

AMS has no persistent background worker process — there's no task queue to run.
The one piece of scheduled work today is Xero invoice syncing: `python manage.py fetch_invoice_updates` should be run periodically (every 15 minutes in the provider's own stack) as a fallback for any Xero webhook that doesn't arrive.
Run it however your platform schedules one-off commands (a cron job, or a platform feature like DigitalOcean App Platform's scheduled jobs — see the [Provisioning runbook](../hosting/provisioning-runbook.md#2-server-setup-digitalocean-app-platform) for that specific setup) — it only applies if Xero billing is enabled.

## Email service providers

AMS sends transactional email through [Anymail](https://anymail.readthedocs.io/en/stable/), selected with `DJANGO_EMAIL_ESP`.
Three providers are supported:

- **Mailgun** (default) — after setting up a domain in Mailgun, two credentials are required: a Sending Key for the Django website, and an SMTP credential for the Discourse server (if the forum is enabled).
- **Postmark** — requires a Server API Token (`POSTMARK_SERVER_TOKEN`).
- **Mailtrap** — requires an API Token (`MAILTRAP_API_TOKEN`); mainly useful for testing, since it can sandbox sent mail instead of delivering it.

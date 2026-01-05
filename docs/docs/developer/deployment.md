# Deployment

Upon a push to the `main` branch, a Docker image is built and stored on [GitHub Container Registry](https://github.com/digital-technologies-teachers-aotearoa/ams/pkgs/container/ams-django).

## Development environment

When the Docker image is built, this image is automatically deployed to the development environment hosted on DigitalOcean.
The development environment is avaiable at [django-rnnrj.ondigitalocean.app](https://django-rnnrj.ondigitalocean.app/).

This website is managed by the `.do/app.yaml` configuration file, and this will override any configuration done on the DigitalOcean website.

All [secrets are stored within GitHub](https://github.com/digital-technologies-teachers-aotearoa/ams/settings/environments/9546005305/edit) and are available to the GitHub Actions workflow.
These secrets are then passed through to the DigitalOcean deployment step, and rendered into the `.do/app.yaml` configuration file.

## Production environment

By running an [AMS Docker image](https://ghcr.io/digital-technologies-teachers-aotearoa/ams-django), the software can be deployed in a production environment.
This can be run on any managed platform that supports Docker containers, such as [DigitalOcean](https://www.digitalocean.com/), or you can manage it yourself with a system such as [Kubernetes](https://kubernetes.io/).

### Requirements

- Postgres database
- Media storage (storage buckets)
    - Media storage requires Amazon S3, DigitalOcean Spaces, or [any other compatible providers listed here](https://django-storages.readthedocs.io/en/latest/backends/s3_compatible/index.html).
    - Additional details regarding media related environment variables can be found on [this settings page](https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings), matching settings by suffix (for example: `AWS_S3_ENDPOINT_URL` and `DJANGO_MEDIA_PUBLIC_ENDPOINT_URL` are equivalent).
    - Storage buckets should have policies applied to them to match expected behaviour by AMS.
      Default policies are provided within the [`compose/production/media-storage` directory](https://github.com/digital-technologies-teachers-aotearoa/ams/tree/main/compose/production/media-storage), with a [README providing additional information about these files](https://github.com/digital-technologies-teachers-aotearoa/ams/blob/main/compose/production/media-storage/README.md).

### Environment variables

The following environment variables are available, with some required for running AMS:

| Variable | Requirement | Example Value | Description |
|---|---|---|---|
| `SITE_DOMAIN` | 🔴 Required | `ams.com` | The domain the website is hosted on |
| `SITE_PORT` | ⚪ Optional | `80` | The port number the website is accessible at |
| `POSTGRES_HOST` | 🔴 Required | `postgres` | The hostname of the PostgreSQL database server |
| `POSTGRES_PORT` | 🔴 Required | `5432` | The port of the PostgreSQL database server |
| `POSTGRES_DB` | 🔴 Required | `ams` | The database name of the PostgreSQL database server |
| `POSTGRES_USER` | 🔴 Required | `username` | The name of the user to access the PostgreSQL server |
| `POSTGRES_PASSWORD` | 🔴 Required | `password` | The password of the user to access the PostgreSQL |
| `DJANGO_SECRET_KEY` | 🔴 Required | `secret-key` | The Django secret key |
| `DJANGO_ADMIN_URL` | 🔴 Required | `admin/` | The URL for the Django admin |
| `DJANGO_ALLOWED_HOSTS` | 🔴 Required | `*` | The allowed hosts for Django |
| `MAILGUN_API_KEY` | 🔴 Required | `redacted-api-key` | The API key for Mailgun |
| `MAILGUN_DOMAIN` | 🔴 Required | `sandbox.mailgun.org` | The domain for Mailgun |
| `MAILGUN_API_URL` | 🔴 Required | `https://api.mailgun.net` | The API URL for Mailgun |
| `SENTRY_DSN` | 🔴 Required | `https://123@456.ingest.de.sentry.io/789` | The DSN value for Sentry observability |
| `AMS_BILLING_SERVICE_CLASS` | 🔴 Required | `ams.billing.providers.xero.XeroBillingService` | The provider to use for billing |
| `AMS_BILLING_EMAIL_WHITELIST_REGEX` | ⚪ Optional | `@domain.com` | Allowed emails to send billing emails to (sends all emails when unset) |
| `DISCOURSE_REDIRECT_DOMAIN` | 🔴 Required | `https://forum.ams.com` | The domain of the forum to send users to |
| `DISCOURSE_CONNECT_SECRET` | 🔴 Required | `redacted-secret` | The secret used in SSO Discourse communication |
| `DJANGO_MEDIA_PUBLIC_BUCKET_NAME` | 🔴 Required | `public-media` | The name of the bucket used for public media storage |
| `DJANGO_MEDIA_PUBLIC_ENDPOINT_URL` | 🔴 Required | `https://syd1.digitaloceanspaces.com` | Custom URL to use when connecting to public media storage, including scheme |
| `DJANGO_MEDIA_PUBLIC_ACCESS_KEY` | 🔴 Required | `G789DFGH349VH` | Access key used for updating the public media storage |
| `DJANGO_MEDIA_PUBLIC_SECRET_KEY` | 🔴 Required | `DSGF987DGF9D8` | Secret key used for updating the public media storage |
| `DJANGO_MEDIA_PUBLIC_REGION_NAME` | ⚪ Optional | `syd1` | Name of the region to use  for public media storage |
| `DJANGO_MEDIA_PUBLIC_CUSTOM_DOMAIN` | ⚪ Optional | `https://syd1.digitaloceanspaces.com` | Custom URL to use when connecting to public media storage, including scheme. |
| `DJANGO_MEDIA_PUBLIC_BUCKET_NAME` | 🔴 Required | `public-media` | The name of the bucket used for public media storage |
| `DJANGO_MEDIA_PRIVATE_ENDPOINT_URL` | 🔴 Required | `https://private-media.ams.com` | Custom URL to use when connecting to private media storage, including scheme |
| `DJANGO_MEDIA_PRIVATE_ACCESS_KEY` | 🔴 Required | `G789DFGH349VH` | Access key used for updating the private media storage |
| `DJANGO_MEDIA_PRIVATE_SECRET_KEY` | 🔴 Required | `DSGF987DGF9D8` | Secret key used for updating the private media storage |
| `DJANGO_MEDIA_PRIVATE_REGION_NAME` | ⚪ Optional | `syd1` | Name of the region to use  for private media storage |
| `DJANGO_MEDIA_PRIVATE_CUSTOM_DOMAIN` | ⚪ Optional | `https://private-media.ams.com` | Custom URL to use when connecting to private media storage, including scheme. |
| `DJANGO_WAGTAIL_AMS_ADMIN_HELPERS` | ⚪ Optional | `True` | Shows helper text within the Wagtail CMS admin. |
| `AMS_NOTIFY_STAFF_ORGANISATION_EVENTS` | ⚪ Optional | `True` | Notifies staff of organisation creation events. |
| `AMS_NOTIFY_STAFF_MEMBERSHIP_EVENTS` | ⚪ Optional | `True` | Notifies staff of membership creation events. |
| `AMS_REQUIRE_FREE_MEMBERSHIP_APPROVAL` | ⚪ Optional | `False` | Require manual approval of free memberships. |

## Deployment steps

During the deployment, there is a Django management command `deploy_steps` that will perform the following steps:

1. Migrate the database.
2. Check required CMS pages are present.

## Services

The following provides details on services recommended for use with AMS.

### Mailgun

Using Mailgun for emails is officially supported by AMS.
After setting up a domain in Mailgun, there are two types of credentials required.

1. A 'Sending Key' for the Django website.
2. A 'SMTP credential' for the Discourse server.
